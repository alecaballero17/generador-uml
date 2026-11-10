(() => {
    const byId = id => document.getElementById(id);
    let cursor = 0, room = '', loading = false;
    const seen = new Set();
    byId('teamActor').value = localStorage.getItem('uml-team-name') || '';
    byId('teamActor').oninput = () => {
        localStorage.setItem('uml-team-name', byId('teamActor').value.trim());
        byId('teamActor').setCustomValidity('');
        byId('teamActor').removeAttribute('aria-invalid');
        byId('teamNameError').hidden = true;
    };
    function resetRoom() {
        if (room === state.projectId) return;
        room = state.projectId; cursor = 0; seen.clear(); byId('teamMessages').replaceChildren();
    }
    function show(entry) {
        if (seen.has(entry.id)) return;
        seen.add(entry.id);
        const row = document.createElement('article');
        row.className = 'team-entry';
        row.dataset.kind = entry.kind;
        row.dataset.eventId = entry.id;
        const meta = document.createElement('div');
        meta.className = 'team-entry-meta';
        const author = document.createElement('strong');
        author.textContent = entry.kind === 'answer' ? `✦ ${entry.actor}` : entry.kind === 'decision' ? `Acuerdo · ${entry.actor}` : entry.actor;
        const time = document.createElement('span');
        // SQLite CURRENT_TIMESTAMP stores UTC without a timezone suffix.
        // Explicit offsets in newer ISO timestamps must remain unchanged.
        const timestamp = String(entry.created || '');
        const utcTimestamp = /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?$/.test(timestamp)
            ? timestamp.replace(' ', 'T') + 'Z' : timestamp;
        const date = new Date(utcTimestamp);
        time.textContent = Number.isNaN(date.getTime()) ? entry.created : date.toLocaleString('es', {day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});
        meta.append(author, time);
        const body = document.createElement('div');
        body.className = 'team-entry-text';
        body.textContent = entry.content.text;
        row.append(meta, body);
        if (entry.kind === 'answer') {
            const listen = document.createElement('button');
            listen.className = 'team-listen btn-secondary';
            listen.textContent = 'Escuchar respuesta';
            listen.onclick = () => ConversationalAssistant.speak(entry.content.text);
            row.append(listen);
        }
        if (entry.content.actions?.length) {
            const details = document.createElement('pre');
            details.style.whiteSpace = 'pre-wrap';
            details.textContent = JSON.stringify(entry.content.actions, null, 2);
            const disclosure = document.createElement('details');
            const summary = document.createElement('summary');
            summary.textContent = 'Ver detalle de los cambios propuestos';
            disclosure.append(summary, details);
            row.append(disclosure);
            const apply = document.createElement('button');
            apply.className = 'btn-primary';
            apply.textContent = 'Aplicar estos cambios al diagrama compartido';
            apply.onclick = async () => {
                apply.disabled = true;
                apply.textContent = 'Aplicando cambios…';
                try {
                    if (collaborationState.inflight || !sameDiagram(state.model.toJSON(), collaborationState.base))
                        throw new Error('Espera a que tus cambios estén sincronizados.');
                    if (entry.content.revision !== collaborationState.revision) throw new Error('Propuesta antigua. Solicita una nueva.');
                    const diagram = ConversationalAssistant.previewActions(entry.content.actions);
                    const response = await umlApiFetch(`/api/collaboration/${encodeURIComponent(state.projectId)}/apply-proposal`, {
                        method:'POST', headers:{'Content-Type':'application/json',Authorization:`Bearer ${collaborationState.token}`},
                        body:JSON.stringify({diagram,revision:entry.content.revision,actor:byId('teamActor').value,proposalId:entry.id})});
                    const result = await response.json();
                    if (!response.ok) throw new Error(result.detail || 'No se pudo aplicar');
                    byId('teamStatus').textContent = 'Cambios guardados y compartidos.';
                    apply.textContent = '✓ Cambios aplicados';
                    apply.style.cursor = 'default';
                } catch(error) { byId('teamStatus').textContent = error.message; apply.disabled = false; apply.textContent = 'Reintentar aplicar cambios'; }
            };
            row.append(apply);
        }
        const list = byId('teamMessages');
        const next = [...list.children].find(child => Number(child.dataset.eventId) > entry.id);
        list.insertBefore(row, next || null);
    }
    async function load() {
        if (loading || !collaborationState.token) return;
        resetRoom(); loading = true;
        const currentRoom = room;
        try {
            let more = true;
            while (more && state.projectId === currentRoom) {
                const response = await umlApiFetch(`/api/collaboration/${encodeURIComponent(room)}/conversation?after=${cursor}`, {
                    headers:{Authorization:`Bearer ${collaborationState.token}`}});
                if (!response.ok) throw new Error('No se pudo recuperar el historial compartido');
                const data = await response.json();
                if (state.projectId !== currentRoom) break;
                for (const entry of data.events) { show(entry); cursor = Math.max(cursor, entry.id); }
                more = data.events.length === 200;
            }
        } catch (error) { byId('teamStatus').textContent = error.message; }
        finally { loading = false; }
    }
    async function send(askAI, proposeChanges = false, decision = false) {
        const actor = byId('teamActor').value.trim(), message = byId('teamMessage').value.trim();
        if (!actor) {
            const field = byId('teamActor');
            byId('teamNameError').hidden = false;
            field.setAttribute('aria-invalid', 'true');
            field.setCustomValidity('Escribí tu nombre para enviar la consulta.');
            field.focus(); field.reportValidity();
            return;
        }
        if (!message) {
            const field = byId('teamMessage');
            field.setCustomValidity('Escribí una consulta o un mensaje antes de enviar.');
            field.focus(); field.reportValidity();
            return;
        }
        localStorage.setItem('uml-team-name', actor);
        byId('teamDecision').disabled = byId('teamPropose').disabled = byId('teamSend').disabled = byId('teamAsk').disabled = true;
        byId('teamStatus').textContent = askAI ? 'Esperando respuesta compartida de la IA…' : 'Enviando…';
        const started = Date.now();
        const activeButton = byId(askAI ? (proposeChanges ? 'teamPropose' : 'teamAsk') : (decision ? 'teamDecision' : 'teamSend'));
        const originalLabel = activeButton.textContent;
        activeButton.textContent = 'Enviando…';
        const progress = setInterval(() => {
            activeButton.textContent = `Esperando respuesta · ${Math.floor((Date.now() - started) / 1000)} s`;
        }, 1000);
        try {
            const response = await umlApiFetch(`/api/collaboration/${encodeURIComponent(state.projectId)}/conversation`, {
                method:'POST', headers:{'Content-Type':'application/json',Authorization:`Bearer ${collaborationState.token}`},
                body:JSON.stringify({actor,message,askAI,proposeChanges,decision})});
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'No se pudo enviar');
            if (byId('teamMessage').value.trim() === message) byId('teamMessage').value = '';
            byId('teamStatus').textContent = 'Guardado en el historial del equipo.';
            await load();
        } catch(error) { byId('teamStatus').textContent = error.message; }
        finally { clearInterval(progress); activeButton.textContent = originalLabel; byId('teamDecision').disabled = byId('teamPropose').disabled = byId('teamSend').disabled = byId('teamAsk').disabled = false; }
    }
    byId('openTeamChat').onclick = () => { byId('teamChatDialog').showModal(); load(); };
    byId('teamClose').onclick = () => byId('teamChatDialog').close();
    byId('teamSend').onclick = () => send(false);
    byId('teamAsk').onclick = () => send(true);
    byId('teamPropose').onclick = () => send(true, true);
    byId('teamDecision').onclick = () => send(false, false, true);
    byId('teamMessage').oninput = () => byId('teamMessage').setCustomValidity('');
    window.TeamAssistant = {
        request(text) {
            byId('teamMessage').value = text;
            if (!byId('teamChatDialog').open) byId('teamChatDialog').showModal();
            load();
            byId('teamStatus').textContent = 'Elige Consultar IA o Solicitar cambios: tu intervención será visible para el equipo.';
        }
    };
    window.addEventListener('team-event', event => {
        resetRoom();
        const fresh = !seen.has(event.detail.id);
        show(event.detail);
        if (fresh && event.detail.kind === 'answer' && byId('teamAudio').checked)
            ConversationalAssistant.speak(event.detail.content.text);
    });
    window.addEventListener('team-connected', load);
})();
