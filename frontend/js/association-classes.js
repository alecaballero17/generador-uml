/* Association classes stay explicit on the canvas; generators lower the links. */
function associationClassCandidate(model, classId) {
    const cls=model.getClass(classId);
    if(!cls||cls.isAbstract||cls.isInterface||model.relationships.some(r=>r.associationClassId===classId))return null;
    const links=model.relationships.filter(r=>r.source.classId===classId||r.target.classId===classId);
    if(links.length!==2)return null;
    const ends=links.map(r=>({rel:r,parent:r.source.classId===classId?r.target:r.source,detail:r.source.classId===classId?r.source:r.target}));
    if(ends.some(e=>e.rel.type!=='association'||e.rel.associationClassId||e.parent.multiplicity!=='1'||!['*','0..*','1..*'].includes(e.detail.multiplicity))||ends[0].parent.classId===ends[1].parent.classId)return null;
    return {type:'association',source:ends[0].parent.classId,target:ends[1].parent.classId,
        sourceMult:ends[1].detail.multiplicity,targetMult:ends[0].detail.multiplicity,
        associationClassId:classId,replaceRelationshipIds:links.map(r=>r.id)};
}

document.getElementById('btnAssociationClass')?.addEventListener('click',()=>{
    const candidate=associationClassCandidate(state.model,state.selectedId);
    if(!candidate){showToast('Selecciona una clase intermedia con dos asociaciones: 1 en cada clase principal y muchos en la intermedia.','info');return;}
    openMobileRelationship(candidate);
});
