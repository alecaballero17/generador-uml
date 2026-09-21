const localAI={worker:null,pending:null,recorder:null,stream:null,chunks:[],timer:null};
function supplementPhotoDraft(text, command) {
    const correction=command.trim().replace(/[.!?]+$/,'').match(/^en (?:la )?clase (.+?),?\s+(?:cambia|corrige|renombra) (?:el )?atributo (.+?)\s+(?:por|a)\s+([\p{L}_][\p{L}\p{N}_]*)$/iu);
    const plan=correction ? {action:'correctPhotoAttribute',name:correction[1],oldName:correction[2],newName:correction[3]} : UMLCommands.parse(command);
    const blocks=text.trim() ? text.trim().split(/\r?\n\s*\r?\n/).map(b=>b.split(/\r?\n/)) : [];
    const key=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/gi,'').toLowerCase();
    const matches=blocks.filter(lines=>key(lines[0])===key(plan.name||''));
    const additions=(plan.attributes||[]).map(a=>`${a.name}: ${a.type}`);
    if(plan.action==='correctPhotoAttribute') {
        if(matches.length!==1)throw new Error('No se encontró una única clase con ese nombre en la foto.');
        const lines=matches[0], candidates=[];
        for(let i=1;i<lines.length;i++){
            if(lines[i].includes('('))continue;
            const parts=lines[i].match(/^(\s*[+~#-]?\s*)([^:]+?)(\s*:\s*.*)?$/);
            if(!parts)continue;
            if(key(parts[2])===key(plan.oldName))candidates.push({index:i,parts});
            else if(key(parts[2])===key(plan.newName))throw new Error('Ya existe un atributo con el nombre nuevo.');
        }
        if(candidates.length!==1)throw new Error('Indica el nombre de un único atributo del borrador.');
        const {index,parts}=candidates[0];
        lines[index]=parts[1]+plan.newName+(parts[3]||'');
    } else if(plan.action==='createClass') {
        if(matches.length)throw new Error('Esa clase ya está en la foto. Indica qué atributo agregar.');
        blocks.push([plan.name,...additions]);
    } else if(plan.action==='addAttributes') {
        if(matches.length!==1)throw new Error('No se encontró una única clase con ese nombre en la foto.');
        const lines=matches[0];
        const existing=new Set(lines.slice(1).filter(line=>!line.includes('(')).map(line=>key(line.replace(/^[+~#-]\s*/,'').split(':')[0])));
        for(const attribute of plan.attributes){
            if(existing.has(key(attribute.name)))throw new Error(`El atributo ${attribute.name} ya existe; corrígelo en el texto.`);
            existing.add(key(attribute.name));
        }
        const operation=lines.findIndex((line,index)=>index>0 && line.includes('('));
        lines.splice(operation<0 ? lines.length : operation,0,...additions);
    } else throw new Error('Para complementar la foto, indica la clase y los atributos que quieres agregar.');
    return blocks.map(lines=>lines.join('\n')).join('\n\n');
}
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
                try {
                    photoArea.value = supplementPhotoDraft(photoArea.value, result.text);
                } catch(error) {
                    const status=document.getElementById('mobilePhotoStatus');
                    if(status)status.textContent=`No se cambió el borrador: ${error.message} Texto reconocido: ${result.text}`;
                    aiStatus('Revisa la transcripción; el borrador de la foto se conserva.');
                    return;
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
        localStorage.removeItem('uml_offline_prepared');
        if(!('serviceWorker' in navigator))throw new Error('Este navegador no admite instalación sin conexión');
        await navigator.serviceWorker.register('/sw.js');await navigator.serviceWorker.ready;
        const cache=await caches.open('uml-local-ai-v1');
        const manifestResponse=await fetch('/assets/offline-files.json',{cache:'no-store'});
        if(!manifestResponse.ok)throw new Error('No se pudo obtener la lista de archivos sin conexión.');
        const manifest=await manifestResponse.json();
        if(!Array.isArray(manifest)||!manifest.length||manifest.some(path=>typeof path!=='string'||!path.startsWith('/')||path.startsWith('//')))throw new Error('La lista de archivos sin conexión es inválida.');
        for(let i=0;i<manifest.length;i++) {
            aiStatus(`Preparando archivos sin conexión ${i+1}/${manifest.length}`);
            if(!manifest[i].startsWith('/assets/') || !await cache.match(manifest[i])) {const response=await fetch(manifest[i],{cache:'no-cache'});if(!response.ok)throw new Error(`Falta el archivo ${manifest[i]}`);await cache.put(manifest[i],response);}
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
function detectPhotoConnections(image, boxes, markers = []) {
    const {width:w,height:h,data}=image, mask=new Uint8Array(w*h);
    for(let i=0;i<mask.length;i++)mask[i]=data[i*4]+data[i*4+1]+data[i*4+2]<390?1:0;
    for(const b of boxes)for(let y=Math.max(0,b.y-8);y<Math.min(h,b.y+b.height+9);y++)
        mask.fill(0,y*w+Math.max(0,b.x-8),y*w+Math.min(w,b.x+b.width+9));
    const connections=[],ambiguous=[],suggestions=[];
    const queue=new Int32Array(w*h);
    for(let seed=0;seed<mask.length;seed++) {
        if(!mask[seed])continue;
        let head=0,tail=1;queue[0]=seed;mask[seed]=0;
        const touched=new Set(),markerDistances=markers.map(()=>Infinity);
        while(head<tail){const pos=queue[head++],x=pos%w,y=Math.floor(pos/w);
            markers.forEach((m,i)=>{markerDistances[i]=Math.min(markerDistances[i],Math.hypot(x-m.x,y-m.y));});
            boxes.forEach((b,i)=>{if(x>=b.x-13&&x<=b.x+b.width+13&&y>=b.y-13&&y<=b.y+b.height+13)touched.add(i);});
            for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
                const nx=x+dx,ny=y+dy;if(nx<0||ny<0||nx>=w||ny>=h)continue;
                const next=ny*w+nx;if(mask[next]){mask[next]=0;queue[tail++]=next;}
            }
        }
        if(tail<25||touched.size<2)continue;
        const indices=[...touched].sort((a,b)=>a-b);
        const localMarkers=markers.filter((m,i)=>markerDistances[i]<=18&&indices.includes(m.box));
        if(indices.length===2&&localMarkers.length===1&&localMarkers[0].kind==='hollowDiamond') {
            const source=localMarkers[0].box,target=indices.find(i=>i!==source);
            suggestions.push({source,target,type:'aggregation',reason:'Rombo vacío conectado a la línea'});
        }
        const target=indices.length===2?connections:ambiguous;
        if(!target.some(item=>item.join(',')===indices.join(',')))target.push(indices);
    }
    return {connections,ambiguous,suggestions};
}
// Recognize enclosed hollow markers; text inside class boxes is excluded.
function detectPhotoMarkers(image, boxes) {
    const {width:w,height:h,data}=image, seen=new Uint8Array(w*h),queue=new Int32Array(w*h),markers=[];
    const white=i=>data[i*4]+data[i*4+1]+data[i*4+2]>=450;
    for(let seed=0;seed<seen.length;seed++) {
        if(seen[seed]||!white(seed))continue;
        let head=0,tail=1,minX=w,maxX=0,minY=h,maxY=0,border=false;queue[0]=seed;seen[seed]=1;
        while(head<tail){const pos=queue[head++],x=pos%w,y=Math.floor(pos/w);
            minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);
            if(x===0||y===0||x===w-1||y===h-1)border=true;
            for(let direction=0;direction<4;direction++){
                const nx=x+(direction===0?-1:direction===1?1:0),ny=y+(direction===2?-1:direction===3?1:0);
                if(nx<0||ny<0||nx>=w||ny>=h)continue;const next=ny*w+nx;
                if(!seen[next]&&white(next)){seen[next]=1;queue[tail++]=next;}
            }
        }
        const bw=maxX-minX+1,bh=maxY-minY+1,cx=(minX+maxX)/2,cy=(minY+maxY)/2;
        if(border||bw<7||bh<7||bw>70||bh>70||tail<25||tail/(bw*bh)<.3||tail/(bw*bh)>.75)continue;
        if(boxes.some(b=>cx>=b.x-5&&cx<=b.x+b.width+5&&cy>=b.y-5&&cy<=b.y+b.height+5))continue;
        const rows=new Array(bh).fill(0),cols=new Array(bw).fill(0);
        for(let i=0;i<tail;i++){rows[Math.floor(queue[i]/w)-minY]++;cols[queue[i]%w-minX]++;}
        const peak=values=>{const max=Math.max(...values),indices=values.map((v,i)=>v>=max*.9?i:-1).filter(i=>i>=0);return indices.reduce((a,b)=>a+b,0)/indices.length/(values.length-1);};
        const px=peak(cols),py=peak(rows),middle=v=>v>.28&&v<.72;
        let kind=null;
        if(middle(px)&&middle(py))kind='hollowDiamond';
        else if((middle(px)&&(py<.2||py>.8))||(middle(py)&&(px<.2||px>.8)))kind='hollowTriangle';
        if(!kind)continue;
        const distances=boxes.map((b,i)=>({index:i,d:Math.hypot(Math.max(b.x-5-cx,0,cx-b.x-b.width-5),Math.max(b.y-5-cy,0,cy-b.y-b.height-5))})).sort((a,b)=>a.d-b.d);
        if(!distances.length||distances[0].d>25)continue;
        if(distances[1]&&distances[1].d-distances[0].d<5)continue;
        markers.push({kind,box:distances[0].index,x:cx,y:cy});
    }
    return markers;
}
function estimatePhotoSkew(image) {
    const {width,height,data}=image, points=[];
    const stride=Math.max(1,Math.ceil(Math.max(width,height)/600));
    for(let y=0;y<height;y+=stride)for(let x=0;x<width;x+=stride){
        const i=(y*width+x)*4;
        if(data[i+3]>128 && data[i]+data[i+1]+data[i+2]<420)points.push([x/stride,y/stride]);
    }
    if(points.length<100)return 0;
    const size=Math.ceil((width+height)/stride)*2+4;
    const score=degrees=>{
        const angle=degrees*Math.PI/180,s=Math.sin(angle),c=Math.cos(angle);
        const rows=new Uint32Array(size);let value=0;
        for(const [x,y] of points){const k=Math.round(y*c-x*s)+Math.floor(size/2);if(k>=0&&k<size)rows[k]++;}
        for(const count of rows)value+=count*count;
        return value;
    };
    const initial=score(0);let best=initial,angle=0;
    for(let candidate=-12;candidate<=12;candidate+=0.5){const value=score(candidate);if(value>best){best=value;angle=candidate;}}
    // Leave weak evidence unchanged rather than rotating arbitrary photographs.
    return Math.abs(angle)>=0.5 && best>initial*1.2 ? angle : 0;
}
function straightenPhotoCanvas(canvas) {
    const angle=estimatePhotoSkew(canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height));
    if(!angle)return canvas;
    const radians=-angle*Math.PI/180,c=Math.abs(Math.cos(radians)),s=Math.abs(Math.sin(radians));
    const result=document.createElement('canvas');
    result.width=Math.ceil(canvas.width*c+canvas.height*s);
    result.height=Math.ceil(canvas.height*c+canvas.width*s);
    const ctx=result.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,result.width,result.height);
    ctx.translate(result.width/2,result.height/2);ctx.rotate(radians);ctx.drawImage(canvas,-canvas.width/2,-canvas.height/2);
    return result;
}
async function photoCanvas(file) {
    const bitmap=await createImageBitmap(file);
    const canvas=document.createElement('canvas');
    const scale=Math.min(1,1800/Math.max(bitmap.width,bitmap.height));
    canvas.width=Math.round(bitmap.width*scale);canvas.height=Math.round(bitmap.height*scale);
    canvas.getContext('2d').drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close();
    return straightenPhotoCanvas(canvas);
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
        const pixels=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height);
        const markers=detectPhotoMarkers(pixels,boxes);
        return {text:blocks.join('\n\n'),structured:true,count:blocks.length,names,markers,...detectPhotoConnections(pixels,boxes,markers)};
    } finally {
        await worker.terminate();
    }
}
