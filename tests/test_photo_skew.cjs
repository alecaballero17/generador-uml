const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('frontend/js/local-ai.js','utf8'),ctx={};vm.createContext(ctx);
vm.runInContext(source.slice(source.indexOf('function estimatePhotoSkew'),source.indexOf('async function photoCanvas')),ctx);
function fixture(degrees){
 const width=400,height=320,data=new Uint8ClampedArray(width*height*4).fill(255);
 const a=degrees*Math.PI/180;
 function pixel(x,y){const xx=Math.round(200+(x-200)*Math.cos(a)-(y-160)*Math.sin(a)),yy=Math.round(160+(x-200)*Math.sin(a)+(y-160)*Math.cos(a));if(xx>=0&&yy>=0&&xx<width&&yy<height){const i=(yy*width+xx)*4;data[i]=data[i+1]=data[i+2]=0;}}
 for(const [left,top] of [[40,45],[220,155]]){
  for(const dy of [0,25,60,100])for(let x=left;x<left+130;x++)for(let t=0;t<2;t++)pixel(x,top+dy+t);
  for(let y=top;y<top+102;y++){pixel(left,y);pixel(left+129,y);}
 }
 return {width,height,data};
}
for(const angle of [-10,-5,0,4,11])assert(Math.abs(ctx.estimatePhotoSkew(fixture(angle))-angle)<=0.5,`angle ${angle}`);
assert.equal(ctx.estimatePhotoSkew({width:100,height:100,data:new Uint8ClampedArray(40000).fill(255)}),0);
console.log('Local photo skew: both directions, aligned diagram and blank image passed.');
