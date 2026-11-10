"""Local, serialized build jobs. Logs and artifacts survive browser disconnects."""
import json
import os
import re
import shutil
import subprocess
import threading
import uuid
import zipfile
from pathlib import Path

from .springboot_generator import SpringBootGenerator
from .flutter_generator import FlutterGenerator
from .postman_generator import PostmanGenerator


class BuildPipeline:
    def __init__(self, root):
        self.root = Path(root)
        self.lock = threading.RLock()
        self.active = None

    def directory(self, job_id):
        if not re.fullmatch(r'[a-f0-9]{32}', job_id):
            raise ValueError('Identificador de compilación inválido')
        return self.root / ('build_' + job_id)

    def status(self, job_id):
        directory = self.directory(job_id)
        with self.lock:
            status = json.loads((directory / 'status.json').read_text(encoding='utf-8'))
        if status['state'] == 'running' and self.active != job_id:
            status.update(state='interrupted', message='Servidor reiniciado. Inicia una nueva compilación.')
        log = directory / 'build.log'
        if log.exists():
            with log.open('rb') as stream:
                stream.seek(max(0, log.stat().st_size - 16000))
                status['log'] = stream.read().decode('utf-8', errors='replace')
        return status

    def _status(self, directory, **values):
        with self.lock:
            pending = directory / 'status.tmp'
            pending.write_text(json.dumps(values, ensure_ascii=False), encoding='utf-8')
            pending.replace(directory / 'status.json')

    def start(self, diagram, package):
        with self.lock:
            if self.active:
                raise RuntimeError('Ya hay una compilación activa: ' + self.active)
            for tool in ('flutter', 'mvn', 'java'):
                if not shutil.which(tool):
                    raise ValueError('Falta instalar o añadir al PATH: ' + tool)
            job_id = uuid.uuid4().hex
            directory = self.directory(job_id)
            directory.mkdir(parents=True)
            self.active = job_id
            self._status(directory, id=job_id, state='running', stage='Preparación', message='Preparando proyecto')
            threading.Thread(target=self._build, args=(job_id, diagram, package), daemon=True).start()
            return job_id

    def _run(self, command, directory, log, timeout=1800):
        # Commands and arguments are fixed by the server, never supplied by HTTP.
        options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
        with log.open('ab', buffering=0) as stream:
            stream.write(('\n$ ' + ' '.join(command) + '\n').encode())
            process = subprocess.Popen(command, cwd=directory, stdout=stream, stderr=subprocess.STDOUT, **options)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
                else:
                    process.kill()
                process.wait()
                raise RuntimeError('Tiempo máximo excedido; consulta el registro de compilación')
            if code:
                raise RuntimeError('Falló ' + Path(command[0]).name + '. Consulta el registro para ver la causa.')

    def _build(self, job_id, diagram, package):
        directory = self.directory(job_id)
        log = directory / 'build.log'
        def stage(name):
            self._status(directory, id=job_id, state='running', stage=name, message=name)
            with log.open('a', encoding='utf-8') as stream:
                stream.write('\n' + name + '\n')
        try:
            stage('Generando backend, Flutter y Postman')
            (directory / 'diagrama.json').write_text(json.dumps(diagram.to_dict(), ensure_ascii=False, indent=2), encoding='utf-8')
            SpringBootGenerator(diagram, base_package=package).generate_to_disk(str(directory / 'springboot'))
            FlutterGenerator(diagram, package_name=package,
                             api_base_url='http://127.0.0.1:8087/api').generate_to_disk(str(directory / 'flutter_app'))
            (directory / 'postman_collection.json').write_text(PostmanGenerator(diagram).generate_json(), encoding='utf-8')
            (directory / 'LEEME.txt').write_text(
                '1. Backend: desde springboot ejecuta mvn spring-boot:run -Dspring-boot.run.profiles=demo -Dspring-boot.run.arguments=--server.port=8087\n'
                '2. Instala aplicacion.apk. Por USB ejecuta adb reverse tcp:8087 tcp:8087.\n'
                '3. La app inicia en http://127.0.0.1:8087/api (USB). Puedes cambiarlo en Ajustes.\n'
                '4. Importa postman_collection.json en Postman y ejecuta la colección en orden.\n'
                '5. Para Wi-Fi inicia el backend con SERVER_ADDRESS=0.0.0.0 y usa la IP LAN del PC.\n'
                'La base demo persiste en springboot/data; el perfil normal usa PostgreSQL.\n'
                'La APK es de pruebas (firma debug). No se ha verificado automáticamente un teléfono físico.\n', encoding='utf-8')
            stage('Compilando y probando backend')
            self._run([shutil.which('mvn'), '-B', 'package'], directory / 'springboot', log)
            stage('Resolviendo dependencias Flutter')
            self._run([shutil.which('flutter'), 'pub', 'get'], directory / 'flutter_app', log, 600)
            stage('Probando interfaz Flutter')
            self._run([shutil.which('flutter'), 'test'], directory / 'flutter_app', log, 600)
            stage('Compilando APK Android (el registro muestra el progreso real)')
            self._run([shutil.which('flutter'), 'build', 'apk', '--debug'], directory / 'flutter_app', log)
            apk = directory / 'flutter_app/build/app/outputs/flutter-apk/app-debug.apk'
            if not apk.is_file():
                raise RuntimeError('Flutter terminó sin producir el APK esperado')
            shutil.copy2(apk, directory / 'aplicacion.apk')
            stage('Empaquetando entrega')
            with zipfile.ZipFile(directory / 'entrega.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                for file in directory.rglob('*'):
                    relative = file.relative_to(directory)
                    if not file.is_file() or any(p in {'build', '.gradle', '.dart_tool', 'target', 'data', '.idea', '.git'} for p in relative.parts):
                        continue
                    if file.name in {'entrega.zip', 'status.json', 'local.properties', 'build.log', 'status.tmp'}:
                        continue
                    archive.write(file, relative)
            self._status(directory, id=job_id, state='succeeded', stage='Completado', message='Backend y APK compilados. Listos para probar en el teléfono.')
        except Exception as exc:
            with log.open('a', encoding='utf-8') as stream:
                stream.write('\nERROR: ' + str(exc) + '\n')
            self._status(directory, id=job_id, state='failed', stage='Error', message=str(exc))
        finally:
            with self.lock:
                self.active = None
