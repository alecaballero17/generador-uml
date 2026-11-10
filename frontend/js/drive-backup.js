/* Google Identity Services: user consent + drive.file, no token persistence. */
const DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive.file';
let driveIdentityLoading;

function loadDriveIdentity() {
    if (window.google?.accounts?.oauth2) return Promise.resolve();
    if (driveIdentityLoading) return driveIdentityLoading;
    driveIdentityLoading = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client'; script.async = true;
        const timeout = setTimeout(() => fail(), 15000);
        const fail = () => { clearTimeout(timeout); script.remove(); driveIdentityLoading = null; reject(new Error('No se pudo conectar con Google. Revisá tu conexión y reintentá.')); };
        script.onload = () => { clearTimeout(timeout); if (window.google?.accounts?.oauth2) resolve(); else fail(); };
        script.onerror = fail; document.head.append(script);
    });
    return driveIdentityLoading;
}

function driveBackupFile(diagram) {
    // Serialize only the UML model, never browser storage or collaboration tokens.
    const text = JSON.stringify(diagram, null, 2);
    const file = new Blob([text], {type:'application/json'});
    if (file.size > 5 * 1024 * 1024) throw new Error('El diagrama supera 5 MB. Descargalo como JSON desde Exportar.');
    const name = String(diagram.name || 'Diagrama').replace(/[^\p{L}\p{N}_ -]/gu,'_').slice(0,80);
    const stamp = new Date().toISOString().replace(/[:.]/g,'-');
    return {file, name:`${name}_${stamp}.json`};
}

async function uploadDiagramToDrive(backup, token, signal) {
    const boundary = 'uml_' + crypto.randomUUID();
    const metadata = {name:backup.name, mimeType:'application/json', description:'Respaldo editable de GeneradorUML. Para restaurarlo, descargá este JSON y usá Importar en el editor.'};
    const body = new Blob([
        `--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n`,
        JSON.stringify(metadata),
        `\r\n--${boundary}\r\nContent-Type: application/json\r\n\r\n`, backup.file,
        `\r\n--${boundary}--\r\n`
    ], {type:`multipart/related; boundary=${boundary}`});
    const response = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink', {
        method:'POST', headers:{Authorization:`Bearer ${token}`}, body,
        signal:signal ? AbortSignal.any([signal, AbortSignal.timeout(60000)]) : AbortSignal.timeout(60000)
    });
    if (!response.ok) {
        if (response.status === 401) throw new Error('La autorización venció. Volvé a conectar tu cuenta.');
        if (response.status === 403) throw new Error('Google no permitió guardar. Revisá el permiso de Drive y que la API esté habilitada.');
        throw new Error('No se pudo confirmar el respaldo en Drive. Revisá tu Drive antes de reintentar.');
    }
    const result = await response.json();
    if (!result.id) throw new Error('Google no confirmó el archivo. Revisá tu Drive antes de reintentar.');
    return result;
}

async function showDriveBackup() {
    if (document.getElementById('driveBackupDialog')) return;
    const backup = driveBackupFile(state.model.toJSON());
    const dialog = document.createElement('dialog'); dialog.id='driveBackupDialog'; dialog.className='drive-backup-dialog';
    dialog.innerHTML = `<span aria-hidden="true" style="font-size:32px">☁</span><h2>Tu trabajo, siempre con vos.</h2>
        <p>Guardá una copia editable de este diagrama en tu Google Drive, aunque el servidor se reinicie.</p>
        <div class="drive-backup-file"></div>
        <p>Elegís tu cuenta y autorizás a GeneradorUML a guardar sus archivos. El respaldo incluye clases, relaciones y posiciones del diagrama.</p>
        <p class="drive-status" role="status" aria-live="polite">Preparando conexión con Google…</p>
        <button class="btn-primary" id="driveConnectSave" disabled>Conectar Google y guardar</button>
        <button class="btn-secondary" id="driveBackupClose">Cerrar</button>`;
    dialog.querySelector('.drive-backup-file').textContent = backup.name;
    document.body.append(dialog); dialog.showModal();
    const status = dialog.querySelector('.drive-status'), button=dialog.querySelector('#driveConnectSave');
    let generation=0, authTimer=null, uploadController=null;
    const stop=()=>{
        generation++; clearTimeout(authTimer); authTimer=null;
        uploadController?.abort(); uploadController=null;
    };
    // Closing remains available even if Google never sends either callback.
    const close=()=>{stop();dialog.close();dialog.remove();};
    dialog.querySelector('#driveBackupClose').onclick=close;
    dialog.addEventListener('cancel', event=>{event.preventDefault();close();});
    const report=(message,error=false)=>{status.textContent=message;status.dataset.error=String(error);};
    const release=()=>{stop();button.disabled=false;button.textContent='Reintentar conexión con Google';};
    try {
        const response=await umlApiFetch('/api/integrations/google-drive',{cache:'no-store'});
        if (!response.ok) throw new Error('No se pudo consultar la conexión con Drive. Reintentá en unos segundos.');
        const config=await response.json();
        if (!config.configured) throw new Error('Google Drive todavía no está habilitado en esta instalación. Falta configurar la conexión con Google. Tu diagrama sigue guardado localmente.');
        await loadDriveIdentity();
        if (!dialog.isConnected) return;
        button.disabled=false;report('Listo para guardar. Google te pedirá elegir tu cuenta y autorizar el acceso.');
        button.onclick=()=>{
            stop(); const attempt=generation;
            const active=()=>dialog.isConnected && attempt===generation;
            button.disabled=true;button.textContent='Esperando a Google…';
            report('Esperando tu autorización en Google…');
            authTimer=setTimeout(()=>{
                if (!active()) return;
                release();report('Google no devolvió la autorización. Cerrá la ventana anterior de Google y reintentá. Todavía no se envió el respaldo.',true);
            },120000);
            try {
                // Separate callbacks per attempt prevent a late authorization
                // from uploading after cancellation or starting a second upload.
                const client=window.google.accounts.oauth2.initTokenClient({
                    client_id:config.clientId, scope:DRIVE_SCOPE, include_granted_scopes:false,
                    error_callback:error=>{
                        if (!active()) return;
                        release();
                        report(error?.type==='popup_closed' ? 'Se cerró la ventana de Google. Podés reintentar o cerrar este panel.' : 'No se completó la autorización. Permití la ventana de Google o reintentá.',true);
                    },
                    callback:async result=>{
                        if (!active()) return;
                        clearTimeout(authTimer);authTimer=null;
                        let expectedGeneration=attempt;
                        try {
                            if (result.error || !result.access_token || !window.google.accounts.oauth2.hasGrantedAllScopes(result,DRIVE_SCOPE)) {
                                release();report('No se concedió permiso para guardar en Drive. No se subió el respaldo.',true);return;
                            }
                            // Consume this authorization before awaiting network I/O.
                            generation++; const uploadGeneration=generation;expectedGeneration=generation;
                            uploadController=new AbortController();
                            report('Guardando tu diagrama en Drive…');button.textContent='Guardando en Drive…';
                            const saved=await uploadDiagramToDrive(backup,result.access_token,uploadController.signal);
                            if (!dialog.isConnected || uploadGeneration!==generation) return;
                            uploadController=null;
                            report('✓ Respaldo guardado en tu Google Drive.');
                            button.textContent='Guardado en Drive';
                            const link=document.createElement('a');link.className='btn-secondary';
                            link.textContent='Ver respaldo en Drive';link.target='_blank';link.rel='noopener noreferrer';
                            link.href='https://drive.google.com/file/d/'+encodeURIComponent(saved.id)+'/view';
                            button.after(link);
                        } catch(error) {
                            if (!dialog.isConnected || expectedGeneration!==generation || error.name==='AbortError') return;
                            release();report(error.name==='TimeoutError'?'Google demoró en responder. Revisá tu Drive antes de reintentar.':error.message,true);
                        }
                    }
                });
                client.requestAccessToken({prompt:'select_account'});
            }
            catch (_) {release();report('No se pudo abrir Google. Permití las ventanas emergentes y reintentá.',true);}
        };
    } catch(error) { report(error.message,true); }
}

document.getElementById('btnDriveBackup')?.addEventListener('click',()=>{
    showDriveBackup().catch(error=>showToast(error.message,'error'));
});
