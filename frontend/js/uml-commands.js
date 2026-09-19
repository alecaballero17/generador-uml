(function(root) {
    const normalize = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim();
    function identifier(text,pascal=false) {
        const words=normalize(text).replace(/[^a-zA-Z0-9_ ]/g,' ').trim().split(/\s+/);
        let name=words.map((word,i)=>i===0&&!pascal ? word.charAt(0).toLowerCase()+word.slice(1) : word.charAt(0).toUpperCase()+word.slice(1)).join('');
        if (name.toLowerCase()==='id'&&!pascal)name='id';
        if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) throw new Error('El nombre debe comenzar con una letra');
        if (/^(class|interface|void|public|private|static|return|new|final|enum|extends|implements)$/i.test(name)) throw new Error('Ese nombre está reservado por el lenguaje');
        return name;
    }
    function attributes(text) {
        if (!text?.trim()) return [];
        const types={
            texto:'String',cadena:'String',string:'String',text:'String',
            entero:'Integer',integer:'Integer',int:'Integer',numero:'Integer',
            long:'Long',id:'Long',ide:'Long',identificador:'Long',
            decimal:'Double',double:'Double',flotante:'Double',float:'Double',
            booleano:'Boolean',boolean:'Boolean',bool:'Boolean',
            fecha:'LocalDate',localdate:'LocalDate',date:'LocalDate'
        };
        const defaultNames={
            Integer:'edad',
            Long:'id',
            String:'descripcion',
            Double:'monto',
            Boolean:'activo',
            LocalDate:'fecha'
        };
        const parts=text.replace(/\s+y\s+/gi,',').split(/[,;]/).map(s=>s.trim()).filter(Boolean);
        const result=parts.map((part,index)=>{
            let match=part.match(/^(?:(.+?)(?:\s+(?:de\s+)?tipo\s+|\s*:\s*))([a-z]+)$/i);
            let rawName, typeKey;
            if(match) {
                rawName=match[1].trim();
                typeKey=match[2].toLowerCase();
                if(/^(de|del)$/i.test(rawName)) rawName=null;
            } else {
                match=part.match(/^(?:de\s+tipo\s+|:\s*)([a-z]+)$/i);
                if(match) { typeKey=match[1].toLowerCase(); rawName=null; }
                else { rawName=part.trim(); typeKey=null; }
            }
            let type=typeKey&&types[typeKey]?types[typeKey]:(/^(?:id|identificador)$/i.test(part.trim())?'Long':'String');
            if(!rawName) {
                if(!match&&!types[part.trim().toLowerCase()]) {
                    rawName=part.trim();
                } else {
                    rawName=defaultNames[type]||('atributo'+(index+1));
                }
            }
            const name=identifier(rawName);
            return {name,type};
        });
        if(new Set(result.map(a=>a.name.toLowerCase())).size!==result.length) throw new Error('Hay atributos repetidos');
        return result;
    }
    function parse(text) {
        let clean=normalize(text).replace(/[.!?]+$/,'')
            .replace(/\b(?:la|el|los|las)?\s*tributos?\b/gi,'atributos')
            .replace(/\b(?:atrivutos|adributos)\b/gi,'atributos')
            .replace(/\b(?:una\s+)?gran\s+([a-zA-Z])/gi,'clase $1')
            .replace(/\b(?:i\s*de|i\s*d)\b/gi,'id')
            .replace(/\bde\s+tipo\s+ide\b/gi,'de tipo id');
        // Explicit class reference also supports the natural class-first ordering.
        const classFirst=clean.match(/^(?:a\s+)?(?:la\s+)?clase\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*,?\s+(?:agregale|agrega|anadele|anade)\s+(?:el\s+|los\s+)?atributos?\s+(.+)$/i);
        if(classFirst)return {action:'addAttributes',name:identifier(classFirst[1],true),attributes:attributes(classFirst[2])};
        let match=clean.match(/^(?:por favor\s+)?(?:quiero\s+(?:crear|una)|necesito\s+(?:crear|una)|creo\s+que\s+es|crear|crea|creame|creo|agrega|agregar|haz|genera|generar|nueva)?\s*(?:una\s+|la\s+|el\s+)?clase\s+(?:llamada\s+)?(.+?)(?:\s+(?:que\s+tenga|con)\s+(?:los\s+|las\s+|el\s+|la\s+)?(?:atributos?|campos?|propiedades?)\s*(.*))?$/i);
        if(match) {
            if(/\b(?:con|tenga|atributos?|campos?)\b/i.test(match[1]))throw new Error('No pude separar el nombre de la clase de sus atributos. Usa: Usuario con atributos id, nombre y telefono.');
            return {action:'createClass',name:identifier(match[1],true),attributes:attributes(match[2])};
        }
        match=clean.match(/^(?:agrega|agregar|anade|anadir)\s+(?:el\s+|los\s+)?atributos?\s+(.+?)\s+(?:a|en)\s+(?:la\s+)?clase\s+(.+)$/i);
        if(match) return {action:'addAttributes',name:identifier(match[2],true),attributes:attributes(match[1])};
        match=clean.match(/^(?:elimina|eliminar|borra|borrar)\s+(?:la\s+)?clase\s+(.+)$/i);
        if(match) return {action:'deleteClass',name:identifier(match[1],true)};
        throw new Error('Prueba: Crea una clase Usuario con atributos id, nombre de tipo texto y edad de tipo entero');
    }
    const api={parse,identifier,attributes};
    if(typeof module!=='undefined') module.exports=api;
    root.UMLCommands=api;
})(typeof window==='undefined'?globalThis:window);
