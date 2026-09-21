const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const code = fs.readFileSync('frontend/js/mobile.js', 'utf8');

// Set up mock DOM and state
let undoSaved = false;
let rendered = false;
let persisted = false;
let broadcasted = false;
let refreshed = false;

const mockClass = {
    id: 'cls-1',
    name: 'Factura',
    attributes: [{ id: 'attr-1', name: 'total', type: 'Double', visibility: '-' }],
    operations: [{ id: 'op-1', name: 'calcularTotal', returnType: 'Double', visibility: '+', parameters: [] }],
    addAttribute(a) { this.attributes.push(a); },
    addOperation(o) { this.operations.push(o); },
    removeOperation(id) { this.operations = this.operations.filter(o => o.id !== id); }
};

const state = {
    model: {
        classes: [mockClass],
        relationships: [],
        toJSON() { return { classes: this.classes, relationships: this.relationships }; }
    },
    selectedId: null,
    selectedType: null
};

const collaborationState = {
    role: 'editor'
};

const ctx = vm.createContext({
    state,
    collaborationState,
    saveUndo: () => { undoSaved = true; },
    renderAll: () => { rendered = true; },
    persistCollaboration: () => { persisted = true; },
    broadcastChange: () => { broadcasted = true; },
    refreshMobileCards: () => { refreshed = true; },
    showToast: () => {},
    crypto: { randomUUID: () => 'uuid-' + Math.random().toString(36).slice(2) },
    document: {
        getElementById: () => null,
        createElement: (tag) => {
            const el = {
                tagName: tag,
                children: [],
                className: '',
                textContent: '',
                innerHTML: '',
                style: {},
                elements: {},
                append(...children) { this.children.push(...children); },
                replaceChildren() { this.children = []; },
                querySelector(sel) { return this[sel] || null; },
                querySelectorAll() { return []; },
                showModal() {},
                close() {},
                remove() {}
            };
            return el;
        },
        body: {
            append() {}
        }
    },
    $: () => null,
    UMLCommands: {
        identifier: (n, p) => n,
        parse: () => null
    }
});

// Load applyUMLPlan and reviewMobileCommand
vm.runInContext(code.slice(code.indexOf('function applyUMLPlan'), code.indexOf('function reviewMobileCommand')), ctx);

// Test 1: applyUMLPlan adds operation to existing class
ctx.applyUMLPlan({
    action: 'addOperation',
    name: 'Factura',
    operation: {
        name: 'anular',
        returnType: 'Boolean',
        visibility: '+',
        parameters: [{ name: 'motivo', type: 'String' }]
    }
});

assert.equal(mockClass.operations.length, 2);
assert.equal(mockClass.operations[1].name, 'anular');
assert.equal(mockClass.operations[1].returnType, 'Boolean');
assert.equal(mockClass.operations[1].parameters.length, 1);
assert.equal(undoSaved, true);
assert.equal(rendered, true);

// Test 2: duplicate operation throws error
assert.throws(() => {
    ctx.applyUMLPlan({
        action: 'addOperation',
        name: 'Factura',
        operation: { name: 'anular', returnType: 'void' }
    });
}, /ya existe/);

// Test 3: viewer role rejects adding operation
collaborationState.role = 'viewer';
assert.throws(() => {
    ctx.applyUMLPlan({
        action: 'addOperation',
        name: 'Factura',
        operation: { name: 'nuevaOp', returnType: 'void' }
    });
}, /solo lectura/);
collaborationState.role = 'editor';

// Test 4: removeOperation works on mockClass
mockClass.removeOperation('op-1');
assert.equal(mockClass.operations.length, 1);
assert.equal(mockClass.operations[0].name, 'anular');

// Test 5: applyUMLPlan deleteOperation
ctx.applyUMLPlan({
    action: 'deleteOperation',
    name: 'Factura',
    operationName: 'anular'
});
assert.equal(mockClass.operations.length, 0);

// Test 6: applyUMLPlan renameClass
ctx.applyUMLPlan({
    action: 'renameClass',
    oldName: 'Factura',
    newName: 'Comprobante'
});
assert.equal(mockClass.name, 'Comprobante');

console.log('✓ Operaciones móviles (creación, duplicados, permisos, renombrado y borrado) verificadas correctamente.');

