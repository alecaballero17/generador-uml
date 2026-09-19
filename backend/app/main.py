"""
GeneradorUML — FastAPI Main Application

Punto de entrada del backend. Sirve la API REST y el editor web estático.
"""

from __future__ import annotations
import os
import json
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models.uml_model import (
    UMLDiagram, UMLClass, UMLAttribute, UMLOperation, UMLParameter,
    UMLRelationship, RelationshipEnd, Position, Size,
    Visibility, RelationshipType
)
from .models.uml_validator import UMLValidator
from .services.springboot_generator import SpringBootGenerator
from .services.flutter_generator import FlutterGenerator
from .services.postman_generator import PostmanGenerator
from .services.xmi_adapter import XMIAdapter
from .services.mdj_adapter import MDJAdapter
from .services.photo_interpreter import PhotoInterpreter
from .services.gemini_assistant import GeminiAssistant

# ─── App Setup ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="GeneradorUML API",
    description="Herramienta CASE para crear diagramas UML y generar aplicaciones",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory project store (SQLite for persistence in production) ────────

projects: dict[str, dict] = {}  # project_id -> {diagram: UMLDiagram, ...}

# ─── Paths ─────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ─── Pydantic Models ──────────────────────────────────────────────────────

class DiagramData(BaseModel):
    """Pydantic model for receiving diagram JSON from the frontend."""
    id: Optional[str] = None
    name: str = "Nuevo Diagrama"
    description: str = ""
    classes: list[dict] = []
    relationships: list[dict] = []
    version: str = "1.0.0"
    umlVersion: str = "2.5.1"
    diagram: Optional[dict] = None


class GenerationRequest(BaseModel):
    """Request for code generation."""
    diagram: DiagramData
    basePackage: str = "com.generated.app"
    generateFlutter: bool = True
    generatePostman: bool = True


class ProjectSaveRequest(BaseModel):
    """Request to save a project."""
    projectId: Optional[str] = None
    name: str = "Nuevo Proyecto"
    diagram: DiagramData


# ─── API Routes ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint (used by mobile and web to verify connectivity)."""
    return {"status": "ok", "service": "GeneradorUML", "timestamp": datetime.now().isoformat()}


# ─── Diagram Validation ───────────────────────────────────────────────────

@app.post("/api/validate")
async def validate_diagram(data: DiagramData):
    """Validate a UML diagram against UML 2.5+ rules."""
    diagram = UMLDiagram.from_dict(data.model_dump())
    validator = UMLValidator(diagram)
    result = validator.validate()
    return result.to_dict()


# ─── Code Generation ──────────────────────────────────────────────────────

@app.post("/api/generate")
async def generate_code(request: GenerationRequest):
    """Generate Spring Boot + Flutter code from a UML diagram."""
    diagram = UMLDiagram.from_dict(request.diagram.model_dump())

    # Validate first
    validator = UMLValidator(diagram)
    validation = validator.validate()
    if not validation.is_valid:
        errors = [i for i in validation.issues if i.severity.value == "error"]
        if errors:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "El diagrama tiene errores de validación",
                    "validation": validation.to_dict()
                }
            )

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    project_dir = OUTPUT_DIR / f"project_{timestamp}"
    project_dir.mkdir(parents=True, exist_ok=True)

    results = {"files": [], "errors": [], "warnings": []}

    # Generate Spring Boot
    try:
        sb_dir = project_dir / "springboot"
        generator = SpringBootGenerator(
            diagram=diagram,
            base_package=request.basePackage,
            output_dir=str(sb_dir)
        )
        created_files = generator.generate_to_disk(str(sb_dir))
        results["files"].extend([str(f) for f in created_files])
        results["springbootDir"] = str(sb_dir)
    except Exception as e:
        results["errors"].append(f"Error generando Spring Boot: {str(e)}")

    # Generate Postman collection
    if request.generatePostman:
        try:
            postman = PostmanGenerator(diagram=diagram)
            postman_json = postman.generate_json()
            postman_path = project_dir / "postman_collection.json"
            postman_path.write_text(postman_json, encoding="utf-8")
            results["files"].append(str(postman_path))
            results["postmanFile"] = str(postman_path)
        except Exception as e:
            results["errors"].append(f"Error generando Postman: {str(e)}")

    # Generate Flutter
    if request.generateFlutter:
        try:
            flutter_dir = project_dir / "flutter_app"
            flutter_gen = FlutterGenerator(
                diagram=diagram,
                app_name=diagram.name,
                package_name=request.basePackage,
            )
            flutter_files = flutter_gen.generate_to_disk(str(flutter_dir))
            results["flutterDir"] = str(flutter_dir)
            results["files"].extend(flutter_files)
        except Exception as e:
            results["errors"].append(f"Error generando Flutter: {str(e)}")

    # Add validation warnings
    for issue in validation.issues:
        if issue.severity.value == "warning":
            results["warnings"].append(issue.message)

    results["projectDir"] = str(project_dir)
    results["timestamp"] = timestamp
    results["diagramName"] = diagram.name
    results["classCount"] = len(diagram.classes)
    results["relationshipCount"] = len(diagram.relationships)

    if results["errors"]:
        return JSONResponse(status_code=500, content=results)
    return results


@app.post("/api/generate/download")
async def generate_and_download(request: GenerationRequest):
    """Generate code and return it as a ZIP file."""
    diagram = UMLDiagram.from_dict(request.diagram.model_dump())

    # Validate
    validator = UMLValidator(diagram)
    validation = validator.validate()

    if not validation.is_valid:
        raise HTTPException(status_code=400, detail=validation.to_dict())

    # Create temp directory for generation
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate Spring Boot
        sb_dir = os.path.join(tmpdir, "springboot")
        generator = SpringBootGenerator(
            diagram=diagram,
            base_package=request.basePackage,
        )
        generator.generate_to_disk(sb_dir)

        # Generate Flutter
        if request.generateFlutter:
            flutter_dir = os.path.join(tmpdir, "flutter_app")
            flutter_gen = FlutterGenerator(
                diagram=diagram,
                app_name=diagram.name,
                package_name=request.basePackage,
            )
            flutter_gen.generate_to_disk(flutter_dir)

        # Generate Postman
        if request.generatePostman:
            postman = PostmanGenerator(diagram=diagram)
            postman_path = os.path.join(tmpdir, "postman_collection.json")
            with open(postman_path, "w", encoding="utf-8") as f:
                f.write(postman.generate_json())

        # Create ZIP
        zip_path = os.path.join(tmpdir, f"{diagram.name.replace(' ', '_')}_generated.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    if file.endswith('.zip'):
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    zipf.write(file_path, arcname)

        # Read zip and return
        with open(zip_path, 'rb') as f:
            zip_content = f.read()

    return StreamingResponse(
        iter([zip_content]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={diagram.name.replace(' ', '_')}_generated.zip"
        }
    )


# ─── Project Management ───────────────────────────────────────────────────

@app.post("/api/projects/save")
async def save_project(request: ProjectSaveRequest):
    """Save a project (diagram + metadata)."""
    import uuid as uuid_mod
    project_id = request.projectId or str(uuid_mod.uuid4())

    diagram = UMLDiagram.from_dict(request.diagram.model_dump())
    diagram.updated_at = datetime.now().isoformat()

    if project_id not in projects:
        diagram.created_at = diagram.updated_at

    projects[project_id] = {
        "id": project_id,
        "name": request.name,
        "diagram": diagram.to_dict(),
        "updatedAt": diagram.updated_at,
    }

    # Also save to disk
    projects_dir = OUTPUT_DIR / "projects"
    projects_dir.mkdir(exist_ok=True)
    project_file = projects_dir / f"{project_id}.json"
    project_file.write_text(
        json.dumps(projects[project_id], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return {"projectId": project_id, "saved": True}


@app.get("/api/projects")
async def list_projects():
    """List all saved projects (local disk + collaborative SQLite rooms)."""
    # Load from disk if empty
    projects_dir = OUTPUT_DIR / "projects"
    if projects_dir.exists():
        for f in projects_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                projects[data["id"]] = data
            except Exception:
                pass

    # Load rooms from collaboration sqlite
    try:
        from .services.collaboration import store as collab_store
        with collab_store.connect() as db:
            rows = db.execute("SELECT id, diagram FROM rooms").fetchall()
            for r_id, r_diagram_str in rows:
                if r_id not in projects:
                    try:
                        d = json.loads(r_diagram_str)
                        projects[r_id] = {
                            "id": r_id,
                            "name": d.get("name", f"Proyecto Colaborativo ({r_id[:8]})"),
                            "diagram": d,
                            "updatedAt": None,
                            "isCollaborative": True
                        }
                    except Exception:
                        pass
    except Exception:
        pass

    return [
        {"id": p["id"], "name": p["name"], "updatedAt": p.get("updatedAt"), "isCollaborative": p.get("isCollaborative", False)}
        for p in projects.values()
    ]


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific project from memory, disk, or collaboration SQLite store."""
    if project_id not in projects:
        # Try loading from disk
        project_file = OUTPUT_DIR / "projects" / f"{project_id}.json"
        if project_file.exists():
            try:
                data = json.loads(project_file.read_text(encoding="utf-8"))
                projects[project_id] = data
            except Exception:
                pass

    if project_id not in projects:
        # Try loading from collaboration sqlite
        try:
            from .services.collaboration import store as collab_store
            collab_snapshot = collab_store.snapshot(project_id)
            if collab_snapshot:
                diagram = collab_snapshot["diagram"]
                projects[project_id] = {
                    "id": project_id,
                    "name": diagram.get("name", "Proyecto Colaborativo"),
                    "diagram": diagram,
                    "updatedAt": None,
                    "isCollaborative": True
                }
        except Exception:
            pass

    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return projects[project_id]


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    projects.pop(project_id, None)
    project_file = OUTPUT_DIR / "projects" / f"{project_id}.json"
    if project_file.exists():
        project_file.unlink()
    return {"deleted": True}


# ─── Import/Export ─────────────────────────────────────────────────────────

@app.post("/api/import/json")
async def import_json(file: UploadFile = File(...)):
    """Import a diagram from a JSON file."""
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        diagram = UMLDiagram.from_dict(data)
        return {"success": True, "diagram": diagram.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error importando: {str(e)}")


@app.post("/api/export/json")
async def export_json(data: DiagramData):
    """Export a diagram as a JSON file."""
    diagram = UMLDiagram.from_dict(data.model_dump())
    content = diagram.to_json()
    return JSONResponse(
        content=json.loads(content),
        headers={
            "Content-Disposition": f"attachment; filename={diagram.name.replace(' ', '_')}.json"
        }
    )

# ─── XMI 2.1 Import/Export (Enterprise Architect / StarUML) ───────────────

@app.post("/api/import/xmi")
async def import_xmi(file: UploadFile = File(...)):
    """Import a diagram from an XMI 2.1 file (Enterprise Architect / StarUML)."""
    try:
        content = await file.read()
        adapter = XMIAdapter()
        diagram = adapter.import_from_xmi(content.decode("utf-8"))
        return {
            "success": True,
            "diagram": diagram.to_dict(),
            "warnings": adapter.warnings,
            "unsupportedElements": adapter.unsupported_elements,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error importando XMI: {str(e)}")


@app.post("/api/export/xmi")
async def export_xmi(data: DiagramData):
    """Export a diagram as XMI 2.1 (compatible with Enterprise Architect / StarUML)."""
    diagram = UMLDiagram.from_dict(data.model_dump())
    adapter = XMIAdapter()
    xmi_content = adapter.export_to_xmi(diagram)
    return JSONResponse(
        content={"xmi": xmi_content, "warnings": adapter.warnings},
        headers={
            "Content-Disposition": f"attachment; filename={diagram.name.replace(' ', '_')}.xmi"
        }
    )


# ─── StarUML .mdj Import/Export ───────────────────────────────────────────

@app.post("/api/import/mdj")
async def import_mdj(file: UploadFile = File(...)):
    """Import a diagram from a StarUML .mdj file."""
    try:
        content = await file.read()
        adapter = MDJAdapter()
        diagram = adapter.import_from_mdj(content.decode("utf-8"))
        return {
            "success": True,
            "diagram": diagram.to_dict(),
            "warnings": adapter.warnings,
            "unsupportedElements": adapter.unsupported_elements,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error importando MDJ: {str(e)}")


@app.post("/api/export/mdj")
async def export_mdj(data: DiagramData):
    """Export a diagram as StarUML .mdj file."""
    diagram = UMLDiagram.from_dict(data.model_dump())
    adapter = MDJAdapter()
    mdj_content = adapter.export_to_mdj(diagram)
    return JSONResponse(
        content=json.loads(mdj_content),
        headers={
            "Content-Disposition": f"attachment; filename={diagram.name.replace(' ', '_')}.mdj"
        }
    )



# ─── Photo / Whiteboard Interpretation ────────────────────────────────────

MAX_PHOTO_SIZE = 15 * 1024 * 1024  # 15 MB

@app.post("/api/photo/interpret")
async def interpret_photo(file: UploadFile = File(...)):
    """Interpreta una fotografía de diagrama UML (pizarra, papel, captura)."""
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="El archivo enviado está vacío.")
        if len(content) > MAX_PHOTO_SIZE:
            raise HTTPException(status_code=413, detail=f"La imagen excede el límite máximo permitido de {MAX_PHOTO_SIZE // (1024 * 1024)} MB.")
        interpreter = PhotoInterpreter()
        result = interpreter.interpret_image_bytes(content)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error interpretando imagen: {str(e)}")


# ─── Conversational Voice Assistant (Siri UML) ───────────────────────────

class AssistantConverseRequest(BaseModel):
    message: str
    diagram: Optional[dict] = None
    history: Optional[list] = None

@app.post("/api/assistant/converse")
async def assistant_converse(req: AssistantConverseRequest):
    """Asistente conversacional de voz tipo Siri para modelado UML."""
    try:
        assistant = GeminiAssistant()
        result = await assistant.converse(
            message=req.message,
            current_diagram=req.diagram,
            history=req.history
        )
        return {"status": "ok", **result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en asistente: {str(e)}")


from .services.collaboration import router as collaboration_router
app.include_router(collaboration_router)


# ─── Serve Frontend ───────────────────────────────────────────────────────

# Mount static files
if FRONTEND_DIR.exists():
    for sub in ["assets", "css", "js"]:
        sub_dir = FRONTEND_DIR / sub
        sub_dir.mkdir(parents=True, exist_ok=True)
        app.mount(f"/{sub}", StaticFiles(directory=str(sub_dir)), name=sub)

    @app.get("/")
    async def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{path:path}")
    async def serve_static(path: str):
        """Serve static files, falling back to index.html for SPA routing."""
        file_path = FRONTEND_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
