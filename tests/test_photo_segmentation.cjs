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
const hints=ctx.detectPhotoConnections({width,height,data},boxes,[{kind:'hollowDiamond',box:0,x:145,y:75}]);
assert.equal(hints.suggestions.length,1);assert.equal(hints.suggestions[0].source,0);assert.equal(hints.suggestions[0].target,1);assert.equal(hints.suggestions[0].type,'aggregation');
assert.equal(ctx.detectPhotoConnections({width,height,data},boxes,[{kind:'hollowDiamond',box:0,x:10,y:280}]).suggestions.length,0,'Distant markers must not classify connections');
assert.equal(ctx.detectPhotoConnections({width,height,data},boxes,[{kind:'hollowTriangle',box:0,x:145,y:75}]).suggestions.length,0,'Triangle alone must not imply a solid inheritance line');

// One UML class: outer rectangle, two compartment dividers, three attributes
// and one operation.  The small H-like glyph must not become a second class.
const wide=620,tall=360,diagramPixels=new Uint8ClampedArray(wide*tall*4).fill(255);
const mark=(x,y)=>{const i=(y*wide+x)*4;diagramPixels[i]=diagramPixels[i+1]=diagramPixels[i+2]=0;};
const stroke=(x1,y1,x2,y2)=>{for(let y=y1;y<=y2;y++)for(let x=x1;x<=x2;x++)mark(x,y);};
for(const y of [35,95,245,325])stroke(120,y,470,y+2);stroke(120,35,122,327);stroke(468,35,470,327);
// Text-like short marks in all three compartments; none spans the box width.
for(const [x,y] of [[175,60],[170,125],[170,160],[170,195],[170,275]]){stroke(x,y,x+30,y+3);stroke(x,y,x+2,y+22);stroke(x+28,y,x+30,y+22);}
// A closed, glyph-sized H-like shape inside the attributes compartment.
stroke(280,48,282,82);stroke(320,48,322,82);stroke(280,63,322,65);
const one=ctx.detectPhotoBoxes({width:wide,height:tall,data:diagramPixels});
assert.equal(one.length,1,'one UML box with compartments must not be split into glyph-sized classes');
assert(one[0].headerBottom>one[0].y&&one[0].attributesBottom>one[0].headerBottom,'compartment coordinates must remain ordered');
const cleaned=ctx.removePhotoRuleLines({width:wide,height:tall,data:diagramPixels.slice()});
const blackAt=(x,y)=>cleaned.data[(y*wide+x)*4]<128;
assert.equal(blackAt(300,35),false,'outer horizontal rule must be removed before OCR');
assert.equal(blackAt(281,63),true,'short text/glyph strokes must not be removed as UML rules');
const cleanedCanvas={width:wide,height:tall,getContext(){return {getImageData(){return cleaned;}}}};
assert.equal(ctx.photoTextBands(cleanedCanvas).length,5,'name, three attributes and one operation must remain as separate OCR bands');

// Structural variants use only proportional geometry.  They deliberately
// contain no class-name or UML-member text, so these assertions cannot pass by
// recognizing a fixture's wording.
function geometricClass({scale=1,dividers=[],nearFullText=false,brokenBorders=false,brokenHorizontal=false}={}) {
    const imageWidth=1000,imageHeight=700,pixels=new Uint8ClampedArray(imageWidth*imageHeight*4).fill(255);
    const dot=(x,y)=>{const i=(y*imageWidth+x)*4;pixels[i]=pixels[i+1]=pixels[i+2]=0;};
    const rule=(x1,y1,x2,y2)=>{for(let y=Math.round(y1);y<=Math.round(y2);y++)for(let x=Math.round(x1);x<=Math.round(x2);x++)dot(x,y);};
    const x=Math.round(150*scale),y=Math.round(90*scale),boxWidth=Math.round(440*scale),boxHeight=Math.round(420*scale),right=x+boxWidth,bottom=y+boxHeight;
    if(brokenHorizontal) {
        // Larger than the old 2.5% tolerance but below the bounded 6% bridge
        // used for photograph-like pen lifts in an exterior border.
        const gap=Math.max(4,Math.round(imageWidth*.045)),middle=Math.round((x+right)/2);
        for(const row of [y,bottom]){rule(x,row,middle-Math.ceil(gap/2),row+2);rule(middle+Math.floor(gap/2),row,right,row+2);}
    } else {rule(x,y,right,y+2);rule(x,bottom,right,bottom+2);}
    if(brokenBorders) {
        // Camera noise can leave short holes in a vertical outline. The gaps
        // are small relative to the overall side, not fixed image positions.
        const segment=Math.max(10,Math.round(boxHeight*.07)),gap=Math.max(2,Math.round(boxHeight*.015));
        for(let top=y;top<=bottom;top+=segment+gap){const end=Math.min(bottom,top+segment);rule(x,top,x+2,end);rule(right-2,top,right,end);}
    } else {rule(x,y,x+2,bottom+2);rule(right-2,y,right,bottom+2);}
    for(const fraction of dividers){const row=Math.round(y+boxHeight*fraction);rule(x,row,right,row+2);}
    if(nearFullText) {
        // A long underline/text stroke is intentionally close to a divider,
        // but it stops short of both sides and must not split a compartment.
        const row=Math.round(y+boxHeight*.46);rule(x+Math.round(boxWidth*.06),row,right-Math.round(boxWidth*.06),row+2);
    }
    return {imageWidth,imageHeight,pixels,expected:dividers.length};
}
for(const variant of [
    geometricClass({scale:.55,dividers:[]}),
    geometricClass({scale:.8,dividers:[.38]}),
    geometricClass({scale:1.25,dividers:[.24,.72]}),
    geometricClass({scale:1,dividers:[.28,.74],nearFullText:true}),
    geometricClass({scale:1.1,dividers:[.26,.71],brokenBorders:true}),
    geometricClass({scale:1.1,dividers:[.26,.71],brokenHorizontal:true})
]) {
    const found=ctx.detectPhotoBoxes({width:variant.imageWidth,height:variant.imageHeight,data:variant.pixels});
    assert.equal(found.length,1,'a single rectangular UML class must remain one box at every tested scale');
    assert.equal(found[0].dividerYs.length,variant.expected,'only full-width rules attached to both class borders are compartment dividers');
    assert(found[0].dividerYs.every((row,index,all)=>index===0||row>all[index-1]),'dividers must be ordered geometrically');
}
console.log('Photo segmentation: zero, one and two compartments, near-full text stroke and broken borders passed');
