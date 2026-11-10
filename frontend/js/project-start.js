/* Project entry and recovery never remove the previous browser draft. */
function projectDialog(title, description) {
    const dialog = document.createElement('dialog');
    dialog.className = 'project-start-dialog';
    const heading = document.createElement('h2'); heading.textContent = title;
    const text = document.createElement('p'); text.textContent = description;
    dialog.append(heading, text);
    document.body.append(dialog);
    dialog.showModal();
    return dialog;
}

function projectAction(dialog, label, action, primary = false) {
    const button = document.createElement('button');
    button.type = 'button'; button.textContent = label;
    button.className = primary ? 'btn-primary' : 'btn-secondary';
    button.onclick = action; dialog.append(button);
    return button;
}

async function chooseProjectStart() {
    if (new URLSearchParams(location.search).has('project')) return false;
    return new Promise(resolve => {
        const dialog = projectDialog('¿Qué querés crear hoy?',
            'Empezá un diagrama nuevo o retomá el último proyecto guardado en este navegador.');
        dialog.addEventListener('cancel', event => event.preventDefault());
        const finish = fresh => { dialog.close(); dialog.remove(); resolve(fresh); };
        projectAction(dialog, 'Nuevo proyecto', () => finish(true), true);
        if (localStorage.getItem('last_collaboration_project') || localStorage.getItem('generador_uml_current')) {
            projectAction(dialog, 'Retomar proyecto guardado', () => finish(false));
        }
    });
}

async function recoverProjectCopy() {
    // Keep the old capability/draft under its original ID before creating a copy.
    persistCollaboration();
    if (collaborationState.localSaveFailed) throw new Error('No se pudo respaldar tu diagrama. Descargá la copia JSON primero.');
    const diagram = copyDiagram(state.model.toJSON());
    const result = await umlApiFetch('/api/collaboration/projects', {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({diagram})
    });
    if (!result.ok) throw new Error('No se pudo crear la copia compartida. Tu diagrama sigue guardado localmente.');
    const data = await result.json();
    clearTimeout(collaborationState.reconnect);
    if (state.ws) { state.ws.onclose = null; state.ws.close(); state.ws = null; }
    state.projectId = data.projectId;
    Object.assign(collaborationState, {token:data.token, base:data.diagram, revision:data.revision,
        role:'admin', pendingOffline:null, inflight:null, conflict:null, ready:false});
    const url = new URL(location.href);
    url.searchParams.set('project', data.projectId); url.searchParams.delete('build');
    url.hash = new URLSearchParams({access:data.token}).toString();
    history.replaceState(null, '', url);
    persistCollaboration();
    await initWebSocket();
}

function showProjectRecovery() {
    if (document.getElementById('projectRecovery')) return;
    const hasDraft = state.model.classes.length > 0;
    const dialog = projectDialog('Este enlace ya no está disponible',
        hasDraft ? 'El servidor no reconoce el permiso de este proyecto. Tu diagrama sigue en este navegador. Podés respaldarlo y crear una nueva copia compartida con un enlace nuevo.'
            : 'El servidor no reconoce este enlace. Pedí uno vigente a quien compartió el proyecto o empezá un proyecto nuevo.');
    dialog.id = 'projectRecovery';
    const status = document.createElement('p'); status.setAttribute('role','status'); dialog.append(status);
    if (hasDraft) {
        projectAction(dialog, 'Descargar respaldo JSON', () => {
            const url = URL.createObjectURL(new Blob([JSON.stringify(state.model.toJSON(), null, 2)], {type:'application/json'}));
            const link = document.createElement('a'); link.href = url; link.download = 'respaldo-diagrama.json'; link.click();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        });
        const recover = projectAction(dialog, 'Recuperar como proyecto compartido', async () => {
            recover.disabled = true; status.textContent = 'Creando una copia de tu diagrama…';
            try { await recoverProjectCopy(); dialog.close(); dialog.remove(); }
            catch (error) { status.textContent = error.message; recover.disabled = false; }
        }, true);
    }
    projectAction(dialog, 'Ir al inicio', () => { persistCollaboration(); location.assign('/'); });
    projectAction(dialog, 'Conservar esta vista', () => { dialog.close(); dialog.remove(); });
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btnProjectStart')?.addEventListener('click', () => {
        persistCollaboration(); location.assign('/');
    });
});
