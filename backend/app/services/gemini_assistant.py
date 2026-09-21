"""
GeneradorUML — Asistente Conversacional Inteligente (Gemini Flash)

Proporciona un asistente de voz tipo "Siri" para modelado UML:
- Interpreta lenguaje natural conversacional en español.
- Genera una respuesta hablada concisa y amigable (TTS).
- Traduce las solicitudes a acciones estructuradas sobre el diagrama UML.
"""

from __future__ import annotations
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger("gemini_assistant")

def _load_env_key() -> str:
    """Busca GEMINI_API_KEY en variables de entorno o archivo .env."""
    key = os.environ.get("GEMINI_API_KEY")
    if key and key.strip():
        return key.strip()
    
    # Buscar en backend/.env o raiz/.env
    for env_path in [
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
    ]:
        if env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
            except Exception:
                pass
    return ""

SYSTEM_INSTRUCTION = """
Las referencias como "agregale" se resuelven usando el historial y el diagrama actual. Si hay varias clases posibles y no hay una referencia clara, pregunta cuál y devuelve actions vacío. No adivines palabras de una transcripción ambigua. No declares que guardaste cambios: tu salida propone acciones y la aplicación confirma su ejecución. Nunca uses "etc" como atributo. Los nombres y tipos deben ser válidos; teléfono es String para conservar prefijos y ceros.

Eres 'Siri UML', un asistente de voz inteligente, ágil y conversacional integrado en GeneradorUML.
Tu propósito es ayudar al usuario a diseñar y refinar su diagrama de clases UML mientras dialogan.

Instrucciones de comportamiento:
1. Habla en español natural, profesional y amigable.
2. Sé muy conciso en 'spoken_response' (máximo 2 oraciones breves) porque tu respuesta será leída en voz alta por el sintetizador de voz del teléfono.
3. Comprende expresiones coloquiales, descripciones de negocio, peticiones de cambios o correcciones sobre la marcha (ej: "cambiame X por Y", "agrégale precio", "elimina la relación", "ahora crea una clase...").
4. Tipos de datos soportados: String, Integer, Double, Boolean, LocalDate, Long. Si el usuario no especifica tipo, deduce el más adecuado para el atributo.
5. Considera siempre las 'CLASES Y RELACIONES ACTUALES' del diagrama para no duplicar datos, o para modificarlas cuando el usuario lo solicite.

Tipos de acciones soportadas en 'actions':
- createClass: { "action": "createClass", "name": string, "attributes": [{ "name": string, "type": string }] }
- addAttributes: { "action": "addAttributes", "name": string, "attributes": [{ "name": string, "type": string }] }
- removeAttribute: { "action": "removeAttribute", "name": string, "attributeName": string }
- updateAttribute: { "action": "updateAttribute", "name": string, "oldAttributeName": string, "newAttributeName": string, "type": string }
- deleteClass: { "action": "deleteClass", "name": string }
- addRelationship: { "action": "addRelationship", "source": string, "target": string, "type": "association"|"aggregation"|"composition"|"generalization"|"realization"|"dependency", "multiplicitySource": string, "multiplicityTarget": string }
- deleteRelationship: { "action": "deleteRelationship", "source": string, "target": string, "type": string (opcional) }
- addOperation: { "action": "addOperation", "name": string, "operationName": string, "returnType": string, "parameters": [{ "name": string, "type": string }] }
- deleteOperation: { "action": "deleteOperation", "name": string, "operationName": string }
- renameClass: { "action": "renameClass", "oldName": string, "newName": string }

DEBES responder SIEMPRE en formato JSON estricto con esta estructura:
{
  "spoken_response": "Texto conciso para ser leído en voz alta...",
  "actions": [ ... ]
}
"""

class GeminiAssistant:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or _load_env_key()
        self.models_to_try = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3-flash-preview", "gemini-2.5-flash-lite"]

    async def converse(self, message: str, current_diagram: Optional[Dict[str, Any]] = None, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no configurada. Agrega tu clave en el archivo .env del backend.")

        # Resumen del diagrama actual para dar contexto al modelo
        diagram_summary = ""
        if current_diagram and isinstance(current_diagram, dict):
            classes_info = []
            for c in current_diagram.get("classes", []):
                attrs = [f"{a.get('name')}: {a.get('type', 'String')}" for a in c.get("attributes", [])]
                classes_info.append(f"Clase '{c.get('name')}': [{', '.join(attrs)}]")
            rels_info = []
            names = {c.get("id"): c.get("name") for c in current_diagram.get("classes", [])}
            for r in current_diagram.get("relationships", []):
                source, target = r.get("source", {}), r.get("target", {})
                rels_info.append(f"{names.get(source.get('classId'), '?')} [{source.get('multiplicity', '')}] -> {names.get(target.get('classId'), '?')} [{target.get('multiplicity', '')}] ({r.get('type')})")
            diagram_summary = f"\n\nESTADO ACTUAL DEL DIAGRAMA:\nClases existentes:\n" + "\n".join(classes_info or ["(Ninguna clase creada todavía)"])
            if rels_info:
                diagram_summary += "\nRelaciones existentes:\n" + "\n".join(rels_info)

        # Construir contenido
        contents = []
        if history:
            for item in history[-6:]: # últimos 6 turnos para mantener contexto rápido
                contents.append({
                    "role": "user" if item.get("role") == "user" else "model",
                    "parts": [{"text": item.get("text", "")}]
                })
        
        user_prompt = message
        if diagram_summary:
            user_prompt += diagram_summary

        contents.append({
            "role": "user",
            "parts": [{"text": user_prompt}]
        })

        system_instruction = SYSTEM_INSTRUCTION

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.25
            }
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            last_err = None
            for model_name in self.models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
                try:
                    response = await client.post(url, json=payload, headers={"x-goog-api-key": self.api_key})
                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                parsed = json.loads(parts[0]["text"])
                                return {
                                    "spoken_response": parsed.get("spoken_response", "Entendido, he actualizado el diagrama."),
                                    "actions": parsed.get("actions", []),
                                    "model_used": model_name
                                }
                    else:
                        last_err = f"Status {response.status_code}: {response.text[:200]}"
                except Exception as e:
                    last_err = type(e).__name__
                    continue

            raise RuntimeError(f"Error consultando Gemini API: {last_err}")
