const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
let error='';const field=value=>({value,append(){}});const elements={source:field('a'),target:field('b'),type:field('generalization'),sourceMult:field('1'),targetMult:field('0..*')};
const form={elements};const alert={set textContent(v){error=v}};const dialog={querySelector:s=>s==='form'?form:s==='[role=alert]'?alert:{},showModal(){},close(){},remove(){}};
const ctx={document:{createElement:t=>t==='dialog'?dialog:{},body:{append(){}}},collaborationState:{role:'admin'},showToast(){},saveUndo(){},renderAll(){},persistCollaboration(){},broadcastChange(){},refreshMobileCards(){},crypto:require('crypto').webcrypto};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('frontend/js/app.js','utf8').split('const state =')[0]+`const state={model:new UMLModel()};const a=new UMLClassNode('Hija');a.id='a';const b=new UMLClassNode('Padre');b.id='b';state.model.addClass(a);state.model.addClass(b);`,ctx);
const code=fs.readFileSync('frontend/js/mobile.js','utf8');vm.runInContext(code.slice(code.indexOf('function openMobileRelationship(')),ctx);
vm.runInContext('openMobileRelationship()',ctx);form.onsubmit({preventDefault(){}});assert.equal(vm.runInContext('state.model.relationships.length',ctx),1);
elements.source.value='b';elements.target.value='a';form.onsubmit({preventDefault(){}});assert(error.includes('ciclo'));assert.equal(vm.runInContext('state.model.relationships.length',ctx),1);
console.log('Relaciones móviles: creación local y prevención de ciclo verificadas.');

assert.equal(vm.runInContext('state.model.relationships[0].source.multiplicity',ctx),null);
assert.equal(vm.runInContext('state.model.relationships[0].target.multiplicity',ctx),null);
elements.type.value='association';elements.sourceMult.value='';elements.targetMult.value='';form.onsubmit({preventDefault(){}});
assert.equal(vm.runInContext('state.model.relationships[1].source.multiplicity',ctx),null);
assert.equal(vm.runInContext('state.model.relationships[1].target.multiplicity',ctx),null);

// Test candidate pre-population and direction swap button
const swapBtn = {};
dialog.querySelector = s => s === 'form' ? form : s === '[role=alert]' ? alert : s === '#btnSwapDirection' ? swapBtn : {};
vm.runInContext("openMobileRelationship({source:'a',target:'b',type:'composition',sourceMult:'1',targetMult:'1..*'})", ctx);
assert.equal(elements.source.value, 'a');
assert.equal(elements.target.value, 'b');
assert.equal(elements.type.value, 'composition');
assert.equal(elements.sourceMult.value, '1');
assert.equal(elements.targetMult.value, '1..*');
assert.equal(typeof swapBtn.onclick, 'function');
swapBtn.onclick();
assert.equal(elements.source.value, 'b');
assert.equal(elements.target.value, 'a');
console.log('Inversión de dirección y precarga de candidatos verificadas.');

