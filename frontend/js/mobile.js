let mobilePlan=null;
function applyUMLPlan(plan) {
    if(collaborationState.role==='viewer')throw new Error('Este enlace es de solo lectura');
    const existing=state.model.classes.find(c=>c.name.toLowerCase()===plan.name.toLowerCase());
    if(plan.action==='createClass' && existing)throw new Error('Esa clase ya existe; usa Agrega atributo');
    if(plan.action!=='createClass'&&!existing)throw new Error('No existe la clase indicada');
    if(plan.action==='addAttributes'&&plan.attributes.some(a=>existing.attributes.some(b=>a.name.toLowerCase()===b.name.toLowerCase())))throw new Error('Uno de los atributos ya existe');
    saveUndo();
    if(plan.action==='deleteClass')state.model.removeClass(existing.id);
    else {
        const cls=existing||new UMLClassNode(plan.name,60+state.model.classes.length*240,100);
        for(const attr of plan.attributes)cls.addAttribute({...attr,id:crypto.randomUUID(),visibility:'-',constraints:[]});
        if(!existing)state.model.addClass(cls);
        state.selectedId=cls.id;state.selectedType='class';
    }
    renderAll();persistCollaboration();broadcastChange();refreshMobileCards();
}
function reviewMobileCommand() {
    try {
        mobilePlan=UMLCommands.parse($('#mobileCommand').value);
        const summary=mobilePlan.action==='deleteClass'?`Eliminar ${mobilePlan.name} y sus relaciones`: `${mobilePlan.action==='createClass'?'Crear':'Agregar a'} ${mobilePlan.name}: ${mobilePlan.attributes.map(a=>`${a.name}: ${a.type}`).join(', ')||'sin atributos'}`;
        $('#mobileReview').textContent=summary;$('#applyMobileCommand').disabled=false;
    }catch(e){mobilePlan=null;$('#mobileReview').textContent=e.message;$('#applyMobileCommand').disabled=true;}
}
function refreshMobileCards() {
    const container=$('#mobileClasses');if(!container)return;
    const signature=JSON.stringify(state.model.toJSON());if(container.dataset.signature===signature)return;container.dataset.signature=signature;
    container.replaceChildren();
    if(!state.model.classes.length){const empty=document.createElement('p');empty.textContent='Tu diagrama está vacío. Dicta una clase o escribe un comando para comenzar.';container.append(empty);return;}
    for(const cls of state.model.classes) {
        const card=document.createElement('article');card.className='mobile-class-card';
        const title=document.createElement('h3');title.textContent=cls.name;
        const attrs=document.createElement('ul');
        for(const attr of cls.attributes){const li=document.createElement('li');li.textContent=`${attr.name}: ${attr.type}`;attrs.append(li);}
        const edit=document.createElement('button');edit.textContent='Agregar atributo';edit.className='btn-secondary';edit.onclick=()=>{$('#mobileCommand').value=`Agrega atributo nombre de tipo texto a clase ${cls.name}`;$('#mobileCommand').focus();};
        card.append(title,attrs,edit);container.append(card);
    }
}
function reviewPhotoText(text) {
    // One class per blank-separated block. User explicitly reviews OCR before applying.
    return text.trim().split(/\n\s*\n/).filter(Boolean).map(block=>{
        const lines=block.split('\n').map(s=>s.trim().replace(/^[+\-#~]\s*/, '')).filter(Boolean);
        const name=UMLCommands.identifier(lines.shift(),true);
        const attributes=lines.filter(line=>!line.includes('(')).map(line=>UMLCommands.attributes(line)[0]);
        return {action:'createClass',name,attributes};
    });
}
function initMobileEditor() {
    const forced=new URLSearchParams(location.search).get('view')==='mobile';
    if(forced||matchMedia('(max-width: 760px)').matches)document.body.classList.add('mobile-editor');
    $('#mobileMode').addEventListener('click',()=>{document.body.classList.toggle('mobile-editor');refreshMobileCards();});
    $('#reviewMobileCommand').onclick=reviewMobileCommand;
    $('#applyMobileCommand').onclick=()=>{
        try {if(!mobilePlan)return;applyUMLPlan(mobilePlan);$('#mobileReview').textContent='Cambio aplicado y guardado en este dispositivo.';mobilePlan=null;$('#applyMobileCommand').disabled=true;}
        catch(e){$('#mobileReview').textContent=e.message;}
    };
    $('#mobileCommand').addEventListener('input',()=>{mobilePlan=null;$('#applyMobileCommand').disabled=true;});
    $('#mobileMic').onclick=toggleLocalRecording;
    $('#prepareOffline').onclick=prepareOffline;
    $('#mobileAudio').onchange=async event=>{const file=event.target.files[0];if(file)try{await transcribeLocalFile(file);}catch(e){aiStatus(e.message);}};
    $('#mobilePhoto').onchange=async event=>{
        const file=event.target.files[0];if(!file)return;
        try {$('#mobilePhotoText').value=await recognizeLocalPhoto(file);$('#mobilePhotoReview').hidden=false;aiStatus('Revisa el texto detectado. Separa cada clase con una línea vacía. Las relaciones no se adivinan.');}catch(e){aiStatus(e.message);}
    };
    $('#applyPhotoText').onclick=()=>{
        try {
            const plans=reviewPhotoText($('#mobilePhotoText').value);
            const names=plans.map(p=>p.name.toLowerCase());
            if(new Set(names).size!==names.length||state.model.classes.some(c=>names.includes(c.name.toLowerCase())))throw new Error('Hay nombres de clases repetidos; corrige el texto antes de importar');
            for(const plan of plans)applyUMLPlan(plan);
            aiStatus(`Importadas ${plans.length} clases revisadas. Revisa atributos y añade las relaciones.`);
        }catch(e){aiStatus(e.message);}
    };
    $('#mobileImport').onclick=()=>$('#btnImport').click();
    $('#mobileExport').onclick=()=>$('#btnExport').click();
    $('#mobileShare').onclick=showShareDialog;
    setInterval(refreshMobileCards,500);refreshMobileCards();
    if('serviceWorker'in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
}
initMobileEditor();
