const localAI={worker:null,pending:null,recorder:null,stream:null,chunks:[],timer:null};
function aiStatus(message) {document.getElementById('mobileAIStatus').textContent=message;}
function runLocalVoice(payload) {
    if(localAI.pending) return Promise.reject(new Error('Espera a que termine el audio anterior'));
    if(!localAI.worker) {
        localAI.worker=new Worker('/js/voice-worker.js',{type:'module'});
        localAI.worker.onmessage=event=>{
            const data=event.data;
            if(data.status) aiStatus(data.status);
            if(data.error||data.ready||typeof data.text==='string') {
                const pending=localAI.pending;localAI.pending=null;
                if(!pending)return;
                if(data.error)pending.reject(new Error(data.error));else pending.resolve(data);
            }
        };
        localAI.worker.onerror=()=>{const p=localAI.pending;localAI.pending=null;localAI.worker.terminate();localAI.worker=null;p?.reject(new Error('No se pudo iniciar el motor local. Prepara los archivos e inténtalo de nuevo.'));};
    }
    return new Promise((resolve,reject)=>{localAI.pending={resolve,reject};localAI.worker.postMessage(payload);});
}
async function transcribeLocalFile(file,language='spanish') {
    const context=new AudioContext();
    try {
        const decoded=await context.decodeAudioData(await file.arrayBuffer());
        if(decoded.duration>60)throw new Error('Usa audios de hasta un minuto');
        const offline=new OfflineAudioContext(1,Math.ceil(decoded.duration*16000),16000);
        const source=offline.createBufferSource();source.buffer=decoded;source.connect(offline.destination);source.start();
        const audio=(await offline.startRendering()).getChannelData(0);
        const result=await runLocalVoice({type:'transcribe',audio,language});
        document.getElementById('mobileCommand').value=result.text;
        aiStatus('Transcripción local lista. Revisa el texto y pulsa Revisar comando.');
    } finally {await context.close();}
}
async function toggleLocalRecording() {
    const button=document.getElementById('mobileMic');
    if(localAI.recorder?.state==='recording') {localAI.recorder.stop();return;}
    try {
        aiStatus('Preparando el motor antes de grabar…');button.disabled=true;
        await runLocalVoice({type:'prepare'});
        localAI.stream=await navigator.mediaDevices.getUserMedia({audio:true});
        localAI.chunks=[];
        localAI.recorder=new MediaRecorder(localAI.stream);
        localAI.recorder.ondataavailable=e=>{if(e.data.size)localAI.chunks.push(e.data);};
        localAI.recorder.onstop=async()=>{
            clearTimeout(localAI.timer);localAI.stream.getTracks().forEach(track=>track.stop());
            button.textContent='Dictar diagrama';button.disabled=true;
            try {await transcribeLocalFile(new Blob(localAI.chunks,{type:localAI.recorder.mimeType}));}catch(e){aiStatus(e.message);}finally{button.disabled=false;}
        };
        localAI.recorder.start();button.textContent='Detener grabación';button.disabled=false;
        aiStatus('Grabando. Tu audio se procesa aquí y no se envía al servidor.');
        localAI.timer=setTimeout(()=>{if(localAI.recorder?.state==='recording')localAI.recorder.stop();},30000);
    } catch(error) {localAI.stream?.getTracks().forEach(track=>track.stop());aiStatus(error.message);button.disabled=false;}
}
async function prepareOffline() {
    const button=document.getElementById('prepareOffline');button.disabled=true;
    try {
        if(!('serviceWorker' in navigator))throw new Error('Este navegador no admite instalación sin conexión');
        await navigator.serviceWorker.register('/sw.js');await navigator.serviceWorker.ready;
        const cache=await caches.open('uml-local-ai-v1');
        const manifest=await (await fetch('/assets/offline-files.json')).json();
        for(let i=0;i<manifest.length;i++) {
            aiStatus(`Preparando archivos sin conexión ${i+1}/${manifest.length}`);
            if(!await cache.match(manifest[i])) {const response=await fetch(manifest[i]);if(!response.ok)throw new Error(`Falta el archivo ${manifest[i]}`);await cache.put(manifest[i],response);}
        }
        await runLocalVoice({type:'prepare'});
        await navigator.storage?.persist?.();
        localStorage.setItem('uml_offline_prepared','yes');
        aiStatus('Archivos y motor de voz preparados. El navegador puede borrar almacenamiento si falta espacio.');
    } catch(error) {aiStatus(error.message);} finally {button.disabled=false;}
}
async function recognizeLocalPhoto(file) {
    if(!window.Tesseract) {
        await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='/assets/vendor/tesseract.min.js';script.onload=resolve;script.onerror=()=>reject(new Error('Prepara los archivos OCR antes de desconectarte'));document.head.append(script);});
    }
    aiStatus('Leyendo la imagen en este dispositivo…');
    const worker=await Tesseract.createWorker('eng',1,{workerPath:'/assets/vendor/worker.min.js',corePath:'/assets/vendor/',langPath:'/assets/vendor/',logger:m=>{if(m.status)aiStatus(`Foto: ${m.status} ${Math.round((m.progress||0)*100)}%`);}});
    try {const result=await worker.recognize(file);return result.data.text;}finally{await worker.terminate();}
}
