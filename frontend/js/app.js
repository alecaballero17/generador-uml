/**
 * GeneradorUML — Main Application
 *
 * Interactive UML class diagram editor with SVG canvas, drag-and-drop,
 * real-time property editing, code generation, voice input, and photo import.
 */

// ═══════════════════════════════════════════════════════════════════════════
// Data Model (mirrors the Python backend model)
// ═══════════════════════════════════════════════════════════════════════════

class UMLModel {
    constructor() {
        this.id = crypto.randomUUID();
        this.name = 'Nuevo Diagrama';
        this.description = '';
        this.classes = [];
        this.relationships = [];
        this.version = '1.0.0';
        this.umlVersion = '2.5.1';
    }

    addClass(cls) { this.classes.push(cls); return cls; }
    removeClass(id) {
        this.classes = this.classes.filter(c => c.id !== id);
        this.relationships = this.relationships.filter(
            r => r.source.classId !== id && r.target.classId !== id
        );
    }
    getClass(id) { return this.classes.find(c => c.id === id); }
    addRelationship(rel) { this.relationships.push(rel); return rel; }
    removeRelationship(id) { this.relationships = this.relationships.filter(r => r.id !== id); }

    toJSON() {
        return {
            id: this.id, name: this.name, description: this.description,
            classes: this.classes.map(c => c.toJSON()),
            relationships: this.relationships.map(r => r.toJSON()),
            version: this.version, umlVersion: this.umlVersion,
        };
    }

    static fromJSON(data) {
        const model = new UMLModel();
        model.id = data.id || crypto.randomUUID();
        model.name = data.name || 'Nuevo Diagrama';
        model.description = data.description || '';
        model.classes = (data.classes || []).map(c => UMLClassNode.fromJSON(c));
        model.relationships = (data.relationships || []).map(r => UMLRelNode.fromJSON(r));
        model.version = data.version || '1.0.0';
        model.umlVersion = data.umlVersion || '2.5.1';
        return model;
    }
}

class UMLClassNode {
    constructor(name = 'NuevaClase', x = 100, y = 100) {
        this.id = crypto.randomUUID();
        this.name = name;
        this.visibility = '+';
        this.isAbstract = false;
        this.isInterface = false;
        this.stereotype = null;
        this.attributes = [];
        this.operations = [];
        this.position = { x, y };
        this.size = { width: 200, height: 120 };
    }

    addAttribute(attr = null) {
        const a = attr || { id: crypto.randomUUID(), name: 'atributo', type: 'String', visibility: '-', multiplicity: null, defaultValue: null, isStatic: false, isFinal: false, isDerived: false, constraints: [] };
        if (!a.id) a.id = crypto.randomUUID();
        this.attributes.push(a);
        return a;
    }

    addOperation(op = null) {
        const o = op || { id: crypto.randomUUID(), name: 'operacion', parameters: [], returnType: 'void', visibility: '+', isAbstract: false, isStatic: false, isConstructor: false, bodyDescription: null };
        if (!o.id) o.id = crypto.randomUUID();
        this.operations.push(o);
        return o;
    }

    removeAttribute(id) { this.attributes = this.attributes.filter(a => a.id !== id); }
    removeOperation(id) { this.operations = this.operations.filter(o => o.id !== id); }

    computeHeight() {
        const headerH = this.isInterface || this.isAbstract ? 44 : 36;
        const attrH = Math.max(this.attributes.length * 18 + 8, 24);
        const opH = Math.max(this.operations.length * 18 + 8, 24);
        this.size.height = headerH + attrH + opH;
        return this.size.height;
    }

    toJSON() {
        return {
            id: this.id, name: this.name, visibility: this.visibility,
            isAbstract: this.isAbstract, isInterface: this.isInterface,
            stereotype: this.stereotype,
            attributes: this.attributes,
            operations: this.operations,
            position: { ...this.position },
            size: { ...this.size },
        };
    }

    static fromJSON(data) {
        const cls = new UMLClassNode(data.name, data.position?.x || 0, data.position?.y || 0);
        cls.id = data.id || crypto.randomUUID();
        cls.visibility = data.visibility || '+';
        cls.isAbstract = data.isAbstract || false;
        cls.isInterface = data.isInterface || false;
        cls.stereotype = data.stereotype || null;
        cls.attributes = (data.attributes || []).map(a => ({ ...a, id: a.id || crypto.randomUUID() }));
        cls.operations = (data.operations || []).map(o => ({ ...o, id: o.id || crypto.randomUUID() }));
        cls.size = data.size || { width: 200, height: 120 };
        cls.computeHeight();
        return cls;
    }
}

class UMLRelNode {
    constructor(type = 'association', sourceId = '', targetId = '') {
        this.id = crypto.randomUUID();
        this.type = type;
        this.source = { classId: sourceId, role: null, multiplicity: '1', navigable: true };
        this.target = { classId: targetId, role: null, multiplicity: '0..*', navigable: true };
        this.name = null;
        this.label = null;
        this.vertices = [];
    }

    toJSON() {
        return {
            id: this.id, type: this.type,
            source: { ...this.source },
            target: { ...this.target },
            name: this.name, label: this.label,
            vertices: this.vertices.map(v => ({ ...v })),
        };
    }

    static fromJSON(data) {
        const rel = new UMLRelNode(data.type, data.source?.classId, data.target?.classId);
        rel.id = data.id || crypto.randomUUID();
        rel.source = { ...data.source };
        rel.target = { ...data.target };
        rel.name = data.name || null;
        rel.label = data.label || null;
        rel.vertices = (data.vertices || []).map(v => ({ ...v }));
        return rel;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SVG Namespace and Utilities
// ═══════════════════════════════════════════════════════════════════════════

function escapeHTML(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

const SVG_NS = 'http://www.w3.org/2000/svg';

function svgEl(tag, attrs = {}) {
    const el = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
        el.setAttribute(k, v);
    }
    return el;
}

function truncText(text, maxLen = 28) {
    return text.length > maxLen ? text.substring(0, maxLen - 2) + '…' : text;
}

// ═══════════════════════════════════════════════════════════════════════════
// Application State
// ═══════════════════════════════════════════════════════════════════════════

const state = {
    model: new UMLModel(),
    selectedId: null,
    selectedType: null, // 'class' or 'relationship'
    activeTool: null,
    zoom: 1,
    panX: 0,
    panY: 0,
    isPanning: false,
    panStart: { x: 0, y: 0 },
    isDragging: false,
    dragTarget: null,
    dragOffset: { x: 0, y: 0 },
    isDrawingRel: false,
    relSource: null,
    tempLine: null,
    undoStack: [],
    redoStack: [],
    classCounter: 1,
    projectId: new URLSearchParams(location.search).get('project') || localStorage.getItem('last_collaboration_project') || crypto.randomUUID(),
    pendingPhotoFile: null,
    detectedDiagram: null,
    ws: null,
    isRemoteUpdate: false,
};

// ═══════════════════════════════════════════════════════════════════════════
// DOM References
// ═══════════════════════════════════════════════════════════════════════════

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const canvas = $('#canvas');
const diagramLayer = $('#diagramLayer');
const classesLayer = $('#classesLayer');
const relationshipsLayer = $('#relationshipsLayer');
const canvasContainer = $('#canvasContainer');

// ═══════════════════════════════════════════════════════════════════════════
// Undo/Redo
// ═══════════════════════════════════════════════════════════════════════════

function saveUndo() {
    state.undoStack.push(JSON.stringify(state.model.toJSON()));
    if (state.undoStack.length > 50) state.undoStack.shift();
    state.redoStack = [];
}

function undo() {
    if (state.undoStack.length === 0) return;
    state.redoStack.push(JSON.stringify(state.model.toJSON()));
    const prev = JSON.parse(state.undoStack.pop());
    state.model = UMLModel.fromJSON(prev);
    renderAll();
    showToast('Deshacer', 'info');
}

function redo() {
    if (state.redoStack.length === 0) return;
    state.undoStack.push(JSON.stringify(state.model.toJSON()));
    const next = JSON.parse(state.redoStack.pop());
    state.model = UMLModel.fromJSON(next);
    renderAll();
    showToast('Rehacer', 'info');
}

// ═══════════════════════════════════════════════════════════════════════════
// Rendering — Classes
// ═══════════════════════════════════════════════════════════════════════════

function renderClassNode(cls) {
    cls.computeHeight();
    const { x, y } = cls.position;
    const { width, height } = cls.size;

    const g = svgEl('g', {
        class: `uml-class${state.selectedId === cls.id && state.selectedType === 'class' ? ' class-selected' : ''}`,
        'data-id': cls.id,
        transform: `translate(${x}, ${y})`,
    });

    // Add gradient definition for class header
    const defs = svgEl('defs');
    const grad = svgEl('linearGradient', { id: `hg-${cls.id}`, x1: '0', y1: '0', x2: '1', y2: '1' });
    const stop1 = svgEl('stop', { offset: '0%', 'stop-color': cls.isInterface ? 'rgba(124,58,237,0.2)' : cls.isAbstract ? 'rgba(99,102,241,0.2)' : 'rgba(99,102,241,0.15)' });
    const stop2 = svgEl('stop', { offset: '100%', 'stop-color': cls.isInterface ? 'rgba(168,85,247,0.08)' : cls.isAbstract ? 'rgba(168,85,247,0.08)' : 'rgba(168,85,247,0.05)' });
    grad.appendChild(stop1);
    grad.appendChild(stop2);
    defs.appendChild(grad);
    g.appendChild(defs);

    // Border rectangle
    const borderStyle = cls.isInterface ? 'stroke-dasharray: 6 3;' : '';
    const border = svgEl('rect', {
        class: 'class-border',
        width, height, rx: '6',
        style: borderStyle,
    });
    g.appendChild(border);

    // Header background
    const headerH = cls.isInterface || cls.isAbstract || cls.stereotype ? 44 : 36;
    const headerBg = svgEl('rect', {
        x: '1', y: '1', width: width - 2, height: headerH - 1, rx: '5',
        fill: `url(#hg-${cls.id})`,
    });
    g.appendChild(headerBg);

    // Stereotype or type label
    let nameY = headerH / 2;
    if (cls.isInterface || cls.isAbstract || cls.stereotype) {
        const stereoText = cls.isInterface ? '«interface»' : cls.isAbstract ? '«abstract»' : `«${cls.stereotype}»`;
        const stereo = svgEl('text', {
            class: 'class-stereotype-text',
            x: width / 2, y: 14,
        });
        stereo.textContent = stereoText;
        g.appendChild(stereo);
        nameY = 32;
    }

    // Class name
    const nameText = svgEl('text', {
        class: 'class-name-text',
        x: width / 2, y: nameY,
        style: cls.isAbstract ? 'font-style: italic;' : '',
    });
    nameText.textContent = truncText(cls.name, 24);
    g.appendChild(nameText);

    // Divider 1 (after header)
    const div1 = svgEl('line', {
        class: 'class-divider',
        x1: 0, y1: headerH, x2: width, y2: headerH,
    });
    g.appendChild(div1);

    // Attributes
    let yPos = headerH + 4;
    if (cls.attributes.length === 0) {
        const emptyAttr = svgEl('text', {
            class: 'class-attr-text', x: 8, y: yPos + 12,
            opacity: '0.3',
        });
        emptyAttr.textContent = '(sin atributos)';
        g.appendChild(emptyAttr);
        yPos += 20;
    } else {
        for (const attr of cls.attributes) {
            const attrText = svgEl('text', {
                class: 'class-attr-text', x: 8, y: yPos + 13,
            });
            const label = `${attr.visibility || '-'} ${attr.name}: ${attr.type}`;
            attrText.textContent = truncText(label, 30);
            g.appendChild(attrText);
            yPos += 18;
        }
    }
    yPos += 4;

    // Divider 2 (after attributes)
    const div2 = svgEl('line', {
        class: 'class-divider',
        x1: 0, y1: yPos, x2: width, y2: yPos,
    });
    g.appendChild(div2);
    yPos += 4;

    // Operations
    if (cls.operations.length === 0) {
        const emptyOp = svgEl('text', {
            class: 'class-op-text', x: 8, y: yPos + 12,
            opacity: '0.3',
        });
        emptyOp.textContent = '(sin operaciones)';
        g.appendChild(emptyOp);
    } else {
        for (const op of cls.operations) {
            const opText = svgEl('text', {
                class: 'class-op-text', x: 8, y: yPos + 13,
            });
            const params = (op.parameters || []).map(p => `${p.name}: ${p.type}`).join(', ');
            const retType = op.returnType && op.returnType !== 'void' ? `: ${op.returnType}` : '';
            const label = `${op.visibility || '+'} ${op.name}(${params})${retType}`;
            opText.textContent = truncText(label, 30);
            g.appendChild(opText);
            yPos += 18;
        }
    }

    // Connection points (shown on hover)
    const connPoints = [
        { cx: width / 2, cy: 0 },      // top
        { cx: width, cy: height / 2 },  // right
        { cx: width / 2, cy: height },  // bottom
        { cx: 0, cy: height / 2 },      // left
    ];
    for (const p of connPoints) {
        const cp = svgEl('circle', {
            class: 'connection-point',
            cx: p.cx, cy: p.cy, r: '5',
            'data-class-id': cls.id,
        });
        g.appendChild(cp);
    }

    // Resize handle
    const resize = svgEl('rect', {
        class: 'class-resize-handle',
        x: width - 12, y: height - 12, width: 12, height: 12,
        rx: '2',
    });
    g.appendChild(resize);

    return g;
}

// ═══════════════════════════════════════════════════════════════════════════
// Rendering — Relationships
// ═══════════════════════════════════════════════════════════════════════════

function getClassCenter(cls) {
    return { x: cls.position.x + cls.size.width / 2, y: cls.position.y + cls.size.height / 2 };
}

function getConnectionPoint(sourceCls, targetCls) {
    const sc = getClassCenter(sourceCls);
    const tc = getClassCenter(targetCls);
    const dx = tc.x - sc.x;
    const dy = tc.y - sc.y;

    function edgePoint(cls, cx, cy, tox, toy) {
        const w2 = cls.size.width / 2;
        const h2 = cls.size.height / 2;
        const ddx = tox - cx;
        const ddy = toy - cy;
        if (ddx === 0 && ddy === 0) return { x: cx, y: cy };
        const sx = ddx !== 0 ? w2 / Math.abs(ddx) : Infinity;
        const sy = ddy !== 0 ? h2 / Math.abs(ddy) : Infinity;
        const s = Math.min(sx, sy);
        return { x: cx + ddx * s, y: cy + ddy * s };
    }

    const sp = edgePoint(sourceCls, sc.x, sc.y, tc.x, tc.y);
    const tp = edgePoint(targetCls, tc.x, tc.y, sc.x, sc.y);
    return { source: sp, target: tp };
}

function renderRelationship(rel) {
    const sourceCls = state.model.getClass(rel.source.classId);
    const targetCls = state.model.getClass(rel.target.classId);
    if (!sourceCls || !targetCls) return null;

    const { source: sp, target: tp } = getConnectionPoint(sourceCls, targetCls);

    const g = svgEl('g', {
        class: `uml-relationship${state.selectedId === rel.id && state.selectedType === 'relationship' ? ' rel-selected' : ''}`,
        'data-id': rel.id,
    });

    // Line style based on relationship type
    let lineClass = 'rel-line';
    let markerStart = '';
    let markerEnd = '';

    switch (rel.type) {
        case 'association':
            markerEnd = 'url(#arrowOpen)';
            break;
        case 'aggregation':
            markerStart = 'url(#diamondEmpty)';
            break;
        case 'composition':
            markerStart = 'url(#diamondFull)';
            break;
        case 'generalization':
            markerEnd = 'url(#arrowClosed)';
            break;
        case 'realization':
            markerEnd = 'url(#arrowClosed)';
            lineClass += ' rel-dashed';
            break;
        case 'dependency':
            markerEnd = 'url(#arrowOpen)';
            lineClass += ' rel-dashed';
            break;
    }

    // Draw the line
    const line = svgEl('line', {
        class: lineClass,
        x1: sp.x, y1: sp.y,
        x2: tp.x, y2: tp.y,
    });
    if (markerStart) line.setAttribute('marker-start', markerStart);
    if (markerEnd) line.setAttribute('marker-end', markerEnd);
    g.appendChild(line);

    // Invisible thick line for easier click targeting
    const hitLine = svgEl('line', {
        x1: sp.x, y1: sp.y, x2: tp.x, y2: tp.y,
        stroke: 'transparent', 'stroke-width': '12',
    });
    g.appendChild(hitLine);

    // Multiplicities
    const midX = (sp.x + tp.x) / 2;
    const midY = (sp.y + tp.y) / 2;
    const angle = Math.atan2(tp.y - sp.y, tp.x - sp.x);
    const offsetX = Math.sin(angle) * 14;
    const offsetY = -Math.cos(angle) * 14;

    if (rel.source.multiplicity && rel.type !== 'generalization' && rel.type !== 'realization') {
        const smult = svgEl('text', {
            class: 'rel-multiplicity',
            x: sp.x + (tp.x - sp.x) * 0.15 + offsetX,
            y: sp.y + (tp.y - sp.y) * 0.15 + offsetY,
        });
        smult.textContent = rel.source.multiplicity;
        g.appendChild(smult);
    }

    if (rel.target.multiplicity && rel.type !== 'generalization' && rel.type !== 'realization') {
        const tmult = svgEl('text', {
            class: 'rel-multiplicity',
            x: sp.x + (tp.x - sp.x) * 0.85 + offsetX,
            y: sp.y + (tp.y - sp.y) * 0.85 + offsetY,
        });
        tmult.textContent = rel.target.multiplicity;
        g.appendChild(tmult);
    }

    // Relationship name/label
    if (rel.name) {
        const label = svgEl('text', {
            class: 'rel-label',
            x: midX + offsetX * 1.5, y: midY + offsetY * 1.5,
        });
        label.textContent = rel.name;
        g.appendChild(label);
    }

    return g;
}

// ═══════════════════════════════════════════════════════════════════════════
// Render All
// ═══════════════════════════════════════════════════════════════════════════

function renderAll() {
    // Clear layers
    classesLayer.innerHTML = '';
    relationshipsLayer.innerHTML = '';

    // Render relationships first (behind classes)
    for (const rel of state.model.relationships) {
        const el = renderRelationship(rel);
        if (el) relationshipsLayer.appendChild(el);
    }

    // Render classes
    for (const cls of state.model.classes) {
        const el = renderClassNode(cls);
        classesLayer.appendChild(el);
    }

    // Update transform
    diagramLayer.setAttribute('transform', `translate(${state.panX}, ${state.panY}) scale(${state.zoom})`);

    // Show/hide overlay
    const overlay = $('#canvasOverlay');
    if (state.model.classes.length === 0) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }

    // Update properties panel
    updatePropertiesPanel();

    // Debounced sync for real-time collaboration on local changes
    if (!state.isRemoteUpdate && typeof debouncedBroadcast === 'function') {
        debouncedBroadcast(300);
    }
}

let _broadcastTimer = null;
function debouncedBroadcast(delay = 300) {
    clearTimeout(_broadcastTimer);
    _broadcastTimer = setTimeout(() => {
        if (typeof broadcastChange === 'function') broadcastChange();
    }, delay);
}

// ═══════════════════════════════════════════════════════════════════════════
// Properties Panel
// ═══════════════════════════════════════════════════════════════════════════

function updatePropertiesPanel() {
    const noSel = $('#noSelection');
    const classProp = $('#classProperties');
    const relProp = $('#relationshipProperties');

    noSel.classList.add('hidden');
    classProp.classList.add('hidden');
    relProp.classList.add('hidden');

    if (!state.selectedId) {
        noSel.classList.remove('hidden');
        return;
    }

    if (state.selectedType === 'class') {
        const cls = state.model.getClass(state.selectedId);
        if (!cls) { noSel.classList.remove('hidden'); return; }

        classProp.classList.remove('hidden');
        $('#propClassName').value = cls.name;
        $('#propClassType').value = cls.isInterface ? 'interface' : cls.isAbstract ? 'abstract' : 'class';
        $('#propClassVisibility').value = cls.visibility;

        renderAttributesList(cls);
        renderOperationsList(cls);
    } else if (state.selectedType === 'relationship') {
        const rel = state.model.relationships.find(r => r.id === state.selectedId);
        if (!rel) { noSel.classList.remove('hidden'); return; }

        relProp.classList.remove('hidden');
        $('#propRelType').value = rel.type;
        $('#propRelName').value = rel.name || '';
        $('#propRelSourceRole').value = rel.source.role || '';
        $('#propRelSourceMult').value = rel.source.multiplicity || '1';
        $('#propRelTargetRole').value = rel.target.role || '';
        $('#propRelTargetMult').value = rel.target.multiplicity || '0..*';
    }
}

function renderAttributesList(cls) {
    const list = $('#attributesList');
    list.innerHTML = '';
    for (const attr of cls.attributes) {
        const row = document.createElement('div');
        row.className = 'item-row';
        row.innerHTML = `
            <select class="item-visibility" data-attr-id="${escapeHTML(attr.id)}" data-field="visibility">
                <option value="+" ${attr.visibility === '+' ? 'selected' : ''}>+</option>
                <option value="-" ${attr.visibility === '-' ? 'selected' : ''}>-</option>
                <option value="#" ${attr.visibility === '#' ? 'selected' : ''}>#</option>
                <option value="~" ${attr.visibility === '~' ? 'selected' : ''}>~</option>
            </select>
            <input class="item-name" value="${escapeHTML(attr.name)}" data-attr-id="${escapeHTML(attr.id)}" data-field="name" placeholder="nombre" spellcheck="false">
            <input class="item-type" value="${escapeHTML(attr.type)}" data-attr-id="${escapeHTML(attr.id)}" data-field="type" placeholder="tipo" spellcheck="false">
            <button class="item-delete" data-attr-id="${escapeHTML(attr.id)}" title="Eliminar atributo">×</button>
        `;
        list.appendChild(row);
    }

    // Bind events
    list.querySelectorAll('.item-name, .item-type').forEach(input => {
        input.addEventListener('change', (e) => {
            saveUndo();
            const attrId = e.target.dataset.attrId;
            const field = e.target.dataset.field;
            const attr = cls.attributes.find(a => a.id === attrId);
            if (attr) { attr[field] = e.target.value; renderAll(); }
        });
    });
    list.querySelectorAll('.item-visibility').forEach(select => {
        select.addEventListener('change', (e) => {
            saveUndo();
            const attrId = e.target.dataset.attrId;
            const attr = cls.attributes.find(a => a.id === attrId);
            if (attr) { attr.visibility = e.target.value; renderAll(); }
        });
    });
    list.querySelectorAll('.item-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            saveUndo();
            cls.removeAttribute(e.target.dataset.attrId);
            renderAll();
        });
    });
}

function renderOperationsList(cls) {
    const list = $('#operationsList');
    list.innerHTML = '';
    for (const op of cls.operations) {
        const row = document.createElement('div');
        row.className = 'item-row';
        row.innerHTML = `
            <select class="item-visibility" data-op-id="${escapeHTML(op.id)}" data-field="visibility">
                <option value="+" ${op.visibility === '+' ? 'selected' : ''}>+</option>
                <option value="-" ${op.visibility === '-' ? 'selected' : ''}>-</option>
                <option value="#" ${op.visibility === '#' ? 'selected' : ''}>#</option>
                <option value="~" ${op.visibility === '~' ? 'selected' : ''}>~</option>
            </select>
            <input class="item-name" value="${escapeHTML(op.name)}" data-op-id="${escapeHTML(op.id)}" data-field="name" placeholder="nombre" spellcheck="false">
            <input class="item-type" value="${escapeHTML(op.returnType || 'void')}" data-op-id="${escapeHTML(op.id)}" data-field="returnType" placeholder="retorno" spellcheck="false">
            <button class="item-delete" data-op-id="${escapeHTML(op.id)}" title="Eliminar operación">×</button>
        `;
        list.appendChild(row);
    }

    list.querySelectorAll('.item-name, .item-type').forEach(input => {
        input.addEventListener('change', (e) => {
            saveUndo();
            const opId = e.target.dataset.opId;
            const field = e.target.dataset.field;
            const op = cls.operations.find(o => o.id === opId);
            if (op) { op[field] = e.target.value; renderAll(); }
        });
    });
    list.querySelectorAll('.item-visibility').forEach(select => {
        select.addEventListener('change', (e) => {
            saveUndo();
            const opId = e.target.dataset.opId;
            const op = cls.operations.find(o => o.id === opId);
            if (op) { op.visibility = e.target.value; renderAll(); }
        });
    });
    list.querySelectorAll('.item-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            saveUndo();
            cls.removeOperation(e.target.dataset.opId);
            renderAll();
        });
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// Canvas Interaction
// ═══════════════════════════════════════════════════════════════════════════

function getSVGPoint(e) {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - state.panX) / state.zoom;
    const y = (e.clientY - rect.top - state.panY) / state.zoom;
    return { x, y };
}

// Mouse down on canvas
canvasContainer.addEventListener('mousedown', (e) => {
    if (e.button === 1 || (e.button === 0 && e.altKey)) {
        // Middle click or Alt+click: start panning
        state.isPanning = true;
        state.panStart = { x: e.clientX - state.panX, y: e.clientY - state.panY };
        canvasContainer.style.cursor = 'grabbing';
        e.preventDefault();
        return;
    }

    const target = e.target;
    const classGroup = target.closest('.uml-class');
    const relGroup = target.closest('.uml-relationship');
    const connPoint = target.closest('.connection-point');

    if (connPoint && state.activeTool && ['association', 'aggregation', 'composition', 'generalization', 'realization', 'dependency'].includes(state.activeTool)) {
        // Start drawing a relationship from connection point
        const classId = connPoint.dataset.classId;
        state.isDrawingRel = true;
        state.relSource = classId;
        const point = getSVGPoint(e);
        state.tempLine = svgEl('line', {
            class: 'temp-line',
            x1: point.x, y1: point.y, x2: point.x, y2: point.y,
        });
        diagramLayer.appendChild(state.tempLine);
        e.preventDefault();
        return;
    }

    if (classGroup) {
        const classId = classGroup.dataset.id;

        if (state.activeTool && ['association', 'aggregation', 'composition', 'generalization', 'realization', 'dependency'].includes(state.activeTool)) {
            // Start drawing relationship
            state.isDrawingRel = true;
            state.relSource = classId;
            const cls = state.model.getClass(classId);
            const center = getClassCenter(cls);
            state.tempLine = svgEl('line', {
                class: 'temp-line',
                x1: center.x, y1: center.y, x2: center.x, y2: center.y,
            });
            diagramLayer.appendChild(state.tempLine);
        } else {
            // Select and start dragging
            saveUndo();
            state.selectedId = classId;
            state.selectedType = 'class';
            state.isDragging = true;
            state.dragTarget = classId;
            const cls = state.model.getClass(classId);
            const point = getSVGPoint(e);
            state.dragOffset = { x: point.x - cls.position.x, y: point.y - cls.position.y };
            renderAll();
        }
        e.preventDefault();
        return;
    }

    if (relGroup) {
        state.selectedId = relGroup.dataset.id;
        state.selectedType = 'relationship';
        renderAll();
        e.preventDefault();
        return;
    }

    // Click on empty canvas
    if (state.activeTool === 'class' || state.activeTool === 'interface' || state.activeTool === 'abstract') {
        // Create new class
        saveUndo();
        const point = getSVGPoint(e);
        const cls = new UMLClassNode(`Clase${state.classCounter++}`, point.x - 100, point.y - 60);
        if (state.activeTool === 'interface') {
            cls.isInterface = true;
            cls.name = `IInterfaz${state.classCounter - 1}`;
        } else if (state.activeTool === 'abstract') {
            cls.isAbstract = true;
            cls.name = `AbstractClase${state.classCounter - 1}`;
        }
        state.model.addClass(cls);
        state.selectedId = cls.id;
        state.selectedType = 'class';
        // Deactivate tool after creation
        setActiveTool(null);
        renderAll();
        showToast(`Clase "${cls.name}" creada`, 'success');
        return;
    }

    // Deselect
    if (!state.isPanning) {
        state.selectedId = null;
        state.selectedType = null;
        renderAll();
    }

    // Start panning with left button on empty space
    if (e.button === 0 && !classGroup && !relGroup) {
        state.isPanning = true;
        state.panStart = { x: e.clientX - state.panX, y: e.clientY - state.panY };
        canvasContainer.style.cursor = 'grabbing';
    }
});

// Mouse move
canvasContainer.addEventListener('mousemove', (e) => {
    if (state.isPanning) {
        state.panX = e.clientX - state.panStart.x;
        state.panY = e.clientY - state.panStart.y;
        diagramLayer.setAttribute('transform', `translate(${state.panX}, ${state.panY}) scale(${state.zoom})`);
        return;
    }

    if (state.isDragging && state.dragTarget) {
        const cls = state.model.getClass(state.dragTarget);
        if (cls) {
            const point = getSVGPoint(e);
            cls.position.x = Math.round((point.x - state.dragOffset.x) / 10) * 10;
            cls.position.y = Math.round((point.y - state.dragOffset.y) / 10) * 10;
            renderAll();
        }
        return;
    }

    if (state.isDrawingRel && state.tempLine) {
        const point = getSVGPoint(e);
        state.tempLine.setAttribute('x2', point.x);
        state.tempLine.setAttribute('y2', point.y);
    }
});

// Mouse up
canvasContainer.addEventListener('mouseup', (e) => {
    if (state.isPanning) {
        state.isPanning = false;
        canvasContainer.style.cursor = '';
    }

    if (state.isDragging) {
        state.isDragging = false;
        state.dragTarget = null;
        if (typeof debouncedBroadcast === 'function') debouncedBroadcast(50);
    }

    if (state.isDrawingRel) {
        const target = e.target.closest('.uml-class');
        if (target && target.dataset.id !== state.relSource) {
            saveUndo();
            const rel = new UMLRelNode(state.activeTool, state.relSource, target.dataset.id);
            state.model.addRelationship(rel);
            state.selectedId = rel.id;
            state.selectedType = 'relationship';
            showToast('Relación creada', 'success');
        }

        if (state.tempLine) {
            state.tempLine.remove();
            state.tempLine = null;
        }
        state.isDrawingRel = false;
        state.relSource = null;
        setActiveTool(null);
        renderAll();
    }
});

// Mouse wheel for zoom
canvasContainer.addEventListener('wheel', (e) => {
    if(document.body.classList.contains('mobile-editor') && !e.ctrlKey && !e.metaKey)return;
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.05 : 0.05;
    const newZoom = Math.max(0.2, Math.min(3, state.zoom + delta));

    // Zoom toward cursor position
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const ratio = newZoom / state.zoom;
    state.panX = mx - (mx - state.panX) * ratio;
    state.panY = my - (my - state.panY) * ratio;
    state.zoom = newZoom;

    diagramLayer.setAttribute('transform', `translate(${state.panX}, ${state.panY}) scale(${state.zoom})`);
    $('#zoomLevel').textContent = `${Math.round(state.zoom * 100)}%`;
}, { passive: false });

// Double-click to edit class name
canvasContainer.addEventListener('dblclick', (e) => {
    const classGroup = e.target.closest('.uml-class');
    if (classGroup) {
        const classId = classGroup.dataset.id;
        state.selectedId = classId;
        state.selectedType = 'class';
        renderAll();
        // Focus the name input
        setTimeout(() => {
            const nameInput = $('#propClassName');
            if (nameInput) { nameInput.focus(); nameInput.select(); }
        }, 50);
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// Tool Selection
// ═══════════════════════════════════════════════════════════════════════════

function setActiveTool(tool) {
    state.activeTool = tool;
    $$('.tool-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tool === tool);
    });
    // Change cursor
    if (tool === 'class' || tool === 'interface' || tool === 'abstract') {
        canvasContainer.style.cursor = 'crosshair';
    } else if (tool && ['association', 'aggregation', 'composition', 'generalization', 'realization', 'dependency'].includes(tool)) {
        canvasContainer.style.cursor = 'crosshair';
    } else {
        canvasContainer.style.cursor = '';
    }
}

$$('.tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tool = btn.dataset.tool;
        setActiveTool(state.activeTool === tool ? null : tool);
    });
});

// ═══════════════════════════════════════════════════════════════════════════
// Property Panel Event Bindings
// ═══════════════════════════════════════════════════════════════════════════

// Class properties
$('#propClassName').addEventListener('input', (e) => {
    const cls = state.model.getClass(state.selectedId);
    if (cls) { cls.name = e.target.value; renderAll(); }
});

$('#propClassType').addEventListener('change', (e) => {
    saveUndo();
    const cls = state.model.getClass(state.selectedId);
    if (cls) {
        cls.isAbstract = e.target.value === 'abstract';
        cls.isInterface = e.target.value === 'interface';
        renderAll();
    }
});

$('#propClassVisibility').addEventListener('change', (e) => {
    saveUndo();
    const cls = state.model.getClass(state.selectedId);
    if (cls) { cls.visibility = e.target.value; renderAll(); }
});

$('#btnAddAttribute').addEventListener('click', () => {
    const cls = state.model.getClass(state.selectedId);
    if (cls) {
        saveUndo();
        cls.addAttribute();
        renderAll();
    }
});

$('#btnAddOperation').addEventListener('click', () => {
    const cls = state.model.getClass(state.selectedId);
    if (cls) {
        saveUndo();
        cls.addOperation();
        renderAll();
    }
});

// Relationship properties
$('#propRelType').addEventListener('change', (e) => {
    saveUndo();
    const rel = state.model.relationships.find(r => r.id === state.selectedId);
    if (rel) { rel.type = e.target.value; renderAll(); }
});

$('#propRelName').addEventListener('input', (e) => {
    const rel = state.model.relationships.find(r => r.id === state.selectedId);
    if (rel) { rel.name = e.target.value || null; renderAll(); }
});

$('#propRelSourceRole').addEventListener('input', (e) => {
    const rel = state.model.relationships.find(r => r.id === state.selectedId);
    if (rel) { rel.source.role = e.target.value || null; }
});

$('#propRelSourceMult').addEventListener('change', (e) => {
    saveUndo();
    const rel = state.model.relationships.find(r => r.id === state.selectedId);
    if (rel) { rel.source.multiplicity = e.target.value; renderAll(); }
});

$('#propRelTargetRole').addEventListener('input', (e) => {
    const rel = state.model.relationships.find(r => r.id === state.selectedId);
    if (rel) { rel.target.role = e.target.value || null; }
});

$('#propRelTargetMult').addEventListener('change', (e) => {
    saveUndo();
    const rel = state.model.relationships.find(r => r.id === state.selectedId);
    if (rel) { rel.target.multiplicity = e.target.value; renderAll(); }
});

// ═══════════════════════════════════════════════════════════════════════════
// Action Buttons
// ═══════════════════════════════════════════════════════════════════════════

$('#btnUndo').addEventListener('click', undo);
$('#btnRedo').addEventListener('click', redo);

$('#btnDelete').addEventListener('click', () => {
    if (!state.selectedId) return;
    saveUndo();
    if (state.selectedType === 'class') {
        const cls = state.model.getClass(state.selectedId);
        state.model.removeClass(state.selectedId);
        showToast(`Clase "${cls?.name}" eliminada`, 'info');
    } else if (state.selectedType === 'relationship') {
        state.model.removeRelationship(state.selectedId);
        showToast('Relación eliminada', 'info');
    }
    state.selectedId = null;
    state.selectedType = null;
    renderAll();
});

$('#btnZoomIn').addEventListener('click', () => {
    state.zoom = Math.min(3, state.zoom + 0.1);
    diagramLayer.setAttribute('transform', `translate(${state.panX}, ${state.panY}) scale(${state.zoom})`);
    $('#zoomLevel').textContent = `${Math.round(state.zoom * 100)}%`;
});

$('#btnZoomOut').addEventListener('click', () => {
    state.zoom = Math.max(0.2, state.zoom - 0.1);
    diagramLayer.setAttribute('transform', `translate(${state.panX}, ${state.panY}) scale(${state.zoom})`);
    $('#zoomLevel').textContent = `${Math.round(state.zoom * 100)}%`;
});

$('#btnZoomFit').addEventListener('click', () => {
    if (state.model.classes.length === 0) return;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const cls of state.model.classes) {
        minX = Math.min(minX, cls.position.x);
        minY = Math.min(minY, cls.position.y);
        maxX = Math.max(maxX, cls.position.x + cls.size.width);
        maxY = Math.max(maxY, cls.position.y + cls.size.height);
    }
    const rect = canvasContainer.getBoundingClientRect();
    const pw = rect.width - 80;
    const ph = rect.height - 80;
    const dw = maxX - minX;
    const dh = maxY - minY;
    state.zoom = Math.min(pw / dw, ph / dh, 1.5);
    state.panX = (rect.width - dw * state.zoom) / 2 - minX * state.zoom;
    state.panY = (rect.height - dh * state.zoom) / 2 - minY * state.zoom;
    diagramLayer.setAttribute('transform', `translate(${state.panX}, ${state.panY}) scale(${state.zoom})`);
    $('#zoomLevel').textContent = `${Math.round(state.zoom * 100)}%`;
});

// ═══════════════════════════════════════════════════════════════════════════
// Keyboard Shortcuts
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener('keydown', (e) => {
    // Don't intercept when typing in inputs
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

    if (e.ctrlKey && e.key === 'z') { e.preventDefault(); undo(); }
    if (e.ctrlKey && e.key === 'y') { e.preventDefault(); redo(); }
    if (e.ctrlKey && e.key === 's') { e.preventDefault(); saveProject(); }
    if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); $('#btnDelete').click(); }
    if (e.key === 'Escape') { setActiveTool(null); state.selectedId = null; state.selectedType = null; renderAll(); }
    if (e.key === 'c') { setActiveTool('class'); }
    if (e.key === 'i') { setActiveTool('interface'); }
});

// ═══════════════════════════════════════════════════════════════════════════
// Project Management
// ═══════════════════════════════════════════════════════════════════════════

$('#projectName').addEventListener('change', (e) => {
    state.model.name = e.target.value;
});

async function saveProject() {
    try {
        state.model.name = $('#projectName').value;
        const response = await fetch('/api/projects/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                projectId: state.model.id,
                name: state.model.name,
                diagram: state.model.toJSON(),
            }),
        });
        const data = await response.json();
        showToast('Proyecto guardado', 'success');

        // Also save to localStorage for offline
        localStorage.setItem(`project_${state.model.id}`, JSON.stringify(state.model.toJSON()));
    } catch (err) {
        // Offline fallback: save to localStorage
        localStorage.setItem(`project_${state.model.id}`, JSON.stringify(state.model.toJSON()));
        showToast('Guardado localmente (sin conexión)', 'warning');
    }
}

$('#btnSave').addEventListener('click', saveProject);

// ═══════════════════════════════════════════════════════════════════════════
// Validation
// ═══════════════════════════════════════════════════════════════════════════

$('#btnValidate').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.model.toJSON()),
        });
        const result = await response.json();
        showValidation(result);
    } catch (err) {
        showToast('Error al validar. ¿El servidor está corriendo?', 'error');
    }
});

function showValidation(result) {
    const panel = $('#validationPanel');
    const body = $('#validationResults');
    panel.classList.remove('hidden');

    if (result.isValid && result.issues.length === 0) {
        body.innerHTML = '<div class="val-issue info"><span class="val-icon">✓</span> El diagrama es válido según UML 2.5+</div>';
        showToast('Diagrama válido ✓', 'success');
        return;
    }

    let html = '';
    const icons = { error: '✕', warning: '⚠', info: 'ℹ' };
    for (const issue of result.issues) {
        html += `<div class="val-issue ${escapeHTML(issue.severity)}">
            <span class="val-icon">${icons[issue.severity]}</span>
            <span>${escapeHTML(issue.message)}</span>
        </div>`;
    }
    body.innerHTML = html;

    if (!result.isValid) {
        showToast(`${result.errorCount} error(es), ${result.warningCount} advertencia(s)`, 'warning');
    } else {
        showToast(`Válido con ${result.warningCount} advertencia(s)`, 'info');
    }
}

$('#btnCloseValidation').addEventListener('click', () => {
    $('#validationPanel').classList.add('hidden');
});

// ═══════════════════════════════════════════════════════════════════════════
// Code Generation
// ═══════════════════════════════════════════════════════════════════════════

$('#btnGenerateCode').addEventListener('click', showGeneratePanel);
$('#tabGenerate').addEventListener('click', showGeneratePanel);

function showGeneratePanel() {
    const panel = $('#generatePanel');
    panel.classList.remove('hidden');

    // Update stats
    let totalAttrs = 0, totalOps = 0;
    for (const cls of state.model.classes) {
        totalAttrs += cls.attributes.length;
        totalOps += cls.operations.length;
    }
    $('#statClasses').textContent = state.model.classes.length;
    $('#statRelationships').textContent = state.model.relationships.length;
    $('#statAttributes').textContent = totalAttrs;
    $('#statOperations').textContent = totalOps;
}

$('#btnCloseGenerate').addEventListener('click', () => {
    $('#generatePanel').classList.add('hidden');
});

$('#btnStartGeneration').addEventListener('click', async () => {
    const progressEl = $('#genProgress');
    const logEl = $('#progressLog');
    const fillEl = $('#progressFill');
    const resultsEl = $('#genResults');

    progressEl.classList.remove('hidden');
    resultsEl.classList.add('hidden');
    logEl.innerHTML = '';
    fillEl.style.width = '0%';

    function log(msg, type = 'info') {
        const line=document.createElement("div"); line.className=`log-${type}`; line.textContent=`→ ${msg}`; logEl.append(line);
        logEl.scrollTop = logEl.scrollHeight;
    }

    try {
        log('Generando archivos en el servidor…');
        fillEl.style.width = '0%';
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                diagram: state.model.toJSON(),
                basePackage: $('#genPackage').value,
                generateFlutter: $('#genFlutter').checked,
                generatePostman: $('#genPostman').checked,
            }),
        });

        const result = await response.json();

        if (response.ok && !result.errors?.length) {
            fillEl.style.width = '100%';
            log(`Generación completada: ${result.files?.length || 0} archivos creados`, 'success');

            if (result.warnings) {
                result.warnings.forEach(w => log(w, 'warning'));
            }
            if (result.errors && result.errors.length > 0) {
                result.errors.forEach(e => log(e, 'error'));
            }

            resultsEl.classList.remove('hidden');
            resultsEl.innerHTML = `
                <strong>✓ Aplicación generada exitosamente</strong><br>
                <span style="font-size: 12px; color: var(--text-secondary);">
                    Directorio: ${escapeHTML(result.projectDir)}<br>
                    Clases: ${result.classCount} | Relaciones: ${result.relationshipCount}
                </span>
            `;
            showToast('¡Código generado exitosamente!', 'success');
        } else {
            fillEl.style.width = '100%';
            fillEl.style.background = 'var(--error)';
            log(`Error: ${result.errors?.join('; ') || result.error || result.detail || 'Error desconocido'}`, 'error');
            if (result.validation) {
                result.validation.issues.forEach(i => log(`${i.severity}: ${i.message}`, i.severity));
            }
        }
    } catch (err) {
        fillEl.style.width = '100%';
        fillEl.style.background = 'var(--error)';
        log(`Error de conexión: ${err.message}. ¿El servidor está corriendo?`, 'error');
    }
});

$('#btnDownloadZip').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/generate/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                diagram: state.model.toJSON(),
                basePackage: $('#genPackage').value,
                generateFlutter: $('#genFlutter').checked,
                generatePostman: $('#genPostman').checked,
            }),
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${state.model.name.replace(/ /g, '_')}_generated.zip`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('Descarga iniciada', 'success');
        } else {
            showToast('Error al generar ZIP', 'error');
        }
    } catch (err) {
        showToast('Error de conexión', 'error');
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// Import / Export
// ═══════════════════════════════════════════════════════════════════════════

function downloadFile(filename, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

$('#btnExport').addEventListener('click', () => {
    $('#exportModal').classList.remove('hidden');
});

$('#btnCloseExport').addEventListener('click', () => {
    $('#exportModal').classList.add('hidden');
});

$('#btnExportJSON').addEventListener('click', () => {
    const json = JSON.stringify(state.model.toJSON(), null, 2);
    downloadFile(`${state.model.name.replace(/ /g, '_')}.json`, json, 'application/json');
    $('#exportModal').classList.add('hidden');
    showToast('Diagrama exportado en formato JSON (nativo)', 'success');
});

$('#btnExportXMI').addEventListener('click', async () => {
    try {
        showToast('Generando XMI 2.1...', 'info');
        const res = await fetch('/api/export/xmi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ diagram: state.model.toJSON() }),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        downloadFile(`${state.model.name.replace(/ /g, '_')}.xmi`, data.xmi, 'application/xml');
        $('#exportModal').classList.add('hidden');
        showToast('Exportado a XMI 2.1 (Enterprise Architect / StarUML)', 'success');
    } catch (err) {
        showToast(`Error exportando XMI: ${err.message}`, 'error');
    }
});

$('#btnExportMDJ').addEventListener('click', async () => {
    try {
        showToast('Generando StarUML MDJ...', 'info');
        const res = await fetch('/api/export/mdj', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ diagram: state.model.toJSON() }),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        downloadFile(`${state.model.name.replace(/ /g, '_')}.mdj`, JSON.stringify(data, null, 2), 'application/json');
        $('#exportModal').classList.add('hidden');
        showToast('Exportado a StarUML (.mdj)', 'success');
    } catch (err) {
        showToast(`Error exportando MDJ: ${err.message}`, 'error');
    }
});

function generateStandaloneSVG() {
    if (state.model.classes.length === 0) {
        return '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"><rect width="100%" height="100%" fill="#12121a"/><text x="200" y="100" fill="#a0a0b8" text-anchor="middle" font-family="sans-serif">Diagrama vacío</text></svg>';
    }

    // Calculate bounding box of all classes
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const cls of state.model.classes) {
        minX = Math.min(minX, cls.position.x);
        minY = Math.min(minY, cls.position.y);
        maxX = Math.max(maxX, cls.position.x + cls.size.width);
        maxY = Math.max(maxY, cls.position.y + cls.size.height);
    }

    const pad = 60;
    const vbX = Math.floor(Math.max(0, minX - pad));
    const vbY = Math.floor(Math.max(0, minY - pad));
    const vbW = Math.ceil((maxX - vbX) + pad);
    const vbH = Math.ceil((maxY - vbY) + pad);

    // Clone the diagram layer
    const diagramLayer = $('#diagramLayer').cloneNode(true);
    diagramLayer.setAttribute('transform', 'translate(0,0) scale(1)');

    // Remove interactive connection points
    diagramLayer.querySelectorAll('.connection-point').forEach(el => el.remove());

    const serializer = new XMLSerializer();
    const layerContent = serializer.serializeToString(diagramLayer);

    return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vbX} ${vbY} ${vbW} ${vbH}" width="${vbW}" height="${vbH}">
  <defs>
    <style>
      .class-border { fill: #1e1e2e; stroke: #4f46e5; stroke-width: 1.5; rx: 6px; }
      .class-header-bg { rx: 6px; }
      .class-name-text { fill: #ffffff; font-family: 'Inter', system-ui, -apple-system, sans-serif; font-size: 13px; font-weight: 600; text-anchor: middle; dominant-baseline: central; }
      .class-stereotype-text { fill: #c084fc; font-family: 'Inter', system-ui, -apple-system, sans-serif; font-size: 10px; font-style: italic; text-anchor: middle; dominant-baseline: central; }
      .class-attr-text { fill: #cbd5e1; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 11px; dominant-baseline: central; }
      .class-op-text { fill: #94a3b8; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 11px; dominant-baseline: central; }
      .class-divider { stroke: #3a3a54; stroke-width: 1; opacity: 0.8; }
      .rel-line { stroke: #94a3b8; stroke-width: 1.5; fill: none; }
      .rel-mult { fill: #a0a0b8; font-family: 'Inter', system-ui, sans-serif; font-size: 11px; }
      .rel-label { fill: #e2e8f0; font-family: 'Inter', system-ui, sans-serif; font-size: 11px; font-style: italic; text-anchor: middle; }
    </style>
    <!-- Arrow markers for relationships -->
    <marker id="arrowOpen" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
        <path d="M0,0 L10,3.5 L0,7" fill="none" stroke="#94a3b8" stroke-width="1.5"/>
    </marker>
    <marker id="arrowClosed" markerWidth="12" markerHeight="8" refX="12" refY="4" orient="auto">
        <path d="M0,0 L12,4 L0,8 Z" fill="none" stroke="#94a3b8" stroke-width="1.5"/>
    </marker>
    <marker id="diamondEmpty" markerWidth="14" markerHeight="8" refX="0" refY="4" orient="auto">
        <path d="M0,4 L7,0 L14,4 L7,8 Z" fill="#12121a" stroke="#94a3b8" stroke-width="1.5"/>
    </marker>
    <marker id="diamondFull" markerWidth="14" markerHeight="8" refX="0" refY="4" orient="auto">
        <path d="M0,4 L7,0 L14,4 L7,8 Z" fill="#94a3b8" stroke="#94a3b8" stroke-width="1.5"/>
    </marker>
  </defs>
  <!-- Background Rect for standalone viewing -->
  <rect x="${vbX}" y="${vbY}" width="${vbW}" height="${vbH}" fill="#12121a" rx="8"/>
  ${layerContent}
</svg>`;
}

$('#btnExportSVG').addEventListener('click', () => {
    try {
        const svgStr = generateStandaloneSVG();
        downloadFile(`${state.model.name.replace(/ /g, '_')}.svg`, svgStr, 'image/svg+xml');
        $('#exportModal').classList.add('hidden');
        showToast('Diagrama exportado como imagen SVG autónoma', 'success');
    } catch (err) {
        showToast(`Error exportando SVG: ${err.message}`, 'error');
    }
});

$('#btnImport').addEventListener('click', () => {
    $('#importFileInput').click();
});

$('#importFileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    showToast(`Procesando archivo ${file.name}...`, 'info');

    try {
        let importedDiagram = null;
        let warnings = [];

        if (ext === 'xmi' || ext === 'xml') {
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/api/import/xmi', { method: 'POST', body: formData });
            if (!res.ok) {
                const errJson = await res.json().catch(() => ({ detail: 'Error en servidor' }));
                throw new Error(errJson.detail || 'Error en importador XMI');
            }
            const data = await res.json();
            importedDiagram = data.diagram;
            warnings = data.warnings || [];
        } else if (ext === 'mdj') {
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/api/import/mdj', { method: 'POST', body: formData });
            if (!res.ok) {
                const errJson = await res.json().catch(() => ({ detail: 'Error en servidor' }));
                throw new Error(errJson.detail || 'Error en importador MDJ');
            }
            const data = await res.json();
            importedDiagram = data.diagram;
            warnings = data.warnings || [];
        } else {
            // JSON: can be native GeneradorUML or StarUML JSON
            const text = await file.text();
            const parsed = JSON.parse(text);
            if (parsed._type === 'Project') {
                const formData = new FormData();
                formData.append('file', file);
                const res = await fetch('/api/import/mdj', { method: 'POST', body: formData });
                if (!res.ok) throw new Error(await res.text());
                const data = await res.json();
                importedDiagram = data.diagram;
                warnings = data.warnings || [];
            } else {
                importedDiagram = parsed;
            }
        }

        if (importedDiagram) {
            saveUndo();
            state.model = UMLModel.fromJSON(importedDiagram);
            state.classCounter = state.model.classes.length + 1;
            $('#projectName').value = state.model.name;
            state.selectedId = null;
            state.selectedType = null;
            renderAll();
            saveCurrentProjectToStorage();
            broadcastChange();

            let msg = `Diagrama "${state.model.name}" importado (${state.model.classes.length} clases)`;
            if (warnings.length > 0) {
                msg += ` con ${warnings.length} advertencia(s)`;
                showToast(msg, 'warning');
            } else {
                showToast(msg, 'success');
            }
        }
    } catch (err) {
        showToast(`Error al importar: ${err.message}`, 'error');
    }

    e.target.value = '';
});

// ═══════════════════════════════════════════════════════════════════════════
// Voice Input
// ═══════════════════════════════════════════════════════════════════════════

$('#btnVoice').addEventListener('click', () => {
    $('#voiceModal').classList.remove('hidden');
});

$('#btnCloseVoice').addEventListener('click', () => {
    $('#voiceModal').classList.add('hidden');
    if (window._recognition) { window._recognition.stop(); }
});

$('#btnStartVoice').addEventListener('click', () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        showToast('Reconocimiento de voz no soportado en este navegador', 'error');
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    window._recognition = recognition;
    recognition.lang = 'es-ES';
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = () => {
        $('#voiceIndicator').classList.add('active');
        $('#voiceStatus').textContent = 'Escuchando...';
        $('#btnStartVoice').textContent = '⏹ Detener';
        $('#btnApplyVoice').disabled = true;
    };

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(r => r[0].transcript)
            .join('');
        $('#voiceTranscript').textContent = transcript;

        if (event.results[0].isFinal) {
            $('#btnApplyVoice').disabled = false;
        }
    };

    recognition.onend = () => {
        $('#voiceIndicator').classList.remove('active');
        $('#voiceStatus').textContent = 'Dictado completado';
        $('#btnStartVoice').textContent = '🎤 Comenzar';
    };

    recognition.onerror = (event) => {
        $('#voiceIndicator').classList.remove('active');
        $('#voiceStatus').textContent = `Error: ${event.error}`;
        $('#btnStartVoice').textContent = '🎤 Comenzar';
    };

    recognition.start();
});

$('#btnApplyVoice').addEventListener('click', () => {
    const transcript = $('#voiceTranscript').textContent.trim().toLowerCase();
    if (!transcript) return;

    saveUndo();
    const result = parseVoiceCommand(transcript);
    if (result.success) {
        showToast(result.message, 'success');
        renderAll();
    } else {
        showToast(result.message, 'warning');
    }

    $('#voiceTranscript').textContent = '';
    $('#btnApplyVoice').disabled = true;
});

function toCamelCase(str) {
    const parts = str.trim().split(/\s+/);
    if (parts.length === 1) return parts[0];
    return parts[0].toLowerCase() + parts.slice(1).map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase()).join('');
}

function parseVoiceCommand(text) {
    text = text.trim();

    // 1. "crear (una|la)? clase (llamada)? X"
    let match = text.match(/crear\s+(?:una\s+|la\s+)?clase\s+(?:llamada\s+)?([a-zA-Z0-9_\s]+)/i);
    if (match) {
        const rawName = match[1].trim();
        const words = rawName.split(/\s+/);
        // Capitalize class name in PascalCase
        const name = words.map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join('');
        const cls = new UMLClassNode(name, 100 + Math.random() * 350, 100 + Math.random() * 250);
        state.model.addClass(cls);
        state.classCounter++;
        return { success: true, message: `Clase "${name}" creada exitosamente` };
    }

    // 2. "agregar (un|el)? atributo <nombre> (de tipo|tipo) <tipo> (a|en|para) (la clase)? <clase>"
    match = text.match(/agregar\s+(?:un\s+|el\s+)?atributo\s+(.+?)\s+(?:de\s+tipo|tipo)\s+(\w+)\s+(?:a|en|para)\s+(?:la\s+clase\s+)?(\w+)/i);
    if (match) {
        const rawAttrName = match[1].trim();
        const attrName = toCamelCase(rawAttrName);
        const attrType = match[2].charAt(0).toUpperCase() + match[2].slice(1);
        const rawClassName = match[3].trim();
        const className = rawClassName.charAt(0).toUpperCase() + rawClassName.slice(1);

        let cls = state.model.classes.find(c => c.name.toLowerCase() === className.toLowerCase());
        let autoCreatedMsg = '';
        if (!cls) {
            // Auto-crear la clase si no existía previamente
            cls = new UMLClassNode(className, 100 + Math.random() * 350, 100 + Math.random() * 250);
            state.model.addClass(cls);
            state.classCounter++;
            autoCreatedMsg = ` (Clase "${className}" creada automáticamente)`;
        }

        cls.addAttribute({ id: crypto.randomUUID(), name: attrName, type: attrType, visibility: '-', constraints: [] });
        return { success: true, message: `Atributo "${attrName}: ${attrType}" agregado a "${cls.name}"${autoCreatedMsg}` };
    }

    // 3. "agregar (una|la)? operación <nombre> (a|en) <clase> (que retorna)? <tipo>"
    match = text.match(/agregar\s+(?:una\s+|la\s+)?operaci[oó]n\s+(.+?)\s+(?:a|en)\s+(?:la\s+clase\s+)?(\w+)(?:\s+(?:que\s+)?retorna\s+(\w+))?/i);
    if (match) {
        const rawOpName = match[1].trim();
        const opName = toCamelCase(rawOpName);
        const rawClassName = match[2].trim();
        const className = rawClassName.charAt(0).toUpperCase() + rawClassName.slice(1);
        const returnType = match[3] ? match[3].charAt(0).toUpperCase() + match[3].slice(1) : 'void';

        let cls = state.model.classes.find(c => c.name.toLowerCase() === className.toLowerCase());
        if (!cls) {
            cls = new UMLClassNode(className, 100 + Math.random() * 350, 100 + Math.random() * 250);
            state.model.addClass(cls);
            state.classCounter++;
        }
        cls.addOperation({ id: crypto.randomUUID(), name: opName, parameters: [], returnType, visibility: '+' });
        return { success: true, message: `Operación "${opName}(): ${returnType}" agregada a "${cls.name}"` };
    }

    // 4. "crear relación (de)? <tipo> (de|desde) <origen> (a|hacia) <destino>"
    match = text.match(/crear\s+(?:una\s+)?relaci[oó]n\s+(?:de\s+)?(\w+)\s+(?:de|desde)\s+(?:la\s+clase\s+)?(\w+)\s+(?:a|hacia)\s+(?:la\s+clase\s+)?(\w+)/i);
    if (match) {
        const relTypeMap = {
            'asociación': 'association', 'asociacion': 'association',
            'agregación': 'aggregation', 'agregacion': 'aggregation',
            'composición': 'composition', 'composicion': 'composition',
            'herencia': 'generalization', 'generalización': 'generalization',
            'realización': 'realization', 'realizacion': 'realization',
            'dependencia': 'dependency',
        };
        const relType = relTypeMap[match[1].toLowerCase()] || 'association';
        const sourceName = match[2].charAt(0).toUpperCase() + match[2].slice(1);
        const targetName = match[3].charAt(0).toUpperCase() + match[3].slice(1);

        const sourceCls = state.model.classes.find(c => c.name.toLowerCase() === sourceName.toLowerCase());
        const targetCls = state.model.classes.find(c => c.name.toLowerCase() === targetName.toLowerCase());

        if (sourceCls && targetCls) {
            const rel = new UMLRelNode(relType, sourceCls.id, targetCls.id);
            state.model.addRelationship(rel);
            return { success: true, message: `Relación de ${match[1]} creada de "${sourceCls.name}" a "${targetCls.name}"` };
        }
        return { success: false, message: `Clases no encontradas en el lienzo: "${sourceName}" o "${targetName}"` };
    }

    return { success: false, message: `Comando no reconocido: "${text}"` };
}

// ═══════════════════════════════════════════════════════════════════════════
// Photo Import & Vision Interpretation
// ═══════════════════════════════════════════════════════════════════════════

$('#btnPhoto').addEventListener('click', () => {
    $('#photoModal').classList.remove('hidden');
});

$('#btnClosePhoto').addEventListener('click', () => {
    $('#photoModal').classList.add('hidden');
});

const dropzone = $('#photoDropzone');
dropzone.addEventListener('click', () => $('#photoInput').click());
dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handlePhotoFile(file);
});

$('#photoInput').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handlePhotoFile(file);
});

function handlePhotoFile(file) {
    state.pendingPhotoFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        $('#photoImage').src = e.target.result;
        $('#photoPreview').classList.remove('hidden');
        $('#photoActions').classList.remove('hidden');
        $('#photoReviewContainer').classList.add('hidden');
        dropzone.classList.add('hidden');
    };
    reader.readAsDataURL(file);
}

$('#btnProcessPhoto').addEventListener('click', async () => {
    if (!state.pendingPhotoFile) {
        showToast('Selecciona o arrastra una imagen primero', 'warning');
        return;
    }

    const btn = $('#btnProcessPhoto');
    btn.disabled = true;
    btn.textContent = '⌛ Interpretando con Visión Artificial...';
    showToast('Procesando imagen con Visión por Computadora y OCR...', 'info');

    try {
        const formData = new FormData();
        formData.append('file', state.pendingPhotoFile);
        const isMobile = (location.host === 'appassets.androidplatform.net' || location.protocol === 'file:');
        const apiOrigin = isMobile ? 'http://127.0.0.1:8000' : '';
        const response = await fetch(`${apiOrigin}/api/photo/interpret`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({ detail: 'Error en servidor' }));
            throw new Error(errData.detail || 'Error procesando imagen');
        }

        const result = await response.json();
        state.detectedDiagram = result.diagram;

        // Render Review in Modal
        const reviewContainer = $('#photoReviewContainer');
        reviewContainer.classList.remove('hidden');

        const badge = $('#photoConfidenceBadge');
        const confPercent = Math.round((result.confidence || 0.75) * 100);
        badge.textContent = `Confianza: ${confPercent}%`;
        badge.className = `confidence-badge ${confPercent < 70 ? 'warning' : ''}`;

        const stats = $('#photoReviewStats');
        stats.innerHTML = `
            <span><strong>${result.detectedClassCount || 0}</strong> clases detectadas</span>
            <span><strong>${result.detectedRelationshipCount || 0}</strong> relaciones detectadas</span>
        `;

        const notes = $('#photoReviewNotes');
        let notesHtml = '<div><strong>Detalles de la detección:</strong></div>';
        if (result.detectedBoxes && result.detectedBoxes.length > 0) {
            notesHtml += '<ul>' + result.detectedBoxes.map(b => `<li>Caja detectada: <em>${escapeHTML(b.name)}</em> (${b.w}x${b.h}px)</li>`).join('') + '</ul>';
        }
        if (result.warnings && result.warnings.length > 0) {
            notesHtml += '<div style="color: var(--warning); margin-top: 4px;">⚠️ Advertencias:</div><ul>' + result.warnings.map(w => `<li>${escapeHTML(w)}</li>`).join('') + '</ul>';
        }
        if (result.reviewNotes && result.reviewNotes.length > 0) {
            notesHtml += '<ul>' + result.reviewNotes.map(n => `<li>${escapeHTML(n)}</li>`).join('') + '</ul>';
        }
        notes.innerHTML = notesHtml;

        showToast(`Interpretación completada: ${result.detectedClassCount} clases encontradas`, 'success');
    } catch (err) {
        showToast(`Error al interpretar fotografía: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Interpretar Diagrama';
    }
});

$('#btnAcceptPhotoDiagram').addEventListener('click', () => {
    if (!state.detectedDiagram) return;
    saveUndo();
    state.model = UMLModel.fromJSON(state.detectedDiagram);
    state.classCounter = state.model.classes.length + 1;
    $('#projectName').value = state.model.name;
    state.selectedId = null;
    state.selectedType = null;
    renderAll();
    saveCurrentProjectToStorage();
    broadcastChange();
    $('#photoModal').classList.add('hidden');
    showToast(`Diagrama importado al lienzo (${state.model.classes.length} clases)`, 'success');
});

$('#btnDiscardPhotoDiagram').addEventListener('click', () => {
    $('#photoReviewContainer').classList.add('hidden');
    $('#photoPreview').classList.add('hidden');
    $('#photoActions').classList.add('hidden');
    dropzone.classList.remove('hidden');
    state.pendingPhotoFile = null;
    state.detectedDiagram = null;
});

// ═══════════════════════════════════════════════════════════════════════════
// Save Project & Storage Persistence
// ═══════════════════════════════════════════════════════════════════════════

function saveCurrentProjectToStorage() {
    try {
        const serialized = JSON.stringify(state.model.toJSON());
        localStorage.setItem('generador_uml_current', serialized);
        localStorage.setItem(`project_${state.projectId}`, serialized);
    } catch (e) {
        console.warn('No se pudo guardar en localStorage', e);
    }
}

async function saveProject() {
    broadcastChange();
    persistCollaboration();
    showToast(state.ws?.readyState === WebSocket.OPEN ? 'Guardado local; sincronización automática activa' : 'Guardado en este dispositivo. Se sincronizará al reconectar.', 'info');
}

$('#btnSave').addEventListener('click', saveProject);

window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        saveProject();
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// Real-Time Collaboration (WebSocket)
// ═══════════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════
// Toast Notifications
// ═══════════════════════════════════════════════════════════════════════════

function showToast(message, type = 'info') {
    const container = $('#toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    toast.textContent = `${icons[type] || ''} ${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ═══════════════════════════════════════════════════════════════════════════
// Tabs
// ═══════════════════════════════════════════════════════════════════════════

$$('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        $$('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (btn.dataset.tab === 'generate') {
            showGeneratePanel();
        } else {
            $('#generatePanel').classList.add('hidden');
        }
    });
});

// ═══════════════════════════════════════════════════════════════════════════
// Initialize
// ═══════════════════════════════════════════════════════════════════════════

function init() {
    // Check if previous project exists in localStorage
    try {
        const shared = savedCollaboration();
        const cached = shared ? JSON.stringify(shared.diagram) : (!new URLSearchParams(location.search).has('project') ? localStorage.getItem('generador_uml_current') : null);
        if (cached) {
            const data = JSON.parse(cached);
            if (data && data.classes) {
                state.model = UMLModel.fromJSON(data);
                state.classCounter = state.model.classes.length + 1;
                $('#projectName').value = state.model.name;
            }
        }
    } catch (e) { /* ignore */ }

    renderAll();
    initWebSocket();
    // Debounced broadcast on real changes + gentle 3-second fallback heartbeat
    setInterval(broadcastChange, 3000);
    $('#btnShare').addEventListener('click', showShareDialog);

    // Autosave every 30 seconds
    setInterval(saveCurrentProjectToStorage, 30000);

    console.log('%c GeneradorUML v1.0 ', 'background: linear-gradient(135deg, #818cf8, #c084fc); color: white; font-size: 16px; padding: 8px 16px; border-radius: 8px; font-weight: bold;');
    console.log('Editor UML con generación de Spring Boot + Flutter');
}

init();
