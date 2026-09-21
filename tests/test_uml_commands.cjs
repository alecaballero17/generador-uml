const assert=require('node:assert/strict');
const parser=require('../frontend/js/uml-commands.js');
assert.deepEqual(parser.parse('Créame una clase Usuario con atributos ID, nombre de tipo texto y edad de tipo entero'),{action:'createClass',name:'Usuario',attributes:[{name:'id',type:'Long'},{name:'nombre',type:'String'},{name:'edad',type:'Integer'}]});
assert.equal(parser.parse('crea una clase OrdenCompra').name,'OrdenCompra');
assert.equal(parser.parse('agrega atributo fechaNacimiento de tipo fecha a clase Usuario').attributes[0].type,'LocalDate');
assert.throws(()=>parser.parse('hola como estas'));
assert.throws(()=>parser.parse('crea clase Usuario con atributos nombre, nombre'));


assert.equal(parser.parse('crea una gran Persona con atributo nombre de tipo texto y edad de tipo entero').name,'Persona');
assert.equal(parser.parse('crea clase Usuario con atributo id de tipo id').attributes[0].type,'Long');
assert.equal(parser.attributes('código: texto, precio: decimal')[0].name,'codigo');
assert.equal(parser.attributes('código: texto, precio: decimal')[1].name,'precio');



assert.throws(()=>parser.parse('Creo una clase usuario con híde nombre y teléfono.'));
assert.throws(()=>parser.parse('Crea una clase Usuario con id, nombre y telefono'));

assert.deepEqual(parser.parse('Agregá el atributo correo a la clase Usuario'),{action:'addAttributes',name:'Usuario',attributes:[{name:'correo',type:'String'}]});
assert.deepEqual(parser.parse('A la clase Usuario agregale el atributo dirección'),{action:'addAttributes',name:'Usuario',attributes:[{name:'direccion',type:'String'}]});
assert.deepEqual(parser.parse('Clase Usuario, agregale el atributo apellido'),{action:'addAttributes',name:'Usuario',attributes:[{name:'apellido',type:'String'}]});
assert.equal(parser.attributes('apellido')[0].type,'String');
assert.equal(parser.attributes('id')[0].type,'Long');
assert.throws(()=>parser.parse('agregale correo'));

// Tests de relaciones UML offline
assert.deepEqual(parser.parse('Perro hereda de Animal'), {
    action: 'addRelationship', source: 'Perro', target: 'Animal', type: 'generalization'
});
assert.deepEqual(parser.parse('crear herencia entre Perro y Animal'), {
    action: 'addRelationship', source: 'Perro', target: 'Animal', type: 'generalization'
});
assert.deepEqual(parser.parse('crear relacion de composicion entre Cliente y Mascota'), {
    action: 'addRelationship', source: 'Cliente', target: 'Mascota', type: 'composition'
});
assert.deepEqual(parser.parse('crear relacion de agregacion entre Departamento y Empleado'), {
    action: 'addRelationship', source: 'Departamento', target: 'Empleado', type: 'aggregation'
});
assert.deepEqual(parser.parse('relacionar Cliente con Pedido'), {
    action: 'addRelationship', source: 'Cliente', target: 'Pedido', type: 'association'
});
assert.deepEqual(parser.parse('relacionar Factura con Cliente de tipo composicion'), {
    action: 'addRelationship', source: 'Factura', target: 'Cliente', type: 'composition'
});
assert.deepEqual(parser.parse('Documento implementa Exportable'), {
    action: 'addRelationship', source: 'Documento', target: 'Exportable', type: 'realization'
});
assert.deepEqual(parser.parse('agrega el metodo calcularTotal a la clase Factura'), {
    action: 'addOperation', name: 'Factura', operation: { name: 'calcularTotal', visibility: '+', returnType: 'void', parameters: [] }
});
assert.deepEqual(parser.parse('agrega la operacion pagar(monto: Double): Boolean a Pedido'), {
    action: 'addOperation', name: 'Pedido', operation: { name: 'pagar', visibility: '+', returnType: 'Boolean', parameters: [{ name: 'monto', type: 'Double' }] }
});
assert.deepEqual(parser.parse('A la clase Factura agregale el metodo anular'), {
    action: 'addOperation', name: 'Factura', operation: { name: 'anular', visibility: '+', returnType: 'void', parameters: [] }
});
assert.deepEqual(parser.parse('renombra la clase Factura a Recibo'), {
    action: 'renameClass', oldName: 'Factura', newName: 'Recibo'
});
assert.deepEqual(parser.parse('elimina el metodo anular de la clase Factura'), {
    action: 'deleteOperation', name: 'Factura', operationName: 'anular'
});
assert.deepEqual(parser.parse('crear interfaz Exportable'), {
    action: 'createClass', name: 'Exportable', isInterface: true, attributes: []
});
assert.deepEqual(parser.parse('crear clase abstracta Figura con atributo color de tipo texto'), {
    action: 'createClass', name: 'Figura', isAbstract: true, attributes: [{ name: 'color', type: 'String' }]
});
assert.deepEqual(parser.parse('elimina el atributo telefono de la clase Usuario'), {
    action: 'removeAttribute', name: 'Usuario', attributeName: 'telefono'
});
assert.deepEqual(parser.parse('elimina la relacion entre Cliente y Mascota'), {
    action: 'deleteRelationship', source: 'Cliente', target: 'Mascota'
});

console.log('Comandos UML: todas las verificaciones pasaron.');


