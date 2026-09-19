const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const ctx={};vm.createContext(ctx);
const source=fs.readFileSync('frontend/js/local-ai.js','utf8');
vm.runInContext(source.slice(source.indexOf('function detectPhotoBoxes'),source.indexOf('async function photoCanvas')),ctx);
const width=400,height=300,data=new Uint8ClampedArray(width*height*4).fill(255);
const pixel=(x,y)=>{const i=(y*width+x)*4;data[i]=data[i+1]=data[i+2]=0;};
const line=(x1,y1,x2,y2)=>{for(let y=y1;y<=y2;y++)for(let x=x1;x<=x2;x++)pixel(x,y);};
assert.equal(ctx.detectPhotoBoxes({width,height,data}).length,0);
for(const [x,y] of [[20,20],[230,120]]){for(const dy of [0,25,70,110])line(x,y+dy,x+120,y+dy+2);line(x,y,x+2,y+112);line(x+118,y,x+120,y+112);}
line(140,75,180,77);line(178,75,180,175);line(180,173,230,175); // connector must not merge the two boxes
const boxes=ctx.detectPhotoBoxes({width,height,data});assert.equal(boxes.length,2);assert.ok(boxes.every(b=>b.headerBottom>b.y&&b.attributesBottom>b.headerBottom));
console.log('Photo segmentation: blank image and connected class boxes passed');

const links=ctx.detectPhotoConnections({width,height,data},boxes);assert.equal(links.connections.length,1);assert.equal(links.ambiguous.length,0);
