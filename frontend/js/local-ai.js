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
    const minWidth=Math.max(90,Math.round(w*.045)),minHeight=Math.max(60,Math.round(h*.06));
    // A pen lift or a photographed/reflected section can interrupt a border
    // by several percent of the image width. This is still bounded; the
    // resulting candidate must independently satisfy both vertical sides.
    const horizontalGap=Math.max(3,Math.round(w*.06));
    const endpointTolerance=Math.max(5,Math.round(w*.06));
    // This is deliberately used only *after* an outer rectangle has been
    // found. A photographed outer border may be interrupted, whereas a
    // divider is recognized from broad horizontal evidence inside that box.
    // Text strokes can be long, but they do not have enough ink near both
    // interior ends and across most of the row. Measurements are box-relative.
    const structuralBands=(left,right,top,bottom)=>{
        const span=Math.max(1,right-left),edge=Math.max(8,Math.round(span*.06)),rows=[];
        for(let y=top;y<=bottom;y++){
            const inkAt=x=>{for(let dy=-2;dy<=2;dy++)if(y+dy>=0&&y+dy<h&&dark(x,y+dy))return true;return false;};
            let covered=0;
            for(let x=left;x<=right;x++){
                if(inkAt(x))covered++;
            }
            const endDensity=side=>{
                let ink=0,total=0;
                // Ignore the actual vertical border: it is dark on every row
                // and would otherwise make any nearby text look connected.
                const start=side==='left'?left+1:left-edge,end=side==='left'?left+edge:right-1;
                for(let x=start;x<=end;x++){total++;if(inkAt(x))ink++;}
                return total?ink/total:0;
            };
            // The 0.62 coverage accepts antialiasing and small gaps; 0.20 at
            // both ends rejects a long underline isolated from the borders.
            if(covered/(span+1)>=.62&&endDensity('left')>=.20&&endDensity('right')>=.20)rows.push(y);
        }
        const bands=[];
        for(const y of rows){const last=bands[bands.length-1];if(last&&y-last.bottom<=3)last.bottom=y;else bands.push({top:y,bottom:y});}
        return bands.map(b=>({top:b.top,bottom:b.bottom,center:Math.round((b.top+b.bottom)/2)}));
    };
    const groups=[];
    for(let y=0;y<h;y++) {
        let start=-1,lastInk=-1;
        for(let x=0;x<=w;x++) {
            if(x<w&&dark(x,y)){if(start<0)start=x;lastInk=x;continue;}
            // A photographed rule can contain a short white break from glare,
            // antialiasing or a pen lift. Keep one candidate span while the
            // gap remains small relative to the whole source image.
            if(start>=0&&x-lastInk<=horizontalGap)continue;
            if(start>=0&&lastInk-start+1>=Math.max(55,w*.045)) {
                const right=lastInk+1;
                let group=groups.find(g=>Math.abs(g.x-start)<=endpointTolerance&&Math.abs(g.right-right)<=endpointTolerance);
                if(!group){group={x:start,right,rows:[]};groups.push(group);}
                const last=group.rows[group.rows.length-1];
                if(last!==undefined&&y-last<5)group.rows[group.rows.length-1]=y;
                else group.rows.push(y);
            }
            start=-1;lastInk=-1;
        }
    }
    const boxes=[];
    for(const g of groups) {
        if(g.rows.length<2)continue;
        const top=g.rows[0],bottom=g.rows[g.rows.length-1];
        if(g.right-g.x<minWidth||bottom-top<minHeight)continue;
        const verticalTolerance=Math.max(4,Math.round((g.right-g.x)*.06));
        const vertical=x=>{let hits=0;for(let y=top;y<=bottom;y++){let found=false;for(let dx=-verticalTolerance;dx<=verticalTolerance;dx++)if(x+dx>=0&&x+dx<w&&dark(x+dx,y))found=true;if(found)hits++;}return hits/(bottom-top+1);};
        if(vertical(g.x)<.72||vertical(g.right-1)<.72)continue;
        const bands=structuralBands(g.x,g.right-1,top,bottom);
        // Do not require a perfect horizontal/vertical join here. The prior
        // candidate plus tolerant vertical-support check establishes the outer
        // rectangle; bands are only candidates for internal compartments.
        const inset=Math.max(3,Math.round(Math.min(g.right-g.x,bottom-top)*.015));
        const minCompartment=Math.max(12,Math.round((bottom-top)*.06));
        const dividerYs=bands.slice(1,-1).map(b=>b.center).filter(y=>y-top>=minCompartment&&bottom-y>=minCompartment);
        const headerBottom=dividerYs[0]===undefined ? bottom-inset : dividerYs[0]-inset;
        const attributesBottom=dividerYs[1]===undefined ? bottom-inset : dividerYs[1]-inset;
        boxes.push({x:g.x+inset,y:top+inset,width:g.right-g.x-inset*2,height:bottom-top-inset*2,
            // Metadata only: retained for the opt-in OCR diagnostic view.
            outerX:g.x,outerY:top,outerWidth:g.right-g.x,outerHeight:bottom-top,dividerYs,headerBottom,attributesBottom,dividerPadding:inset});
    }
    // A large UML box can contain glyphs or small closed shapes.  They are not
    // independent classes, even when their strokes accidentally satisfy the
    // rectangle heuristic.
    return boxes.sort((a,b)=>b.width*b.height-a.width*a.height).filter((box,index,all)=>
        !all.slice(0,index).some(outer=>box.x>=outer.x&&box.y>=outer.y&&box.x+box.width<=outer.x+outer.width&&box.y+box.height<=outer.y+outer.height)
    ).sort((a,b)=>a.y-b.y||a.x-b.x);
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
// OCR needs text, not the rectangle and compartment rules that surround it.
// Keep this browser-only so the web and Android WebView use the same pipeline.
function photoOtsuThreshold(gray) {
    const histogram=new Uint32Array(256);let sum=0,total=gray.length;
    for(const value of gray){histogram[value]++;sum+=value;}
    let sumBackground=0,weightBackground=0,best=-1,threshold=175;
    for(let i=0;i<256;i++){
        weightBackground+=histogram[i];if(!weightBackground)continue;
        const weightForeground=total-weightBackground;if(!weightForeground)break;
        sumBackground+=i*histogram[i];
        const meanBackground=sumBackground/weightBackground,meanForeground=(sum-sumBackground)/weightForeground;
        const variance=weightBackground*weightForeground*(meanBackground-meanForeground)**2;
        if(variance>best){best=variance;threshold=i;}
    }
    return Math.max(80,Math.min(220,threshold));
}
function removePhotoRuleLines(image) {
    const {width,height,data}=image,black=(x,y)=>data[(y*width+x)*4]<128;
    const erase=[];
    // A UML divider spans most of its compartment.  Short '-' characters and
    // operation punctuation are deliberately below these limits.
    const horizontal=Math.max(42,Math.round(width*.55));
    for(let y=0;y<height;y++){
        let start=-1;
        for(let x=0;x<=width;x++){
            if(x<width&&black(x,y)){if(start<0)start=x;continue;}
            if(start>=0&&x-start>=horizontal)erase.push([start,y,x-1,y]);
            start=-1;
        }
    }
    const vertical=Math.max(42,Math.round(height*.78));
    for(let x=0;x<width;x++){
        let start=-1;
        for(let y=0;y<=height;y++){
            if(y<height&&black(x,y)){if(start<0)start=y;continue;}
            if(start>=0&&y-start>=vertical)erase.push([x,start,x,y-1]);
            start=-1;
        }
    }
    for(const [x1,y1,x2,y2] of erase)for(let y=y1;y<=y2;y++)for(let x=x1;x<=x2;x++){
        const i=(y*width+x)*4;data[i]=data[i+1]=data[i+2]=255;
    }
    return image;
}
function binarizePhotoOcrCanvas(source) {
    const canvas=document.createElement('canvas');canvas.width=source.width;canvas.height=source.height;
    const ctx=canvas.getContext('2d');ctx.drawImage(source,0,0);
    const pixels=ctx.getImageData(0,0,canvas.width,canvas.height),gray=new Uint8Array(canvas.width*canvas.height);
    for(let p=0;p<gray.length;p++){
        const i=p*4;gray[p]=Math.round(.2126*pixels.data[i]+.7152*pixels.data[i+1]+.0722*pixels.data[i+2]);
    }
    const threshold=photoOtsuThreshold(gray);
    for(let p=0;p<gray.length;p++){
        const i=p*4,value=gray[p]<threshold?0:255;pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=value;pixels.data[i+3]=255;
    }
    ctx.putImageData(pixels,0,0);return canvas;
}
function removePhotoRulesFromCanvas(canvas) {
    const ctx=canvas.getContext('2d');const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
    removePhotoRuleLines(pixels);ctx.putImageData(pixels,0,0);return canvas;
}
function preparePhotoOcrCanvas(source) {
    return removePhotoRulesFromCanvas(binarizePhotoOcrCanvas(source));
}
function photoOcrDebugEnabled() {
    try{return new URLSearchParams(window.location.search).get('ocrDebug')==='1';}catch{return false;}
}
function addPhotoOcrDiagnostic(diagnostics,stage,details={}) {
    if(diagnostics)diagnostics.push({stage,...details});
}
function addPhotoOcrDiagnosticImage(diagnostics,stage,canvas,details={}) {
    if(diagnostics)addPhotoOcrDiagnostic(diagnostics,stage,{...details,width:canvas.width,height:canvas.height,image:canvas.toDataURL('image/png')});
}
// Kept separate from the recognizer so diagnostics stay opt-in and never send
// an image or OCR result off the device.
function renderPhotoOcrDiagnostics(diagnostics,container) {
    if(!diagnostics?.length||!container)return;
    container.querySelector('#photoOcrDiagnostics')?.remove();
    const details=document.createElement('details');details.id='photoOcrDiagnostics';details.open=true;
    const summary=document.createElement('summary');summary.textContent='Diagnóstico OCR local (solo esta sesión)';details.append(summary);
    for(const item of diagnostics){
        const section=document.createElement('section');section.style.cssText='margin:10px 0;padding:8px;border:1px solid #bbb;';
        const heading=document.createElement('strong');heading.textContent=item.stage;section.append(heading);
        const meta={...item};delete meta.stage;delete meta.image;
        if(Object.keys(meta).length){const pre=document.createElement('pre');pre.style.whiteSpace='pre-wrap';pre.textContent=JSON.stringify(meta,null,2);section.append(pre);}
        if(item.image){const image=document.createElement('img');image.src=item.image;image.alt=item.stage;image.style.cssText='display:block;max-width:100%;border:1px solid #777;background:white;';section.append(image);}
        details.append(section);
    }
    container.append(details);
}
function photoTextBands(canvas) {
    const {width,height,data}=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height);
    const rows=[];const minimum=Math.max(2,Math.round(width*.002));
    for(let y=0;y<height;y++){
        let ink=0;for(let x=0;x<width;x++)if(data[(y*width+x)*4]<128)ink++;
        if(ink>=minimum)rows.push(y);
    }
    const bands=[];
    for(const row of rows){
        const last=bands[bands.length-1];
        if(last&&row-last.bottom<=7)last.bottom=row;else bands.push({top:row,bottom:row});
    }
    return bands.filter(b=>b.bottom-b.top>=7).map(b=>{
        let left=width,right=-1;
        for(let y=b.top;y<=b.bottom;y++)for(let x=0;x<width;x++)if(data[(y*width+x)*4]<128){left=Math.min(left,x);right=Math.max(right,x);}
        const pad=8,x=Math.max(0,left-pad),y=Math.max(0,b.top-pad),w=Math.min(width-x,right-left+1+pad*2),h=Math.min(height-y,b.bottom-b.top+1+pad*2);
        return {x,y,width:w,height:h};
    }).filter(b=>b.width>0&&b.height>0);
}
function photoEditDistance(a,b) {
    const previous=Array.from({length:b.length+1},(_,i)=>i);
    for(let i=0;i<a.length;i++){
        const current=[i+1];for(let j=0;j<b.length;j++)current.push(Math.min(current[j]+1,previous[j+1]+1,previous[j]+(a[i]===b[j]?0:1)));
        previous.splice(0,previous.length,...current);
    }
    return previous[b.length];
}
function normalizePhotoType(raw) {
    const value=raw.replace(/[^A-Za-z0-9_\[\]]/g,'');if(!value)return '';
    const array=value.endsWith('[]'),base=array?value.slice(0,-2):value;
    const known=['String','Integer','Double','Boolean','LocalDate','Long','void'];
    const exact=known.find(type=>type.toLowerCase()===base.toLowerCase());
    const corrected=exact||known.find(type=>photoEditDistance(base.toLowerCase(),type.toLowerCase())===1);
    return (corrected||base)+(array?'[]':'');
}
function normalizePhotoOcrText(text, kind='body') {
    const chunks=String(text||'').replace(/\r/g,'').split('\n').flatMap(line=>line.split(/(?=\s[+\-#~]\s*[A-Za-z_])/));
    const kept=[];
    for(let line of chunks){
        line=line.trim().replace(/[|│┌┐└┘├┤─]+/g,'').replace(/([A-Za-z])!+(?=\s|$)/g,'$1').trim();if(!line)continue;
        if(kind==='name'){
            if(/^[A-Za-z_][A-Za-z0-9_ ]*$/.test(line))kept.push(line.replace(/\s+/g,' '));
            continue;
        }
        const operation=line.match(/^([+\-#~])?\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)\s*(?::\s*([A-Za-z][A-Za-z0-9_\[\]]*))?$/);
        if(operation){kept.push(`${operation[1]||'+'}${operation[2]}(${operation[3].trim()})${operation[4]?`: ${normalizePhotoType(operation[4])||operation[4]}`:''}`);continue;}
        // OCR can leave a border fragment after an otherwise valid member.
        // Keep the UML core (name + first type token) rather than rejecting a
        // complete attribute because of that unrelated trailing fragment.
        const attribute=line.match(/^\s*[\[\]{}|]*\s*([+\-#~])?\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*([A-Za-z][A-Za-z0-9_\[\]]*)(?:\s+.*)?$/);
        if(attribute){const type=normalizePhotoType(attribute[3]);if(type)kept.push(`${attribute[1]||'-'}${attribute[2]}: ${type}`);}
    }
    return kept.join('\n');
}
function normalizePhotoLooseMember(raw) {
    // Used only for a non-header OCR band that has already failed the strict
    // UML grammar. Cameras can erase '-' and ':' while leaving a reliable
    // identifier and type token. Operations contain parentheses and do not
    // match this narrow two-token fallback.
    const line=String(raw||'').trim().replace(/^[\[\]{}|_\s]+/,'').replace(/[\[\]{}|\s]+$/,'');
    const match=line.match(/^([+\-#~])?\s*([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z][A-Za-z0-9_\[\]]*)$/);
    if(!match)return '';
    const type=normalizePhotoType(match[3]);
    return type?`${match[1]||'-'}${match[2]}: ${type}`:'';
}
function normalizePhotoBandReadings(readings, kind='body') {
    if(kind!=='mixed')return normalizePhotoOcrText(readings.join('\n'),kind);
    let name='',members=[];
    for(const raw of readings){
        if(!name){const candidate=normalizePhotoOcrText(raw,'name');if(candidate){name=candidate.replace(/\n/g,' ').trim();continue;}}
        const member=normalizePhotoOcrText(raw,'body')||normalizePhotoLooseMember(raw);if(member)members.push(member);
    }
    return {name,body:members.join('\n')};
}
function countStructuredPhotoBlocks(text) {
    const identifier=/^[\p{L}_][\p{L}\p{N}_ ]*$/u;
    const attribute=/^[+\-#~]?\s*[\p{L}_][\p{L}\p{N}_]*\s*:\s*[\p{L}_][\p{L}\p{N}_]*(?:\[\])?$/u;
    const operation=/^[+\-#~]?\s*[\p{L}_][\p{L}\p{N}_]*\s*\([^()]*\)\s*(?::\s*[\p{L}_][\p{L}\p{N}_]*(?:\[\])?)?$/u;
    return String(text||'').trim().split(/\n\s*\n/).filter(Boolean).filter(block=>{
        const lines=block.split('\n').map(line=>line.trim()).filter(Boolean);
        if(lines.length<2||!identifier.test(lines[0]))return false;
        return lines.slice(1).every(line=>attribute.test(line)||operation.test(line));
    }).length;
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
        const diagnostics=photoOcrDebugEnabled()?[]:null;
        addPhotoOcrDiagnosticImage(diagnostics,'00. Imagen tras escala y enderezado',canvas);
        const boxes=detectPhotoBoxes(canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height));
        addPhotoOcrDiagnostic(diagnostics,'01. Cajas y compartimentos detectados',{boxes:boxes.map((box,index)=>({index:index+1,outer:{x:box.outerX,y:box.outerY,width:box.outerWidth,height:box.outerHeight},inner:{x:box.x,y:box.y,width:box.width,height:box.height},headerBottom:box.headerBottom,attributesBottom:box.attributesBottom,dividerYs:box.dividerYs}))});
        if(!boxes.length) {
            // A clean digital export may omit UML rectangles.  It still gets
            // the same line-level preprocessing instead of raw full-page OCR.
            const prepared=preparePhotoOcrCanvas(canvas),bands=photoTextBands(prepared);
            await worker.setParameters({tessedit_pageseg_mode:'7',tessedit_char_whitelist:'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_+-#~:(),.[]* /',preserve_interword_spaces:'1'});
            const readings=[];
            for(const band of bands.length?bands:[{x:0,y:0,width:prepared.width,height:prepared.height}]){
                const line=document.createElement('canvas');line.width=band.width;line.height=band.height;
                line.getContext('2d').drawImage(prepared,band.x,band.y,band.width,band.height,0,0,band.width,band.height);
                readings.push((await worker.recognize(line)).data.text);
            }
            const first=normalizePhotoOcrText(readings.shift()||'','name');
            const body=normalizePhotoOcrText(readings.join('\n'),'body');
            const text=[first,body].filter(Boolean).join('\n');
            const count=countStructuredPhotoBlocks(text);
            addPhotoOcrDiagnostic(diagnostics,'Resultado final sin cajas',{raw:readings.join('\n'),name:first,body,text});
            return {text,structured:count>0,count,diagnostics};
        }
        const whitelist='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_+-#~:(),.[]* /';
        const blocks=[], names=[];
        const cropCanvas=(source,x,y,width,height,scale=1)=>{
            const crop=document.createElement('canvas');crop.width=Math.max(1,Math.round(width*scale));crop.height=Math.max(1,Math.round(height*scale));
            crop.getContext('2d').drawImage(source,x,y,width,height,0,0,crop.width,crop.height);return crop;
        };
        const read=async(box,top,bottom,kind,label)=>{
            const height=Math.max(1,bottom-top);
            const interior=cropCanvas(canvas,box.x,top,box.width,height);
            addPhotoOcrDiagnosticImage(diagnostics,`${label}. 03. Recorte interior tras margen`,interior,{bounds:{x:box.x,y:top,width:box.width,height}});
            const crop=cropCanvas(canvas,box.x,top,box.width,height,3);
            addPhotoOcrDiagnosticImage(diagnostics,`${label}. 04. Recorte escalado x3`,crop);
            const binarized=binarizePhotoOcrCanvas(crop);
            addPhotoOcrDiagnosticImage(diagnostics,`${label}. 05. Binarización Otsu`,binarized);
            const prepared=removePhotoRulesFromCanvas(binarized);
            addPhotoOcrDiagnosticImage(diagnostics,`${label}. 06. Después de eliminar reglas`,prepared);
            const bands=photoTextBands(prepared);
            addPhotoOcrDiagnostic(diagnostics,`${label}. 07. Bandas de texto`,{bands});
            await worker.setParameters({tessedit_pageseg_mode:'7',tessedit_char_whitelist:whitelist,preserve_interword_spaces:'1'});
            const readings=[];
            for(const [index,band] of (bands.length?bands:[{x:0,y:0,width:prepared.width,height:prepared.height}]).entries()){
                const line=document.createElement('canvas');line.width=band.width;line.height=band.height;
                line.getContext('2d').drawImage(prepared,band.x,band.y,band.width,band.height,0,0,band.width,band.height);
                addPhotoOcrDiagnosticImage(diagnostics,`${label}. 08. Imagen enviada a Tesseract, banda ${index+1}`,line,{band});
                let raw=(await worker.recognize(line)).data.text;
                // A single-line mode can return nothing for small handwritten
                // or low-contrast bands. Try the sparse-line mode only then.
                if(!raw.trim()){
                    await worker.setParameters({tessedit_pageseg_mode:'13',tessedit_char_whitelist:whitelist,preserve_interword_spaces:'1'});
                    const alternate=(await worker.recognize(line)).data.text;
                    addPhotoOcrDiagnostic(diagnostics,`${label}. 09b. Tesseract alternativo, banda ${index+1}`,{raw:alternate});
                    if(alternate.trim())raw=alternate;
                    await worker.setParameters({tessedit_pageseg_mode:'7',tessedit_char_whitelist:whitelist,preserve_interword_spaces:'1'});
                }
                readings.push(raw);
                addPhotoOcrDiagnostic(diagnostics,`${label}. 09. Tesseract bruto, banda ${index+1}`,{raw});
            }
            const normalized=normalizePhotoBandReadings(readings,kind);
            addPhotoOcrDiagnostic(diagnostics,`${label}. 10. Después de sanitize/filter`,{raw:readings.join('\n'),normalized});
            return normalized;
        };
        for(let i=0;i<boxes.length;i++) {
            update(`Leyendo clase ${i+1} de ${boxes.length}…`,25+70*i/boxes.length);
            const box=boxes[i];
            const outer=cropCanvas(canvas,box.outerX,box.outerY,box.outerWidth,box.outerHeight);
            addPhotoOcrDiagnosticImage(diagnostics,`Clase ${i+1}. 02. Recorte original de caja antes de limpieza`,outer,{bounds:{x:box.outerX,y:box.outerY,width:box.outerWidth,height:box.outerHeight}});
            const dividerGap=Math.max(2,(box.dividerPadding||3)*2);
            let name='',attrs='',methods='';
            if(!box.dividerYs.length){
                // Divider lines may be faint or broken in a photograph. The
                // text bands are still ordered top-to-bottom, so use them as a
                // semantic fallback without inventing geometric separators.
                const fallback=await read(box,box.y,box.y+box.height,'mixed',`Clase ${i+1}, bandas sin divisor`);
                name=fallback.name;attrs=fallback.body;
            } else {
                name=await read(box,box.y,box.headerBottom,'name',`Clase ${i+1}, nombre`);
                attrs=box.attributesBottom>box.headerBottom+dividerGap ? await read(box,box.headerBottom+dividerGap,box.attributesBottom,'body',`Clase ${i+1}, atributos`) : '';
                methods=box.y+box.height>box.attributesBottom+dividerGap ? await read(box,box.attributesBottom+dividerGap,box.y+box.height,'body',`Clase ${i+1}, operaciones`) : '';
            }
            names.push(name.replace(/\n/g,' ').trim());
            if(name)blocks.push(name.replace(/\n/g,' ')+'\n'+(attrs+'\n'+methods).split('\n').map(line=>line.trim()).filter(Boolean).join('\n'));
        }
        update('Lectura terminada; revisa las clases antes de importar.',100);
        const pixels=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height);
        const markers=detectPhotoMarkers(pixels,boxes);
        const text=blocks.join('\n\n');
        addPhotoOcrDiagnostic(diagnostics,'11. Texto final ensamblado',{text,names,blocks});
        return {text,structured:true,count:blocks.length,names,markers,diagnostics,...detectPhotoConnections(pixels,boxes,markers)};
    } finally {
        await worker.terminate();
    }
}
