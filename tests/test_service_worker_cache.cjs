const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const events={},deleted=[];let claimed=false;
const ctx={URL,location:{origin:'https://uml.test'},fetch:async()=>{throw Error('offline')},self:{addEventListener:(name,fn)=>events[name]=fn,clients:{claim(){claimed=true}}},caches:{keys:async()=>['uml-shell-v2','uml-shell-v3','uml-shell-v4','uml-local-ai-v1','transformers-cache','other-app'],delete:async name=>{deleted.push(name);return true},open:async()=>({match:async()=> 'current code'}),match:async()=> 'obsolete code'}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('frontend/sw.js','utf8'),ctx);
(async()=>{
 let pending;events.activate({waitUntil:p=>pending=p});await pending;
 assert.deepEqual(deleted,['uml-shell-v2','uml-shell-v3']);assert(claimed);
 let response;events.fetch({request:{url:'https://uml.test/js/app.js',method:'GET'},respondWith:p=>response=p});
 assert.equal(await response,'current code');
 console.log('Service worker update preserves offline models and unrelated caches; only old shells removed.');
})().catch(error=>{console.error(error);process.exitCode=1});
