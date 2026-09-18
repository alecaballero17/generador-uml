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
        const types={texto:'String',cadena:'String',string:'String',entero:'Integer',integer:'Integer',int:'Integer',long:'Long',decimal:'Double',double:'Double',booleano:'Boolean',boolean:'Boolean',bool:'Boolean',fecha:'LocalDate',localdate:'LocalDate'};
        const parts=text.replace(/\s+y\s+/gi,',').split(/[,;]/).map(s=>s.trim()).filter(Boolean);
        const result=parts.map(part=>{
            const match=part.match(/^(.+?)(?:\s+(?:de\s+)?tipo\s+|\s*:\s*)([a-z]+)$/i);
            const name=identifier(match?match[1]:part);
            const type=match?types[match[2].toLowerCase()]:name.toLowerCase()==='id'?'Long':'String';
            if (!type) throw new Error('Tipo no reconocido; usa texto, entero, decimal, booleano o fecha');
            return {name,type};
        });
        if(new Set(result.map(a=>a.name.toLowerCase())).size!==result.length) throw new Error('Hay atributos repetidos');
        return result;
    }
    function parse(text) {
        const clean=normalize(text).replace(/[.!?]+$/,'').replace(/\ba tributos\b/gi,'atributos');
        let match=clean.match(/^(?:por favor\s+)?(?:crear|crea|creame|creo|agrega|agregar)\s+(?:una\s+|la\s+)?clase\s+(?:llamada\s+)?(.+?)(?:\s+(?:que\s+tenga|con)\s+(?:los\s+)?(?:atributos?\s+)?(.+))?$/i);
        if(match) return {action:'createClass',name:identifier(match[1],true),attributes:attributes(match[2])};
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
