const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('frontend/js/drive-backup.js','utf8');
function scenario(){
    const elements={};let dialog=null,uploads=0,id=0;
    const timers=new Map(),clients=[];
    function element(){return {disabled:false,textContent:'',dataset:{},setAttribute(){},after(){}};}
    const ctx={Blob,crypto,AbortSignal,AbortController,
        setTimeout(fn){timers.set(++id,fn);return id;},clearTimeout(id){timers.delete(id);},
        state:{model:{toJSON:()=>({name:'Prueba',classes:[],relationships:[]})}},
        umlApiFetch:async()=>({ok:true,json:async()=>({configured:true,clientId:'test.apps.googleusercontent.com'})}),
        window:{google:{accounts:{oauth2:{hasGrantedAllScopes:()=>true,
            initTokenClient(config){clients.push(config);return {requestAccessToken(){}};}
        }}}},
        fetch:async()=>{uploads++;return {ok:true,json:async()=>({id:'backup'})};},
        document:{
            getElementById(id){return id==='driveBackupDialog'?dialog:null;},
            createElement(tag){
                if(tag!=='dialog')return element();
                dialog={isConnected:false,showModal(){},close(){},remove(){this.isConnected=false;},
                    addEventListener(){},querySelector(key){return elements[key] ||= element();}};
                return dialog;
            },body:{append(el){el.isConnected=true;}}
        }
    };
    vm.createContext(ctx);vm.runInContext(source,ctx);
    return {ctx,elements,timers,clients,get uploads(){return uploads;},get dialog(){return dialog;}};
}
(async()=>{
    const a=scenario();await a.ctx.showDriveBackup();
    a.elements['#driveConnectSave'].onclick();
    assert.equal(a.elements['#driveConnectSave'].disabled,true);
    assert.equal(a.elements['#driveBackupClose'].disabled,false);
    a.elements['#driveBackupClose'].onclick();
    assert.equal(a.dialog.isConnected,false);assert.equal(a.timers.size,0);
    await a.clients[0].callback({access_token:'late'});assert.equal(a.uploads,0);

    const b=scenario();await b.ctx.showDriveBackup();b.elements['#driveConnectSave'].onclick();
    [...b.timers.values()][0](); // Google returns neither success nor failure.
    assert.equal(b.elements['#driveConnectSave'].disabled,false);
    assert.match(b.elements['.drive-status'].textContent,/no devolvió/);
    b.elements['#driveConnectSave'].onclick();
    await b.clients[0].callback({access_token:'obsolete'});assert.equal(b.uploads,0);
    b.clients[1].error_callback({type:'popup_closed'});
    assert.equal(b.elements['#driveConnectSave'].disabled,false);
    b.elements['#driveConnectSave'].onclick();
    await b.clients[2].callback({access_token:'valid'});
    assert.equal(b.uploads,1);assert.match(b.elements['.drive-status'].textContent,/Respaldo guardado/);
    await b.clients[2].callback({access_token:'duplicate'});assert.equal(b.uploads,1);

    const c=scenario();await c.ctx.showDriveBackup();c.elements['#driveConnectSave'].onclick();
    c.ctx.window.google.accounts.oauth2.hasGrantedAllScopes=()=>{throw new Error('SDK failure');};
    await c.clients[0].callback({access_token:'valid'});
    assert.equal(c.elements['#driveConnectSave'].disabled,false);assert.equal(c.uploads,0);
    console.log('OAuth: cerrar siempre disponible, espera limitada, reintento, callbacks tardios ignorados y carga unica: OK.');
})().catch(error=>{console.error(error);process.exitCode=1;});
