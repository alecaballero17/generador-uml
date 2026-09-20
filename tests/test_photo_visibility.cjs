const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const ctx={crypto:require('crypto').webcrypto,document:{getElementById(){return null}},collaborationState:{role:'admin'},saveUndo(){},renderAll(){},persistCollaboration(){},broadcastChange(){},refreshMobileCards(){}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('frontend/js/uml-commands.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('frontend/js/app.js','utf8').split('const state =')[0]+'const state={model:new UMLModel()};',ctx);
const source=fs.readFileSync('frontend/js/mobile.js','utf8');vm.runInContext(source.slice(source.indexOf('function applyUMLPlan'),source.indexOf('function reviewMobileCommand')),ctx);vm.runInContext(source.slice(source.indexOf('function reviewPhotoText'),source.indexOf('function openMobileForm')),ctx);
vm.runInContext("applyUMLPlan(reviewPhotoText('Bank\\n+code\\n-address\\n#branch\\n~region\\nother')[0])",ctx);
assert.equal(vm.runInContext("state.model.classes[0].attributes.map(a=>a.visibility).join('')",ctx),'+-#~-');
assert.equal(vm.runInContext('state.model.classes[0].attributes.length',ctx),5);
console.log('Photo import preserves all four UML visibilities and default private.');

vm.runInContext("applyUMLPlan(reviewPhotoText('Account\\n+number\\n+deposit()\\n-withdraw(): Boolean')[0])",ctx);
assert.equal(vm.runInContext('state.model.classes[1].operations.length',ctx),2);
assert.equal(vm.runInContext('state.model.classes[1].operations[1].visibility',ctx),'-');

vm.runInContext("applyUMLPlan(reviewPhotoText('Service\\n+save(id: Long, names: String[]): Boolean')[0])",ctx);
assert.equal(vm.runInContext('state.model.classes[2].operations[0].parameters.length',ctx),2);
assert.equal(vm.runInContext('state.model.classes[2].operations[0].parameters[1].type',ctx),'String[]');
assert.equal(vm.runInContext('state.model.classes[2].operations[0].returnType',ctx),'Boolean');
assert.throws(()=>vm.runInContext("reviewPhotoText('Bad\\n+save(id: Long, id: String)')",ctx),/repetidos/);
assert.throws(()=>vm.runInContext("reviewPhotoText('Bad\\n+save(???)')",ctx),/nombre: Tipo/);
vm.runInContext(source.slice(source.indexOf('function buildPhotoDiagram'),source.indexOf('function reviewPhotoText')),ctx);
assert.equal(vm.runInContext("buildPhotoDiagram('Example\\n+find(id: Long): String').classes[0].operations[0].parameters[0].type",ctx),'Long');
const previous=vm.runInContext('JSON.stringify(state.model.toJSON())',ctx);
assert.throws(()=>vm.runInContext("buildPhotoDiagram('Same\\n+x\\n\\nSame\\n+y')",ctx),/repetidos/);
assert.equal(vm.runInContext('JSON.stringify(state.model.toJSON())',ctx),previous,'Invalid review must not modify current diagram');
assert.throws(()=>vm.runInContext("reviewPhotoText('Bad\\n+id\\n+id')",ctx),/Atributos repetidos/);
