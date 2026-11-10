const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const original={name:'Primer parcial',classes:[{id:'venta',name:'Venta'}],relationships:[]};
let online=false,connects=0;
const backups=new Map();
const ctx={URL,URLSearchParams,clearTimeout,setTimeout,document:{addEventListener(){}},
    location:{href:'https://uml.test/?project=old#access=old-token',search:'?project=old'},
    state:{projectId:'old',model:{toJSON:()=>original}},
    collaborationState:{token:'old-token',base:original,revision:7,pendingOffline:original},
    copyDiagram:x=>structuredClone(x),
    persistCollaboration(){backups.set(ctx.state.projectId,structuredClone(original));},
    umlApiFetch:async(path,opts)=>{
        assert.equal(path,'/api/collaboration/projects');
        assert.deepEqual(JSON.parse(opts.body).diagram,original);
        return {ok:online,json:async()=>({projectId:'new',token:'new-token',diagram:original,revision:0})};
    },
    history:{replaceState(a,b,url){ctx.location.href=url.href;}},
    initWebSocket:async()=>{connects++;}
};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('frontend/js/project-start.js','utf8'),ctx);
(async()=>{
    // Failed recovery must leave the existing ID, permission and diagram untouched.
    await assert.rejects(ctx.recoverProjectCopy(),/No se pudo crear/);
    assert.equal(ctx.state.projectId,'old');assert.equal(ctx.collaborationState.token,'old-token');
    assert.deepEqual(backups.get('old'),original);assert.equal(connects,0);
    online=true;
    await ctx.recoverProjectCopy();
    assert.equal(ctx.state.projectId,'new');assert.equal(ctx.collaborationState.token,'new-token');
    assert.equal(ctx.collaborationState.pendingOffline,null);assert.equal(connects,1);
    assert.deepEqual(backups.get('old'),original);assert.deepEqual(backups.get('new'),original);
    assert.equal(new URL(ctx.location.href).searchParams.get('project'),'new');
    assert.equal(new URL(ctx.location.href).hash,'#access=new-token');
    assert.equal(await ctx.chooseProjectStart(),false); // Shared links never open the new-project chooser.
    console.log('Recuperacion: respaldo previo, fallo sin perdida, nueva sala y permiso, enlace actualizado: OK.');
})().catch(error=>{console.error(error);process.exitCode=1;});
