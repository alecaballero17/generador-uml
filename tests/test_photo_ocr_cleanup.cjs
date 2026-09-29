const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('frontend/js/local-ai.js','utf8');
const ctx={};vm.createContext(ctx);
vm.runInContext(source.slice(source.indexOf('function photoEditDistance'),source.indexOf('async function photoCanvas')),ctx);

const merged='- amount : Doubl! - quantity : Intege\n- ff 4 1 4 30 BR ~AF\n+ calculateTotal()';
assert.equal(
  ctx.normalizePhotoOcrText(merged,'body'),
  '-amount: Double\n-quantity: Integer\n+calculateTotal()',
  'OCR cleanup must split merged UML members, repair one-character primitive OCR errors, and discard non-UML noise'
);
assert.equal(ctx.normalizePhotoOcrText('Catalog Item','name'),'Catalog Item');
assert.equal(ctx.normalizePhotoOcrText('| ---- |\n45 1 !','body'),'');
assert.equal(
  ctx.normalizePhotoOcrText('[ - amount: Double J','body'),
  '-amount: Double',
  'a valid member must survive an OCR border artifact after its type'
);
assert.equal(
  ctx.normalizePhotoLooseMember('[___balance Doubls ]'),
  '-balance: Double',
  'a non-header band with erased UML punctuation must retain its identifier and recognizable type'
);
assert.equal(ctx.normalizePhotoLooseMember('+ total()'),'', 'operations must not be mistaken for punctuation-damaged attributes');
assert.equal(
  ctx.normalizePhotoOcrText('+ find(code: Long): String','body'),
  '+find(code: Long): String',
  'operation signature must survive cleanup'
);
const compactOcr='NombreClase\n-atributo: String\n-otro: Double';
assert.equal(ctx.countStructuredPhotoBlocks(compactOcr),1,'a clean unboxed OCR class must be reported as structured');
const fallbackBands=ctx.normalizePhotoBandReadings(['Receipt','- number: String','+ total(): Double'],'mixed');
assert.equal(fallbackBands.name,'Receipt','ordered text bands must preserve the class name when divider rules are faint');
assert.equal(fallbackBands.body,'-number: String\n+total(): Double','ordered text bands must preserve UML members when divider rules are faint');

// Feed cleaned OCR through the same parser and model builder used by the UI.
const modelCtx={crypto:require('crypto').webcrypto,document:{getElementById(){return null}},collaborationState:{role:'admin'},saveUndo(){},renderAll(){},persistCollaboration(){},broadcastChange(){},refreshMobileCards(){}};
vm.createContext(modelCtx);
vm.runInContext(fs.readFileSync('frontend/js/uml-commands.js','utf8'),modelCtx);
vm.runInContext(fs.readFileSync('frontend/js/app.js','utf8').split('const state =')[0]+'const state={model:new UMLModel()};',modelCtx);
vm.runInContext(source.slice(source.indexOf('function photoEditDistance'),source.indexOf('async function photoCanvas')),modelCtx);
const mobile=fs.readFileSync('frontend/js/mobile.js','utf8');
vm.runInContext(mobile.slice(mobile.indexOf('function preparePhotoImport'),mobile.indexOf('function openMobileForm')),modelCtx);
const first=modelCtx.normalizePhotoOcrText('- amount : Doubl!\n+ calculateTotal()','body');
const second=modelCtx.normalizePhotoOcrText('# code : Long','body');
const diagram=modelCtx.buildPhotoDiagram(`CatalogItem\n${first}\n\nCustomer\n${second}`);
assert.equal(diagram.classes.length,2,'multiple OCR blocks must become multiple classes');
assert.equal(diagram.classes[0].attributes[0].type,'Double','typed attribute must reach UMLModel');
assert.equal(diagram.classes[0].attributes[0].visibility,'-','attribute visibility must reach UMLModel');
assert.equal(diagram.classes[0].operations[0].name,'calculateTotal','operation must reach UMLModel');
assert.equal(diagram.classes[1].attributes[0].visibility,'#','all UML visibilities remain parseable');
const imported=modelCtx.preparePhotoImport(compactOcr);
assert.equal(imported.classes.length,1,'compact visibility syntax must import as one UML class');
assert.equal(imported.classes[0].attributes.length,2,'compact visibility syntax must preserve both attributes');
console.log('Photo OCR cleanup: structured UML lines preserved and border noise rejected.');
