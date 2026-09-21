// Shared endpoint for the packaged editor and the browser editor.
function umlBackendOrigin() {
    if(location.host!=='appassets.androidplatform.net' && location.protocol!=='file:')return location.origin;
    const configured=localStorage.getItem('uml_backend_url')||'http://127.0.0.1:8000';
    const url=new URL(configured);
    if(!['http:','https:'].includes(url.protocol)||url.username||url.password)throw new Error('Dirección de servidor inválida');
    return url.origin;
}
function umlApiFetch(path,options) {return fetch(new URL(path,umlBackendOrigin()).href,options);}
/* Shared projects: persistent snapshots, capability links, field-level merge. */
const collaborationClientId = sessionStorage.getItem('uml_client_id') || crypto.randomUUID();
sessionStorage.setItem('uml_client_id', collaborationClientId);
const collaborationStorageKey = () => `collaboration_${(typeof state !== 'undefined' ? state.projectId : '')}_${collaborationClientId}`;
function savedCollaboration() {
    if (typeof state === 'undefined' || !state.projectId) return null;
    const latest=localStorage.getItem(`collaboration_latest_${state.projectId}`);
    for (const key of new Set([collaborationStorageKey(), latest, `collaboration_${state.projectId}`])) {
        if (!key) continue;
        try {
            const saved=JSON.parse(localStorage.getItem(key) || 'null');
            if (saved && saved.diagram && Array.isArray(saved.diagram.classes)) return saved;
        } catch (_) { /* Keep the damaged copy; try the next recoverable draft. */ }
    }
    return null;
}
const collaborationState = { base: null, revision: 0, token: null, role: 'admin', inflight: null, conflict: null, ready: false, reconnect: null, localSaveFailed: false, pendingOffline: null, reconnectAttempts: 0 };
const copyDiagram = value => JSON.parse(JSON.stringify(value));
const stableDiagram = x => Array.isArray(x) ? x.map(stableDiagram) : x && typeof x === 'object' ? Object.fromEntries(Object.keys(x).sort().map(k=>[k,stableDiagram(x[k])])) : x;
const sameDiagram = (a,b) => JSON.stringify(stableDiagram(a)) === JSON.stringify(stableDiagram(b));
function mergeDiagrams(base, local, remote, preferLocal = false, path = 'diagrama') {
    if (sameDiagram(local, base)) return remote;
    if (sameDiagram(remote, base) || sameDiagram(local, remote)) return local;
    const objects = [base,local,remote].every(x => x && typeof x === 'object' && !Array.isArray(x));
    if (objects) {
        const result = {};
        for (const key of new Set([...Object.keys(base),...Object.keys(local),...Object.keys(remote)])) {
            const merged = mergeDiagrams(base[key], local[key], remote[key], preferLocal, `${path}.${key}`);
            if (merged !== undefined) result[key] = merged;
        }
        return result;
    }
    if ([base,local,remote].every(Array.isArray) && [base,local,remote].every(a => a.every(x => x && typeof x.id === 'string'))) {
        const maps = [base,local,remote].map(a => Object.fromEntries(a.map(x => [x.id,x])));
        const joined = mergeDiagrams(...maps, preferLocal, path);
        return [...new Set([...remote,...local].map(x=>x.id))].filter(id=>joined[id]).map(id=>joined[id]);
    }
    if (preferLocal) return local;
    throw new Error(path);
}
function syncBadge(text) { $('#collabStatus').textContent = text; }
function offlineSyncMessage() {
    if (collaborationState.localSaveFailed) return 'Sin conexión · no se pudo guardar; no cierres la app';
    const pending = collaborationState.pendingOffline ? ' · cambios pendientes' : '';
    return `Sin conexión · guardado local${pending}`;
}
function refreshSyncBadge(participants) {
    if (collaborationState.localSaveFailed) return syncBadge('No se pudo guardar localmente; no cierres la app');
    if (collaborationState.conflict) return syncBadge('Conflicto: revisa tus cambios');
    if (collaborationState.inflight) return syncBadge('Guardando cambios…');
    if (collaborationState.role==='viewer') return syncBadge('Solo lectura');
    if (collaborationState.pendingOffline) return syncBadge('Cambios pendientes · esperando conexión');
    if (!sameDiagram(state.model.toJSON(),collaborationState.base)) return syncBadge('Cambios pendientes de sincronizar');
    syncBadge(participants === undefined ? 'Sincronizado' : `${participants} participantes · edición`);
}
function persistCollaboration() {
    try {
        const payload = {base: collaborationState.base, revision: collaborationState.revision, token: collaborationState.token, diagram: state.model.toJSON()};
        if (collaborationState.pendingOffline) payload.pendingOffline = collaborationState.pendingOffline;
        localStorage.setItem(collaborationStorageKey(), JSON.stringify(payload));
        if (!sameDiagram(state.model.toJSON(),collaborationState.base) || !localStorage.getItem(`collaboration_latest_${state.projectId}`)) localStorage.setItem(`collaboration_latest_${state.projectId}`,collaborationStorageKey());
        localStorage.setItem('last_collaboration_project',state.projectId);
        saveCurrentProjectToStorage();
        collaborationState.localSaveFailed=false;
    } catch (_) { collaborationState.localSaveFailed=true; syncBadge('No se pudo guardar localmente; no cierres la app'); }
}
function savePendingOffline() {
    if (!collaborationState.base) return;
    const diagram = copyDiagram(state.model.toJSON());
    if (sameDiagram(diagram, collaborationState.base)) return;
    collaborationState.pendingOffline = diagram;
    persistCollaboration();
}
function restorePendingOffline() {
    try {
        const saved = JSON.parse(localStorage.getItem(collaborationStorageKey()) || 'null');
        collaborationState.pendingOffline = saved?.pendingOffline || null;
    } catch (_) {
        collaborationState.pendingOffline = null;
    }
}
function flushOfflineQueue() {
    if (!collaborationState.pendingOffline || collaborationState.inflight || collaborationState.conflict) return;
    if (collaborationState.role === 'viewer' || !collaborationState.base || state.ws?.readyState !== WebSocket.OPEN) return;
    const pending = collaborationState.pendingOffline;
    collaborationState.pendingOffline = null;
    try {
        const current = state.model.toJSON();
        const merged = sameDiagram(current, pending) ? pending : mergeDiagrams(collaborationState.base, current, pending, true);
        collaborationState.inflight = copyDiagram(merged);
        state.ws.send(JSON.stringify({type:'update', revision:collaborationState.revision, diagram:merged}));
        syncBadge('Enviando cambios pendientes…');
    } catch (error) {
        collaborationState.pendingOffline = pending;
        collaborationState.inflight = null;
        syncBadge('Error al fusionar cambios offline');
    }
    persistCollaboration();
}
function applySharedDiagram(diagram) {
    state.isRemoteUpdate = true;
    state.model = UMLModel.fromJSON(diagram);
    $('#projectName').value = state.model.name;
    renderAll();
    state.isRemoteUpdate = false;
}
function handleSharedSnapshot(msg, acknowledged = false) {
    if (msg.revision < collaborationState.revision) return;
    const current = state.model.toJSON();
    const base = acknowledged ? collaborationState.inflight : collaborationState.base;
    if (acknowledged) collaborationState.inflight = null;
    else if (collaborationState.inflight) return;
    try {
        const joined = base ? mergeDiagrams(base,current,msg.diagram) : msg.diagram;
        collaborationState.base = copyDiagram(msg.diagram);
        collaborationState.revision = msg.revision;
        if (!sameDiagram(current,joined)) applySharedDiagram(joined);
        persistCollaboration();
        broadcastChange();
    } catch (error) { showCollaborationConflict(msg,base,current,error.message); }
}
function showCollaborationConflict(msg,base,local,path) {
    collaborationState.inflight = null;
    collaborationState.conflict = {msg,base,local};
    try { localStorage.setItem(`conflict_${state.projectId}_${Date.now()}`,JSON.stringify(local)); } catch (_) {}
    syncBadge('Conflicto: revisa tus cambios');
    let dialog = document.getElementById('collaborationConflict');
    if (dialog) dialog.remove();
    dialog = document.createElement('dialog'); dialog.id='collaborationConflict';
    const title = document.createElement('h2'); title.textContent='Cambios simultáneos';
    const text = document.createElement('p'); text.textContent=`Se editó el mismo dato (${path}). Tu copia se conservó localmente. Elige cómo resolverlo.`;
    dialog.append(title,text);
    for (const [label,value] of [['Tu diagrama',local],['Diagrama compartido',msg.diagram]]) {
        const caption=document.createElement('h3'); caption.textContent=label;
        const area=document.createElement('textarea'); area.readOnly=true; area.value=JSON.stringify(value,null,2); area.style.cssText='width:100%;height:140px'; dialog.append(caption,area);
    }
    for (const [label,keep] of [['Usar versión compartida',false],['Conservar mis cambios en conflicto',true]]) {
        const button=document.createElement('button'); button.textContent=label; button.className='btn-primary';
        button.onclick=()=>{
            const choice=collaborationState.conflict;
            const merged=keep ? mergeDiagrams(choice.base,choice.local,choice.msg.diagram,true) : choice.msg.diagram;
            collaborationState.base=copyDiagram(choice.msg.diagram); collaborationState.revision=choice.msg.revision;
            collaborationState.conflict=null; applySharedDiagram(merged); dialog.close(); dialog.remove(); persistCollaboration(); broadcastChange();
        }; dialog.append(button);
    }
    dialog.addEventListener('cancel',event=>event.preventDefault());
    document.body.append(dialog); dialog.showModal();
}
function broadcastChange() {
    if (state.isRemoteUpdate) return;
    persistCollaboration();
    if (!collaborationState.ready || collaborationState.conflict) return;
    if (collaborationState.role==='viewer' || collaborationState.inflight || !collaborationState.base) return;
    if (state.ws?.readyState!==WebSocket.OPEN) {
        savePendingOffline();
        return;
    }
    const diagram=copyDiagram(state.model.toJSON());
    if (sameDiagram(diagram,collaborationState.base)) return;
    collaborationState.inflight=diagram;
    try {
        state.ws.send(JSON.stringify({type:'update',revision:collaborationState.revision,diagram}));
        syncBadge('Guardando cambios…');
    } catch(error) {
        collaborationState.inflight=null;
        savePendingOffline();
        syncBadge(offlineSyncMessage());
        state.ws.close();
    }
}
async function initWebSocket() {
    clearTimeout(collaborationState.reconnect);
    if (state.ws && [WebSocket.OPEN,WebSocket.CONNECTING].includes(state.ws.readyState)) return;
    try {
        if (!collaborationState.token) {
            const params=new URLSearchParams(location.hash.slice(1));
            const saved=savedCollaboration();
            collaborationState.token=params.get('access')||saved?.token;
            if (saved) { collaborationState.base=saved.base; collaborationState.revision=saved.revision; }
            if (!collaborationState.token) {
                if (new URLSearchParams(location.search).has('project')) throw new Error('Falta el enlace de acceso');
                const isMobile = (location.host === 'appassets.androidplatform.net' || location.protocol === 'file:');
                const apiOrigin = umlBackendOrigin();
                const result=await fetch(`${apiOrigin}/api/collaboration/projects`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({diagram:state.model.toJSON()})});
                if (!result.ok) throw new Error('Servidor no disponible');
                const data=await result.json();
                state.projectId=data.projectId; collaborationState.token=data.token;
                collaborationState.base=data.diagram; collaborationState.revision=data.revision;
            }
            const url=new URL(location.href); url.searchParams.set('project',state.projectId); url.hash=`access=${collaborationState.token}`;
            history.replaceState(null,'',url);
        }
        collaborationState.ready=true;
        collaborationState.reconnectAttempts=0;
        restorePendingOffline();
        const isMobile = (location.host === 'appassets.androidplatform.net' || location.protocol === 'file:');
        const backendUrl = new URL(umlBackendOrigin());
        const wsHost = backendUrl.host;
        const protocol = backendUrl.protocol==='https:' ? 'wss:' : 'ws:';
        state.ws=new WebSocket(`${protocol}//${wsHost}/ws/collaboration/${encodeURIComponent(state.projectId)}`);
        state.ws.onopen=()=>{ state.ws.send(JSON.stringify({token:collaborationState.token})); };
        state.ws.onmessage=event=>{
            const msg=JSON.parse(event.data);
            if (msg.role) collaborationState.role=msg.role;
            collaborationState.ready=true;
            if (msg.type==='snapshot' || msg.type==='ack') {
                handleSharedSnapshot(msg,msg.type==='ack');
                refreshSyncBadge();
                if (!collaborationState.inflight && !collaborationState.conflict) flushOfflineQueue();
            } else if (msg.type==='presence') refreshSyncBadge(msg.count);
            else if (msg.type==='conflict') showCollaborationConflict(msg,collaborationState.base,state.model.toJSON(),msg.message);
            else if (msg.type==='error') { collaborationState.inflight=null; showToast(msg.message,'error'); }
            if (collaborationState.role==='viewer') {
                document.querySelectorAll('#sidebar button,#propertiesPanel input,#propertiesPanel button,#propertiesPanel select,#projectName,#btnImport,#btnPhoto,#btnVoice').forEach(el=>el.disabled=true);
                canvasContainer.style.pointerEvents='none';
            }
            persistCollaboration();
        };
        state.ws.onclose=event=>{
            if (collaborationState.inflight) { savePendingOffline(); collaborationState.inflight=null; }
            syncBadge(event.code===4403?'Enlace sin permiso':offlineSyncMessage());
            if (event.code!==4403) {
                collaborationState.reconnectAttempts++;
                const delay = Math.min(3000 * Math.pow(1.5, Math.min(collaborationState.reconnectAttempts, 8)), 30000);
                collaborationState.reconnect=setTimeout(initWebSocket, delay);
            }
        };
        state.ws.onerror=()=>syncBadge(offlineSyncMessage());
    } catch(error) {
        collaborationState.ready=true;
        syncBadge(error.message==='Falta el enlace de acceso'?error.message:offlineSyncMessage());
        collaborationState.reconnect=setTimeout(initWebSocket,3000);
    }
}

async function fetchRoomRevisions() {
    if (!state.projectId || !collaborationState.token) {
        throw new Error('No hay sesión de proyecto colaborativo activa');
    }
    const res = await umlApiFetch(`/api/collaboration/${state.projectId}/revisions`, {
        headers: { 'Authorization': `Bearer ${collaborationState.token}` }
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Error al consultar revisiones' }));
        throw new Error(err.detail || 'Error al consultar historial');
    }
    return await res.json();
}

async function revertRoomRevision(revision) {
    if (!state.projectId || !collaborationState.token) {
        throw new Error('No hay sesión de proyecto colaborativo activa');
    }
    if (collaborationState.role !== 'admin') {
        throw new Error('Solo el administrador del proyecto puede revertir revisiones');
    }
    const res = await umlApiFetch(`/api/collaboration/${state.projectId}/revert/${revision}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${collaborationState.token}` }
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Error al revertir revisión' }));
        throw new Error(err.detail || 'Error al revertir versión');
    }
    return await res.json();
}

async function showShareDialog() {
    if (!collaborationState.token || state.ws?.readyState !== WebSocket.OPEN) { showToast('Conecta con el servidor para compartir', 'warning'); return; }
    if (collaborationState.role !== 'admin') { showToast('Pide un enlace al administrador del proyecto', 'info'); return; }
    const dialog = document.createElement('dialog');
    dialog.className = 'collaboration-share-modal';
    dialog.innerHTML = `
        <div style="padding:20px;max-width:440px;display:flex;flex-direction:column;gap:12px;color:#f8fafc;background:#1e1e2e;border-radius:12px;border:1px solid #3b3b54;font-family:sans-serif;">
            <h3 style="margin:0;font-size:17px;font-weight:600;">Compartir y Control de Revisiones</h3>
            <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.4;">Genera un enlace para invitar a otros colaboradores con permisos diferenciados (edición o solo lectura).</p>
            <div style="display:flex;gap:8px;align-items:center;">
                <select id="inviteRoleSelect" style="padding:8px 12px;border-radius:6px;border:1px solid #4f46e5;background:#12121a;color:#fff;font-size:13px;flex:1;">
                    <option value="editor">Puede editar (Editor)</option>
                    <option value="viewer">Solo lectura (Visualizador)</option>
                </select>
                <button id="btnCreateInvite" class="btn-primary" style="padding:8px 14px;font-size:13px;background:#4f46e5;color:#fff;border:none;border-radius:6px;cursor:pointer;">Crear enlace</button>
            </div>
            <input id="inviteOutput" readonly placeholder="El enlace generado aparecerá aquí..." style="padding:8px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#cbd5e1;font-size:12px;width:100%;box-sizing:border-box;">
            
            <hr style="border:none;border-top:1px solid #334155;margin:6px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:13px;font-weight:600;color:#e2e8f0;">Historial de Revisiones</span>
                <span id="currentRevBadge" style="font-size:11px;background:#312e81;color:#a5b4fc;padding:2px 8px;border-radius:10px;">Rev. ${collaborationState.revision}</span>
            </div>
            <div id="revisionsContainer" style="max-height:120px;overflow-y:auto;background:#0f172a;border-radius:6px;border:1px solid #334155;padding:6px;display:flex;flex-direction:column;gap:4px;font-size:12px;">
                <span style="color:#64748b;font-style:italic;padding:4px;">Cargando historial...</span>
            </div>

            <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:6px;">
                <button id="btnCloseShare" style="padding:6px 14px;border-radius:6px;border:1px solid #475569;background:transparent;color:#cbd5e1;cursor:pointer;">Cerrar</button>
            </div>
        </div>
    `;
    document.body.append(dialog);
    dialog.showModal();

    dialog.querySelector('#btnCreateInvite').onclick = async () => {
        const role = dialog.querySelector('#inviteRoleSelect').value;
        const response = await umlApiFetch(`/api/collaboration/${state.projectId}/invite`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${collaborationState.token}` },
            body: JSON.stringify({ role })
        });
        if (!response.ok) { showToast('No se pudo crear el enlace', 'error'); return; }
        const invite = await response.json();
        const url = new URL('/', umlBackendOrigin());
        url.searchParams.set('project', state.projectId);
        url.hash = `access=${invite.token}`;
        const out = dialog.querySelector('#inviteOutput');
        out.value = url.href;
        out.select();
        showToast('Enlace creado y copiado al campo', 'success');
    };

    // Load revisions list
    try {
        const revData = await fetchRoomRevisions();
        const container = dialog.querySelector('#revisionsContainer');
        container.innerHTML = '';
        if (revData && revData.revisions && revData.revisions.length > 0) {
            revData.revisions.slice().reverse().forEach(revNum => {
                const row = document.createElement('div');
                row.style.display = 'flex';
                row.style.justifyContent = 'space-between';
                row.style.alignItems = 'center';
                row.style.padding = '4px 8px';
                row.style.borderRadius = '4px';
                row.style.background = revNum === revData.currentRevision ? '#1e1b4b' : '#1e293b';

                const label = document.createElement('span');
                label.textContent = `Revisión #${revNum}${revNum === revData.currentRevision ? ' (actual)' : ''}`;
                label.style.color = revNum === revData.currentRevision ? '#818cf8' : '#cbd5e1';

                row.append(label);
                if (revNum !== revData.currentRevision) {
                    const btnRev = document.createElement('button');
                    btnRev.textContent = 'Restaurar';
                    btnRev.style.cssText = 'padding:2px 8px;font-size:11px;background:#4338ca;color:#fff;border:none;border-radius:4px;cursor:pointer;';
                    btnRev.onclick = async () => {
                        if (confirm(`¿Deseas restaurar el diagrama a la Revisión #${revNum}?`)) {
                            try {
                                await revertRoomRevision(revNum);
                                showToast(`Diagrama revertido a Revisión #${revNum}`, 'success');
                                dialog.close();
                                dialog.remove();
                            } catch (err) {
                                showToast(err.message, 'error');
                            }
                        }
                    };
                    row.append(btnRev);
                }
                container.append(row);
            });
        } else {
            container.innerHTML = '<span style="color:#64748b;padding:4px;">No hay revisiones previas</span>';
        }
    } catch (e) {
        const container = dialog.querySelector('#revisionsContainer');
        if (container) container.innerHTML = `<span style="color:#ef4444;padding:4px;">Error: ${e.message}</span>`;
    }

    dialog.querySelector('#btnCloseShare').onclick = () => { dialog.close(); dialog.remove(); };
}

function showServerConnectionDialog() {
    const dialog = document.createElement('dialog');
    const currentUrl = umlBackendOrigin();
    dialog.innerHTML = `
        <div style="padding:18px;max-width:380px;display:flex;flex-direction:column;gap:12px;color:#f8fafc;background:#1e293b;border-radius:12px;border:1px solid #334155;">
            <h3 style="margin:0;font-size:16px;">Conexión y Sincronización</h3>
            <p style="margin:0;font-size:12px;color:#94a3b8;">Configura el servidor o únete a un proyecto para sincronizar Web y Móvil en tiempo real:</p>
            <label style="font-size:12px;font-weight:600;">Dirección Backend:</label>
            <input id="cfgBackendUrl" style="padding:8px;border-radius:6px;border:1px solid #475569;background:#0f172a;color:#fff;font-size:13px;">
            <span style="font-size:11px;color:#64748b;">• USB / Emulador: http://127.0.0.1:8000<br>• Wi-Fi local: http://192.168.1.50:8000</span>
            <label style="font-size:12px;font-weight:600;margin-top:4px;">Enlace o ID de Proyecto (Web):</label>
            <input id="cfgProjectLink" placeholder="Pegar enlace de la Web (opcional)..." style="padding:8px;border-radius:6px;border:1px solid #475569;background:#0f172a;color:#fff;font-size:13px;">
            <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:10px;">
                <button id="btnCancelCfg" style="padding:6px 12px;border-radius:6px;border:1px solid #475569;background:transparent;color:#cbd5e1;cursor:pointer;">Cerrar</button>
                <button id="btnApplyCfg" style="padding:6px 14px;border-radius:6px;border:none;background:#6366f1;color:#fff;font-weight:bold;cursor:pointer;">Conectar</button>
            </div>
        </div>
    `;
    document.body.append(dialog);
    dialog.querySelector('#cfgBackendUrl').value=currentUrl;
    dialog.showModal();
    dialog.querySelector('#btnCancelCfg').onclick = () => { dialog.close(); dialog.remove(); };
    dialog.querySelector('#btnApplyCfg').onclick = () => {
        const url = dialog.querySelector('#cfgBackendUrl').value.trim();
        const link = dialog.querySelector('#cfgProjectLink').value.trim();
        try {
            const backend=new URL(url);
            if(!['http:','https:'].includes(backend.protocol)||backend.username||backend.password)throw new Error('Usa una dirección HTTP o HTTPS válida.');
            const destination=new URL(location.href);
            if(link) {
                const shared=new URL(link);
                const project=shared.searchParams.get('project');
                const token=new URLSearchParams(shared.hash.slice(1)).get('access');
                if(!['http:','https:'].includes(shared.protocol)||!project||!token)throw new Error('Pega el enlace completo del proyecto, incluido su permiso de acceso.');
                destination.searchParams.set('project',project);
                destination.hash=new URLSearchParams({access:token}).toString();
            }
            persistCollaboration();
            localStorage.setItem('uml_backend_url',backend.origin);
            // A fresh page loads the target draft and token without carrying the previous room's revision.
            history.replaceState(null,'',destination.href);
            location.reload();
        } catch(error) {showToast(error.message,'error');}

    };
}

document.addEventListener('DOMContentLoaded', () => {
    const statusBadge = document.getElementById('collabStatus');
    if (statusBadge) {
        statusBadge.style.cursor = 'pointer';
        statusBadge.addEventListener('click', showServerConnectionDialog);
    }
});

window.addEventListener('online', () => {
    collaborationState.reconnectAttempts = 0;
    syncBadge('Red restablecida · reconectando…');
    initWebSocket();
});

window.addEventListener('offline', () => {
    savePendingOffline();
    syncBadge(offlineSyncMessage());
});

