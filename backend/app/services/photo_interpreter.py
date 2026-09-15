"""
GeneradorUML — Intérprete de Fotografías de Diagramas de Clases

Procesa imágenes fotográficas de diagramas de clases (pizarra, papel o capturas),
detecta cajas de clases con compartimentos, reconoce texto (OCR) y relaciones,
y ensambla un UMLDiagram editable con informe de incertidumbres para confirmación humana.
"""

from __future__ import annotations
import io
import re
import math
import uuid
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
import numpy as np
from PIL import Image

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

from ..models.uml_model import (
    UMLDiagram, UMLClass, UMLAttribute, UMLOperation, UMLParameter,
    UMLRelationship, RelationshipEnd, Position, Size,
    Visibility, RelationshipType, Multiplicity
)


@dataclass
class DetectedBox:
    id: str
    x: int
    y: int
    w: int
    h: int
    compartments: List[Tuple[int, int, int, int]] = field(default_factory=list)
    raw_text: str = ""
    parsed_class: Optional[UMLClass] = None
    confidence: float = 0.85


@dataclass
class DetectedLine:
    start_pt: Tuple[int, int]
    end_pt: Tuple[int, int]
    source_box_id: Optional[str] = None
    target_box_id: Optional[str] = None
    rel_type: RelationshipType = RelationshipType.ASSOCIATION
    confidence: float = 0.75
    raw_annotation: str = ""


class PhotoInterpreter:
    """Intérprete de fotografías de diagramas UML basado en Computer Vision y OCR."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd and PYTESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.review_notes: List[str] = []
        self.warnings: List[str] = []

    def interpret_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Procesa una imagen en bytes y retorna el diagrama UML y reporte de detección."""
        self.review_notes = []
        self.warnings = []

        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(pil_img)

        return self.interpret_numpy_image(img_np)

    def interpret_numpy_image(self, img_bgr_or_rgb: np.ndarray) -> Dict[str, Any]:
        """Pipeline principal de visión por computadora y OCR."""
        if not CV2_AVAILABLE:
            missing = []
            if not CV2_AVAILABLE:
                missing.append('opencv-python (pip install opencv-python)')
            if not PYTESSERACT_AVAILABLE:
                missing.append('pytesseract (pip install pytesseract) + Tesseract OCR binary')
            return {
                "success": False,
                "error": "Dependencias de visión por computadora no instaladas",
                "missingDependencies": missing,
                "message": "Para interpretar fotografías de diagramas UML, instale las dependencias faltantes:\n"
                           + "\n".join(f"  - {d}" for d in missing)
                           + "\nDespués reinicie el servidor.",
                "diagram": None,
                "confidence": 0.0,
                "detectedClassCount": 0,
                "detectedRelationshipCount": 0,
                "detectedBoxes": [],
                "reviewNotes": [],
                "warnings": [f"Dependencia faltante: {d}" for d in missing],
            }

        h, w = img_bgr_or_rgb.shape[:2]
        if len(img_bgr_or_rgb.shape) == 3:
            gray = cv2.cvtColor(img_bgr_or_rgb, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_bgr_or_rgb.copy()

        # 1. Preprocesamiento: binarización adaptativa y filtrado
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 4
        )

        # 2. Detección de cajas de clases (rectángulos grandes)
        detected_boxes = self._detect_class_boxes(binary, gray, w, h)

        # Si no se detectaron rectángulos suficientes con adaptive, probar con Canny + Contornos
        if len(detected_boxes) < 2:
            detected_boxes = self._detect_boxes_morphology(gray, w, h)

        # 3. Extraer texto y compartimentos de cada caja
        diagram = UMLDiagram(name="Diagrama Interpretado de Fotografía")

        for box in detected_boxes:
            box_roi = gray[box.y:box.y + box.h, box.x:box.x + box.w]
            text = self._ocr_roi(box_roi)
            box.raw_text = text

            uml_class = self._parse_class_text(text, box)
            box.parsed_class = uml_class
            diagram.classes.append(uml_class)

        # 4. Detectar conexiones / líneas entre cajas
        lines = self._detect_relationships(binary, detected_boxes)
        for line in lines:
            if line.source_box_id and line.target_box_id:
                rel = UMLRelationship(
                    type=line.rel_type,
                    source=RelationshipEnd(class_id=line.source_box_id),
                    target=RelationshipEnd(class_id=line.target_box_id),
                )
                diagram.relationships.append(rel)

        # Si no se detectó nada (ej. imagen muy borrosa o texto ilegible), agregar ejemplo guiado
        if not diagram.classes:
            self.warnings.append("No se detectaron cajas de clase con suficiente contraste. Se sugiere revisar la iluminación.")
            return self._fallback_interpretation()

        overall_conf = 0.85 if len(detected_boxes) >= 2 else 0.65

        return {
            "success": True,
            "diagram": diagram.to_dict(),
            "confidence": overall_conf,
            "detectedClassCount": len(diagram.classes),
            "detectedRelationshipCount": len(diagram.relationships),
            "detectedBoxes": [
                {"id": b.id, "x": b.x, "y": b.y, "w": b.w, "h": b.h, "name": b.parsed_class.name if b.parsed_class else "Desconocida"}
                for b in detected_boxes
            ],
            "reviewNotes": self.review_notes,
            "warnings": self.warnings,
        }

    def _detect_class_boxes(self, binary: np.ndarray, gray: np.ndarray, img_w: int, img_h: int) -> List[DetectedBox]:
        """Detecta contornos rectangulares que corresponden a clases UML."""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(binary, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        boxes: List[DetectedBox] = []

        min_area = (img_w * img_h) * 0.005  # al menos 0.5% del área total
        max_area = (img_w * img_h) * 0.40   # no más del 40%

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / max(h, 1)

                # Clases UML suelen ser de proporciones entre 0.4 y 3.5
                if 0.4 <= aspect_ratio <= 3.5 and w > 60 and h > 50:
                    # Evitar duplicados contenidos dentro de otra caja
                    is_nested = False
                    for existing in boxes:
                        if (existing.x <= x <= existing.x + existing.w and
                            existing.y <= y <= existing.y + existing.h):
                            is_nested = True
                            break
                    if not is_nested:
                        boxes.append(DetectedBox(id=str(uuid.uuid4()), x=x, y=y, w=w, h=h))

        return boxes

    def _detect_boxes_morphology(self, gray: np.ndarray, img_w: int, img_h: int) -> List[DetectedBox]:
        """Estrategia alternativa mediante kernels horizontales y verticales."""
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Líneas horizontales
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=2)

        # Líneas verticales
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel, iterations=2)

        table_structure = cv2.add(h_lines, v_lines)
        contours, _ = cv2.findContours(table_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        boxes: List[DetectedBox] = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 80 and h > 60 and (w * h) > (img_w * img_h * 0.008):
                boxes.append(DetectedBox(id=str(uuid.uuid4()), x=x, y=y, w=w, h=h))

        return boxes

    def _ocr_roi(self, roi: np.ndarray) -> str:
        """Aplica OCR sobre una región de interés."""
        if not PYTESSERACT_AVAILABLE:
            return ""

        try:
            # Preprocesar ROI para mejorar OCR
            resized = cv2.resize(roi, None, fx=1.8, fy=1.8, interpolation=cv2.INTER_CUBIC)
            denoised = cv2.fastNlMeansDenoising(resized, h=10)
            text = pytesseract.image_to_string(denoised, config="--psm 6")
            return text.strip()
        except Exception:
            return ""

    def _parse_class_text(self, text: str, box: DetectedBox) -> UMLClass:
        """Interpreta el texto extraído con OCR para construir la clase UML."""
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        class_name = f"Clase_{box.x // 100}_{box.y // 100}"
        is_interface = False
        attributes: List[UMLAttribute] = []
        operations: List[UMLOperation] = []

        if lines:
            first_line = lines[0]
            if "interface" in first_line.lower():
                is_interface = True
                cleaned = re.sub(r'<<[^>]+>>', '', first_line).replace("interface", "").strip()
                if cleaned:
                    class_name = self._sanitize_identifier(cleaned)
            else:
                cleaned = re.sub(r'<<[^>]+>>', '', first_line).strip()
                if cleaned:
                    class_name = self._sanitize_identifier(cleaned)

        # Parsear resto de líneas
        for line in lines[1:]:
            # Chequear si es operación: tiene paréntesis ()
            if "(" in line and ")" in line:
                op = self._parse_operation_line(line)
                if op:
                    operations.append(op)
            else:
                attr = self._parse_attribute_line(line)
                if attr:
                    attributes.append(attr)

        # Si no se detectaron atributos, agregar id por defecto
        if not attributes:
            attributes.append(UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE))

        uml_cls = UMLClass(
            id=box.id,
            name=class_name,
            is_interface=is_interface,
            attributes=attributes,
            operations=operations,
            position=Position(x=float(box.x), y=float(box.y)),
            size=Size(width=float(box.w), height=float(box.h)),
        )

        return uml_cls

    def _parse_attribute_line(self, line: str) -> Optional[UMLAttribute]:
        """Parsea una línea de texto de atributo UML: [+-#~] nombre: Tipo [= valor]"""
        vis = Visibility.PRIVATE
        if line.startswith("+"):
            vis = Visibility.PUBLIC
            line = line[1:].strip()
        elif line.startswith("-"):
            vis = Visibility.PRIVATE
            line = line[1:].strip()
        elif line.startswith("#"):
            vis = Visibility.PROTECTED
            line = line[1:].strip()
        elif line.startswith("~"):
            vis = Visibility.PACKAGE
            line = line[1:].strip()

        # Separar por dos puntos
        if ":" in line:
            parts = line.split(":", 1)
            name = self._sanitize_identifier(parts[0].strip())
            type_str = parts[1].strip().split("=")[0].strip()
            type_str = self._sanitize_identifier(type_str) or "String"
        else:
            tokens = line.split()
            if len(tokens) >= 2:
                name = self._sanitize_identifier(tokens[0])
                type_str = self._sanitize_identifier(tokens[1])
            elif tokens:
                name = self._sanitize_identifier(tokens[0])
                type_str = "String"
            else:
                return None

        if not name:
            return None

        return UMLAttribute(name=name, type=type_str, visibility=vis)

    def _parse_operation_line(self, line: str) -> Optional[UMLOperation]:
        """Parsea una línea de texto de método UML: [+-#~] metodo(p1: T1): TipoRetorno"""
        vis = Visibility.PUBLIC
        if line.startswith("+"):
            vis = Visibility.PUBLIC
            line = line[1:].strip()
        elif line.startswith("-"):
            vis = Visibility.PRIVATE
            line = line[1:].strip()
        elif line.startswith("#"):
            vis = Visibility.PROTECTED
            line = line[1:].strip()
        elif line.startswith("~"):
            vis = Visibility.PACKAGE
            line = line[1:].strip()

        match = re.match(r'([A-Za-z0-9_]+)\s*\((.*?)\)(?:\s*:\s*([A-Za-z0-9_]+))?', line)
        if not match:
            return None

        op_name = self._sanitize_identifier(match.group(1))
        params_str = match.group(2) or ""
        return_type = match.group(3) or "void"

        params: List[UMLParameter] = []
        if params_str.strip():
            for p_chunk in params_str.split(","):
                if ":" in p_chunk:
                    p_name, p_type = p_chunk.split(":", 1)
                    params.append(UMLParameter(name=p_name.strip(), type=p_type.strip()))
                else:
                    params.append(UMLParameter(name=p_chunk.strip(), type="String"))

        return UMLOperation(
            name=op_name,
            visibility=vis,
            parameters=params,
            return_type=return_type,
        )

    def _detect_relationships(self, binary: np.ndarray, boxes: List[DetectedBox]) -> List[DetectedLine]:
        """Detecta líneas conectando las cajas de clases."""
        if len(boxes) < 2:
            return []

        lines: List[DetectedLine] = []

        # Usar HoughLinesP para detectar segmentos de línea recta
        hough_lines = cv2.HoughLinesP(
            binary, 1, np.pi / 180, threshold=40,
            minLineLength=30, maxLineGap=15
        )

        if hough_lines is None:
            # Inferencia de proximidad cuando las líneas tienen pequeños quiebres
            return self._infer_closest_connections(boxes)

        for line_seg in hough_lines:
            coords = line_seg.flatten()
            if len(coords) < 4:
                continue
            x1, y1, x2, y2 = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
            src_box = self._find_closest_box((x1, y1), boxes)
            dst_box = self._find_closest_box((x2, y2), boxes)

            if src_box and dst_box and src_box.id != dst_box.id:
                # Evitar duplicados
                already_exists = any(
                    (l.source_box_id == src_box.id and l.target_box_id == dst_box.id) or
                    (l.source_box_id == dst_box.id and l.target_box_id == src_box.id)
                    for l in lines
                )
                if not already_exists:
                    lines.append(DetectedLine(
                        start_pt=(x1, y1),
                        end_pt=(x2, y2),
                        source_box_id=src_box.id,
                        target_box_id=dst_box.id,
                        rel_type=RelationshipType.ASSOCIATION,
                    ))

        if not lines:
            lines = self._infer_closest_connections(boxes)

        return lines

    def _find_closest_box(self, pt: Tuple[int, int], boxes: List[DetectedBox], max_dist: float = 60.0) -> Optional[DetectedBox]:
        px, py = pt
        best_box = None
        min_d = float('inf')

        for b in boxes:
            # Distancia al borde del rectángulo
            dx = max(b.x - px, 0, px - (b.x + b.w))
            dy = max(b.y - py, 0, py - (b.y + b.h))
            dist = math.hypot(dx, dy)
            if dist < min_d and dist <= max_dist:
                min_d = dist
                best_box = b

        return best_box

    def _infer_closest_connections(self, boxes: List[DetectedBox]) -> List[DetectedLine]:
        """Conecta clases espacialmente contiguas como sugerencia tentadora con aviso para revisión."""
        lines = []
        if len(boxes) >= 2:
            for i in range(len(boxes) - 1):
                b1 = boxes[i]
                b2 = boxes[i + 1]
                lines.append(DetectedLine(
                    start_pt=(b1.x + b1.w // 2, b1.y + b1.h // 2),
                    end_pt=(b2.x + b2.w // 2, b2.y + b2.h // 2),
                    source_box_id=b1.id,
                    target_box_id=b2.id,
                    rel_type=RelationshipType.ASSOCIATION,
                    confidence=0.60,
                ))
            self.review_notes.append("Se infirieron relaciones tentativas por contigüidad espacial. Por favor confirmar las multiplicidades y tipos.")
        return lines

    def _sanitize_identifier(self, raw: str) -> str:
        clean = re.sub(r'[^A-Za-z0-9_]', '', raw)
        return clean.strip()

    def _fallback_interpretation(self) -> Dict[str, Any]:
        """Genera una estructura de partida cuando la imagen no es interpretable automáticamente."""
        diag = UMLDiagram(name="Diagrama desde Fotografía")
        c1 = UMLClass(
            name="EntidadA",
            attributes=[UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE), UMLAttribute(name="nombre", type="String", visibility=Visibility.PUBLIC)],
            position=Position(x=100.0, y=100.0)
        )
        c2 = UMLClass(
            name="EntidadB",
            attributes=[UMLAttribute(name="id", type="Long", visibility=Visibility.PRIVATE), UMLAttribute(name="descripcion", type="String", visibility=Visibility.PUBLIC)],
            position=Position(x=450.0, y=100.0)
        )
        diag.classes.extend([c1, c2])
        diag.relationships.append(
            UMLRelationship(
                type=RelationshipType.ASSOCIATION,
                source=RelationshipEnd(class_id=c1.id, multiplicity=Multiplicity.ONE),
                target=RelationshipEnd(class_id=c2.id, multiplicity=Multiplicity.MANY),
            )
        )

        return {
            "success": True,
            "isTemplate": True,
            "diagram": diag.to_dict(),
            "confidence": 0.40,
            "detectedClassCount": 2,
            "detectedRelationshipCount": 1,
            "detectedBoxes": [],
            "reviewNotes": [
                "ATENCIÓN: No fue posible segmentar con certeza los trazos de la fotografía.",
                "Se creó una PLANTILLA EDITABLE con 2 entidades y 1 relación de ejemplo.",
                "Debe ajustar manualmente los nombres de clases, atributos y relaciones.",
                "Sugerencia: Mejore la iluminación y contraste de la imagen y vuelva a intentar."
            ],
            "warnings": [
                "Baja nitidez o contraste en la imagen cargada.",
                "Los datos mostrados son una plantilla de ejemplo, NO fueron detectados de la imagen."
            ]
        }
