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

        const classFirstOp = clean.match(/^(?:a\s+)?(?:la\s+)?clase\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*,?\s+(?:agregale|agrega|anadele|anade)\s+(?:el\s+|la\s+)?(?:metodo|operacion)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\(([^()]*)\))?(?:\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\[\])?))?$/i);
        if (classFirstOp) {
            const rawParams = classFirstOp[3] || '';
            const parameters = rawParams.trim() ? rawParams.split(',').map(raw => {
                const pMatch = raw.trim().match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*(?::\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\[\])?))?$/);
                if (!pMatch) throw new Error('Parámetro inválido; usa nombre: Tipo');
                return { name: identifier(pMatch[1]), type: pMatch[2] || 'String' };
            }) : [];
            if (new Set(parameters.map(p => p.name.toLowerCase())).size !== parameters.length) throw new Error('Parámetros repetidos en el método');
            return {
                action: 'addOperation',
                name: identifier(classFirstOp[1], true),
                operation: {
                    name: identifier(classFirstOp[2]),
                    visibility: '+',
                    returnType: classFirstOp[4] || 'void',
                    parameters
                }
            };
        }

        // Relaciones entre clases
        const relTypeMap = {
            composicion: 'composition',
            agregacion: 'aggregation',
            asociacion: 'association',
            herencia: 'generalization',
            realizacion: 'realization',
            dependencia: 'dependency'
        };

        // 1. Herencia: "Perro hereda de Animal" o "crear herencia entre Perro y Animal"
        const inhMatch = clean.match(/^(?:(?:crear|agregar)\s+)?(?:una\s+)?herencia\s+(?:entre|de)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:y|a|hacia)\s+([a-zA-Z_][a-zA-Z0-9_]*)$/i) ||
                         clean.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s+hereda\s+de\s+([a-zA-Z_][a-zA-Z0-9_]*)$/i);
        if (inhMatch) {
            const src = inhMatch[1];
            const tgt = inhMatch[2];
            return { action: 'addRelationship', source: identifier(src, true), target: identifier(tgt, true), type: 'generalization' };
        }

        // 2. Realización: "Documento implementa Exportable" o "crear realizacion entre Documento y Exportable"
        const realMatch = clean.match(/^(?:(?:crear|agregar)\s+)?(?:una\s+)?realizacion\s+(?:entre|de)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:y|a)\s+([a-zA-Z_][a-zA-Z0-9_]*)$/i) ||
                          clean.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s+implementa\s+(?:a\s+)?(?:la\s+)?(?:interfaz\s+)?([a-zA-Z_][a-zA-Z0-9_]*)$/i);
        if (realMatch) {
            const src = realMatch[1];
            const tgt = realMatch[2];
            return { action: 'addRelationship', source: identifier(src, true), target: identifier(tgt, true), type: 'realization' };
        }

        // 3. Relación tipada: "crear relacion de composicion entre Cliente y Mascota"
        const typedRelMatch = clean.match(/^(?:crear|agregar)\s+(?:una\s+)?relacion\s+(?:de\s+)?(composicion|agregacion|asociacion|dependencia)\s+entre\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+y\s+([a-zA-Z_][a-zA-Z0-9_]*)$/i);
        if (typedRelMatch) {
            const type = relTypeMap[typedRelMatch[1].toLowerCase()] || 'association';
            return { action: 'addRelationship', source: identifier(typedRelMatch[2], true), target: identifier(typedRelMatch[3], true), type };
        }

        // 4. Relación genérica o conectar: "relacionar Cliente con Pedido [de tipo composicion]" o "conectar Factura con Cliente"
        const connMatch = clean.match(/^(?:relacionar|conectar)\s+(?:a\s+)?(?:la\s+clase\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s+con\s+(?:la\s+clase\s+)?([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+(?:con|de\s+tipo)\s+(composicion|agregacion|asociacion|herencia|realizacion|dependencia))?$/i);
        if (connMatch) {
            const type = connMatch[3] ? (relTypeMap[connMatch[3].toLowerCase()] || 'association') : 'association';
            return { action: 'addRelationship', source: identifier(connMatch[1], true), target: identifier(connMatch[2], true), type };
        }

        // 5. "crear relacion entre Cliente y Pedido"
        const simpleRelMatch = clean.match(/^(?:crear|agregar)\s+(?:una\s+)?relacion\s+entre\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+y\s+([a-zA-Z_][a-zA-Z0-9_]*)$/i);
        if (simpleRelMatch) {
            return { action: 'addRelationship', source: identifier(simpleRelMatch[1], true), target: identifier(simpleRelMatch[2], true), type: 'association' };
        }

        let ifaceMatch = clean.match(/^(?:por favor\s+)?(?:quiero\s+(?:crear|una)|necesito\s+(?:crear|una)|crear|crea|creame|agrega|agregar|nueva)?\s*(?:una\s+|la\s+)?interfaz\s+(?:llamada\s+)?([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+(?:con|que\s+tenga)\s+(?:metodos?|operaciones?)\s*(.*))?$/i);
        if (ifaceMatch) {
            return {
                action: 'createClass',
                name: identifier(ifaceMatch[1], true),
                isInterface: true,
                attributes: []
            };
        }

        let abstractMatch = clean.match(/^(?:por favor\s+)?(?:quiero\s+(?:crear|una)|necesito\s+(?:crear|una)|crear|crea|creame|agrega|agregar|nueva)?\s*(?:una\s+|la\s+)?clase\s+abstracta\s+(?:llamada\s+)?(.+?)(?:\s+(?:que\s+tenga|con)\s+(?:los\s+|las\s+|el\s+|la\s+)?(?:atributos?|campos?|propiedades?)\s*(.*))?$/i);
        if (abstractMatch) {
            return {
                action: 'createClass',
                name: identifier(abstractMatch[1], true),
                isAbstract: true,
                attributes: attributes(abstractMatch[2])
            };
        }

        let match=clean.match(/^(?:por favor\s+)?(?:quiero\s+(?:crear|una)|necesito\s+(?:crear|una)|creo\s+que\s+es|crear|crea|creame|creo|agrega|agregar|haz|genera|generar|nueva)?\s*(?:una\s+|la\s+|el\s+)?clase\s+(?:llamada\s+)?(.+?)(?:\s+(?:que\s+tenga|con)\s+(?:los\s+|las\s+|el\s+|la\s+)?(?:atributos?|campos?|propiedades?)\s*(.*))?$/i);
        if(match) {
            if(/\b(?:con|tenga|atributos?|campos?)\b/i.test(match[1]))throw new Error('No pude separar el nombre de la clase de sus atributos. Usa: Usuario con atributos id, nombre y telefono.');
            return {action:'createClass',name:identifier(match[1],true),attributes:attributes(match[2])};
        }
        match=clean.match(/^(?:agrega|agregar|anade|anadir)\s+(?:el\s+|los\s+)?atributos?\s+(.+?)\s+(?:a|en)\s+(?:la\s+)?clase\s+(.+)$/i);
        if(match) return {action:'addAttributes',name:identifier(match[2],true),attributes:attributes(match[1])};
        match=clean.match(/^(?:agrega|agregar|anade|anadir)\s+(?:el\s+|la\s+)?(?:metodo|operacion)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\(([^()]*)\))?(?:\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\[\])?))?\s+(?:a|en)\s+(?:la\s+)?(?:clase\s+)?([a-zA-Z_][a-zA-Z0-9_]*)$/i);
        if(match) {
            const rawParams = match[2] || '';
            const parameters = rawParams.trim() ? rawParams.split(',').map(raw => {
                const pMatch = raw.trim().match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*(?::\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\[\])?))?$/);
                if (!pMatch) throw new Error('Parámetro inválido; usa nombre: Tipo');
                return { name: identifier(pMatch[1]), type: pMatch[2] || 'String' };
            }) : [];
            if (new Set(parameters.map(p => p.name.toLowerCase())).size !== parameters.length) throw new Error('Parámetros repetidos en el método');
            return {
                action: 'addOperation',
                name: identifier(match[4], true),
                operation: {
                    name: identifier(match[1]),
                    visibility: '+',
                    returnType: match[3] || 'void',
                    parameters
                }
            };
        }
        match=clean.match(/^(?:renombra|renombrar|cambia el nombre de|cambiar el nombre de)\s+(?:la\s+)?(?:clase\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:a|por)\s+([a-zA-Z_][a-zA-Z0-9_]*)$/i);
        if(match) return {action:'renameClass',oldName:identifier(match[1],true),newName:identifier(match[2],true)};
        match=clean.match(/^(?:elimina|eliminar|borra|borrar)\s+(?:el\s+|la\s+)?(?:metodo|operacion)\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\(\))?\s+(?:de|en)\s+(?:la\s+)?(?:clase\s+)?([a-zA-Z_][a-zA-Z0-9_]*)$/i);
        if(match) return {action:'deleteOperation',name:identifier(match[2],true),operationName:identifier(match[1])};
        match=clean.match(/^(?:elimina|eliminar|borra|borrar)\s+(?:el\s+)?atributo\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:de|en)\s+(?:la\s+)?(?:clase\s+)?([a-zA-Z_][a-zA-Z0-9_]*)$/i);
        if(match) return {action:'removeAttribute',name:identifier(match[2],true),attributeName:identifier(match[1])};
        match=clean.match(/^(?:elimina|eliminar|borra|borrar)\s+(?:la\s+)?relacion\s+(?:de\s+[a-zA-Z_]+\s+)?entre\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+y\s+([a-zA-Z_][a-zA-Z0-9_]*)$/i);
        if(match) return {action:'deleteRelationship',source:identifier(match[1],true),target:identifier(match[2],true)};
        match=clean.match(/^(?:elimina|eliminar|borra|borrar)\s+(?:la\s+)?clase\s+(.+)$/i);
        if(match) return {action:'deleteClass',name:identifier(match[1],true)};
        throw new Error('Prueba: Crea una clase Usuario con atributos id, nombre de tipo texto y edad de tipo entero');
    }
    const api={parse,identifier,attributes};
    if(typeof module!=='undefined') module.exports=api;
    root.UMLCommands=api;
})(typeof window==='undefined'?globalThis:window);
