import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.models.uml_model import UMLDiagram
from backend.app.services.xmi_adapter import XMIAdapter
from backend.app.services.mdj_adapter import MDJAdapter

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "diagramas")
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Cargar el diagrama veterinaria
json_path = os.path.join(os.path.dirname(__file__), "..", "examples", "veterinaria.json")
with open(json_path, "r", encoding="utf-8") as f:
    diag_data = json.load(f)

diag = UMLDiagram.from_dict(diag_data)

# 2. Exportar XMI 2.1
xmi_content = XMIAdapter().export_to_xmi(diag)
with open(os.path.join(OUT_DIR, "diagrama_veterinaria.xmi"), "w", encoding="utf-8") as f:
    f.write(xmi_content)

# 3. Exportar StarUML MDJ
mdj_content = MDJAdapter().export_to_mdj(diag)
with open(os.path.join(OUT_DIR, "diagrama_veterinaria.mdj"), "w", encoding="utf-8") as f:
    f.write(mdj_content)

# 4. Copiar JSON nativo
with open(os.path.join(OUT_DIR, "diagrama_veterinaria.json"), "w", encoding="utf-8") as f:
    json.dump(diag_data, f, indent=2, ensure_ascii=False)

# 5. Generar SVG puro autónomo de alta calidad
svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1150 720" width="100%" height="100%" style="background:#0f172a; font-family:'Segoe UI',Roboto,Helvetica,sans-serif;">
  <defs>
    <!-- Gradientes y filtros -->
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>
    <linearGradient id="compGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6"/>
      <stop offset="100%" stop-color="#6d28d9"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="115%" height="115%">
      <feDropShadow dx="0" dy="8" stdDeviation="6" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
    <marker id="assocArrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="#60a5fa" stroke-width="1.8"/>
    </marker>
    <marker id="diamondComp" viewBox="0 0 12 12" refX="0" refY="6" markerWidth="9" markerHeight="9" orient="auto">
      <path d="M 0 6 L 6 1 L 12 6 L 6 11 Z" fill="#8b5cf6" stroke="#c4b5fd" stroke-width="1.2"/>
    </marker>
  </defs>

  <text x="40" y="48" font-size="24" font-weight="bold" fill="#f8fafc" letter-spacing="0.5">🐾 Sistema Veterinaria — Diagrama de Clases UML 2.5</text>
  <text x="40" y="74" font-size="13" fill="#94a3b8">Generado por GeneradorUML CASE Tool • Arquitectura de Entidades y Relaciones</text>

  <!-- CLASE CLIENTE (x:40, y:110, w:270, h:240) -->
  <g filter="url(#shadow)">
    <rect x="40" y="110" width="270" height="240" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
    <rect x="40" y="110" width="270" height="42" rx="10" fill="url(#compGrad)"/>
    <rect x="40" y="142" width="270" height="10" fill="url(#compGrad)"/>
    <text x="175" y="136" font-size="16" font-weight="bold" fill="#ffffff" text-anchor="middle">Cliente</text>
    <line x1="40" y1="152" x2="310" y2="152" stroke="#334155" stroke-width="1.5"/>
    <!-- Atributos -->
    <text x="54" y="174" font-size="12" fill="#cbd5e1">- nombre : String</text>
    <text x="54" y="194" font-size="12" fill="#cbd5e1">- apellido : String</text>
    <text x="54" y="214" font-size="12" fill="#cbd5e1">- telefono : String</text>
    <text x="54" y="234" font-size="12" fill="#cbd5e1">- email : String</text>
    <text x="54" y="254" font-size="12" fill="#cbd5e1">- direccion : String</text>
    <line x1="40" y1="268" x2="310" y2="268" stroke="#334155" stroke-width="1.5"/>
    <!-- Métodos -->
    <text x="54" y="290" font-size="12" fill="#38bdf8">+ registrar() : void</text>
    <text x="54" y="310" font-size="12" fill="#38bdf8">+ actualizar() : void</text>
    <text x="54" y="330" font-size="12" fill="#38bdf8">+ obtenerMascotas() : List</text>
  </g>

  <!-- CLASE MASCOTA (x:440, y:110, w:270, h:250) -->
  <g filter="url(#shadow)">
    <rect x="440" y="110" width="270" height="250" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
    <rect x="440" y="110" width="270" height="42" rx="10" fill="url(#headerGrad)"/>
    <rect x="440" y="142" width="270" height="10" fill="url(#headerGrad)"/>
    <text x="575" y="136" font-size="16" font-weight="bold" fill="#ffffff" text-anchor="middle">Mascota</text>
    <line x1="440" y1="152" x2="710" y2="152" stroke="#334155" stroke-width="1.5"/>
    <!-- Atributos -->
    <text x="454" y="174" font-size="12" fill="#cbd5e1">- nombre : String</text>
    <text x="454" y="194" font-size="12" fill="#cbd5e1">- especie : String</text>
    <text x="454" y="214" font-size="12" fill="#cbd5e1">- raza : String</text>
    <text x="454" y="234" font-size="12" fill="#cbd5e1">- fechaNacimiento : LocalDate</text>
    <text x="454" y="254" font-size="12" fill="#cbd5e1">- peso : Double</text>
    <text x="454" y="274" font-size="12" fill="#cbd5e1">- sexo : String</text>
    <line x1="440" y1="288" x2="710" y2="288" stroke="#334155" stroke-width="1.5"/>
    <!-- Métodos -->
    <text x="454" y="310" font-size="12" fill="#38bdf8">+ calcularEdad() : Integer</text>
    <text x="454" y="330" font-size="12" fill="#38bdf8">+ obtenerHistorial() : List</text>
  </g>

  <!-- CLASE VETERINARIO (x:40, y:430, w:270, h:240) -->
  <g filter="url(#shadow)">
    <rect x="40" y="430" width="270" height="240" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
    <rect x="40" y="430" width="270" height="42" rx="10" fill="url(#headerGrad)"/>
    <rect x="40" y="462" width="270" height="10" fill="url(#headerGrad)"/>
    <text x="175" y="456" font-size="16" font-weight="bold" fill="#ffffff" text-anchor="middle">Veterinario</text>
    <line x1="40" y1="472" x2="310" y2="472" stroke="#334155" stroke-width="1.5"/>
    <!-- Atributos -->
    <text x="54" y="494" font-size="12" fill="#cbd5e1">- nombre : String</text>
    <text x="54" y="514" font-size="12" fill="#cbd5e1">- apellido : String</text>
    <text x="54" y="534" font-size="12" fill="#cbd5e1">- especialidad : String</text>
    <text x="54" y="554" font-size="12" fill="#cbd5e1">- matricula : String</text>
    <text x="54" y="574" font-size="12" fill="#cbd5e1">- telefono : String</text>
    <line x1="40" y1="588" x2="310" y2="588" stroke="#334155" stroke-width="1.5"/>
    <!-- Métodos -->
    <text x="54" y="610" font-size="12" fill="#38bdf8">+ atenderCita(cita: Cita) : void</text>
    <text x="54" y="630" font-size="12" fill="#38bdf8">+ prescribirTratamiento() : Tratamiento</text>
  </g>

  <!-- CLASE CITA (x:440, y:430, w:270, h:250) -->
  <g filter="url(#shadow)">
    <rect x="440" y="430" width="270" height="250" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
    <rect x="440" y="430" width="270" height="42" rx="10" fill="url(#headerGrad)"/>
    <rect x="440" y="462" width="270" height="10" fill="url(#headerGrad)"/>
    <text x="575" y="456" font-size="16" font-weight="bold" fill="#ffffff" text-anchor="middle">Cita</text>
    <line x1="440" y1="472" x2="710" y2="472" stroke="#334155" stroke-width="1.5"/>
    <!-- Atributos -->
    <text x="454" y="494" font-size="12" fill="#cbd5e1">- fecha : LocalDateTime</text>
    <text x="454" y="514" font-size="12" fill="#cbd5e1">- motivo : String</text>
    <text x="454" y="534" font-size="12" fill="#cbd5e1">- diagnostico : String</text>
    <text x="454" y="554" font-size="12" fill="#cbd5e1">- estado : String</text>
    <text x="454" y="574" font-size="12" fill="#cbd5e1">- observaciones : String</text>
    <line x1="440" y1="588" x2="710" y2="588" stroke="#334155" stroke-width="1.5"/>
    <!-- Métodos -->
    <text x="454" y="610" font-size="12" fill="#38bdf8">+ confirmar() : void</text>
    <text x="454" y="630" font-size="12" fill="#38bdf8">+ cancelar() : void</text>
    <text x="454" y="650" font-size="12" fill="#38bdf8">+ completar() : void</text>
  </g>

  <!-- CLASE TRATAMIENTO (x:840, y:430, w:270, h:230) -->
  <g filter="url(#shadow)">
    <rect x="840" y="430" width="270" height="230" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
    <rect x="840" y="430" width="270" height="42" rx="10" fill="url(#headerGrad)"/>
    <rect x="840" y="462" width="270" height="10" fill="url(#headerGrad)"/>
    <text x="975" y="456" font-size="16" font-weight="bold" fill="#ffffff" text-anchor="middle">Tratamiento</text>
    <line x1="840" y1="472" x2="1110" y2="472" stroke="#334155" stroke-width="1.5"/>
    <!-- Atributos -->
    <text x="854" y="494" font-size="12" fill="#cbd5e1">- descripcion : String</text>
    <text x="854" y="514" font-size="12" fill="#cbd5e1">- medicamento : String</text>
    <text x="854" y="534" font-size="12" fill="#cbd5e1">- dosis : String</text>
    <text x="854" y="554" font-size="12" fill="#cbd5e1">- duracionDias : Integer</text>
    <text x="854" y="574" font-size="12" fill="#cbd5e1">- costo : BigDecimal</text>
    <line x1="840" y1="588" x2="1110" y2="588" stroke="#334155" stroke-width="1.5"/>
    <!-- Métodos -->
    <text x="854" y="616" font-size="12" fill="#38bdf8">+ calcularCostoTotal() : BigDecimal</text>
  </g>

  <!-- RELACION 1: Cliente -- Mascota (Composicion) -->
  <path d="M 310 200 L 436 200" stroke="#a855f7" stroke-width="2.5" marker-start="url(#diamondComp)"/>
  <text x="325" y="190" font-size="11" font-weight="bold" fill="#c084fc">1 (dueño)</text>
  <text x="375" y="190" font-size="12" font-style="italic" fill="#e9d5ff">tiene</text>
  <text x="390" y="218" font-size="11" font-weight="bold" fill="#c084fc">1..* (mascotas)</text>

  <!-- RELACION 2: Mascota -- Cita (Asociacion) -->
  <path d="M 575 360 L 575 424" stroke="#60a5fa" stroke-width="2" marker-end="url(#assocArrow)"/>
  <text x="585" y="380" font-size="11" font-weight="bold" fill="#93c5fd">1</text>
  <text x="585" y="400" font-size="12" font-style="italic" fill="#bfdbfe">asiste</text>
  <text x="585" y="420" font-size="11" font-weight="bold" fill="#93c5fd">0..* (citas)</text>

  <!-- RELACION 3: Veterinario -- Cita (Asociacion) -->
  <path d="M 310 540 L 434 540" stroke="#60a5fa" stroke-width="2" marker-end="url(#assocArrow)"/>
  <text x="320" y="530" font-size="11" font-weight="bold" fill="#93c5fd">1</text>
  <text x="365" y="530" font-size="12" font-style="italic" fill="#bfdbfe">atiende</text>
  <text x="385" y="558" font-size="11" font-weight="bold" fill="#93c5fd">0..* (citas)</text>

  <!-- RELACION 4: Cita -- Tratamiento (Asociacion) -->
  <path d="M 710 540 L 834 540" stroke="#60a5fa" stroke-width="2" marker-end="url(#assocArrow)"/>
  <text x="720" y="530" font-size="11" font-weight="bold" fill="#93c5fd">1</text>
  <text x="765" y="530" font-size="12" font-style="italic" fill="#bfdbfe">incluye</text>
  <text x="770" y="558" font-size="11" font-weight="bold" fill="#93c5fd">0..* (tratamientos)</text>

  <!-- Leyenda -->
  <rect x="40" y="685" width="400" height="24" rx="5" fill="#1e293b" opacity="0.8"/>
  <circle cx="55" cy="697" r="5" fill="#a855f7"/>
  <text x="68" y="701" font-size="11" fill="#cbd5e1">Composición (Cascade.ALL)</text>
  <circle cx="210" cy="697" r="5" fill="#60a5fa"/>
  <text x="223" y="701" font-size="11" fill="#cbd5e1">Asociación (@ManyToOne / @OneToMany)</text>
</svg>"""

with open(os.path.join(OUT_DIR, "diagrama_veterinaria.svg"), "w", encoding="utf-8") as f:
    f.write(svg_content)

# 6. Generar visor HTML interactivo completo
html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Visor de Diagramas UML — GeneradorUML</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #0b1120;
      color: #f8fafc;
      padding: 30px;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 25px;
      padding-bottom: 20px;
      border-bottom: 1px solid #1e293b;
    }}
    .title h1 {{
      font-size: 26px;
      font-weight: 700;
      background: linear-gradient(135deg, #60a5fa, #a855f7);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .title p {{ color: #94a3b8; font-size: 14px; margin-top: 4px; }}
    .badge {{
      display: inline-block;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      background: rgba(96, 165, 250, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(96, 165, 250, 0.3);
    }}
    .tabs {{
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
    }}
    .tab-btn {{
      padding: 10px 20px;
      border-radius: 8px;
      background: #1e293b;
      color: #94a3b8;
      border: 1px solid #334155;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s;
    }}
    .tab-btn.active {{
      background: #3b82f6;
      color: #ffffff;
      border-color: #3b82f6;
    }}
    .panel {{
      background: #131d31;
      border: 1px solid #1e293b;
      border-radius: 12px;
      padding: 25px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}
    .downloads {{
      display: flex;
      gap: 12px;
      margin-top: 25px;
      padding-top: 20px;
      border-top: 1px solid #1e293b;
      flex-wrap: wrap;
    }}
    .dl-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: 6px;
      text-decoration: none;
      font-size: 13px;
      font-weight: 500;
      background: #1e293b;
      color: #cbd5e1;
      border: 1px solid #334155;
      transition: all 0.2s;
    }}
    .dl-btn:hover {{
      background: #334155;
      color: #ffffff;
    }}
    .svg-container {{
      width: 100%;
      overflow-x: auto;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title">
      <h1>GeneradorUML — Diagramas de Clases del Proyecto</h1>
      <p>Visualización directa y exportaciones oficiales para Enterprise Architect, StarUML y la Web</p>
    </div>
    <span class="badge">UML 2.5+ Conforme</span>
  </div>

  <div class="tabs">
    <button class="tab-btn active" onclick="showTab('tab-svg')">Gráfico Vectorial SVG</button>
    <button class="tab-btn" onclick="showTab('tab-mermaid')">Render Mermaid.js</button>
    <button class="tab-btn" onclick="showTab('tab-arquitectura')">Arquitectura del Sistema</button>
  </div>

  <div id="tab-svg" class="panel">
    <div class="svg-container">
      {svg_content}
    </div>
  </div>

  <div id="tab-mermaid" class="panel" style="display:none;">
    <div class="mermaid">
classDiagram
    direction LR
    class Cliente {{
        -String nombre
        -String apellido
        -String telefono
        -String email
        -String direccion
        +void registrar()
        +void actualizar()
        +List~Mascota~ obtenerMascotas()
    }}
    class Mascota {{
        -String nombre
        -String especie
        -String raza
        -LocalDate fechaNacimiento
        -Double peso
        -String sexo
        +Integer calcularEdad()
        +List~Cita~ obtenerHistorial()
    }}
    class Veterinario {{
        -String nombre
        -String apellido
        -String especialidad
        -String matricula
        -String telefono
        +void atenderCita(Cita cita)
        +Tratamiento prescribirTratamiento()
    }}
    class Cita {{
        -LocalDateTime fecha
        -String motivo
        -String diagnostico
        -String estado
        -String observaciones
        +void confirmar()
        +void cancelar()
        +void completar()
    }}
    class Tratamiento {{
        -String descripcion
        -String medicamento
        -String dosis
        -Integer duracionDias
        -BigDecimal costo
        +BigDecimal calcularCostoTotal()
    }}
    Cliente "1 (dueño)" *-- "1..* (mascotas)" Mascota : tiene
    Mascota "1" --> "0..* (citas)" Cita : asiste
    Veterinario "1" --> "0..* (citas)" Cita : atiende
    Cita "1" --> "0..* (tratamientos)" Tratamiento : incluye
    </div>
  </div>

  <div id="tab-arquitectura" class="panel" style="display:none;">
    <div class="mermaid">
classDiagram
    direction TB
    class UMLDiagram {{
        +String name
        +List~UMLClass~ classes
        +List~UMLRelationship~ relationships
    }}
    class UMLClass {{
        +String name
        +List~UMLAttribute~ attributes
        +List~UMLOperation~ operations
    }}
    class UMLRelationship {{
        +RelationshipType type
        +RelationshipEnd source
        +RelationshipEnd target
    }}
    class SpringBootGenerator {{
        +generate() dict
        +generate_to_disk(path)
    }}
    class FlutterGenerator {{
        +generate_all() dict
        +generate_to_disk(path)
    }}
    class XMIAdapter {{
        +export_to_xmi()
        +import_from_xmi()
    }}
    class MDJAdapter {{
        +export_to_mdj()
        +import_from_mdj()
    }}
    UMLDiagram *-- UMLClass
    UMLDiagram *-- UMLRelationship
    SpringBootGenerator ..> UMLDiagram
    FlutterGenerator ..> UMLDiagram
    XMIAdapter ..> UMLDiagram
    MDJAdapter ..> UMLDiagram
    </div>
  </div>

  <div class="downloads">
    <span style="font-size: 13px; color: #94a3b8; align-self: center;">Archivos generados en <code>docs/diagramas/</code>:</span>
    <a href="diagrama_veterinaria.svg" download class="dl-btn">⬇️ Descargar SVG</a>
    <a href="diagrama_veterinaria.xmi" download class="dl-btn">⬇️ Descargar XMI 2.1 (Enterprise Architect / StarUML)</a>
    <a href="diagrama_veterinaria.mdj" download class="dl-btn">⬇️ Descargar StarUML (.mdj)</a>
    <a href="diagrama_veterinaria.json" download class="dl-btn">⬇️ Descargar JSON Nativo</a>
  </div>

  <script>
    mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
    function showTab(id) {{
      document.getElementById('tab-svg').style.display = 'none';
      document.getElementById('tab-mermaid').style.display = 'none';
      document.getElementById('tab-arquitectura').style.display = 'none';
      document.getElementById(id).style.display = 'block';
      const btns = document.querySelectorAll('.tab-btn');
      btns.forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
    }}
  </script>
</body>
</html>
"""

with open(os.path.join(OUT_DIR, "diagrama_veterinaria.html"), "w", encoding="utf-8") as f:
    f.write(html_content)

print("Exportación completa en:", OUT_DIR)
for fname in os.listdir(OUT_DIR):
    print(" -", fname)
