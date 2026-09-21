const SHELL='uml-shell-v4';
const FILES=[
    '/',
    '/index.html',
    '/css/index.css',
    '/css/mobile.css',
    '/js/collaboration.js',
    '/js/app.js',
    '/js/uml-commands.js',
    '/js/mobile.js',
    '/js/local-ai.js',
    '/js/conversational-assistant.js',
    '/js/voice-worker.js',
    '/manifest.webmanifest'
];

self.addEventListener('install',event=>{
    event.waitUntil(caches.open(SHELL).then(cache=>cache.addAll(FILES)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate',event=>event.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('uml-shell-')&&k!==SHELL).map(k=>caches.delete(k)))).then(()=>self.clients.claim())
));

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
            const key=(url.pathname==='/'||url.pathname==='/index.html'||event.request.mode==='navigate')?'/':event.request;
            const shell=await caches.open(SHELL);
            return await shell.match(key,{ignoreSearch:true}) || await caches.match(key,{ignoreSearch:true});
        }));
    }
});
