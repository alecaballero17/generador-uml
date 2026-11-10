const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
let error='',saved=0;const field=value=>({value,append(){}});
const elements={source:field(''),target:field(''),type:field('association'),sourceMult:field(''),targetMult:field(''),associationClass:field('')};
const form={elements},dialog={querySelector:s=>s==='form'?form:s==='[role=alert]'?{set textContent(v){error=v}}:{},showModal(){},close(){},remove(){}};
const ctx={crypto:require('crypto').webcrypto,document:{getElementById(){return null},createElement:t=>t==='dialog'?dialog:{},body:{append(){}}},collaborationState:{role:'admin'},showToast(){},saveUndo(){saved++},renderAll(){},persistCollaboration(){},broadcastChange(){},refreshMobileCards(){}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('frontend/js/app.js','utf8').split('const state =')[0]+`
const state={model:new UMLModel()};
for(const [id,name] of [['v','Venta'],['p','Producto'],['d','Detalle']]){const cls=new UMLClassNode(name);cls.id=id;state.model.addClass(cls);}
for(const [parent,count] of [['v','1..*'],['p','*']]){const rel=new UMLRelNode('association',parent,'d');rel.id=parent+'d';rel.source.multiplicity='1';rel.target.multiplicity=count;state.model.addRelationship(rel);}
`,ctx);
vm.runInContext(fs.readFileSync('frontend/js/association-classes.js','utf8'),ctx);
const mobile=fs.readFileSync('frontend/js/mobile.js','utf8');vm.runInContext(mobile.slice(mobile.indexOf('function openMobileRelationship(')),ctx);
vm.runInContext('const candidate=associationClassCandidate(state.model,"d");openMobileRelationship(candidate)',ctx);
assert.equal(elements.sourceMult.value,'*');assert.equal(elements.targetMult.value,'1..*');
assert.equal(vm.runInContext('state.model.relationships.length',ctx),2,'Preparing preview must not change model');
elements.sourceMult.value='1';form.onsubmit({preventDefault(){}});assert(error.includes('ambos extremos'));assert.equal(saved,0);
elements.sourceMult.value='*';form.onsubmit({preventDefault(){}});
assert.equal(saved,1);assert.equal(vm.runInContext('state.model.relationships.length',ctx),1);
assert.equal(vm.runInContext('state.model.relationships[0].associationClassId',ctx),'d');
assert.equal(vm.runInContext('state.model.relationships[0].target.navigable',ctx),false);
assert.equal(vm.runInContext('UMLRelNode.fromJSON(state.model.relationships[0].toJSON()).associationClassId',ctx),'d');
assert.equal(vm.runInContext('associationClassCandidate(state.model,"d")',ctx),null);
console.log('Clase de asociación: vista previa, validación, conversión y persistencia verificadas.');
