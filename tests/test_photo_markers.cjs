const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const ctx={};vm.createContext(ctx);const source=fs.readFileSync('frontend/js/local-ai.js','utf8');vm.runInContext(source.slice(source.indexOf('function detectPhotoMarkers'),source.indexOf('async function photoCanvas')),ctx);
const width=120,height=100,data=new Uint8ClampedArray(width*height*4).fill(255);
for(let y=0;y<height;y++)for(let x=0;x<width;x++){const distance=Math.abs(x-70)+Math.abs(y-40);if(distance>=10&&distance<=13){const i=(y*width+x)*4;data[i]=data[i+1]=data[i+2]=0;}}
const boxes=[{x:10,y:10,width:40,height:70}];const result=ctx.detectPhotoMarkers({width,height,data},boxes);assert.equal(result.length,1);assert.equal(result[0].kind,'hollowDiamond');assert.equal(result[0].box,0);
assert.equal(ctx.detectPhotoMarkers({width,height,data},[{x:1,y:1,width:110,height:90}]).length,0,'Ignore shapes within class boxes');
assert.equal(ctx.detectPhotoMarkers({width,height,data},[]).length,0,'No class to anchor marker');
console.log('Hollow marker detection and exclusion checks passed.');
