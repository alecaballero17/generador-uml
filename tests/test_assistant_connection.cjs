const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('frontend/js/conversational-assistant.js','utf8');
let timeout,cleared=0,calls=[];
const ctx={AbortController,navigator:{onLine:true},window:{location:{host:'localhost',protocol:'http:',origin:'http://localhost'}},localStorage:{getItem:()=>null},setTimeout(fn){timeout=fn;return 1},clearTimeout(){cleared++},fetch:async(url,options)=>{calls.push(url);return {ok:true}}};
vm.createContext(ctx);
vm.runInContext(source.slice(source.indexOf('    async function backendFetch('),source.indexOf('    // ─── Visualizador')),ctx);
(async()=>{
 await ctx.backendFetch('/api/assistant/converse');
 assert.deepEqual(calls,['http://localhost/api/assistant/converse']);assert.equal(cleared,1);
 ctx.umlBackendOrigin=()=> 'https://configured.example';
 await ctx.backendFetch('/api/assistant/converse');assert.equal(calls.at(-1),'https://configured.example/api/assistant/converse');
 ctx.fetch=(url,{signal})=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(Error('timeout'))));
 const pending=ctx.backendFetch('/api/assistant/converse');timeout();await assert.rejects(pending,/timeout/);assert.equal(cleared,3);
 ctx.navigator.onLine=false;await assert.rejects(ctx.backendFetch('/api/assistant/converse'),/Sin conexión/);
 ctx.navigator.onLine=true;delete ctx.umlBackendOrigin;ctx.window.location={host:'appassets.androidplatform.net',protocol:'https:',origin:'https://appassets.androidplatform.net'};
 await assert.rejects(ctx.backendFetch('/api/assistant/converse'),/Configura/);
 assert.equal(calls.length,2,'No probes of fallback hosts');
 console.log('Assistant connection: configured origin, bounded web requests and offline/missing configuration handled.');
})().catch(error=>{console.error(error);process.exitCode=1});
