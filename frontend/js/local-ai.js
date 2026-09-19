const localAI={worker:null,pending:null,recorder:null,stream:null,chunks:[],timer:null};
function aiStatus(message) {document.getElementById('mobileAIStatus').textContent=message; const voiceStatus=document.getElementById('mobileVoiceStatus');if(voiceStatus)voiceStatus.textContent=message;}
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
        console.log('Transcripción obtenida:', result.text);

        if (localAI.photoTarget) {
            localAI.photoTarget = false;
            const photoArea = document.getElementById('mobilePhotoText');
            if (photoArea) {
                let textToAdd = '';
                try {
                    const plan = UMLCommands.parse(result.text);
                    if (plan.action === 'createClass') {
                        const lines = [plan.name, ...plan.attributes.map(a => `${a.name}: ${a.type}`)];
                        textToAdd = lines.join('\n');
                    } else if (plan.action === 'addAttributes') {
                        textToAdd = plan.attributes.map(a => `${a.name}: ${a.type}`).join('\n');
                    }
                } catch(e) {
                    textToAdd = result.text.trim();
                }
                if (textToAdd) {
                    photoArea.value = (photoArea.value.trim() ? photoArea.value.trim() + '\n' : '') + textToAdd;
                }
                const photoReview = document.getElementById('mobilePhotoReview');
                if (photoReview) photoReview.hidden = false;
                const status = document.getElementById('mobilePhotoStatus');
                if (status) status.textContent = `Voz aplicada al borrador: "${result.text}".`;
                aiStatus(`Voz añadida al borrador de la foto.`);
                return;
            }
        }

        const commandInput=document.getElementById('mobileCommand');
        if (commandInput) {
            commandInput.value=result.text;
            commandInput.dispatchEvent(new Event('input',{bubbles:true}));
        }
        if(typeof reviewMobileCommand==='function') {
            reviewMobileCommand();
        }
        aiStatus(`Transcripción: "${result.text}".`);
        window.dispatchEvent(new CustomEvent('voice-transcription-done', { detail: { text: result.text } }));
    } finally {await context.close();}
}
async function toggleLocalRecording(forPhoto = false) {
    const button=forPhoto ? document.getElementById('btnVoiceSupplementPhoto') : document.getElementById('mobileMic');
    if(localAI.recorder?.state==='recording') {
        localAI.recorder.stop();
        window.dispatchEvent(new CustomEvent('voice-recording-stopped'));
        return;
    }
    localAI.photoTarget = !!forPhoto;
    try {
        aiStatus('Preparando el motor antes de grabar…');
        if(button)button.disabled=true;
        window.dispatchEvent(new CustomEvent('voice-recording-preparing'));
        await runLocalVoice({type:'prepare'});
        try {
            localAI.stream=await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false }
            });
        } catch(audioErr) {
            localAI.stream=await navigator.mediaDevices.getUserMedia({audio:true});
        }
        localAI.chunks=[];
        localAI.recorder=new MediaRecorder(localAI.stream);
        localAI.recorder.ondataavailable=e=>{if(e.data.size)localAI.chunks.push(e.data);};
        localAI.recorder.onstop=async()=>{
            if(button) {
                button.classList.remove('is-recording');
                button.textContent=forPhoto ? '🎙️ Dictar corrección o atributo' : 'Dictar diagrama';
                button.disabled=true;
            }
            window.dispatchEvent(new CustomEvent('voice-recording-stopped'));
            aiStatus('Grabación terminada. Transcribiendo en este dispositivo…');
            window.dispatchEvent(new CustomEvent('voice-transcribing'));
            clearTimeout(localAI.timer);
            localAI.stream?.getTracks().forEach(track=>track.stop());
            try {
                await transcribeLocalFile(new Blob(localAI.chunks,{type:localAI.recorder.mimeType}));
            } catch(e) {
                aiStatus(e.message);
                window.dispatchEvent(new CustomEvent('voice-recording-error', { detail: { error: e.message } }));
            } finally {
                if(button)button.disabled=false;
            }
        };
        localAI.recorder.start();
        window.dispatchEvent(new CustomEvent('voice-recording-started', { detail: { stream: localAI.stream } }));
        if(button) {
            button.classList.add('is-recording');
            button.textContent='● Escuchando — Detener';
            button.disabled=false;
        }
        aiStatus(forPhoto ? 'Grabando corrección para la foto… Di el nombre de clase o atributos.' : 'Grabando comando de diagrama…');
        localAI.timer=setTimeout(()=>{if(localAI.recorder?.state==='recording')localAI.recorder.stop();},30000);
    } catch(error) {
        localAI.stream?.getTracks().forEach(track=>track.stop());
        aiStatus('Error de micrófono: '+(error.message||error.name));
        window.dispatchEvent(new CustomEvent('voice-recording-error', { detail: { error: (error.message||error.name) } }));
        if(button)button.disabled=false;
    }
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
    const statusEl = document.getElementById('mobilePhotoStatus');
    const progBar = document.getElementById('mobilePhotoProgressBar');
    const progBox = document.getElementById('mobilePhotoProgress');
    const update = (msg, pct = null) => {
        aiStatus(msg);
        if (statusEl) statusEl.textContent = msg;
        if (progBox && progBar) {
            if (pct !== null) {
                progBox.style.display = 'block';
                progBar.style.width = Math.min(100, Math.max(0, pct)) + '%';
            } else {
                progBox.style.display = 'none';
            }
        }
    };
    if(!window.Tesseract) {
        update('Cargando motor OCR local…', 10);
        await new Promise((resolve,reject)=>{
            const script=document.createElement('script');
            script.src='/assets/vendor/tesseract.min.js';
            script.onload=resolve;
            script.onerror=()=>reject(new Error('No se pudo cargar el archivo tesseract.min.js'));
            document.head.append(script);
        });
    }
    update('Iniciando lector de imagen local…', 25);
    const worker=await Tesseract.createWorker('eng',1,{
        workerPath:'/assets/vendor/worker.min.js',
        corePath:'/assets/vendor/',
        langPath:'/assets/vendor/',
        gzip: false,
        logger:m=>{
            if(m.status) {
                const pct = Math.round((m.progress||0)*100);
                update(`Foto: ${m.status} (${pct}%)`, Math.max(25, pct));
            }
        }
    });
    try {
        update('Reconociendo texto en la imagen…', 75);
        const result=await worker.recognize(file);
        update('¡Texto reconocido con éxito!', 100);
        return result.data.text;
    } finally {
        await worker.terminate();
    }
}
