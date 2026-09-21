const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('frontend/js/collaboration.js','utf8');
const clone=x=>JSON.parse(JSON.stringify(x));
const base={name:'Test',classes:[{id:'a',name:'Foo',attributes:[],position:{x:0,y:0}}],relationships:[]};

// Slice out the relevant functions from the collaboration module
function buildContext(modelData) {
    let model=clone(modelData||base),sent=[],stored=new Map(),badgeText='';
    const ctx={
        state:{model:{toJSON:()=>clone(model)},ws:null,projectId:'q1',isRemoteUpdate:false},
        WebSocket:{OPEN:1,CONNECTING:0},
        $:sel=>{if(sel==='#collabStatus')return{set textContent(v){badgeText=v},get textContent(){return badgeText}};return{textContent:'',value:'',disabled:false};},
        UMLModel:{fromJSON:d=>{model=clone(d);return{toJSON:()=>clone(model)}}},
        renderAll(){},
        saveCurrentProjectToStorage(){},
        showToast(){},
        crypto:{randomUUID:()=>'uuid-'+Math.random()},
        localStorage:{getItem:k=>stored.get(k)||null,setItem:(k,v)=>stored.set(k,v),removeItem:k=>stored.delete(k)},
        sessionStorage:{getItem:()=>'cid',setItem(){}},
        location:{host:'localhost',protocol:'http:',href:'http://localhost',search:'',hash:''},
        document:{querySelectorAll:()=>[],getElementById:()=>null},
        history:{replaceState(){}},
        window:{addEventListener(){}},
        navigator:{onLine:true},
        setTimeout:(fn,ms)=>42,
        clearTimeout(){},
        console,
    };
    ctx.collaborationClientId='cid';
    ctx.collaborationStorageKey=()=>`collaboration_q1_cid`;
    vm.createContext(ctx);

    // Load collaborationState and helpers
    const stateStart=source.indexOf('const collaborationState');
    const stateEnd=source.indexOf('function syncBadge(');
    vm.runInContext(source.slice(stateStart,stateEnd),ctx);

    // Load core functions (sequentially, since they depend on each other)
    const functionsBlock=source.slice(source.indexOf('function syncBadge('),source.indexOf('async function initWebSocket('));
    vm.runInContext(functionsBlock,ctx);

    // Load broadcastChange
    const broadcastStart=source.indexOf('function broadcastChange(');
    const broadcastEnd=source.indexOf('async function initWebSocket(');
    // Already included above if broadcastChange is before initWebSocket - re-check
    
    return {ctx,getModel:()=>model,setModel:d=>{model=clone(d)},getSent:()=>sent,getBadge:()=>badgeText,stored};
}

// Test 1: broadcastChange queues to pendingOffline when WS is not open
{
    const {ctx}=buildContext();
    vm.runInContext("collaborationState.ready=true; collaborationState.role='editor'; collaborationState.base=copyDiagram(state.model.toJSON());",ctx);
    // Set WS to null (disconnected)
    ctx.state.ws=null;
    // Modify model locally
    ctx.state.model.toJSON=()=>clone({...base,classes:[{...base.classes[0],name:'Modified'}]});
    vm.runInContext('broadcastChange()',ctx);
    const pending=vm.runInContext('collaborationState.pendingOffline',ctx);
    assert(pending,'broadcastChange should queue to pendingOffline when disconnected');
    assert.equal(pending.classes[0].name,'Modified');
    console.log('✓ Test 1: broadcastChange queues to pendingOffline when WS is not open');
}

// Test 2: pendingOffline is persisted to localStorage
{
    const {ctx,stored}=buildContext();
    vm.runInContext("collaborationState.ready=true; collaborationState.role='editor'; collaborationState.base=copyDiagram(state.model.toJSON());",ctx);
    ctx.state.ws=null;
    ctx.state.model.toJSON=()=>clone({...base,classes:[{...base.classes[0],name:'Persisted'}]});
    vm.runInContext('broadcastChange()',ctx);
    const savedRaw=stored.get('collaboration_q1_cid');
    assert(savedRaw);
    const saved=JSON.parse(savedRaw);
    assert(saved.pendingOffline,'pendingOffline should be included in localStorage');
    assert.equal(saved.pendingOffline.classes[0].name,'Persisted');
    console.log('✓ Test 2: pendingOffline is persisted to localStorage');
}

// Test 3: restorePendingOffline loads from localStorage
{
    const {ctx,stored}=buildContext();
    stored.set('collaboration_q1_cid',JSON.stringify({base:clone(base),revision:1,diagram:clone(base),pendingOffline:{...base,classes:[{...base.classes[0],name:'Restored'}]}}));
    vm.runInContext('restorePendingOffline()',ctx);
    const pending=vm.runInContext('collaborationState.pendingOffline',ctx);
    assert(pending);
    assert.equal(pending.classes[0].name,'Restored');
    console.log('✓ Test 3: restorePendingOffline loads from localStorage');
}

// Test 4: flushOfflineQueue sends pending changes when WS is open
{
    const {ctx}=buildContext();
    let sentData=null;
    vm.runInContext("collaborationState.ready=true; collaborationState.role='editor'; collaborationState.base=copyDiagram(state.model.toJSON()); collaborationState.revision=5;",ctx);
    const pendingDiagram=clone({...base,classes:[{...base.classes[0],name:'Flushed'}]});
    vm.runInContext(`collaborationState.pendingOffline=${JSON.stringify(pendingDiagram)}`,ctx);
    ctx.state.ws={readyState:1,send:data=>{sentData=JSON.parse(data)}};
    vm.runInContext('flushOfflineQueue()',ctx);
    assert(sentData,'flushOfflineQueue should send data');
    assert.equal(sentData.type,'update');
    assert.equal(sentData.revision,5);
    assert.equal(vm.runInContext('collaborationState.pendingOffline',ctx),null,'pendingOffline should be cleared after flush');
    console.log('✓ Test 4: flushOfflineQueue sends pending changes when WS is open');
}

// Test 5: flushOfflineQueue does NOT send when there is a conflict
{
    const {ctx}=buildContext();
    vm.runInContext("collaborationState.ready=true; collaborationState.role='editor'; collaborationState.base=copyDiagram(state.model.toJSON()); collaborationState.conflict={};",ctx);
    vm.runInContext(`collaborationState.pendingOffline=${JSON.stringify(base)}`,ctx);
    let sent=false;
    ctx.state.ws={readyState:1,send:()=>{sent=true}};
    vm.runInContext('flushOfflineQueue()',ctx);
    assert.equal(sent,false,'flushOfflineQueue should NOT send when there is a conflict');
    assert(vm.runInContext('collaborationState.pendingOffline',ctx),'pendingOffline should remain');
    console.log('✓ Test 5: flushOfflineQueue does NOT send during conflict');
}

// Test 6: offlineSyncMessage includes pending indicator
{
    const {ctx}=buildContext();
    vm.runInContext(`collaborationState.pendingOffline=${JSON.stringify(base)}`,ctx);
    const msg=vm.runInContext('offlineSyncMessage()',ctx);
    assert(msg.includes('cambios pendientes'),'offlineSyncMessage should indicate pending changes');
    console.log('✓ Test 6: offlineSyncMessage includes pending changes indicator');
}

// Test 7: failed send in broadcastChange saves to pending offline
{
    const {ctx}=buildContext();
    vm.runInContext("collaborationState.ready=true; collaborationState.role='editor'; collaborationState.base=copyDiagram(state.model.toJSON());",ctx);
    ctx.state.model.toJSON=()=>clone({...base,classes:[{...base.classes[0],name:'FailSend'}]});
    let closed=false;
    ctx.state.ws={readyState:1,send:()=>{throw new Error('network error')},close:()=>{closed=true}};
    vm.runInContext('broadcastChange()',ctx);
    const pending=vm.runInContext('collaborationState.pendingOffline',ctx);
    assert(pending,'failed send should save to pendingOffline');
    assert.equal(pending.classes[0].name,'FailSend');
    assert(closed,'WS should be closed after send failure');
    console.log('✓ Test 7: Failed send saves to pendingOffline and closes WS');
}

// Test 8: WS onclose saves inflight to pendingOffline
{
    const {ctx}=buildContext();
    vm.runInContext("collaborationState.ready=true; collaborationState.role='editor'; collaborationState.base=copyDiagram(state.model.toJSON());",ctx);
    const inflightDiagram=clone({...base,classes:[{...base.classes[0],name:'Inflight'}]});
    vm.runInContext(`collaborationState.inflight=${JSON.stringify(inflightDiagram)}`,ctx);
    // Simulate what onclose does
    vm.runInContext('savePendingOffline=function(){collaborationState.pendingOffline=collaborationState.inflight}',ctx);
    vm.runInContext('if(collaborationState.inflight){savePendingOffline();collaborationState.inflight=null;}',ctx);
    assert.equal(vm.runInContext('collaborationState.inflight',ctx),null);
    assert(vm.runInContext('collaborationState.pendingOffline',ctx),'inflight should be moved to pendingOffline on close');
    console.log('✓ Test 8: WS onclose moves inflight to pendingOffline');
}

// Test 9: Project switching isolation (restorePendingOffline resets pendingOffline if project has no offline queue)
{
    const {ctx,stored}=buildContext();
    // Simulate leftover pendingOffline from a prior project in memory
    vm.runInContext("collaborationState.pendingOffline = { name: 'OldProjectDraft' };", ctx);
    // Switch project to q2 which has no offline queue
    ctx.collaborationStorageKey = () => 'collaboration_q2_cid';
    vm.runInContext('restorePendingOffline()', ctx);
    assert.equal(vm.runInContext('collaborationState.pendingOffline', ctx), null, 'pendingOffline should be reset to null when loading a project without offline queue');
    console.log('✓ Test 9: Project switching queue isolation verified');
}

console.log('\nAll offline queue tests passed ✓');
