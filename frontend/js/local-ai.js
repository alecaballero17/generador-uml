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
// Detect closed, axis-aligned UML compartments before OCR. No colour assumption.
function detectPhotoBoxes(image) {
    const {width:w,height:h,data}=image;
    const dark=(x,y)=>{const i=(y*w+x)*4;return data[i]+data[i+1]+data[i+2]<330;};
    const groups=[];
    for(let y=0;y<h;y++) {
        let start=-1;
        for(let x=0;x<=w;x++) {
            if(x<w&&dark(x,y)){if(start<0)start=x;continue;}
            if(start>=0&&x-start>=Math.max(55,w*.045)) {
                let group=groups.find(g=>Math.abs(g.x-start)<=5&&Math.abs(g.right-x)<=5);
                if(!group){group={x:start,right:x,rows:[]};groups.push(group);}
                const last=group.rows[group.rows.length-1];
                if(last!==undefined&&y-last<5)group.rows[group.rows.length-1]=y;
                else group.rows.push(y);
            }
            start=-1;
        }
    }
    const boxes=[];
    for(const g of groups) {
        if(g.rows.length<3)continue;
        const top=g.rows[0],bottom=g.rows[g.rows.length-1];
        if(bottom-top<35)continue;
        const vertical=x=>{let hits=0;for(let y=top;y<=bottom;y++){let found=false;for(let dx=-4;dx<=4;dx++)if(x+dx>=0&&x+dx<w&&dark(x+dx,y))found=true;if(found)hits++;}return hits/(bottom-top+1);};
        if(vertical(g.x)<.85||vertical(g.right-1)<.85)continue;
        boxes.push({x:g.x+5,y:top+5,width:g.right-g.x-10,height:bottom-top-10,headerBottom:g.rows[1]-4,attributesBottom:g.rows[2]-4});
    }
    return boxes.sort((a,b)=>a.y-b.y||a.x-b.x);
}
// Candidate connections only: crossings and arrow semantics require review.
function detectPhotoConnections(image, boxes) {
    const {width:w,height:h,data}=image, mask=new Uint8Array(w*h);
    for(let i=0;i<mask.length;i++)mask[i]=data[i*4]+data[i*4+1]+data[i*4+2]<390?1:0;
    for(const b of boxes)for(let y=Math.max(0,b.y-8);y<Math.min(h,b.y+b.height+9);y++)
        mask.fill(0,y*w+Math.max(0,b.x-8),y*w+Math.min(w,b.x+b.width+9));
    const connections=[],ambiguous=[];
    const queue=new Int32Array(w*h);
    for(let seed=0;seed<mask.length;seed++) {
        if(!mask[seed])continue;
        let head=0,tail=1;queue[0]=seed;mask[seed]=0;
        const touched=new Set();
        while(head<tail){const pos=queue[head++],x=pos%w,y=Math.floor(pos/w);
            boxes.forEach((b,i)=>{if(x>=b.x-13&&x<=b.x+b.width+13&&y>=b.y-13&&y<=b.y+b.height+13)touched.add(i);});
            for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
                const nx=x+dx,ny=y+dy;if(nx<0||ny<0||nx>=w||ny>=h)continue;
                const next=ny*w+nx;if(mask[next]){mask[next]=0;queue[tail++]=next;}
            }
        }
        if(tail<25||touched.size<2)continue;
        const indices=[...touched].sort((a,b)=>a-b);
        const target=indices.length===2?connections:ambiguous;
        if(!target.some(item=>item.join(',')===indices.join(',')))target.push(indices);
    }
    return {connections,ambiguous};
}
async function photoCanvas(file) {
    const bitmap=await createImageBitmap(file);
    const canvas=document.createElement('canvas');
    const scale=Math.min(1,1800/Math.max(bitmap.width,bitmap.height));
    canvas.width=Math.round(bitmap.width*scale);canvas.height=Math.round(bitmap.height*scale);
    canvas.getContext('2d').drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close();
    return canvas;
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
        gzip: true,
        logger:m=>{
            if(m.status) {
                const pct = Math.round((m.progress||0)*100);
                update(`Foto: ${m.status} (${pct}%)`, Math.max(25, pct));
            }
        }
    });
    try {
        const canvas=await photoCanvas(file);
        const boxes=detectPhotoBoxes(canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height));
        if(!boxes.length) {
            const result=await worker.recognize(canvas);
            return {text:result.data.text,structured:false,count:0};
        }
        await worker.setParameters({tessedit_pageseg_mode:'6'});
        const blocks=[], names=[];
        const read=async(box,top,bottom)=>{
            const crop=document.createElement('canvas');crop.width=box.width*3;crop.height=Math.max(1,bottom-top)*3;
            const ctx=crop.getContext('2d');ctx.drawImage(canvas,box.x,top,box.width,Math.max(1,bottom-top),0,0,crop.width,crop.height);
            const pixels=ctx.getImageData(0,0,crop.width,crop.height);
            for(let i=0;i<pixels.data.length;i+=4){const v=pixels.data[i]+pixels.data[i+1]+pixels.data[i+2]<420?0:255;pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=v;}
            ctx.putImageData(pixels,0,0);
            return (await worker.recognize(crop)).data.text.trim();
        };
        for(let i=0;i<boxes.length;i++) {
            update(`Leyendo clase ${i+1} de ${boxes.length}…`,25+70*i/boxes.length);
            const box=boxes[i];
            const name=await read(box,box.y,box.headerBottom);
            const attrs=await read(box,box.headerBottom+9,box.attributesBottom);
            const methods=box.y+box.height>box.attributesBottom+10 ? await read(box,box.attributesBottom+9,box.y+box.height) : '';
            names.push(name.replace(/\n/g,' ').trim());
            if(name)blocks.push(name.replace(/\n/g,' ')+'\n'+(attrs+'\n'+methods).split('\n').map(line=>line.trim()).filter(Boolean).join('\n'));
        }
        update('Lectura terminada; revisa las clases antes de importar.',100);
        return {text:blocks.join('\n\n'),structured:true,count:blocks.length,names,...detectPhotoConnections(canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height),boxes)};
    } finally {
        await worker.terminate();
    }
}
