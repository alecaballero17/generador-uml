const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

// Extraer el modelo y las funciones de exportación de app.js
const appCode = fs.readFileSync('frontend/js/app.js', 'utf8');

const ctx = {
    console,
    crypto: require('crypto').webcrypto,
    URLSearchParams,
    location: { search: '', host: 'localhost' },
    localStorage: { getItem: () => null, setItem: () => {} },
    XMLSerializer: class {
        serializeToString(node) { return '<g id="diagramLayer"></g>'; }
    },
    document: {
        getElementById: () => null,
        querySelector: (sel) => {
            if (sel === '#diagramLayer') {
                return {
                    cloneNode: () => ({
                        setAttribute: () => {},
                        querySelectorAll: () => []
                    })
                };
            }
            return { addEventListener: () => {}, classList: { add: () => {}, remove: () => {} } };
        },
        querySelectorAll: () => [],
        addEventListener: () => {},
        body: { appendChild: () => {} }
    },
    window: {
        addEventListener: () => {}
    }
};

vm.createContext(ctx);

// Ejecutar clases y funciones antes de init()
vm.runInContext(appCode.split('function init()')[0], ctx);

// Construir un modelo con herencia, realización, composición, atributos y operaciones
const testScript = `
const model = new UMLModel();
model.name = 'SistemaVeterinario';

const persona = new UMLClassNode('Persona', 100, 50);
persona.isAbstract = true;
persona.addAttribute({ id: 'a1', name: 'id', type: 'Long', visibility: '-' });
persona.addAttribute({ id: 'a2', name: 'nombre', type: 'String', visibility: '+' });
persona.addOperation({ id: 'o1', name: 'getNombreCompleto', parameters: [], returnType: 'String', visibility: '+' });
model.addClass(persona);

const exportable = new UMLClassNode('Exportable', 400, 50);
exportable.isInterface = true;
exportable.addOperation({ id: 'o2', name: 'exportarPdf', parameters: [{ name: 'formato', type: 'String' }], returnType: 'String', visibility: '+' });
model.addClass(exportable);

const veterinario = new UMLClassNode('Veterinario', 100, 250);
veterinario.addAttribute({ id: 'a3', name: 'licencia', type: 'String', visibility: '-' });
model.addClass(veterinario);

const mascota = new UMLClassNode('Mascota', 300, 250);
mascota.addAttribute({ id: 'a4', name: 'nombre', type: 'String', visibility: '-' });
model.addClass(mascota);

// Herencia: Veterinario -> Persona
const genRel = new UMLRelNode('generalization', veterinario.id, persona.id);
model.addRelationship(genRel);

// Realización: Veterinario -> Exportable
const realRel = new UMLRelNode('realization', veterinario.id, exportable.id);
model.addRelationship(realRel);

// Composición: Veterinario -> Mascota (1 a 0..*)
const compRel = new UMLRelNode('composition', veterinario.id, mascota.id);
compRel.source.multiplicity = '1';
compRel.target.multiplicity = '0..*';
model.addRelationship(compRel);

const puml = generatePlantUML(model);
const mmd = generateMermaid(model);
({ puml, mmd });
`;

const result = vm.runInContext(testScript, ctx);

// Verificaciones PlantUML
assert(result.puml.includes('@startuml'), 'Debe comenzar con @startuml');
assert(result.puml.includes('@enduml'), 'Debe terminar con @enduml');
assert(result.puml.includes('abstract class Persona'), 'Persona debe ser abstract class');
assert(result.puml.includes('interface Exportable'), 'Exportable debe ser interface');
assert(result.puml.includes('+getNombreCompleto(): String'), 'getNombreCompleto debe estar formateado');
assert(result.puml.includes('exportarPdf(formato: String): String'), 'Parámetros deben estar formateados');
assert(result.puml.includes('Veterinario --|> Persona'), 'Herencia debe usar --|>');
assert(result.puml.includes('Veterinario ..|> Exportable'), 'Realización debe usar ..|>');
assert(result.puml.includes('Veterinario "1" *-- "0..*" Mascota'), 'Composición debe usar *-- con multiplicidad');

// Verificaciones Mermaid
assert(result.mmd.includes('classDiagram'), 'Debe comenzar con classDiagram');
assert(result.mmd.includes('<<abstract>>'), 'Persona debe tener <<abstract>>');
assert(result.mmd.includes('<<interface>>'), 'Exportable debe tener <<interface>>');
assert(result.mmd.includes('+getNombreCompleto() String'), 'getNombreCompleto en sintaxis Mermaid');
assert(result.mmd.includes('Veterinario --|> Persona') || result.mmd.includes('Persona <|-- Veterinario') || result.mmd.includes('Veterinario <|-- Persona') || result.mmd.includes('<|--'), 'Debe incluir relación de herencia');
assert(result.mmd.includes('--*'), 'Debe incluir símbolo de composición Mermaid --*');

// Verificaciones SVG autónomo y función PNG
const svgTestScript = `
state.model = new UMLModel();
const emptySvg = generateStandaloneSVG();

state.model = model;
const fullSvg = generateStandaloneSVG();

({ emptySvg, fullSvg, hasExportPNG: typeof exportDiagramPNG === 'function' });
`;

const svgResult = vm.runInContext(svgTestScript, ctx);
assert(svgResult.emptySvg.includes('Diagrama vacío'), 'SVG vacío debe contener texto informativo');
assert(svgResult.fullSvg.includes('viewBox="'), 'SVG debe contener atributo viewBox con límites calculados');
assert(svgResult.fullSvg.includes('fill="#12121a"'), 'SVG debe contener fondo oscuro autónomo');
assert(svgResult.fullSvg.includes('arrowClosed'), 'SVG debe contener definiciones de marcadores UML');
assert(svgResult.hasExportPNG === true, 'Función exportDiagramPNG debe estar definida en app.js');

console.log('✓ Pruebas de exportación PlantUML, Mermaid, SVG y PNG aprobadas correctamente.');
