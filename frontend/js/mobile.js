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
            cls.addAttribute({ ...attr, id: crypto.randomUUID(), visibility: '-', constraints: [] });
        }
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

        card.append(header, attrsList, addAttrBtn);
        container.append(card);
    }
}

function reviewPhotoText(text) {
    let clean = text.replace(/\bcddigo\b/gi, 'codigo')
                    .replace(/\bcod1go\b/gi, 'codigo')
                    .replace(/\bc0digo\b/gi, 'codigo');
    return clean.trim().split(/\n\s*\n/).filter(Boolean).map(block => {
        const lines = block.split('\n').map(s => s.trim().replace(/^[+\-#~|│┌┐└┘├┤─]\s*/, '')).filter(Boolean);
        if (!lines.length) return null;
        if (lines.length === 1 && (/^(ejemplo|diagrama|clases|modelo)\b/i.test(lines[0]) || !lines[0].includes(':'))) {
            return null;
        }
        try {
            const name = UMLCommands.identifier(lines.shift(), true);
            const attributes = lines.filter(line => !line.includes('(')).map(line => {
                try { return UMLCommands.attributes(line)[0]; } catch (e) { return null; }
            }).filter(Boolean);
            if (!attributes.length && /^(ejemplo|diagrama)/i.test(name)) return null;
            return { action: 'createClass', name, attributes };
        } catch (e) {
            return null;
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
        siriTextInput.value = '';
        if (window.ConversationalAssistant) {
            ConversationalAssistant.processMessage(msg);
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
            $('#mobilePhotoText').value = rawText;
            $('#mobilePhotoReview').hidden = false;
            if (status) status.textContent = '¡Texto detectado! Puedes editarlo o complementar con voz antes de importar.';
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
            const plans = reviewPhotoText($('#mobilePhotoText').value);
            if (!plans.length) throw new Error('No se detectaron clases válidas. Revisa el texto arriba.');
            const names = plans.map(p => p.name.toLowerCase());
            if (new Set(names).size !== names.length || state.model.classes.some(c => names.includes(c.name.toLowerCase()))) {
                throw new Error('Hay nombres de clases repetidos; corrige el texto antes de importar');
            }
            for (const plan of plans) applyUMLPlan(plan);
            const status = document.getElementById('mobilePhotoStatus');
            if (status) status.textContent = `✓ Importadas ${plans.length} clases al diagrama.`;
            aiStatus(`Importadas ${plans.length} clases revisadas. Revisa atributos y añade las relaciones.`);
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
