const assert=require('node:assert/strict');
const parser=require('../frontend/js/uml-commands.js');
assert.deepEqual(parser.parse('Créame una clase Usuario con atributos ID, nombre de tipo texto y edad de tipo entero'),{action:'createClass',name:'Usuario',attributes:[{name:'id',type:'Long'},{name:'nombre',type:'String'},{name:'edad',type:'Integer'}]});
assert.equal(parser.parse('crea una clase OrdenCompra').name,'OrdenCompra');
assert.equal(parser.parse('agrega atributo fechaNacimiento de tipo fecha a clase Usuario').attributes[0].type,'LocalDate');
assert.throws(()=>parser.parse('hola como estas'));
assert.throws(()=>parser.parse('crea clase Usuario con atributos nombre, nombre'));


assert.equal(parser.parse('Creo una clase cliente con a tributos nombre de tipo texto y edad de tipo entero.').attributes.length,2);

console.log('Comandos UML: 6 verificaciones correctas');
