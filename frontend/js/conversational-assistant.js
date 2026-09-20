/**
 * GeneradorUML — Asistente de Voz Conversacional Inteligente (Siri UML)
 * 
 * Dialoga en lenguaje natural mediante voz (TTS + Whisper/WebSpeech + Gemini Flash),
 * interpreta intenciones de modelado y aplica cambios en tiempo real al diagrama UML.
 */

const ConversationalAssistant = (function() {
    let conversationHistory = [];
    let isSpeaking = false;
    let isBusy = false;

    // ─── Text-To-Speech (Voz del Asistente) ──────────────────────────────────
    function speak(text, onStart, onEnd) {
        if (!('speechSynthesis' in window)) {
            isSpeaking=false;
            updateOrbState('ready');
            if (onEnd) onEnd();
            return;
        }
        try {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'es-ES';
            utterance.rate = 1.08; // Ritmo ágil y natural
            utterance.pitch = 1.0;

            const voices = window.speechSynthesis.getVoices();
            const esVoice = voices.find(v => v.lang.startsWith('es') && (
                v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Paulina') || v.name.includes('Helena') || v.name.includes('Neural')
            )) || voices.find(v => v.lang.startsWith('es'));
            
            if (esVoice) utterance.voice = esVoice;

            utterance.onstart = () => {
                isSpeaking = true;
                updateOrbState('speaking');
                if (onStart) onStart();
            };
            const finish = () => {
                isSpeaking = false;
                updateOrbState('ready');
                if (onEnd) onEnd();
            };
            utterance.onend = finish;
            utterance.onerror = finish;

            window.speechSynthesis.speak(utterance);
        } catch (e) {
            console.warn('SpeechSynthesis error:', e);
            isSpeaking=false;
            updateOrbState('ready');
            if (onEnd) onEnd();
        }
    }

    function stopSpeaking() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            isSpeaking = false;
            updateOrbState('ready');
        }
    }

    let audioCtx = null;
    let audioAnalyser = null;
    let animFrameId = null;

    // Use the configured server only; never probe unrelated LAN addresses.
    async function backendFetch(path, options = {}) {
        if(typeof navigator!=='undefined' && navigator.onLine===false)throw new Error('Sin conexión.');
        const isMobileHost = window.location.host === 'appassets.androidplatform.net' ||
            window.location.protocol === 'file:' || !window.location.origin.startsWith('http');
        const base = typeof umlBackendOrigin === 'function' ? umlBackendOrigin() :
            (isMobileHost ? localStorage.getItem('uml_backend_url') : window.location.origin);
        if (!base) throw new Error('Configura el servidor para usar el asistente en línea.');
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        try {
            return await fetch(`${base}${path}`, {...options, signal:controller.signal});
        } finally { clearTimeout(timeoutId); }
    }
    // ─── Visualizador de Ondas en Tiempo Real (Responde a la voz) ────────────
    function startAudioVisualizer(stream) {
        stopAudioVisualizer();
        if (!stream) return;
        try {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioCtx.createMediaStreamSource(stream);
            audioAnalyser = audioCtx.createAnalyser();
            audioAnalyser.fftSize = 64;
            audioAnalyser.smoothingTimeConstant = 0.75;
            source.connect(audioAnalyser);

            const dataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
            const spans = document.querySelectorAll('#siriSoundwaves span');
            const orb = document.getElementById('siriOrb');

            function renderWaves() {
                if (!audioAnalyser) return;
                animFrameId = requestAnimationFrame(renderWaves);
                audioAnalyser.getByteFrequencyData(dataArray);

                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    sum += dataArray[i];
                }
                const avg = sum / (dataArray.length || 1);

                // Escalar orbe suavemente con la intensidad de la voz
                if (orb && orb.classList.contains('state-listening')) {
                    const scale = 1.0 + Math.min(avg / 90, 0.28);
                    orb.style.transform = `scale(${scale})`;
                }

                // Ajustar altura de las 5 barras
                if (spans && spans.length >= 5) {
                    for (let i = 0; i < 5; i++) {
                        const bin = dataArray[i * 2 + 1] || avg;
                        const h = Math.max(6, Math.min(30, (bin / 255) * 32 + 6));
                        spans[i].style.height = `${h}px`;
                    }
                }
            }
            renderWaves();
        } catch (e) {
            console.warn('AudioVisualizer no iniciado:', e);
        }
    }

    function stopAudioVisualizer() {
        if (animFrameId) {
            cancelAnimationFrame(animFrameId);
            animFrameId = null;
        }
        if (audioCtx) {
            try { audioCtx.close(); } catch (_) {}
            audioCtx = null;
            audioAnalyser = null;
        }
        const orb = document.getElementById('siriOrb');
        if (orb) orb.style.transform = '';
        const spans = document.querySelectorAll('#siriSoundwaves span');
        if (spans) spans.forEach(s => s.style.height = '');
    }

    // ─── Actualización Visual del Orbe Siri ─────────────────────────────────
    function updateOrbState(stateName, customText) {
        const orb = document.getElementById('siriOrb');
        const statusText = document.getElementById('siriStatusText');
        const soundwaves = document.getElementById('siriSoundwaves');
        const stopBtn = document.getElementById('btnSiriStopRecording');
        if (!orb) return;

        orb.classList.remove('state-ready', 'state-preparing', 'state-listening', 'state-thinking', 'state-speaking');
        orb.classList.add(`state-${stateName}`);

        if (stateName === 'listening') {
            if (stopBtn) stopBtn.style.display = 'inline-flex';
        } else {
            if (stopBtn) stopBtn.style.display = 'none';
        }

        if (statusText) {
            if (customText) {
                statusText.textContent = customText;
            } else {
                switch (stateName) {
                    case 'preparing':
                        statusText.textContent = '⏳ Iniciando micrófono y modelo...';
                        if (soundwaves) soundwaves.classList.remove('active');
                        break;
                    case 'listening':
                        statusText.textContent = '🔴 Escuchando tu voz... Toca el orbe para enviar';
                        if (soundwaves) soundwaves.classList.add('active');
                        break;
                    case 'thinking':
                        statusText.textContent = '✨ Gemini está razonando tu modelo...';
                        if (soundwaves) soundwaves.classList.remove('active');
                        break;
                    case 'speaking':
                        statusText.textContent = 'Siri UML está respondiendo...';
                        if (soundwaves) soundwaves.classList.add('active');
                        break;
                    default:
                        statusText.textContent = 'Toca el orbe para hablar con Siri UML';
                        if (soundwaves) soundwaves.classList.remove('active');
                }
            }
        }
    }

    // ─── Ejecución de Acciones en el Diagrama UML ───────────────────────────
    function executeActionUnchecked(act) {
        if (!act || !act.action) return null;
        const actionType = act.action;
        let changeDesc = '';

        if (actionType === 'createClass') {
            const name = (act.name || '').trim();
            if (!name) return null;
            let existing = state.model.classes.find(c => c.name.toLowerCase() === name.toLowerCase());
            if (!existing) {
                const cls = new UMLClassNode(name, 60 + state.model.classes.length * 240, 100);
                if (act.attributes && Array.isArray(act.attributes)) {
                    for (const a of act.attributes) {
                        cls.addAttribute({
                            name: a.name,
                            type: a.type || 'String',
                            id: crypto.randomUUID(),
                            visibility: '-',
                            constraints: []
                        });
                    }
                }
                state.model.addClass(cls);
                changeDesc = `Clase ${name} creada`;
            } else if (act.attributes && Array.isArray(act.attributes)) {
                for (const a of act.attributes) {
                    if (!existing.attributes.some(attr => attr.name.toLowerCase() === a.name.toLowerCase())) {
                        existing.addAttribute({
                            name: a.name,
                            type: a.type || 'String',
                            id: crypto.randomUUID(),
                            visibility: '-',
                            constraints: []
                        });
                    }
                }
                changeDesc = `Atributos agregados a ${name}`;
            }
        } else if (actionType === 'addAttributes') {
            const name = (act.name || '').trim();
            const existing = state.model.classes.find(c => c.name.toLowerCase() === name.toLowerCase());
            if (existing && act.attributes && Array.isArray(act.attributes)) {
                for (const a of act.attributes) {
                    if (!existing.attributes.some(attr => attr.name.toLowerCase() === a.name.toLowerCase())) {
                        existing.addAttribute({
                            name: a.name,
                            type: a.type || 'String',
                            id: crypto.randomUUID(),
                            visibility: '-',
                            constraints: []
                        });
                    }
                }
                changeDesc = `Atributos agregados a ${name}`;
            }
        } else if (actionType === 'updateAttribute') {
            const name = (act.name || '').trim();
            const existing = state.model.classes.find(c => c.name.toLowerCase() === name.toLowerCase());
            if (existing && act.oldAttributeName) {
                const target = existing.attributes.find(a => a.name.toLowerCase() === act.oldAttributeName.toLowerCase());
                if (target) {
                    if (act.newAttributeName) target.name = act.newAttributeName;
                    if (act.type) target.type = act.type;
                    changeDesc = `Atributo ${target.name} actualizado en ${name}`;
                }
            }
        } else if (actionType === 'removeAttribute') {
            const name = (act.name || '').trim();
            const existing = state.model.classes.find(c => c.name.toLowerCase() === name.toLowerCase());
            if (existing && act.attributeName) {
                existing.attributes = existing.attributes.filter(a => a.name.toLowerCase() !== act.attributeName.toLowerCase());
                changeDesc = `Atributo ${act.attributeName} eliminado de ${name}`;
            }
        } else if (actionType === 'deleteClass') {
            const name = (act.name || '').trim();
            const existing = state.model.classes.find(c => c.name.toLowerCase() === name.toLowerCase());
            if (existing) {
                state.model.removeClass(existing.id);
                changeDesc = `Clase ${name} eliminada`;
            }
        } else if (actionType === 'addRelationship') {
            const src = state.model.classes.find(c => c.name.toLowerCase() === (act.source || '').toLowerCase());
            const tgt = state.model.classes.find(c => c.name.toLowerCase() === (act.target || '').toLowerCase());
            if (src && tgt) {
                const rel = new UMLRelNode(act.type || 'association', src.id, tgt.id);
                if (act.multiplicitySource) rel.source.multiplicity = act.multiplicitySource;
                if (act.multiplicityTarget) rel.target.multiplicity = act.multiplicityTarget;
                state.model.addRelationship(rel);
                changeDesc = `Relación ${src.name} ➔ ${tgt.name}`;
            }
        }
        return changeDesc;
    }

    function executeAction(act) {
        if(collaborationState.role==='viewer')throw new Error('Este enlace es de solo lectura.');
        const allowed=['createClass','addAttributes','updateAttribute','removeAttribute','deleteClass','addRelationship'];
        if(!act||!allowed.includes(act.action))throw new Error('La acción propuesta no está disponible.');
        const identifier=value=>{if(typeof value!=='string'||!/^[A-Za-z_][A-Za-z0-9_]*$/.test(value))throw new Error('El nombre propuesto no es válido.');};
        const types=['String','Integer','Double','Boolean','LocalDate','Long'];
        if(act.name)identifier(act.name);
        if(act.attributes!==undefined&&!Array.isArray(act.attributes))throw new Error('Atributos inválidos.');
        for(const attr of act.attributes||[]){identifier(attr.name);if(!types.includes(attr.type))throw new Error('Tipo de atributo no admitido.');}
        if(act.newAttributeName)identifier(act.newAttributeName);
        if(act.type && act.action==='updateAttribute'&&!types.includes(act.type))throw new Error('Tipo de atributo no admitido.');
        if(act.action==='addRelationship'&&!['association','aggregation','composition','generalization'].includes(act.type))throw new Error('Tipo de relación no admitido.');
        const before=JSON.stringify(state.model.toJSON());
        const result=executeActionUnchecked(act);
        if(before===JSON.stringify(state.model.toJSON()))throw new Error('No hubo cambios: el elemento no existe o ya tiene esos datos.');
        if(act.action==='createClass')return result+'. Atributos: '+(act.attributes||[]).map(a=>a.name).join(', ');
        return result;
    }

    // ─── Filtro de Ruido y Artefactos de Silencio (Whisper) ─────────────────
    const NOISE_ARTIFACTS = [
        'música', 'musica', 'music', 'sonido', 'ruido',
        'silencio', 'aplausos', 'risas', 'tos', 'suspiro',
        'subtítulos realizados por la comunidad de amara.org',
        'subtitulado por la comunidad de amara.org',
        'subtítulos por', 'amara.org'
    ];

    function cleanTranscription(raw) {
        if (!raw) return '';
        let t = raw.trim();
        // Quitar etiquetas automáticas de subtítulos como [Música], (música), etc.
        const stripped = t.replace(/\[[^\]]*\]/g, '').replace(/\([^)]*\)/g, '').trim();
        if (!stripped || stripped.length < 2) {
            return '';
        }
        const lower = stripped.toLowerCase();
        for (const noise of NOISE_ARTIFACTS) {
            if (lower === noise || lower.includes('amara.org')) {
                return '';
            }
        }
        return stripped;
    }

    // ─── Proceso Conversacional Inteligente ──────────────────────────────────
    async function processMessage(userMessage) {
        const cleaned = cleanTranscription(userMessage);
        if (!cleaned) {
            updateOrbState('ready', 'No alcancé a escucharte bien. Toca el orbe y habla de nuevo.');
            speak('No te escuché bien, por favor háblame de nuevo.');
            return;
        }

        if (isBusy) {updateOrbState('thinking','Estoy procesando el pedido anterior; tu texto sigue en el campo.');return false;}
        isBusy = true;
        updateOrbState('thinking', '✨ Gemini está razonando tu modelo...');

        // Mostrar burbuja del usuario
        displayChatBubble('user', cleaned);

        const currentDiagram = state.model.toJSON();

        try {
            // Petición al endpoint de Gemini en el backend (compatible con USB / Wi-Fi / Web)
            const res = await backendFetch('/api/assistant/converse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: cleaned,
                    diagram: currentDiagram,
                    history: conversationHistory
                })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Error HTTP ${res.status}`);
            }

            const data = await res.json();
            let spokenResponse = data.spoken_response || '¿Qué cambio querés hacer?';
            const actions = data.actions || [];
            if(!Array.isArray(actions))throw new Error('Respuesta de acciones inválida.');

            let appliedChanges = [];
            if(actions.length) {
                if(!sameDiagram(currentDiagram,state.model.toJSON()))throw new Error('El diagrama cambió durante la consulta. Repetí el pedido sobre la versión actual.');
                const original=state.model;
                state.model=UMLModel.fromJSON(currentDiagram);
                try {
                    for(const act of actions)appliedChanges.push(executeAction(act));
                    const updated=state.model;
                    state.model=original;saveUndo();state.model=updated;
                } catch(error) {
                    state.model=original;
                    const message='No apliqué cambios. '+error.message;
                    displayChatBubble('assistant',message);speak(message);return;
                }
                renderAll();persistCollaboration();broadcastChange();refreshMobileCards();
                spokenResponse=appliedChanges.join('. ')+'.';
            }

            // Actualizar historial conversacional
            conversationHistory.push({ role: 'user', text: cleaned });
            conversationHistory.push({ role: 'assistant', text: spokenResponse });
            if (conversationHistory.length > 8) conversationHistory.splice(0, 2);

            // Mostrar burbuja del asistente con los cambios
            displayChatBubble('assistant', spokenResponse, appliedChanges);

            // Hablar en voz alta
            speak(spokenResponse);

        } catch (err) {
            console.warn('Fallo en Gemini online, aplicando fallback local:', err);
            
            // Fallback sin conexión (offline parser)
            try {
                const localPlan = UMLCommands.parse(cleaned);
                const commandInput=document.getElementById('mobileCommand');
                commandInput.value=cleaned;
                commandInput.dispatchEvent(new Event('input',{bubbles:true}));
                reviewMobileCommand();
                commandInput.closest('section').hidden=false;
                commandInput.scrollIntoView({behavior:'smooth',block:'center'});
                const localText='No pude completar la consulta en línea. Preparé una propuesta local para revisar; todavía no modifiqué el diagrama.';
                updateOrbState('ready',localText);
                displayChatBubble('assistant',localText);
                speak(localText);
            } catch (fallbackErr) {
                const errorMsg = 'No pude completar la consulta en línea ni interpretar la frase localmente. No modifiqué el diagrama. Podés corregir el texto y volver a enviarlo.';
                updateOrbState('ready',errorMsg);
                displayChatBubble('assistant', errorMsg);
                speak(errorMsg);
            }
        } finally {
            isBusy = false;
            if(!isSpeaking)updateOrbState('ready');
        }
    }

    // ─── UI de Burbujas de Chat ──────────────────────────────────────────────
    function displayChatBubble(sender, text, changes = []) {
        const chatContainer = document.getElementById('siriChatFeed');
        if (!chatContainer) return;

        const bubble = document.createElement('div');
        bubble.className = `siri-bubble siri-bubble-${sender}`;

        const textP = document.createElement('p');
        textP.className = 'bubble-text';
        textP.textContent = text;
        bubble.append(textP);

        if (changes && changes.length > 0) {
            const changesWrap = document.createElement('div');
            changesWrap.className = 'bubble-changes-wrap';
            for (const ch of changes) {
                const pill = document.createElement('span');
                pill.className = 'bubble-change-pill';
                pill.textContent = `✓ ${ch}`;
                changesWrap.append(pill);
            }
            bubble.append(changesWrap);
        }

        if (sender === 'assistant') {
            const replayBtn = document.createElement('button');
            replayBtn.type = 'button';
            replayBtn.className = 'bubble-replay-btn';
            replayBtn.innerHTML = '🔊 Repetir';
            replayBtn.onclick = () => speak(text);
            bubble.append(replayBtn);
        }

        chatContainer.append(bubble);
        bubble.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }

    // ─── Interacción con Micrófono y Sesión ────────────────────────────────────
    function toggleVoiceSession() {
        if(isBusy || localAI.pending || document.getElementById('siriOrb')?.classList.contains('state-preparing'))return;
        if (isSpeaking) {
            stopSpeaking();
            return;
        }

        // Si ya está grabando actualmente, detener grabación
        if (typeof localAI !== 'undefined' && localAI.recorder?.state === 'recording') {
            localAI.recorder.stop();
            return;
        }

        // Si está en reposo, iniciar grabación local
        if (typeof toggleLocalRecording === 'function') {
            toggleLocalRecording();
        }
    }

    function onTranscriptionReceived(text) {
        if (!text || !text.trim()) {
            updateOrbState('ready');
            return;
        }
        processMessage(text.trim());
    }

    return {
        isBusy:()=>isBusy,
        speak,
        stopSpeaking,
        processMessage,
        toggleVoiceSession,
        onTranscriptionReceived,
        updateOrbState,
        startAudioVisualizer,
        stopAudioVisualizer
    };
})();

// ─── Eventos del Ciclo de Vida de Grabación y Transcripción ──────────────────
window.addEventListener('voice-recording-preparing', () => {
    ConversationalAssistant.updateOrbState('preparing', '⏳ Iniciando micrófono y motor de voz...');
});

window.addEventListener('voice-recording-started', (e) => {
    ConversationalAssistant.updateOrbState('listening', '🔴 Escuchando... Habla tu comando (Toca para enviar)');
    if (e.detail && e.detail.stream) {
        ConversationalAssistant.startAudioVisualizer(e.detail.stream);
    }
});

window.addEventListener('voice-recording-stopped', () => {
    ConversationalAssistant.stopAudioVisualizer();
    ConversationalAssistant.updateOrbState('thinking', '⚡ Transcribiendo voz con Whisper IA...');
});

window.addEventListener('voice-transcribing', () => {
    ConversationalAssistant.updateOrbState('thinking', '⚡ Transcribiendo voz con Whisper IA...');
});

window.addEventListener('voice-recording-error', (e) => {
    ConversationalAssistant.stopAudioVisualizer();
    ConversationalAssistant.updateOrbState('ready', e.detail?.error ? `Error: ${e.detail.error}` : 'Error de micrófono');
});

// Escuchar evento cuando Whisper o WebSpeech transcriban
window.addEventListener('voice-transcription-done', (e) => {
    if (e.detail && e.detail.text) {
        ConversationalAssistant.onTranscriptionReceived(e.detail.text);
    }
});
