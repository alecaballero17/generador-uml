const SHELL='uml-shell-v21';
const FILES=[
    '/',
    '/index.html',
    '/seguimiento.html',
    '/js/seguimiento.js',
    '/css/seguimiento.css',
    '/css/index.css',
    '/css/photo-import.css',
    '/css/mobile.css',
    '/js/collaboration.js',
    '/js/project-start.js',
    '/js/app.js',
    '/js/uml-commands.js',
    '/js/mobile.js',
    '/js/association-classes.js',
    '/js/local-ai.js',
    '/js/conversational-assistant.js',
    '/js/team-chat.js',
    '/js/voice-worker.js',
    '/manifest.webmanifest'
];

self.addEventListener('install',event=>{
    event.waitUntil(caches.open(SHELL).then(cache=>cache.addAll(FILES)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',event=>event.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('uml-shell-')&&k!==SHELL).map(k=>caches.delete(k)))).then(()=>self.clients.claim())
));

self.addEventListener('push', event => {
    let data;
    try { data = event.data.json(); } catch (_) { return; }
    if (!data || typeof data.room !== 'string') return;
    event.waitUntil(self.registration.showNotification(data.title || 'Equipo UML', {
        body:data.body || 'Hay novedades en tu proyecto', tag:`uml-${data.room}`,
        data:{url:`/seguimiento.html?project=${encodeURIComponent(data.room)}`}
    }));
});
self.addEventListener('notificationclick', event => {
    event.notification.close();
    const target = new URL(event.notification.data?.url || '/seguimiento.html', self.location.origin);
    if (target.origin !== self.location.origin) return;
    event.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(async windows => {
        const existing = windows.find(client => client.url.split('#')[0] === target.href);
        if (existing) return existing.focus();
        return self.clients.openWindow(target.href);
    }));
});

self.addEventListener('fetch',event=>{
    const url=new URL(event.request.url);
    if(event.request.method!=='GET'||url.origin!==location.origin||url.pathname.startsWith('/api/')||url.pathname.startsWith('/ws/'))return;
    if(url.pathname.startsWith('/assets/')) {
        event.respondWith(caches.match(event.request,{ignoreSearch:true}).then(cached=>cached||fetch(event.request)));
    } else {
        event.respondWith(fetch(event.request).then(response=>{
            if(response.ok) {
                const copy=response.clone();
                event.waitUntil(caches.open(SHELL).then(cache=>cache.put(url.pathname,copy)));
            }
            return response;
        }).catch(async()=>{
            const key=url.pathname==='/seguimiento.html'?'/seguimiento.html':(url.pathname==='/'||url.pathname==='/index.html'||event.request.mode==='navigate')?'/':event.request;
            const shell=await caches.open(SHELL);
            return await shell.match(key,{ignoreSearch:true}) || await caches.match(key,{ignoreSearch:true});
        }));
    }
});
