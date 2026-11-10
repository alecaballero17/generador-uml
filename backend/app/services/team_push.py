"""Persisted Web Push subscriptions. Delivery never blocks diagram updates."""
import asyncio
import base64
import hashlib
import json
import logging
import os
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

log = logging.getLogger(__name__)


class TeamPush:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.database = self.directory / 'push.sqlite3'
        self.keyfile = self.directory / 'webpush-private.pem'
        self.tasks = set()
        self.pending = {}
        self.semaphore = asyncio.Semaphore(4)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS subscriptions(room TEXT, owner TEXT, endpoint TEXT, data TEXT, PRIMARY KEY(room,endpoint))')
            db.execute('CREATE TABLE IF NOT EXISTS native_subscriptions(room TEXT, owner TEXT, token TEXT, PRIMARY KEY(room,token))')

    def native_app(self):
        import firebase_admin
        try:
            return firebase_admin.get_app('uml-push')
        except ValueError:
            from firebase_admin import credentials
            # A deployed service normally keeps the credential as an encrypted
            # environment variable; local development may use the ignored file.
            # Supporting both avoids committing a private Firebase key.
            raw_credential = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
            if raw_credential:
                try:
                    service_account = json.loads(raw_credential)
                except json.JSONDecodeError as error:
                    raise ValueError('FIREBASE_SERVICE_ACCOUNT_JSON no contiene JSON válido') from error
                if not isinstance(service_account, dict):
                    raise ValueError('FIREBASE_SERVICE_ACCOUNT_JSON debe ser un objeto JSON')
                return firebase_admin.initialize_app(
                    credentials.Certificate(service_account), name='uml-push'
                )
            path = Path(os.environ.get('FIREBASE_SERVICE_ACCOUNT') or
                        os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or
                        self.directory / 'firebase-service-account.json')
            if not path.is_file():
                raise ValueError('Falta configurar la cuenta de servicio Firebase en el servidor')
            return firebase_admin.initialize_app(credentials.Certificate(str(path)), name='uml-push')

    def native_subscribe(self, room, access, token, remove=False):
        if not isinstance(token, str) or not 20 <= len(token) <= 4096:
            raise ValueError('Token inválido')
        owner = hashlib.sha256(access.encode()).hexdigest()
        with self.connect() as db:
            if remove:
                db.execute('DELETE FROM native_subscriptions WHERE room=? AND owner=? AND token=?', (room,owner,token))
            else:
                self.native_app()
                existing = db.execute('SELECT owner FROM native_subscriptions WHERE room=? AND token=?', (room, token)).fetchone()
                if existing and existing[0] != owner:
                    raise ValueError('Desactiva primero la suscripción del enlace anterior')
                if not existing and db.execute('SELECT count(*) FROM native_subscriptions WHERE room=?', (room,)).fetchone()[0] >= 100:
                    raise ValueError('Límite de dispositivos alcanzado')
                db.execute('INSERT OR REPLACE INTO native_subscriptions VALUES(?,?,?)', (room,owner,token))

    def deliver_native(self, room, event):
        with self.connect() as db:
            tokens = db.execute('SELECT token FROM native_subscriptions WHERE room=?', (room,)).fetchall()
        if not tokens:
            return
        try:
            from firebase_admin import messaging
            app = self.native_app()
            for (token,) in tokens:
                try:
                    messaging.send(messaging.Message(token=token,
                        notification=messaging.Notification(title='Equipo UML', body=f"{event['actor']}: {event['content'].get('text','')}"[:180]),
                        data={'room':room}, android=messaging.AndroidConfig(priority='high',
                            notification=messaging.AndroidNotification(channel_id='uml_updates', default_sound=True, default_vibrate_timings=True))), app=app)
                except messaging.UnregisteredError:
                    with self.connect() as db:
                        db.execute('DELETE FROM native_subscriptions WHERE token=?', (token,))
                except Exception:
                    log.warning('Native notification delivery failed for room %s', room)
        except Exception:
            log.exception('Firebase unavailable')

    def connect(self):
        return sqlite3.connect(self.database)

    def public_key(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        if not self.keyfile.exists():
            key = ec.generate_private_key(ec.SECP256R1())
            encoded = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
            try:
                with self.keyfile.open('xb') as file:
                    file.write(encoded)
            except FileExistsError:
                pass
        key = serialization.load_pem_private_key(self.keyfile.read_bytes(), password=None)
        public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        return base64.urlsafe_b64encode(public).decode().rstrip('=')

    def subscribe(self, room, token, subscription):
        if not isinstance(subscription, dict):
            raise ValueError('Suscripción inválida')
        endpoint = subscription.get('endpoint', '')
        if not isinstance(endpoint, str) or len(endpoint) > 4096:
            raise ValueError('Destino inválido')
        url = urlparse(endpoint)
        host = url.hostname or ''
        allowed = host == 'fcm.googleapis.com' or host == 'updates.push.services.mozilla.com' or host.endswith('.notify.windows.com') or host == 'web.push.apple.com'
        if url.scheme != 'https' or not allowed or url.port not in (None, 443) or url.username or url.password:
            raise ValueError('Proveedor de notificaciones no admitido')
        keys = subscription.get('keys', {})
        for name, size in (('p256dh', 65), ('auth', 16)):
            value = keys.get(name, '') if isinstance(keys, dict) else ''
            if not isinstance(value, str) or len(value) > 128:
                raise ValueError('Clave de suscripción inválida')
            try:
                if len(base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))) != size:
                    raise ValueError()
            except Exception:
                raise ValueError('Clave de suscripción inválida')
        owner = hashlib.sha256(token.encode()).hexdigest()
        with self.connect() as db:
            existing = db.execute('SELECT owner FROM subscriptions WHERE room=? AND endpoint=?', (room, endpoint)).fetchone()
            if existing and existing[0] != owner:
                raise ValueError('Esta suscripción pertenece a otro enlace; desactívala primero')
            count = db.execute('SELECT count(*) FROM subscriptions WHERE room=?', (room,)).fetchone()[0]
            if count >= 100 and not existing:
                raise ValueError('Límite de dispositivos alcanzado')
            db.execute('INSERT OR REPLACE INTO subscriptions VALUES(?,?,?,?)', (room, owner, endpoint, json.dumps(subscription)))

    def unsubscribe(self, room, token, endpoint):
        with self.connect() as db:
            db.execute('DELETE FROM subscriptions WHERE room=? AND owner=? AND endpoint=?', (room, hashlib.sha256(token.encode()).hexdigest(), endpoint))

    def enqueue(self, room, event):
        if event.get('kind') not in ('message', 'answer', 'decision', 'change'):
            return
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM subscriptions WHERE room=? UNION SELECT 1 FROM native_subscriptions WHERE room=? LIMIT 1', (room,room)).fetchone():
                return
        if room in self.pending:
            self.pending[room] = event
            return
        self.pending[room] = event
        task = asyncio.create_task(self.flush(room))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def flush(self, room):
        try:
            while room in self.pending:
                await asyncio.sleep(3)
                async with self.semaphore:
                    event = self.pending[room]
                    await asyncio.to_thread(self.deliver, room, event)
                    if self.pending.get(room) is event:
                        self.pending.pop(room, None)
        finally:
            self.pending.pop(room, None)

    def deliver(self, room, event):
        self.deliver_native(room, event)
        try:
            from pywebpush import webpush, WebPushException
            self.public_key()
            with self.connect() as db:
                rows = db.execute('SELECT endpoint,data FROM subscriptions WHERE room=?', (room,)).fetchall()
            payload = json.dumps({'title':'Actualización del equipo UML', 'body':f"{event['actor']}: {event['content'].get('text', '')}"[:180], 'room':room, 'eventId':event['id']}, ensure_ascii=False)
            for endpoint, data in rows:
                try:
                    webpush(subscription_info=json.loads(data), data=payload, vapid_private_key=str(self.keyfile),
                            vapid_claims={'sub':os.environ.get('WEBPUSH_SUBJECT', 'https://generador-uml.onrender.com')}, ttl=3600, timeout=10)
                except WebPushException as error:
                    if error.response is not None and error.response.status_code in (404, 410):
                        with self.connect() as db:
                            db.execute('DELETE FROM subscriptions WHERE room=? AND endpoint=?', (room, endpoint))
                    else:
                        log.warning('Push delivery failed for room %s', room)
        except Exception:
            log.exception('Push delivery unavailable')
