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
