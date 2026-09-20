let mobilePlan = null;

function applyUMLPlan(plan) {
    if (collaborationState.role === 'viewer') throw new Error('Este enlace es de solo lectura');
    const existing = state.model.classes.find(c => c.name.toLowerCase() === plan.name.toLowerCase());
    if (plan.action === 'createClass' && existing) throw new Error('Esa clase ya existe; usa Agrega atributo');
    if (plan.action !== 'createClass' && !existing) throw new Error('No existe la clase indicada');
    if (plan.action === 'addAttributes' && plan.attributes.some(a => existing.attributes.some(b => a.name.toLowerCase() === b.name.toLowerCase()))) throw new Error('Uno de los atributos ya existe');
    
    saveUndo();
    if (plan.action === 'deleteClass') {
        state.model.removeClass(existing.id);
    } else {
        const cls = existing || new UMLClassNode(plan.name, 60 + state.model.classes.length * 240, 100);
        for (const attr of plan.attributes) {
            cls.addAttribute({ ...attr, id: crypto.randomUUID(), visibility: ['+', '-', '#', '~'].includes(attr.visibility) ? attr.visibility : '-', constraints: [] });
        }
        for (const operation of plan.operations || []) cls.addOperation({...operation, id:crypto.randomUUID()});
        if (!existing) state.model.addClass(cls);
        state.selectedId = cls.id;
        state.selectedType = 'class';
    }
    renderAll();
    persistCollaboration();
    broadcastChange();
    refreshMobileCards();
    
    const toast = document.getElementById('mobileResultStatus');
    if (toast) {
        toast.textContent = '✓ Guardado con éxito: ' + plan.name;
        setTimeout(() => { if (toast.textContent.includes(plan.name)) toast.textContent = ''; }, 4000);
    }
    const cardsEl = document.getElementById('mobileClasses');
    if (cardsEl) cardsEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function reviewMobileCommand() {
    try {
        mobilePlan = UMLCommands.parse($('#mobileCommand').value);
        const summary = mobilePlan.action === 'deleteClass'
            ? `Eliminar ${mobilePlan.name} y sus relaciones`
            : `${mobilePlan.action === 'createClass' ? 'Crear' : 'Agregar a'} ${mobilePlan.name}: ${mobilePlan.attributes.map(a => `${a.name}: ${a.type}`).join(', ') || 'sin atributos'}`;
        $('#mobileReview').textContent = summary;
        $('#applyMobileCommand').disabled = false;
    } catch (e) {
        mobilePlan = null;
        $('#mobileReview').textContent = e.message;
        $('#applyMobileCommand').disabled = true;
    }
}

function getTypeBadgeClass(type) {
    const t = (type || '').toLowerCase();
    if (t.includes('str') || t.includes('text')) return 'type-string';
    if (t.includes('int') || t.includes('long')) return 'type-int';
    if (t.includes('doub') || t.includes('float') || t.includes('dec')) return 'type-double';
    if (t.includes('bool')) return 'type-bool';
    if (t.includes('date') || t.includes('time')) return 'type-date';
    return 'type-other';
}

function refreshMobileCards() {
    const container = $('#mobileClasses');
    if (!container) return;
    const countBadge = document.getElementById('classesCountBadge');
    const classCount = state.model.classes.length;
    if (countBadge) {
        countBadge.textContent = `${classCount} ${classCount === 1 ? 'clase' : 'clases'}`;
    }

    const signature = JSON.stringify(state.model.toJSON());
    if (container.dataset.signature === signature) return;
    container.dataset.signature = signature;
    container.replaceChildren();

    if (!classCount) {
        const emptyState = document.createElement('div');
        emptyState.className = 'classes-empty-state';
        emptyState.innerHTML = `
            <div class="empty-icon-wrap">📐</div>
            <h4 class="empty-title">Tu diagrama está vacío</h4>
            <p class="empty-desc">Toca «Nueva Clase» arriba o pulsa «Dictar Voz» para comenzar.</p>
            <button type="button" class="btn-primary" style="margin:auto; min-height:44px;" id="btnEmptyCreate">
                + Crear primera clase
            </button>
        `;
        emptyState.querySelector('#btnEmptyCreate').onclick = () => openMobileForm();
        container.append(emptyState);
        return;
    }

    for (const cls of state.model.classes) {
        const card = document.createElement('article');
        card.className = 'mobile-class-card';

        // Header
        const header = document.createElement('div');
        header.className = 'mobile-class-card-header';
        
        const headerLeft = document.createElement('div');
        headerLeft.className = 'class-header-left';
        const tag = document.createElement('span');
        tag.className = 'class-type-tag';
        tag.textContent = 'CLASE';
        const title = document.createElement('h3');
        title.textContent = cls.name;
        headerLeft.append(tag, title);

        const delCls = document.createElement('button');
        delCls.type = 'button';
        delCls.className = 'btn-delete-class';
        delCls.innerHTML = `<span>🗑️</span> Eliminar`;
        delCls.title = `Eliminar clase ${cls.name}`;
        delCls.onclick = () => {
            if (confirm(`¿Eliminar la clase «${cls.name}» y sus relaciones?`)) {
                state.model.removeClass(cls.id);
                renderAll();
                persistCollaboration();
                broadcastChange();
                refreshMobileCards();
            }
        };
        header.append(headerLeft, delCls);

        // Attributes
        const attrsList = document.createElement('ul');
        attrsList.className = 'mobile-attr-list';
        if (!cls.attributes.length) {
            const noAttrs = document.createElement('li');
            noAttrs.style.cssText = 'color:var(--text-tertiary); font-size:12px; font-style:italic; padding:4px 8px;';
            noAttrs.textContent = 'Sin atributos definidos';
            attrsList.append(noAttrs);
        } else {
            for (const attr of cls.attributes) {
                const li = document.createElement('li');
                li.className = 'mobile-attr-item';

                const left = document.createElement('div');
                left.className = 'attr-item-left';
                const vis = document.createElement('span');
                vis.className = 'attr-vis-badge';
                vis.textContent = attr.visibility || '-';
                const name = document.createElement('span');
                name.className = 'attr-name-text';
                name.textContent = attr.name;
                left.append(vis, name);

                const right = document.createElement('div');
                right.className = 'attr-item-right';
                const badge = document.createElement('span');
                badge.className = `type-badge ${getTypeBadgeClass(attr.type)}`;
                badge.textContent = attr.type || 'String';
                
                const delAttr = document.createElement('button');
                delAttr.type = 'button';
                delAttr.className = 'btn-del-attr';
                delAttr.textContent = '×';
                delAttr.title = `Eliminar atributo ${attr.name}`;
                delAttr.onclick = (e) => {
                    e.stopPropagation();
                    cls.attributes = cls.attributes.filter(a => a.id !== attr.id);
                    renderAll();
                    persistCollaboration();
                    broadcastChange();
                    refreshMobileCards();
                };

                right.append(badge, delAttr);
                li.append(left, right);
                attrsList.append(li);
            }
        }

        // Footer action
        const addAttrBtn = document.createElement('button');
        addAttrBtn.type = 'button';
        addAttrBtn.className = 'btn-add-attr-card';
        addAttrBtn.innerHTML = `<span>+</span> Agregar Atributo`;
        addAttrBtn.onclick = () => openMobileForm(cls.name);

        const operationsList = document.createElement('div');
        for (const operation of cls.operations || []) {
            const row=document.createElement('p');row.textContent=`${operation.visibility || '+'} ${operation.name}(${(operation.parameters||[]).map(p=>p.name+': '+p.type).join(', ')}) : ${operation.returnType || 'void'}`;
            operationsList.append(row);
        }
        card.append(header, attrsList, operationsList, addAttrBtn);
        container.append(card);
    }
}

function preparePhotoImport(text, mode = 'append') {
    if(!['append','replace'].includes(mode))throw new Error('Modo de importación inválido');
    const imported=buildPhotoDiagram(text);
    const next=UMLModel.fromJSON(state.model.toJSON());
    if(mode==='replace'){next.classes=[];next.relationships=[];}
    const names=new Set(next.classes.map(cls=>cls.name.toLowerCase()));
    if(imported.classes.some(cls=>names.has(cls.name.toLowerCase())))throw new Error('Hay nombres de clases repetidos; corrige el texto antes de importar');
    const hasExisting=next.classes.length>0;
    const offset=next.classes.reduce((max,cls)=>Math.max(max,cls.position.y+(cls.size?.height||120)),0);
    for(const cls of imported.classes){cls.position.y+=hasExisting?offset+60:0;next.addClass(cls);}
    return next;
}
function applyPhotoImport(text) {
    if(collaborationState.role==='viewer')throw new Error('Este enlace es de solo lectura');
    const next=preparePhotoImport(text);
    const count=next.classes.length-state.model.classes.length;
    saveUndo();state.model=next;
    renderAll();persistCollaboration();broadcastChange();refreshMobileCards();
    return count;
}

function buildPhotoDiagram(text) {
    const plans=reviewPhotoText(text);
    if(!plans.length)throw new Error('No se reconocieron clases válidas. Revisa el texto.');
    if(new Set(plans.map(p=>p.name.toLowerCase())).size!==plans.length)throw new Error('Hay nombres de clases repetidos.');
    const diagram=new UMLModel();diagram.name=state.model.name;
    plans.forEach((plan,index)=>{
        const cls=new UMLClassNode(plan.name,60+(index%3)*260,60+Math.floor(index/3)*300);
        plan.attributes.forEach(attr=>cls.addAttribute({...attr,id:crypto.randomUUID()}));
        (plan.operations||[]).forEach(op=>cls.addOperation({...op,id:crypto.randomUUID()}));
        diagram.addClass(cls);
    });
    return diagram;
}
function reviewPhotoText(text) {
    let clean = text.replace(/\bcddigo\b/gi, 'codigo')
                    .replace(/\bcod1go\b/gi, 'codigo')
                    .replace(/\bc0digo\b/gi, 'codigo');
    return clean.trim().split(/\n\s*\n/).filter(Boolean).map(block => {
        const lines = block.split('\n').map(s => s.trim().replace(/^[|│┌┐└┘├┤─]\s*/, '')).filter(Boolean);
        if (!lines.length) return null;
        if (lines.length === 1 && (/^(ejemplo|diagrama|clases|modelo)\b/i.test(lines[0]) || !lines[0].includes(':'))) {
            return null;
        }
        try {
            const name = UMLCommands.identifier(lines.shift(), true);
            const attributes = lines.filter(line => !line.includes('(')).map(line => {
                const visibility = /^[+\-#~]/.test(line) ? line[0] : '-'; const parsed = UMLCommands.attributes(line.replace(/^[+\-#~]\s*/, '')); if(parsed.length!==1)throw new Error('Revisa el atributo: '+line); return {...parsed[0], visibility};
            }).filter(Boolean);
            if(new Set(attributes.map(a=>a.name.toLowerCase())).size!==attributes.length)throw new Error('Atributos repetidos en '+name);
            if (!attributes.length && /^(ejemplo|diagrama)/i.test(name)) return null;
            const operations = lines.filter(line => line.includes('(')).map(line => {
                const match = line.match(/^([+\-#~])?\s*([\p{L}_][\p{L}\p{N}_ ]*)\(([^()]*)\)\s*(?::\s*([\w]+(?:\[\])?))?$/u);
                if (!match) throw new Error('Revisa la firma del método: ' + line);
                const parameters=match[3].trim() ? match[3].split(',').map(raw=>{
                    const parameter=raw.trim().match(/^([\p{L}_][\p{L}\p{N}_]*)\s*:\s*([\p{L}_][\p{L}\p{N}_]*(?:\[\])?)$/u);
                    if(!parameter)throw new Error('Parámetro inválido; usa nombre: Tipo en ' + line);
                    return {name:parameter[1],type:parameter[2]};
                }) : [];
                if(new Set(parameters.map(p=>p.name)).size!==parameters.length)throw new Error('Parámetros repetidos en ' + line);
                return {name:UMLCommands.identifier(match[2]),visibility:match[1] || '+',parameters,returnType:match[4] || 'void',isAbstract:false,isStatic:false,isConstructor:false};
            });
            return { action: 'createClass', name, attributes, operations };
        } catch (e) {
            throw new Error("No se puede importar este bloque: " + e.message);
        }
    }).filter(Boolean);
}

function openMobileForm(className = null) {
    const dialog = document.getElementById('mobileClassForm');
    if (!dialog) return;
    const form = dialog.querySelector('form');
    form.reset();
    form.dataset.className = className || '';
    
    const titleEl = document.getElementById('mobileFormTitle');
    const classLabel = document.getElementById('simpleClassLabel');
    const classNameInput = document.getElementById('simpleClassName');
    const attrNameInput = document.getElementById('simpleAttributeName');
    const errEl = document.getElementById('mobileFormError');

    if (className) {
        titleEl.textContent = 'Agregar atributo a ' + className;
        classLabel.hidden = true;
        classNameInput.required = false;
        attrNameInput.required = true;
    } else {
        titleEl.textContent = 'Crear Nueva Clase';
        classLabel.hidden = false;
        classNameInput.required = true;
        attrNameInput.required = false;
    }
    if (errEl) errEl.textContent = '';
    dialog.showModal();
    (className ? attrNameInput : classNameInput).focus();
}

function initMobileEditor() {
    const relationButton=document.createElement('button');
    relationButton.textContent='Conectar clases';relationButton.className='btn-secondary';
    relationButton.onclick=openMobileRelationship;
    document.getElementById('mobileClasses').before(relationButton);

    const forced = new URLSearchParams(location.search).get('view') === 'mobile';
    if (forced || matchMedia('(max-width: 760px)').matches) {
        document.body.classList.add('mobile-editor');
    }

    const modeBtn = $('#mobileMode');
    if (modeBtn) {
        modeBtn.addEventListener('click', () => {
            document.body.classList.toggle('mobile-editor');
            refreshMobileCards();
        });
    }

    // Top Quick Action Cards
    const btnQuickCreate = document.getElementById('btnQuickCreate');
    if (btnQuickCreate) btnQuickCreate.onclick = () => openMobileForm();

    const voiceSec = document.getElementById('mobileVoiceSection');
    const photoSec = document.getElementById('mobilePhotoSection');

    const btnQuickVoice = document.getElementById('btnQuickVoice');
    if (btnQuickVoice) {
        btnQuickVoice.onclick = () => {
            if (voiceSec) {
                voiceSec.hidden = false;
                voiceSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            if (photoSec) photoSec.hidden = true;
            if (window.ConversationalAssistant) {
                ConversationalAssistant.toggleVoiceSession();
            } else {
                toggleLocalRecording();
            }
        };
    }

    const siriOrb = document.getElementById('siriOrb');
    if (siriOrb) {
        siriOrb.onclick = () => {
            if (window.ConversationalAssistant) {
                ConversationalAssistant.toggleVoiceSession();
            } else {
                toggleLocalRecording();
            }
        };
    }

    const btnSiriStopRecording = document.getElementById('btnSiriStopRecording');
    if (btnSiriStopRecording) {
        btnSiriStopRecording.onclick = () => {
            if (window.ConversationalAssistant) {
                ConversationalAssistant.toggleVoiceSession();
            } else if (typeof localAI !== 'undefined' && localAI.recorder?.state === 'recording') {
                localAI.recorder.stop();
            }
        };
    }

    const siriTextInput = document.getElementById('siriTextInput');
    const btnSiriSendText = document.getElementById('btnSiriSendText');
    const sendSiriText = () => {
        if (!siriTextInput || !siriTextInput.value.trim()) return;
        if(typeof ConversationalAssistant!=='undefined' && ConversationalAssistant.isBusy()){ConversationalAssistant.updateOrbState('thinking','Estoy procesando el pedido anterior. Tu texto no se borró.');return;}
        const msg = siriTextInput.value.trim();
        if (typeof ConversationalAssistant !== 'undefined') {
            ConversationalAssistant.processMessage(msg);
            siriTextInput.value = '';
        }
    };
    if (btnSiriSendText) btnSiriSendText.onclick = sendSiriText;
    if (siriTextInput) {
        siriTextInput.onkeydown = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendSiriText();
            }
        };
    }

    const btnQuickPhoto = document.getElementById('btnQuickPhoto');
    if (btnQuickPhoto) {
        btnQuickPhoto.onclick = () => {
            if (photoSec) {
                photoSec.hidden = false;
                photoSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            if (voiceSec) voiceSec.hidden = true;
            const photoInput = document.getElementById('mobilePhoto');
            if (photoInput) photoInput.click();
        };
    }

    // Close buttons on studio cards
    const btnCloseVoice = document.getElementById('btnCloseVoiceSection');
    if (btnCloseVoice) {
        btnCloseVoice.onclick = () => {
            if (voiceSec) voiceSec.hidden = true;
            if (window.ConversationalAssistant) {
                ConversationalAssistant.stopSpeaking();
            }
            if (typeof localAI !== 'undefined' && localAI.recorder?.state === 'recording') {
                localAI.recorder.stop();
            }
        };
    }

    const btnClosePhoto = document.getElementById('btnClosePhotoSection');
    if (btnClosePhoto) btnClosePhoto.onclick = () => { if (photoSec) photoSec.hidden = true; };

    // Toggle Canvas 2D
    const btnCanvasToggle = document.getElementById('btnToggleVisualCanvas');
    if (btnCanvasToggle) {
        btnCanvasToggle.onclick = () => {
            const mainLayout = document.getElementById('mainLayout');
            if (mainLayout) {
                mainLayout.classList.toggle('visible');
                if (mainLayout.classList.contains('visible')) {
                    mainLayout.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    btnCanvasToggle.style.borderColor = 'var(--accent-primary)';
                } else {
                    btnCanvasToggle.style.borderColor = '';
                }
            }
        };
    }

    // Command reviews & Voice Mic
    $('#reviewMobileCommand').onclick = reviewMobileCommand;
    $('#applyMobileCommand').onclick = () => {
        try {
            if (!mobilePlan) return;
            applyUMLPlan(mobilePlan);
            $('#mobileReview').textContent = '✓ Cambio aplicado y guardado en este dispositivo.';
            mobilePlan = null;
            $('#applyMobileCommand').disabled = true;
            $('#mobileCommand').value = '';
        } catch (e) {
            $('#mobileReview').textContent = e.message;
        }
    };
    $('#mobileCommand').addEventListener('input', () => { reviewMobileCommand(); });
    $('#mobileMic').onclick = () => toggleLocalRecording();

    // Offline preparation
    $('#prepareOffline').onclick = prepareOffline;
    $('#mobileAudio').onchange = async event => {
        const file = event.target.files[0];
        if (file) {
            try { await transcribeLocalFile(file); } catch (e) { aiStatus(e.message); }
        }
    };

    // Photo input & preview
    $('#mobilePhoto').onchange = async event => {
        const file = event.target.files[0];
        if (!file) return;
        if (photoSec) photoSec.hidden = false;
        const preview = document.getElementById('mobilePhotoPreview');
        const status = document.getElementById('mobilePhotoStatus');
        if (preview) {
            preview.src = URL.createObjectURL(file);
            preview.style.display = 'block';
        }
        if (status) status.textContent = 'Cargando y analizando imagen localmente…';
        try {
            const rawText = await recognizeLocalPhoto(file);
            $('#mobilePhotoText').value = rawText.text;
            renderPhotoConnections(rawText);
            $('#mobilePhotoReview').hidden = false;
            if (status) status.textContent = rawText.structured ? `Se separaron ${rawText.count} clases para revisar. Los tipos no indicados se importan como texto. Revisa también los métodos. Las relaciones todavía deben añadirse manualmente.` : 'No se pudieron separar las clases. El texto es una lectura sin verificar: corrígelo antes de importar.';
        } catch (e) {
            if (status) status.textContent = 'Error al leer imagen: ' + e.message;
            aiStatus(e.message);
        }
    };

    const voicePhotoBtn = document.getElementById('btnVoiceSupplementPhoto');
    if (voicePhotoBtn) {
        voicePhotoBtn.onclick = async () => {
            toggleLocalRecording(true);
        };
    }

    $('#applyPhotoText').onclick = () => {
        try {
            const count=applyPhotoImport($('#mobilePhotoText').value);
            const status = document.getElementById('mobilePhotoStatus');
            if (status) status.textContent = `✓ Importadas ${count} clases al diagrama.`;
            aiStatus(`Importadas ${count} clases revisadas. Revisa atributos y añade las relaciones.`);
        } catch (e) {
            const status = document.getElementById('mobilePhotoStatus');
            if (status) status.textContent = 'Error: ' + e.message;
            aiStatus(e.message);
        }
    };

    // Secondary toolbar actions
    $('#mobileImport').onclick = () => $('#btnImport').click();
    $('#mobileExport').onclick = () => $('#btnExport').click();
    $('#mobileShare').onclick = showShareDialog;

    // Mobile Form Modal
    const dialog = document.getElementById('mobileClassForm');
    const closeBtn = document.getElementById('cancelMobileForm');
    const closeXBtn = document.getElementById('cancelMobileFormClose');
    if (closeBtn) closeBtn.onclick = () => dialog.close();
    if (closeXBtn) closeXBtn.onclick = () => dialog.close();

    if (dialog) {
        dialog.querySelector('form').onsubmit = event => {
            event.preventDefault();
            try {
                const existing = event.currentTarget.dataset.className;
                const name = existing || UMLCommands.identifier(document.getElementById('simpleClassName').value.trim(), true);
                const attr = document.getElementById('simpleAttributeName').value.trim();
                const attributes = attr ? [{ name: UMLCommands.identifier(attr, false), type: document.getElementById('simpleAttributeType').value }] : [];
                applyUMLPlan({ action: existing ? 'addAttributes' : 'createClass', name, attributes });
                dialog.close();
            } catch (error) {
                document.getElementById('mobileFormError').textContent = error.message;
            }
        };
    }

    setInterval(refreshMobileCards, 500);
    refreshMobileCards();
    if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
}

initMobileEditor();

function openMobileRelationship(candidate = null) {
    if(collaborationState.role==='viewer'){showToast('Este proyecto es de solo lectura','warning');return;}
    if(!state.model.classes.length){showToast('Crea primero una clase','info');return;}
    const dialog=document.createElement('dialog');
    dialog.innerHTML=`<form><h2>Conectar clases</h2><p>En herencia, el origen es la clase hija y el destino es la clase padre.</p>
    <div style="display:flex;justify-content:flex-end;margin-bottom:6px;"><button type="button" id="btnSwapDirection" class="btn" style="font-size:12px;padding:4px 10px;cursor:pointer;">⇄ Invertir origen y destino</button></div>
    <label>Clase de origen<select name="source"></select></label>
    <label>Clase de destino<select name="target"></select></label>
    <label>Relación<select name="type"><option value="association">Asociación</option><option value="generalization">Herencia</option><option value="aggregation">Agregación</option><option value="composition">Composición</option><option value="dependency">Dependencia</option><option value="realization">Implementa interfaz</option></select></label>
    <label>Multiplicidad de origen<select name="sourceMult"><option value="">Sin especificar</option><option>1</option><option>0..1</option><option>0..*</option><option>1..*</option></select></label>
    <label>Multiplicidad de destino<select name="targetMult"><option value="">Sin especificar</option><option>0..*</option><option>1</option><option>0..1</option><option>1..*</option></select></label>
    <p role="alert"></p><button type="button" id="btnCancelRel">Cancelar</button><button type="submit" class="btn-primary">Guardar relación</button></form>`;
    const form=dialog.querySelector('form');
    for(const cls of state.model.classes)for(const name of ['source','target']){
        const option=document.createElement('option');option.value=cls.id;option.textContent=cls.name;form.elements[name].append(option);
    }
    if(state.model.classes.length>1)form.elements.target.selectedIndex=1;
    if(candidate?.source && candidate?.target){
        form.elements.source.value=candidate.source;
        form.elements.target.value=candidate.target;
        if(candidate.type)form.elements.type.value=candidate.type;
        if(candidate.sourceMult)form.elements.sourceMult.value=candidate.sourceMult;
        if(candidate.targetMult)form.elements.targetMult.value=candidate.targetMult;
    } else if(candidate?.target && !candidate?.source) {
        form.elements.target.value=candidate.target;
        if(candidate.type)form.elements.type.value=candidate.type;
    }
    const updateMultiplicity=()=>{const enabled=['association','aggregation','composition'].includes(form.elements.type.value);form.elements.sourceMult.disabled=!enabled;form.elements.targetMult.disabled=!enabled;};
    form.elements.type.onchange=updateMultiplicity;updateMultiplicity();
    dialog.querySelector('#btnSwapDirection').onclick=()=>{
        const prevSource = form.elements.source.value;
        form.elements.source.value = form.elements.target.value;
        form.elements.target.value = prevSource;
    };
    dialog.querySelector('#btnCancelRel').onclick=()=>{dialog.close();dialog.remove();};
    form.onsubmit=event=>{
        event.preventDefault();
        try {
            const source=form.elements.source.value,target=form.elements.target.value,type=form.elements.type.value;
            if(collaborationState.role==='viewer')throw new Error('Este proyecto es de solo lectura');
            if(!state.model.getClass(source)||!state.model.getClass(target))throw new Error('Una clase fue eliminada. Abre el formulario otra vez.');
            if(type==='generalization'){
                const visited=new Set();
                const reachesSource=id=>{if(id===source)return true;if(visited.has(id))return false;visited.add(id);return state.model.relationships.filter(r=>r.type==='generalization'&&r.source.classId===id).some(r=>reachesSource(r.target.classId));};
                if(reachesSource(target))throw new Error('Esta herencia crearía un ciclo.');
            }
            if(type==='realization'&&!state.model.getClass(target).isInterface)throw new Error('El destino debe ser una interfaz.');
            if(state.model.relationships.some(r=>r.type===type&&r.source.classId===source&&r.target.classId===target))throw new Error('Esta relación ya existe.');
            saveUndo();const relation=new UMLRelNode(type,source,target);
            const hasMultiplicity=['association','aggregation','composition'].includes(type);
            relation.source.multiplicity=hasMultiplicity ? form.elements.sourceMult.value || null : null;
            relation.target.multiplicity=hasMultiplicity ? form.elements.targetMult.value || null : null;
            state.model.addRelationship(relation);renderAll();persistCollaboration();broadcastChange();refreshMobileCards();
            showToast('Relación guardada en el diagrama','success');dialog.close();dialog.remove();
        }catch(error){dialog.querySelector('[role=alert]').textContent=error.message;}
    };
    document.body.append(dialog);dialog.showModal();
}

function renderPhotoConnections(result, container = null) {
    document.getElementById('photoConnectionsReview')?.remove();
    if(!result.connections?.length&&!result.ambiguous?.length)return;
    const section=document.createElement('section');section.id='photoConnectionsReview';
    const title=document.createElement('h3');title.textContent='Conexiones de la foto: revisar';section.append(title);
    const note=document.createElement('p');note.textContent='Son propuestas. Confirma el tipo, la dirección y las multiplicidades mirando la foto. No se agregan automáticamente.';section.append(note);
    const find=index=>{const name=UMLCommands.identifier(result.names[index],true);return state.model.classes.find(c=>c.name.toLowerCase()===name.toLowerCase());};
    for(const marker of result.markers||[]){
        const hint=document.createElement('p');
        const targetCls = find(marker.box);
        if(marker.kind==='hollowTriangle' && targetCls){
            hint.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:8px;';
            hint.innerHTML=`<span>Triángulo junto a <strong>${targetCls.name}</strong> (posible herencia hacia ${targetCls.name})</span>`;
            const btn=document.createElement('button');btn.type='button';btn.className='btn btn-sm';btn.textContent=`Conectar hijo → ${targetCls.name}`;
            btn.onclick=()=>openMobileRelationship({target:targetCls.id,type:'generalization'});
            hint.append(btn);
        } else {
            hint.textContent=marker.kind==='hollowDiamond' ? `Rombo vacío junto a ${result.names[marker.box]}: posible agregación; revisa a qué clase llega la línea.` : `Triángulo vacío junto a ${result.names[marker.box]}: posible herencia o realización; revisa las clases de origen y si la línea es continua.`;
        }
        section.append(hint);
    }
    for(const pair of result.connections||[]){
        const button=document.createElement('button');button.type='button';button.textContent=pair.map(i=>result.names[i]).join(' ↔ ');button.className='btn';
        const suggestion=(result.suggestions||[]).find(s=>pair.includes(s.source)&&pair.includes(s.target));
        if(suggestion)button.textContent+=` — posible ${suggestion.type==='aggregation'?'agregación':suggestion.type}`;
        button.onclick=()=>{try{const source=find(suggestion?suggestion.source:pair[0]),target=find(suggestion?suggestion.target:pair[1]);if(!source||!target)throw new Error('Importa primero las clases o comprueba sus nombres.');openMobileRelationship({source:source.id,target:target.id,type:suggestion?.type,sourceMult:suggestion?.sourceMult,targetMult:suggestion?.targetMult});}catch(error){note.textContent=error.message;}};
        section.append(button);
    }
    const manual=document.createElement('button');manual.type='button';manual.className='btn';manual.textContent='Conectar clases manualmente';manual.onclick=()=>openMobileRelationship();section.append(manual);
    for(const group of result.ambiguous||[]){const text=document.createElement('p');text.textContent='Cruce o ramificación por resolver: '+group.map(i=>result.names[i]).join(', ')+'. Usa Conectar clases para indicar cada relación.';section.append(text);}
    (container || document.getElementById('mobilePhotoReview')).append(section);
}
