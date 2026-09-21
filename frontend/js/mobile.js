let mobilePlan = null;

function applyUMLPlan(plan) {
    if (collaborationState.role === 'viewer') throw new Error('Este enlace es de solo lectura');

    if (plan.action === 'addRelationship') {
        const src = state.model.classes.find(c => c.name.toLowerCase() === (plan.source || '').toLowerCase());
        const tgt = state.model.classes.find(c => c.name.toLowerCase() === (plan.target || '').toLowerCase());
        if (!src || !tgt) throw new Error(`No se encontraron las clases ${plan.source} y ${plan.target} para relacionar`);
        saveUndo();
        const rel = new UMLRelNode(plan.type || 'association', src.id, tgt.id);
        if (plan.multiplicitySource) rel.source.multiplicity = plan.multiplicitySource;
        if (plan.multiplicityTarget) rel.target.multiplicity = plan.multiplicityTarget;
        state.model.addRelationship(rel);
        renderAll();
        persistCollaboration();
        broadcastChange();
        refreshMobileCards();
        const toast = document.getElementById('mobileResultStatus');
        if (toast) {
            toast.textContent = `✓ Relación creada: ${src.name} ➔ ${tgt.name} (${plan.type})`;
            setTimeout(() => { if (toast.textContent.includes(src.name)) toast.textContent = ''; }, 4000);
        }
        return;
    }

    if (plan.action === 'deleteRelationship') {
        const src = state.model.classes.find(c => c.name.toLowerCase() === (plan.source || '').toLowerCase());
        const tgt = state.model.classes.find(c => c.name.toLowerCase() === (plan.target || '').toLowerCase());
        if (!src || !tgt) throw new Error(`No se encontraron las clases ${plan.source} y ${plan.target}`);
        const relIndex = state.model.relationships.findIndex(r =>
            ((r.source.classId === src.id && r.target.classId === tgt.id) ||
             (r.source.classId === tgt.id && r.target.classId === src.id)) &&
            (!plan.type || r.type === plan.type)
        );
        if (relIndex === -1) throw new Error(`No existe relación entre ${src.name} y ${tgt.name}`);
        saveUndo();
        state.model.relationships.splice(relIndex, 1);
        renderAll();
        persistCollaboration();
        broadcastChange();
        refreshMobileCards();
        const toast = document.getElementById('mobileResultStatus');
        if (toast) {
            toast.textContent = `✓ Relación eliminada entre ${src.name} y ${tgt.name}`;
            setTimeout(() => { if (toast.textContent.includes(src.name)) toast.textContent = ''; }, 4000);
        }
        return;
    }

    if (plan.action === 'removeAttribute') {
        const name = (plan.name || '').trim();
        const existing = state.model.classes.find(c => c.name.toLowerCase() === name.toLowerCase());
        if (!existing) throw new Error(`No existe la clase «${name}»`);
        const attr = existing.attributes.find(a => a.name.toLowerCase() === (plan.attributeName || '').toLowerCase());
        if (!attr) throw new Error(`No existe el atributo «${plan.attributeName}» en ${existing.name}`);
        saveUndo();
        existing.removeAttribute(attr.id);
        renderAll();
        persistCollaboration();
        broadcastChange();
        refreshMobileCards();
        const toast = document.getElementById('mobileResultStatus');
        if (toast) {
            toast.textContent = `✓ Atributo ${plan.attributeName} eliminado de ${existing.name}`;
            setTimeout(() => { if (toast.textContent.includes(existing.name)) toast.textContent = ''; }, 4000);
        }
        return;
    }

    if (plan.action === 'addOperation' || plan.action === 'addOperations') {
        const existing = state.model.classes.find(c => c.name.toLowerCase() === (plan.name || '').toLowerCase());
        if (!existing) throw new Error('No existe la clase indicada');
        const ops = plan.operations || (plan.operation ? [plan.operation] : []);
        if (!ops.length) throw new Error('No se especificó ninguna operación');
        for (const op of ops) {
            if (existing.operations.some(o => o.name.toLowerCase() === op.name.toLowerCase())) {
                throw new Error(`El método «${op.name}» ya existe en ${existing.name}`);
            }
        }
        saveUndo();
        for (const op of ops) {
            existing.addOperation({
                id: crypto.randomUUID(),
                name: op.name,
                returnType: op.returnType || 'void',
                visibility: op.visibility || '+',
                parameters: op.parameters || [],
                isAbstract: !!op.isAbstract,
                isStatic: !!op.isStatic,
                isConstructor: !!op.isConstructor
            });
        }
        renderAll();
        persistCollaboration();
        broadcastChange();
        refreshMobileCards();
        const toast = document.getElementById('mobileResultStatus');
        if (toast) {
            toast.textContent = `✓ Método agregado a ${existing.name}: ${ops.map(o => o.name).join(', ')}`;
            setTimeout(() => { if (toast.textContent.includes(existing.name)) toast.textContent = ''; }, 4000);
        }
        return;
    }

    if (plan.action === 'renameClass') {
        const oldName = (plan.oldName || plan.name || '').trim();
        const newName = (plan.newName || '').trim();
        const existing = state.model.classes.find(c => c.name.toLowerCase() === oldName.toLowerCase());
        if (!existing) throw new Error(`No existe la clase «${oldName}»`);
        const collision = state.model.classes.find(c => c.name.toLowerCase() === newName.toLowerCase());
        if (collision) throw new Error(`Ya existe una clase con el nombre «${newName}»`);
        saveUndo();
        existing.name = newName;
        renderAll();
        persistCollaboration();
        broadcastChange();
        refreshMobileCards();
        const toast = document.getElementById('mobileResultStatus');
        if (toast) {
            toast.textContent = `✓ Clase ${oldName} renombrada a ${newName}`;
            setTimeout(() => { if (toast.textContent.includes(newName)) toast.textContent = ''; }, 4000);
        }
        return;
    }

    if (plan.action === 'deleteOperation' || plan.action === 'removeOperation') {
        const name = (plan.name || '').trim();
        const opName = (plan.operationName || plan.operation || '').trim();
        const existing = state.model.classes.find(c => c.name.toLowerCase() === name.toLowerCase());
        if (!existing) throw new Error(`No existe la clase «${name}»`);
        const op = existing.operations.find(o => o.name.toLowerCase() === opName.toLowerCase());
        if (!op) throw new Error(`No existe el método «${opName}» en ${existing.name}`);
        saveUndo();
        existing.removeOperation(op.id);
        renderAll();
        persistCollaboration();
        broadcastChange();
        refreshMobileCards();
        const toast = document.getElementById('mobileResultStatus');
        if (toast) {
            toast.textContent = `✓ Método ${opName} eliminado de ${existing.name}`;
            setTimeout(() => { if (toast.textContent.includes(existing.name)) toast.textContent = ''; }, 4000);
        }
        return;
    }

    const existing = state.model.classes.find(c => c.name.toLowerCase() === plan.name.toLowerCase());
    if (plan.action === 'createClass' && existing) throw new Error('Esa clase ya existe; usa Agrega atributo');
    if (plan.action !== 'createClass' && !existing) throw new Error('No existe la clase indicada');
    if (plan.action === 'addAttributes' && (plan.attributes || []).some(a => existing.attributes.some(b => a.name.toLowerCase() === b.name.toLowerCase()))) throw new Error('Uno de los atributos ya existe');
    
    saveUndo();
    if (plan.action === 'deleteClass') {
        state.model.removeClass(existing.id);
    } else {
        const cls = existing || new UMLClassNode(plan.name, 60 + state.model.classes.length * 240, 100);
        if (plan.isInterface) cls.isInterface = true;
        if (plan.isAbstract) cls.isAbstract = true;
        for (const attr of (plan.attributes || [])) {
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
        let summary = '';
        if (mobilePlan.action === 'deleteClass') {
            summary = `Eliminar ${mobilePlan.name} y sus relaciones`;
        } else if (mobilePlan.action === 'addRelationship') {
            summary = `Relación [${mobilePlan.type}]: ${mobilePlan.source} ➔ ${mobilePlan.target}`;
        } else if (mobilePlan.action === 'deleteRelationship') {
            summary = `Eliminar relación entre ${mobilePlan.source} y ${mobilePlan.target}`;
        } else if (mobilePlan.action === 'removeAttribute') {
            summary = `Eliminar atributo ${mobilePlan.attributeName} de ${mobilePlan.name}`;
        } else if (mobilePlan.action === 'addOperation' || mobilePlan.action === 'addOperations') {
            const ops = mobilePlan.operations || (mobilePlan.operation ? [mobilePlan.operation] : []);
            summary = `Agregar método a ${mobilePlan.name}: ${ops.map(o => `${o.visibility || '+'}${o.name}(${(o.parameters||[]).map(p=>p.name+': '+p.type).join(', ')}) : ${o.returnType || 'void'}`).join(', ')}`;
        } else if (mobilePlan.action === 'renameClass') {
            summary = `Renombrar clase ${mobilePlan.oldName} a ${mobilePlan.newName}`;
        } else if (mobilePlan.action === 'deleteOperation' || mobilePlan.action === 'removeOperation') {
            summary = `Eliminar método ${mobilePlan.operationName} de ${mobilePlan.name}`;
        } else if (mobilePlan.isInterface) {
            summary = `Crear interfaz ${mobilePlan.name}`;
        } else if (mobilePlan.isAbstract) {
            summary = `Crear clase abstracta ${mobilePlan.name}: ${(mobilePlan.attributes || []).map(a => `${a.name}: ${a.type}`).join(', ') || 'sin atributos'}`;
        } else {
            summary = `${mobilePlan.action === 'createClass' ? 'Crear' : 'Agregar a'} ${mobilePlan.name}: ${(mobilePlan.attributes || []).map(a => `${a.name}: ${a.type}`).join(', ') || 'sin atributos'}`;
        }
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

        // Operations list
        const opsList = document.createElement('ul');
        opsList.className = 'mobile-attr-list mobile-ops-list';
        if (cls.operations && cls.operations.length) {
            const opsHeader = document.createElement('li');
            opsHeader.style.cssText = 'color:var(--text-secondary); font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; padding:6px 8px 2px;';
            opsHeader.textContent = 'Métodos';
            opsList.append(opsHeader);

            for (const op of cls.operations) {
                const li = document.createElement('li');
                li.className = 'mobile-attr-item mobile-op-item';

                const left = document.createElement('div');
                left.className = 'attr-item-left';
                const vis = document.createElement('span');
                vis.className = 'attr-vis-badge';
                vis.style.background = 'rgba(99, 102, 241, 0.15)';
                vis.style.color = '#818cf8';
                vis.textContent = op.visibility || '+';
                const name = document.createElement('span');
                name.className = 'attr-name-text';
                const paramStr = (op.parameters || []).map(p => `${p.name}: ${p.type}`).join(', ');
                name.textContent = `${op.name}(${paramStr})`;
                left.append(vis, name);

                const right = document.createElement('div');
                right.className = 'attr-item-right';
                const badge = document.createElement('span');
                badge.className = `type-badge ${getTypeBadgeClass(op.returnType || 'void')}`;
                badge.textContent = op.returnType || 'void';

                const delOp = document.createElement('button');
                delOp.type = 'button';
                delOp.className = 'btn-del-attr';
                delOp.textContent = '×';
                delOp.title = `Eliminar método ${op.name}`;
                delOp.onclick = (e) => {
                    e.stopPropagation();
                    if (collaborationState.role === 'viewer') return;
                    saveUndo();
                    cls.removeOperation(op.id);
                    renderAll();
                    persistCollaboration();
                    broadcastChange();
                    refreshMobileCards();
                };

                right.append(badge, delOp);
                li.append(left, right);
                opsList.append(li);
            }
        }

        // Action buttons
        const actionsRow = document.createElement('div');
        actionsRow.className = 'mobile-card-actions';
        actionsRow.style.cssText = 'display:flex; gap:8px; margin-top:8px;';

        const addAttrBtn = document.createElement('button');
        addAttrBtn.type = 'button';
        addAttrBtn.className = 'btn-add-attr-card';
        addAttrBtn.style.flex = '1';
        addAttrBtn.innerHTML = `<span>+</span> Atributo`;
        addAttrBtn.onclick = () => openMobileForm(cls.name);

        const addOpBtn = document.createElement('button');
        addOpBtn.type = 'button';
        addOpBtn.className = 'btn-add-attr-card';
        addOpBtn.style.flex = '1';
        addOpBtn.style.borderColor = 'rgba(99, 102, 241, 0.5)';
        addOpBtn.innerHTML = `<span>+</span> Método`;
        addOpBtn.onclick = () => openMobileOperationForm(cls.name);

        actionsRow.append(addAttrBtn, addOpBtn);
        card.append(header, attrsList, opsList, actionsRow);
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

function openMobileOperationForm(className) {
    if (collaborationState.role === 'viewer') {
        if (typeof showToast === 'function') showToast('Este proyecto es de solo lectura', 'warning');
        return;
    }
    const cls = state.model.classes.find(c => c.name.toLowerCase() === (className || '').toLowerCase());
    if (!cls) {
        if (typeof showToast === 'function') showToast('Clase no encontrada', 'error');
        return;
    }

    const dialog = document.createElement('dialog');
    dialog.className = 'mobile-bottom-sheet';
    dialog.innerHTML = `
        <form class="mobile-sheet-form">
            <div class="sheet-header">
                <div class="sheet-title-group">
                    <span class="sheet-header-icon">⚙️</span>
                    <h2>Agregar método a ${cls.name}</h2>
                </div>
                <button type="button" class="sheet-close-btn" id="btnCancelOpX" aria-label="Cerrar">×</button>
            </div>
            <div class="sheet-body">
                <label class="sheet-field-label">
                    <span class="label-title">Nombre del método</span>
                    <input name="opName" class="sheet-input" placeholder="Ej: calcularTotal, validar, procesar" required autocomplete="off">
                </label>
                <div class="fields-row" style="display:flex; gap:8px;">
                    <label class="sheet-field-label" style="flex:1;">
                        <span class="label-title">Retorno</span>
                        <select name="returnType" class="sheet-select">
                            <option value="void">void (Sin retorno)</option>
                            <option value="String">String (Texto)</option>
                            <option value="Integer">Integer (Entero)</option>
                            <option value="Double">Double (Decimal)</option>
                            <option value="Boolean">Boolean (Booleano)</option>
                            <option value="LocalDate">LocalDate (Fecha)</option>
                            <option value="Long">Long (ID)</option>
                        </select>
                    </label>
                    <label class="sheet-field-label" style="flex:1;">
                        <span class="label-title">Visibilidad</span>
                        <select name="visibility" class="sheet-select">
                            <option value="+">Público (+)</option>
                            <option value="-">Privado (-)</option>
                            <option value="#">Protegido (#)</option>
                            <option value="~">Paquete (~)</option>
                        </select>
                    </label>
                </div>
                <label class="sheet-field-label">
                    <span class="label-title">Parámetros (Opcional, Ej: monto: Double, activo: Boolean)</span>
                    <input name="parameters" class="sheet-input" placeholder="Ej: monto: Double" autocomplete="off">
                </label>
                <p class="sheet-error-msg" role="alert" style="color:var(--danger, #ef4444); font-size:13px; margin-top:4px;"></p>
            </div>
            <div class="sheet-footer" style="display:flex; gap:8px; justify-content:flex-end; margin-top:12px;">
                <button type="button" class="btn-secondary" id="btnCancelOp">Cancelar</button>
                <button type="submit" class="btn-primary">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    Guardar Método
                </button>
            </div>
        </form>
    `;

    const form = dialog.querySelector('form');
    const errEl = dialog.querySelector('[role=alert]');
    const closeDialog = () => { dialog.close(); dialog.remove(); };
    dialog.querySelector('#btnCancelOp').onclick = closeDialog;
    dialog.querySelector('#btnCancelOpX').onclick = closeDialog;

    form.onsubmit = (e) => {
        e.preventDefault();
        try {
            if (collaborationState.role === 'viewer') throw new Error('Este proyecto es de solo lectura');
            const targetCls = state.model.classes.find(c => c.id === cls.id);
            if (!targetCls) throw new Error('La clase ya no existe');

            const opNameRaw = form.elements.opName.value.trim();
            const opName = UMLCommands.identifier(opNameRaw);
            if (targetCls.operations.some(o => o.name.toLowerCase() === opName.toLowerCase())) {
                throw new Error(`El método «${opName}» ya existe en ${targetCls.name}`);
            }

            const rawParams = (form.elements.parameters.value || '').trim();
            const parameters = rawParams ? rawParams.split(',').map(raw => {
                const pMatch = raw.trim().match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*(?::\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\[\])?))?$/);
                if (!pMatch) throw new Error('Parámetro inválido; usa nombre: Tipo');
                return { name: UMLCommands.identifier(pMatch[1]), type: pMatch[2] || 'String' };
            }) : [];

            if (new Set(parameters.map(p => p.name.toLowerCase())).size !== parameters.length) {
                throw new Error('Parámetros repetidos en el método');
            }

            saveUndo();
            targetCls.addOperation({
                id: crypto.randomUUID(),
                name: opName,
                returnType: form.elements.returnType.value || 'void',
                visibility: form.elements.visibility.value || '+',
                parameters,
                isAbstract: false,
                isStatic: false,
                isConstructor: false
            });

            renderAll();
            persistCollaboration();
            broadcastChange();
            refreshMobileCards();

            if (typeof showToast === 'function') {
                showToast(`Método «${opName}» agregado a ${targetCls.name}`, 'success');
            }
            closeDialog();
        } catch (err) {
            if (errEl) errEl.textContent = err.message;
        }
    };

    document.body.append(dialog);
    dialog.showModal();
    const nameInput = form.querySelector('[name="opName"]');
    if (nameInput) nameInput.focus();
}

function renderPhotoConnections(result, container = null) {
    document.getElementById('photoConnectionsReview')?.remove();
    if(!result.connections?.length&&!result.ambiguous?.length&&!(result.markers||[]).length)return;
    const section=document.createElement('section');section.id='photoConnectionsReview';
    section.style.cssText='margin-top:12px;padding:10px;border:1px solid #334155;border-radius:8px;background:#0f172a;';
    const title=document.createElement('h3');title.textContent='Conexiones detectadas en la foto';title.style.cssText='margin:0 0 8px;font-size:15px;color:#e2e8f0;';section.append(title);
    const note=document.createElement('p');note.textContent='Son propuestas. Confirma el tipo, la dirección y las multiplicidades mirando la foto. No se agregan automáticamente.';note.style.cssText='font-size:12px;color:#94a3b8;margin:0 0 10px;';section.append(note);
    const find=index=>{const name=UMLCommands.identifier(result.names[index],true);return state.model.classes.find(c=>c.name.toLowerCase()===name.toLowerCase());};
    for(const marker of result.markers||[]){
        const hint=document.createElement('div');
        hint.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 8px;margin-bottom:6px;background:#1e293b;border-radius:6px;font-size:13px;';
        const targetCls = find(marker.box);
        if(marker.kind==='hollowTriangle' && targetCls){
            hint.innerHTML=`<span style="flex:1;">△ Triángulo junto a <strong>${targetCls.name}</strong></span>`;
            const btnGroup=document.createElement('div');btnGroup.style.cssText='display:flex;gap:4px;';
            const btnInherit=document.createElement('button');btnInherit.type='button';btnInherit.className='btn btn-sm';btnInherit.textContent=`Herencia → ${targetCls.name}`;btnInherit.style.fontSize='11px';
            btnInherit.onclick=()=>openMobileRelationship({target:targetCls.id,type:'generalization'});
            const btnRealize=document.createElement('button');btnRealize.type='button';btnRealize.className='btn btn-sm';btnRealize.textContent=`Realización → ${targetCls.name}`;btnRealize.style.cssText='font-size:11px;border-color:#818cf8;';
            btnRealize.onclick=()=>openMobileRelationship({target:targetCls.id,type:'realization'});
            btnGroup.append(btnInherit,btnRealize);
            hint.append(btnGroup);
        } else if(marker.kind==='hollowDiamond') {
            hint.innerHTML=`<span style="flex:1;">◇ Rombo vacío junto a <strong>${result.names[marker.box]}</strong>: posible agregación</span>`;
            if(targetCls){
                const btn=document.createElement('button');btn.type='button';btn.className='btn btn-sm';btn.textContent='Agregar agregación';btn.style.fontSize='11px';
                btn.onclick=()=>openMobileRelationship({target:targetCls.id,type:'aggregation'});
                hint.append(btn);
            }
        } else {
            hint.textContent=`Marcador ${marker.kind} junto a ${result.names[marker.box]}: revisa las clases de origen.`;
        }
        section.append(hint);
    }
    for(const pair of result.connections||[]){
        const wrapper=document.createElement('div');wrapper.style.cssText='display:flex;align-items:center;gap:6px;margin-bottom:4px;';
        const button=document.createElement('button');button.type='button';button.className='btn';button.style.cssText='flex:1;font-size:12px;text-align:left;padding:6px 10px;';
        let label=pair.map(i=>result.names[i]).join(' ↔ ');
        const suggestion=(result.suggestions||[]).find(s=>pair.includes(s.source)&&pair.includes(s.target));
        if(suggestion){
            const typeLabels={aggregation:'agregación',composition:'composición',generalization:'herencia',realization:'realización'};
            label+=` — posible ${typeLabels[suggestion.type]||suggestion.type}`;
            if(suggestion.sourceMult||suggestion.targetMult) label+=` (${suggestion.sourceMult||'?'}..${suggestion.targetMult||'?'})`;
        }
        button.textContent=label;
        button.onclick=()=>{try{const source=find(suggestion?suggestion.source:pair[0]),target=find(suggestion?suggestion.target:pair[1]);if(!source||!target)throw new Error('Importa primero las clases o comprueba sus nombres.');openMobileRelationship({source:source.id,target:target.id,type:suggestion?.type,sourceMult:suggestion?.sourceMult,targetMult:suggestion?.targetMult});}catch(error){note.textContent=error.message;}};
        wrapper.append(button);
        section.append(wrapper);
    }
    if(result.ambiguous?.length){
        const ambTitle=document.createElement('h4');ambTitle.textContent='Cruces y ramificaciones';ambTitle.style.cssText='margin:10px 0 4px;font-size:13px;color:#fbbf24;';section.append(ambTitle);
        for(const group of result.ambiguous){
            const text=document.createElement('p');text.style.cssText='font-size:12px;color:#fbbf24;padding:4px 8px;background:#1e293b;border-radius:4px;border-left:3px solid #f59e0b;margin:4px 0;';
            text.textContent='⚠ Cruce o ramificación: '+group.map(i=>result.names[i]).join(', ')+'. Usa «Conectar clases» para cada relación.';
            section.append(text);
        }
    }
    const manual=document.createElement('button');manual.type='button';manual.className='btn';manual.textContent='+ Conectar clases manualmente';manual.style.cssText='margin-top:8px;width:100%;font-size:12px;';manual.onclick=()=>openMobileRelationship();section.append(manual);
    (container || document.getElementById('mobilePhotoReview')).append(section);
}

