const assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const requests=[];let configured=null;
const context={URL,location:{host:'appassets.androidplatform.net',protocol:'https:',origin:'https://appassets.androidplatform.net'},localStorage:{getItem:()=>configured},fetch:(url,options)=>{requests.push({url,options});return Promise.resolve({ok:true})}};
vm.createContext(context);
vm.runInContext(fs.readFileSync('frontend/js/collaboration.js','utf8').split('const collaborationClientId')[0],context);
(async()=>{
 await vm.runInContext("umlApiFetch('/api/generate',{method:'POST'})",context);
 assert.equal(requests[0].url,'http://127.0.0.1:8000/api/generate');
 configured='https://uml.example.test/';
 await vm.runInContext("umlApiFetch('/api/collaboration/demo/invite',{method:'POST'})",context);
 assert.equal(requests[1].url,'https://uml.example.test/api/collaboration/demo/invite');
 context.location={host:'localhost:8765',protocol:'http:',origin:'http://localhost:8765'};
 await vm.runInContext("umlApiFetch('/api/export/xmi')",context);
 assert.equal(requests[2].url,'http://localhost:8765/api/export/xmi');
 context.location={host:'appassets.androidplatform.net',protocol:'https:'};configured='javascript:alert(1)';
 assert.throws(()=>vm.runInContext('umlBackendOrigin()',context));
 console.log('Rutas API: Android, servidor configurado y navegador correctos.');
})().catch(e=>{console.error(e);process.exit(1)});
