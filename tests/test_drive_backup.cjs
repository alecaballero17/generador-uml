const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
let status=200,bodySent;
const ctx={Blob,crypto,AbortSignal,document:{getElementById:()=>null},
    fetch:async(url,options)=>{
        assert(url.startsWith('https://www.googleapis.com/upload/drive/v3/files?'));
        assert.equal(options.headers.Authorization,'Bearer ephemeral-token');
        bodySent=await options.body.text();
        assert(!bodySent.includes('ephemeral-token'));
        return {ok:status===200,status,json:async()=>({id:'file123'})};
    }};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('frontend/js/drive-backup.js','utf8'),ctx);
(async()=>{
    const diagram={name:'Ventas / prueba',classes:[{id:'c1',name:'Venta'}],relationships:[]};
    const backup=ctx.driveBackupFile(diagram);
    assert(backup.name.endsWith('.json'));assert(!backup.name.includes('/'));
    assert.deepEqual(JSON.parse(await backup.file.text()),diagram);
    const result=await ctx.uploadDiagramToDrive(backup,'ephemeral-token');
    assert.equal(result.id,'file123');assert(bodySent.includes('Content-Type: application/json'));
    assert(/"name":\s*"Venta"/.test(bodySent));assert(bodySent.includes('"mimeType":"application/json"'));
    status=403;await assert.rejects(ctx.uploadDiagramToDrive(backup,'ephemeral-token'),/Google no permitió/);
    status=401;await assert.rejects(ctx.uploadDiagramToDrive(backup,'ephemeral-token'),/autorización venció/);
    assert.throws(()=>ctx.driveBackupFile({name:'Grande',classes:['x'.repeat(6*1024*1024)]}),/supera 5 MB/);
    console.log('Drive: respaldo UML editable, multipart, token fuera del archivo y errores de permisos: OK.');
})().catch(error=>{console.error(error);process.exitCode=1;});
