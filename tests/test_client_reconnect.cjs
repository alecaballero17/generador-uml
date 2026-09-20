const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('frontend/js/collaboration.js','utf8');
const clone=x=>JSON.parse(JSON.stringify(x));
const base={name:'Prueba',classes:[{id:'a',name:'Usuario',attributes:[],position:{x:0,y:0}}],relationships:[]};
let model=clone(base),sent=[],conflict=null;
const ctx={state:{model:{toJSON:()=>clone(model)},ws:{readyState:1,send:value=>sent.push(JSON.parse(value))}},WebSocket:{OPEN:1},persistCollaboration(){},syncBadge(){},applySharedDiagram:value=>model=clone(value),showCollaborationConflict:(...args)=>conflict=args};
vm.createContext(ctx);
vm.runInContext(source.slice(source.indexOf('const collaborationState ='),source.indexOf('function syncBadge(')),ctx);
vm.runInContext(source.slice(source.indexOf('function handleSharedSnapshot('),source.indexOf('function showCollaborationConflict(')),ctx);
vm.runInContext(source.slice(source.indexOf('function broadcastChange('),source.indexOf('async function initWebSocket(')),ctx);
ctx.base=clone(base);vm.runInContext("collaborationState.base=base;collaborationState.ready=true;collaborationState.role='editor'",ctx);
model.classes[0].attributes.push({id:'correo',name:'correo'});
const remote=clone(base);remote.classes[0].position.x=410;
ctx.message={revision:1,diagram:remote};vm.runInContext('handleSharedSnapshot(message)',ctx);
assert.equal(model.classes[0].position.x,410);assert.equal(model.classes[0].attributes[0].name,'correo');assert.equal(sent.length,1);
// A second local edit while the first is awaiting acknowledgment must survive.
model.classes[0].attributes.push({id:'telefono',name:'telefono'});
ctx.message={revision:2,diagram:sent[0].diagram};vm.runInContext('handleSharedSnapshot(message,true)',ctx);
assert.equal(sent.length,2);assert.equal(sent[1].diagram.classes[0].attributes.length,2);
ctx.message={revision:1,diagram:remote};vm.runInContext('handleSharedSnapshot(message,true)',ctx);
assert(vm.runInContext('collaborationState.inflight',ctx),'A stale acknowledgment must not discard the pending update');
ctx.message={revision:3,diagram:sent[1].diagram};vm.runInContext('handleSharedSnapshot(message,true)',ctx);
assert.equal(sent.length,2);assert.equal(vm.runInContext('collaborationState.inflight',ctx),null);
// Conflicting names must remain local until an explicit resolution.
model.classes[0].name='Local';const other=clone(sent[1].diagram);other.classes[0].name='Remoto';
ctx.message={revision:4,diagram:other};vm.runInContext('handleSharedSnapshot(message)',ctx);
assert(conflict);assert.equal(model.classes[0].name,'Local');assert.equal(sent.length,2);
console.log('Client reconnect: independent edits merged, edits during acknowledgment retained, conflicts not silently applied.');
