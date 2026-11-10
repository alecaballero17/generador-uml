(() => {
    const el = id => document.getElementById(id);
    function setTheme(theme) {
        document.documentElement.dataset.theme = theme;
        document.querySelectorAll('[data-theme-choice]').forEach(button => {
            button.setAttribute('aria-pressed', String(button.dataset.themeChoice === theme));
        });
        document.querySelector('meta[name="theme-color"]').setAttribute('content', theme === 'dark' ? '#12131e' : '#f7f8fc');
        try { localStorage.setItem('monitor-theme', theme); } catch (_) {}
    }
    document.querySelectorAll('[data-theme-choice]').forEach(button => {
        button.onclick = () => setTheme(button.dataset.themeChoice);
    });
    setTheme(document.documentElement.dataset.theme === 'light' ? 'light' : 'dark');
    const packaged = location.hostname === 'appassets.androidplatform.net';
    const backend = packaged ? localStorage.getItem('uml_backend_url') || 'https://generador-uml.onrender.com' : location.origin;
    const api = (path, options) => fetch(new URL(path, backend), options);
    const room = new URLSearchParams(location.search).get('project');
    const token = new URLSearchParams(location.hash.slice(1)).get('access') || localStorage.getItem(`monitor-access:${room}`);
    const seen = new Set();
    const entries = new Map();
    let activeView = 'inicio', receivingHistory = false;
    function showView(name) {
        if (!['inicio', 'actividad', 'modelo', 'ajustes'].includes(name)) return;
        activeView = name;
        document.querySelectorAll('.view').forEach(view => { view.hidden = view.id !== name; });
        document.querySelectorAll('.bottom-nav [data-view]').forEach(button => {
            if (button.dataset.view === name) button.setAttribute('aria-current', 'page');
            else button.removeAttribute('aria-current');
        });
        if (name === 'actividad') el('activityDot').hidden = true;
        window.scrollTo(0, 0);
    }
    document.querySelectorAll('[data-view]').forEach(button => {
        button.onclick = () => showView(button.dataset.view);
    });
    document.querySelector('.brand').onclick = e => { e.preventDefault(); showView('inicio'); };
    if (!packaged && 'serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
    el('openBrowser').hidden = !packaged || !!window.UMLPush;
    el('openBrowser').onclick = () => {
        if (!room || !token) { status('Abre primero un proyecto.'); return; }
        const target = new URL('/seguimiento.html', backend);
        target.searchParams.set('project', room); target.hash = `access=${token}`;
        if (window.UMLBrowser) UMLBrowser.postMessage(target.href);
        else status('Actualiza la APK para abrir el navegador.');
    };
    let socket, retry, attempts = 0, cursor = 0;
    const status = (text, state = 'waiting') => {
        el('status').textContent = text;
        document.body.classList.toggle('is-connected', state === 'connected');
        document.body.classList.toggle('is-offline', state === 'offline');
        el('connectionLabel').textContent = state === 'connected' ? 'En vivo' : state === 'offline' ? 'Sin conexión' : 'Conectando';
        if (state !== 'connected') el('memberCount').textContent = '—';
    };
    function pushStatus(text) {
        el('pushStatus').textContent = text;
        el('notificationSummary').textContent = text;
    }
    async function nativeRegistration(remove = false) {
        if (!window.UMLPush) throw new Error('Actualiza la APK para activar push nativo.');
        const deviceToken = await new Promise((resolve, reject) => {
            const timer = setTimeout(() => reject(new Error('Firebase tardó demasiado. Intenta nuevamente.')), 20000);
            UMLPush.onmessage = event => {
                clearTimeout(timer);
                try { const result = JSON.parse(event.data); result.token ? resolve(result.token) : reject(new Error(result.error)); }
                catch(error) { reject(error); }
            };
            UMLPush.postMessage('register');
        });
        const response = await api(`/api/collaboration/${encodeURIComponent(room)}/native-push`, {
            method:remove?'DELETE':'POST', headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'}, body:JSON.stringify({token:deviceToken})});
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'No se pudo registrar el dispositivo. Intenta nuevamente.');
        }
        localStorage.setItem(`native-push:${room}`, remove?'off':'on');
        pushStatus(remove ? 'Avisos desactivados para este proyecto.' : 'Notificaciones nativas activadas para este proyecto.');
    }
    const last = localStorage.getItem('monitor-last');
    if (!room && last) {
        try {
            const saved = new URL(last);
            if (saved.origin === location.origin && saved.pathname === '/seguimiento.html' && saved.searchParams.get('project')) {
                location.replace(saved.href);
                return;
            }
        } catch (_) {}
    }
    el('resume').hidden = !last;
    el('resume').onclick = () => {
        try {
            const previous = new URL(last);
            if (previous.origin === location.origin && previous.pathname === '/seguimiento.html') location.assign(previous.href);
        } catch (_) { status('El enlace guardado ya no está disponible.'); }
    };
    async function subscriptionRequest(method, subscription) {
        const response = await api(`/api/collaboration/${encodeURIComponent(room)}/push`, {
            method, headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'}, body:JSON.stringify(subscription)});
        if (!response.ok) throw new Error('El servidor no pudo guardar la preferencia de notificaciones.');
    }
    el('enablePush').onclick = async () => {
        try {
            if (!room || !token) throw new Error('Abre primero un proyecto.');
            if (packaged) { await nativeRegistration(); return; }
            if (packaged || !window.isSecureContext || !('PushManager' in window)) throw new Error('Abre este enlace HTTPS en Chrome para Android para activar push.');
            if (await Notification.requestPermission() !== 'granted') throw new Error('No se concedió permiso para notificaciones.');
            const registration = await navigator.serviceWorker.ready;
            const response = await api(`/api/collaboration/${encodeURIComponent(room)}/push-key`, {headers:{Authorization:`Bearer ${token}`}});
            if (!response.ok) throw new Error('Push no está disponible en el servidor.');
            const {publicKey} = await response.json();
            const encoded = publicKey.replace(/-/g, '+').replace(/_/g, '/');
            const key = Uint8Array.from(atob(encoded + '='.repeat((4 - encoded.length % 4) % 4)), c => c.charCodeAt(0));
            let subscription = await registration.pushManager.getSubscription();
            if (!subscription) subscription = await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:key});
            await subscriptionRequest('POST', subscription.toJSON());
            pushStatus('Notificaciones activadas para este proyecto.');
        } catch(error) { pushStatus(error.message); }
    };
    el('disablePush').onclick = async () => {
        try {
            if (packaged) { await nativeRegistration(true); return; }
            if (!room || !token || !('serviceWorker' in navigator)) return;
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            if (subscription) await subscriptionRequest('DELETE', {endpoint:subscription.endpoint});
            pushStatus('Avisos desactivados para este proyecto.');
        } catch(error) { pushStatus(error.message); }
    };
    function card(parent, title, text) {
        const row = document.createElement('article'), heading = document.createElement('strong'), content = document.createElement('pre');
        heading.textContent = title; content.textContent = text;
        row.append(heading, content); parent.append(row); return row;
    }
    function render(snapshot) {
        el('title').textContent = snapshot.diagram.name || 'Diagrama';
        el('revision').textContent = `Revisión ${snapshot.revision}`;
        el('classCount').textContent = el('classBadge').textContent = snapshot.diagram.classes.length;
        el('relationCount').textContent = el('relationBadge').textContent = snapshot.diagram.relationships.length;
        el('classes').replaceChildren(); el('relations').replaceChildren();
        const names = new Map(snapshot.diagram.classes.map(c => [c.id, c.name]));
        const svg = el('diagram'); svg.replaceChildren();
        const draw = (tag, attrs, text) => {
            const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
            for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
            if (text !== undefined) node.textContent = text;
            svg.append(node); return node;
        };
        const coordinates = new Map();
        const numeric = (n, fallback) => typeof n === 'number' && Number.isFinite(n) ? Math.max(-10000, Math.min(10000, n)) : fallback;
        const nodes = snapshot.diagram.classes.map((c, i) => ({c, x:numeric(c.position?.x ?? c.x, (i % 3) * 300), y:numeric(c.position?.y ?? c.y, Math.floor(i / 3) * 240)}));
        const minX = Math.min(0, ...nodes.map(n => n.x)), minY = Math.min(0, ...nodes.map(n => n.y));
        let width = 600, height = 250;
        for (const {c, x, y} of nodes) {
            const box = {x:x-minX+25,y:y-minY+25,w:220,h:55+(c.attributes || []).length*20};
            coordinates.set(c.id, box); width=Math.max(width,box.x+245); height=Math.max(height,box.y+box.h+25);
        }
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        for (const rel of snapshot.diagram.relationships) {
            const a=coordinates.get(rel.source.classId), b=coordinates.get(rel.target.classId);
            if (!a || !b) continue;
            draw('line',{x1:a.x+a.w/2,y1:a.y+a.h/2,x2:b.x+b.w/2,y2:b.y+b.h/2,stroke:'#9987ca','stroke-width':2});
            draw('text',{x:(a.x+b.x)/2+110,y:(a.y+b.y)/2-8,fill:'#686179','font-size':12},`${rel.source.multiplicity || ''} ${relationName(rel.type)} ${rel.target.multiplicity || ''}`);
        }
        for (const {c} of nodes) {
            const b=coordinates.get(c.id);
            draw('rect',{x:b.x,y:b.y,width:b.w,height:b.h,rx:10,fill:'#f7f5fd',stroke:'#c5b8e5'});
            draw('text',{x:b.x+12,y:b.y+24,fill:'#39304f','font-size':16,'font-weight':650},c.name);
            (c.attributes || []).forEach((a,i)=>draw('text',{x:b.x+12,y:b.y+48+i*20,fill:'#686179','font-size':13},`${a.name}: ${a.type}`));
        }
        for (const cls of snapshot.diagram.classes) card(el('classes'), cls.name,
            [...(cls.attributes || []).map(a => `${a.name}: ${a.type}`), ...(cls.operations || []).map(o => `${o.name}()`)].join('\n') || 'Sin atributos');
        for (const rel of snapshot.diagram.relationships) card(el('relations'), relationName(rel.type),
            `${names.get(rel.source.classId)} (${rel.source.multiplicity || 'sin especificar'}) ↔ ${names.get(rel.target.classId)} (${rel.target.multiplicity || 'sin especificar'})`);
        try { localStorage.setItem(`monitor:${room}`, JSON.stringify(snapshot)); } catch (_) {}
    }
    function relationName(type) {
        return ({association:'Asociación', composition:'Composición', aggregation:'Agregación', generalization:'Herencia', realization:'Realización', dependency:'Dependencia'})[type] || type || 'Relación';
    }
    function localEventTime(created) {
        const timestamp = String(created || '');
        const utcTimestamp = /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?$/.test(timestamp)
            ? timestamp.replace(' ', 'T') + 'Z' : timestamp;
        const date = new Date(utcTimestamp);
        return Number.isNaN(date.getTime()) ? timestamp : date.toLocaleString('es', {
            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
        });
    }
    function event(entry) {
        if (seen.has(entry.id)) return;
        seen.add(entry.id);
        entries.set(entry.id, entry);
        const row = activityCard(entry);
        el('activity').append(row);
        row.dataset.id = entry.id;
        const next = [...el('activity').children].find(c => Number(c.dataset.id) < entry.id);
        if (next) el('activity').insertBefore(row, next);
        el('activityEmpty').hidden = true;
        const recent = [...entries.values()].sort((a, b) => b.id - a.id).slice(0, 3);
        el('recentActivity').replaceChildren(...recent.map(item => activityCard(item, true)));
        if (!receivingHistory && activeView !== 'actividad') el('activityDot').hidden = false;
        try { localStorage.setItem(`monitor-activity:${room}`, JSON.stringify([...entries.values()].sort((a,b) => a.id-b.id).slice(-100))); } catch (_) {}
    }
    function activityCard(entry, compact = false) {
        const row = document.createElement('article');
        row.className = `activity-card${compact ? ' recent-card' : ''}`;
        row.dataset.id = entry.id; row.dataset.kind = entry.kind;
        const avatar = document.createElement('span'); avatar.className = 'avatar';
        const actor = String(entry.actor || 'Integrante');
        avatar.textContent = entry.kind === 'answer' ? 'IA' : actor.split(/\s+/).slice(0, 2).map(name => name.charAt(0)).join('').toUpperCase();
        avatar.setAttribute('aria-hidden', 'true');
        const body = document.createElement('div'), meta = document.createElement('div'); meta.className = 'activity-meta';
        const author = document.createElement('strong'); author.textContent = actor;
        const time = document.createElement('time'); time.textContent = localEventTime(entry.created);
        meta.append(author, time);
        const kind = document.createElement('span'); kind.className = 'activity-kind';
        kind.textContent = ({message:'Mensaje al equipo', answer:'Respuesta de IA', decision:'Acuerdo del equipo', change:'Cambio en el diagrama'})[entry.kind] || 'Actividad';
        const text = document.createElement('p'); text.className = 'activity-text'; text.textContent = entry.content?.text || '';
        body.append(meta, kind, text); row.append(avatar, body);
        return row;
    }
    async function history() {
        if (receivingHistory) return;
        receivingHistory = true;
        try {
            let more = true;
            while (more) {
                const response = await api(`/api/collaboration/${encodeURIComponent(room)}/conversation?after=${cursor}`, {headers:{Authorization:`Bearer ${token}`}});
                if (!response.ok) throw new Error('No se pudo recuperar la conversación');
                const data = await response.json();
                for (const item of data.events) { event(item); cursor = Math.max(cursor, item.id); }
                more = data.events.length === 200;
            }
        } catch (error) { status(error.message); }
        finally { receivingHistory = false; }
    }
    function connect() {
        clearTimeout(retry);
        const endpoint = new URL(`/ws/collaboration/${encodeURIComponent(room)}`, backend);
        endpoint.protocol = endpoint.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(endpoint);
        socket.onopen = () => socket.send(JSON.stringify({token,actor:'Seguimiento móvil'}));
        socket.onmessage = message => {
            const data = JSON.parse(message.data);
            if (data.type === 'snapshot') {
                render(data); status('Conectado · solo seguimiento', 'connected'); attempts = 0;
                el('lastSync').textContent = `Actualizado ${new Date().toLocaleTimeString('es', {hour:'2-digit',minute:'2-digit'})}`;
                localStorage.setItem(`monitor-access:${room}`, token);
                localStorage.setItem('monitor-last', location.href);
                if (packaged && localStorage.getItem(`native-push:${room}`) === 'on')
                    nativeRegistration().catch(error => pushStatus(error.message));
            }
            if (data.type === 'team_event') event(data.event);
            if (data.type === 'presence') { el('memberCount').textContent = data.count; history(); }
        };
        socket.onclose = message => {
            if (message.code === 4403) { status('Enlace no autorizado. Solicita otro enlace al administrador.', 'offline'); showView('ajustes'); return; }
            status('Sin conexión. Se conserva la última vista; reconectando…', 'offline');
            retry = setTimeout(connect, Math.min(30000, 1000 * 2 ** attempts++));
        };
    }
    el('join').onsubmit = e => {
        e.preventDefault();
        try {
            const url = new URL(el('link').value);
            if (!['http:', 'https:'].includes(url.protocol) || !url.searchParams.get('project') || !new URLSearchParams(url.hash.slice(1)).get('access')) throw new Error();
            if (url.username || url.password) throw new Error();
            if (packaged) {
                localStorage.setItem('uml_backend_url', url.origin);
                location.assign(`/seguimiento.html${url.search}${url.hash}`);
            } else { url.pathname = '/seguimiento.html'; location.assign(url.href); }
        } catch (_) { status('Pega un enlace compartido completo.'); }
    };
    if (!room || !token) { status('Abre el enlace de seguimiento de tu equipo.'); showView('ajustes'); return; }
    try {
        const saved = JSON.parse(localStorage.getItem(`monitor:${room}`));
        if (saved) { render(saved); status('Última copia guardada · conectando…', 'offline'); }
        receivingHistory = true;
        const cached = JSON.parse(localStorage.getItem(`monitor-activity:${room}`) || '[]');
        for (const entry of cached) event(entry);
    } catch (_) {} finally { receivingHistory = false; }
    connect();
})();
