const SHELL='uml-shell-v1';
const FILES=['/','/css/index.css','/css/mobile.css','/js/collaboration.js','/js/app.js','/js/uml-commands.js','/js/mobile.js','/js/local-ai.js','/js/voice-worker.js','/manifest.webmanifest'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(SHELL).then(cache=>cache.addAll(FILES)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
self.addEventListener('fetch',event=>{
    const url=new URL(event.request.url);
    if(event.request.method!=='GET'||url.origin!==location.origin||url.pathname.startsWith('/api/')||url.pathname.startsWith('/ws/'))return;
    if(url.pathname.startsWith('/assets/')) {
        event.respondWith(caches.match(event.request,{ignoreSearch:true}).then(cached=>cached||fetch(event.request)));
    } else {
        event.respondWith(fetch(event.request).then(response=>{
            if(response.ok) {const copy=response.clone();event.waitUntil(caches.open(SHELL).then(cache=>cache.put(url.pathname,copy)));}return response;
        }).catch(()=>caches.match(url.pathname==='/'?'/':event.request,{ignoreSearch:true})));
    }
});
