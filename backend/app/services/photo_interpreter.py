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
    source_multiplicity: Optional[str] = None
    target_multiplicity: Optional[str] = None


class PhotoInterpreter:
    """Intérprete de fotografías de diagramas UML basado en Computer Vision y OCR."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd and PYTESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self.review_notes: List[str] = []
        self.warnings: List[str] = []

    def _normalize_illumination(self, gray: np.ndarray) -> np.ndarray:
        """Normaliza la iluminación en fotos de pizarras o papel, reduciendo sombras y gradientes."""
        if not CV2_AVAILABLE:
            return gray
        try:
            # Filtro bilateral para preservar bordes mientras reduce ruido de grano
            filtered = cv2.bilateralFilter(gray, 7, 50, 50)
            # CLAHE para ecualizar contraste local frente a sombras y gradientes de luz
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            return clahe.apply(filtered)
        except Exception:
            return gray

    def _estimate_deskew_angle(self, gray: np.ndarray) -> float:
        """Estima el ángulo de inclinación predominante (skew) de las líneas de cajas en la foto."""
        if not CV2_AVAILABLE:
            return 0.0
        try:
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=40, maxLineGap=20)
            if lines is None or len(lines) == 0:
                return 0.0

            angles = []
            for x1, y1, x2, y2 in lines.reshape(-1, 4):
                dx = x2 - x1
                dy = y2 - y1
                angle = math.degrees(math.atan2(dy, dx))
                # Normalizar alrededor del eje horizontal (-45 a 45)
                if angle < -45:
                    angle += 90
                elif angle > 45:
                    angle -= 90
                # Considerar solo inclinaciones sutiles típicas de fotos tomadas a mano (-15 a 15 grados)
                if 0.8 <= abs(angle) <= 15.0:
                    angles.append(angle)

            if not angles or len(angles) < 2:
                return 0.0

            median_angle = float(np.median(angles))
            return median_angle
        except Exception:
            return 0.0

    def _deskew_image(self, img: np.ndarray, angle: float) -> np.ndarray:
        """Rota la imagen según el ángulo estimado para rectificar las cajas y compartimentos."""
        if not CV2_AVAILABLE or abs(angle) < 0.5:
            return img
        try:
            h, w = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            deskewed = cv2.warpAffine(
                img, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            self.review_notes.append(f"Se corrigió la inclinación de la fotografía ({angle:.1f}°).")
            return deskewed
        except Exception:
            return img

    def interpret_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Procesa una imagen en bytes y retorna el diagrama UML y reporte de detección."""
        self.review_notes = []
        self.warnings = []

        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(pil_img)

        return self.interpret_numpy_image(img_np)

    def interpret_numpy_image(self, img_bgr_or_rgb: np.ndarray) -> Dict[str, Any]:
        """Pipeline principal de visión por computadora y OCR."""
        if not CV2_AVAILABLE or not PYTESSERACT_AVAILABLE:
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

        # 1. Preprocesamiento: normalización de iluminación contra sombras/gradientes
        normalized_gray = self._normalize_illumination(gray)
        skew_angle = self._estimate_deskew_angle(normalized_gray)
        if abs(skew_angle) >= 0.8:
            normalized_gray = self._deskew_image(normalized_gray, skew_angle)
            if len(img_bgr_or_rgb.shape) == 3:
                img_bgr_or_rgb = self._deskew_image(img_bgr_or_rgb, skew_angle)
        blurred = cv2.GaussianBlur(normalized_gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 15, 4
        )

        # 2. Detección de cajas de clases (rectángulos grandes)
        detected_boxes = self._detect_class_boxes(binary, normalized_gray, w, h)

        # Si no se detectaron rectángulos suficientes con adaptive, probar con Canny + Contornos
        if len(detected_boxes) < 2:
            detected_boxes = self._detect_boxes_morphology(normalized_gray, w, h)

        # 3. Extraer texto y compartimentos de cada caja
        diagram = UMLDiagram(name="Diagrama Interpretado de Fotografía")

        for box in detected_boxes:
            box_roi = gray[box.y:box.y + box.h, box.x:box.x + box.w]
            text = self._ocr_roi(box_roi)
            box.raw_text = text
            if not text.strip():
                self.warnings.append("Caja sin texto OCR; requiere revision manual.")
                continue

            uml_class = self._parse_class_text(text, box)
            box.parsed_class = uml_class
            diagram.classes.append(uml_class)

        # 4. Detectar conexiones / líneas entre cajas
        lines = self._detect_relationships(binary, [b for b in detected_boxes if b.parsed_class])
        for line in lines:
            if line.source_box_id and line.target_box_id:
                has_mult = line.rel_type in (RelationshipType.ASSOCIATION, RelationshipType.AGGREGATION, RelationshipType.COMPOSITION)
                src_mult = line.source_multiplicity if (has_mult and line.source_multiplicity) else "1"
                dst_mult = line.target_multiplicity if (has_mult and line.target_multiplicity) else "1"
                rel = UMLRelationship(
                    type=line.rel_type,
                    source=RelationshipEnd(class_id=line.source_box_id, multiplicity=src_mult),
                    target=RelationshipEnd(class_id=line.target_box_id, multiplicity=dst_mult),
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
        except Exception as e:
            err_str = str(e).lower()
            if "tesseract is not installed" in err_str or "not in your path" in err_str:
                warn = "Tesseract OCR no está en el PATH del sistema. Se detectó la geometría de las cajas. Para extracción completa de texto, instale Tesseract OCR."
                if warn not in self.warnings:
                    self.warnings.append(warn)
            return ""

    def _parse_class_text(self, text: str, box: DetectedBox) -> UMLClass:
        """Interpreta el texto extraído con OCR para construir la clase UML."""
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        class_name = f"Clase_{box.x // 100}_{box.y // 100}"
        is_interface = False
        is_abstract = False
        attributes: List[UMLAttribute] = []
        operations: List[UMLOperation] = []

        if lines:
            first_line = lines[0]
            first_lower = first_line.lower()
            if "interface" in first_lower:
                is_interface = True
                cleaned = re.sub(r'<<[^>]+>>', '', first_line).replace("interface", "").strip()
                if cleaned:
                    class_name = self._sanitize_identifier(cleaned)
            elif "abstract" in first_lower:
                is_abstract = True
                cleaned = re.sub(r'<<[^>]+>>', '', first_line).replace("abstract", "").strip()
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
            is_abstract=is_abstract,
            attributes=attributes,
            operations=operations,
            position=Position(x=float(box.x), y=float(box.y)),
            size=Size(width=float(box.w), height=float(box.h)),
        )

        return uml_cls

    def _parse_attribute_line(self, line: str) -> Optional[UMLAttribute]:
        """Parsea una línea de texto de atributo UML: [+-#~] [/] nombre: Tipo [multiplicidad] [= valor] [{restricciones}]"""
        vis = Visibility.PRIVATE
        if line.startswith("+"):
            vis = Visibility.PUBLIC
            line = line[1:].strip()
        elif line.startswith(("-", "–", "—", "•", "*")):
            vis = Visibility.PRIVATE
            line = line[1:].strip()
        elif line.startswith("#"):
            vis = Visibility.PROTECTED
            line = line[1:].strip()
        elif line.startswith("~"):
            vis = Visibility.PACKAGE
            line = line[1:].strip()

        is_derived = False
        if line.startswith("/"):
            is_derived = True
            line = line[1:].strip()

        # Extraer restricciones {id}, {unique}, etc.
        constraints: List[str] = []
        c_match = re.search(r'\{([^}]+)\}', line)
        if c_match:
            constraints.extend(c.strip().lower() for c in c_match.group(1).split(",") if c.strip())
            line = re.sub(r'\{[^}]+\}', '', line).strip()

        s_match = re.search(r'<<([^>]+)>>', line)
        if s_match:
            raw_s = s_match.group(1).lower()
            if "pk" in raw_s or "id" in raw_s:
                constraints.append("id")
            if "unique" in raw_s:
                constraints.append("unique")
            line = re.sub(r'<<[^>]+>>', '', line).strip()

        # Separar default value si existe
        default_val = None
        if "=" in line:
            parts = line.split("=", 1)
            default_val = parts[1].strip()
            line = parts[0].strip()

        # Separar por dos puntos
        if ":" in line:
            parts = line.split(":", 1)
            name = self._sanitize_identifier(parts[0].strip())
            type_str = parts[1].strip()
        else:
            tokens = line.split()
            if len(tokens) >= 2:
                name = self._sanitize_identifier(tokens[0])
                type_str = tokens[1].strip()
            elif tokens:
                name = self._sanitize_identifier(tokens[0])
                type_str = "String"
            else:
                return None

        # Extraer multiplicidad del tipo, ej. String[0..*] o List<int>
        multiplicity = None
        m_match = re.search(r'\[(.*?)\]', type_str)
        if m_match:
            multiplicity = m_match.group(1).strip() or "*"
            type_str = re.sub(r'\[.*?\]', '', type_str).strip()

        type_str = self._sanitize_identifier(type_str) or "String"

        if not name:
            return None

        return UMLAttribute(
            name=name,
            type=type_str,
            visibility=vis,
            multiplicity=multiplicity,
            default_value=default_val,
            is_derived=is_derived,
            constraints=constraints,
        )

    def _parse_operation_line(self, line: str) -> Optional[UMLOperation]:
        """Parsea una línea de texto de método UML: [+-#~] metodo(p1: T1 = def): TipoRetorno [{abstract/static}]"""
        vis = Visibility.PUBLIC
        if line.startswith("+"):
            vis = Visibility.PUBLIC
            line = line[1:].strip()
        elif line.startswith(("-", "–", "—", "•", "*")):
            vis = Visibility.PRIVATE
            line = line[1:].strip()
        elif line.startswith("#"):
            vis = Visibility.PROTECTED
            line = line[1:].strip()
        elif line.startswith("~"):
            vis = Visibility.PACKAGE
            line = line[1:].strip()

        is_abstract = False
        is_static = False
        if "{abstract}" in line.lower() or "<<abstract>>" in line.lower():
            is_abstract = True
            line = re.sub(r'\{abstract\}|<<abstract>>', '', line, flags=re.IGNORECASE).strip()
        if "{static}" in line.lower() or "<<static>>" in line.lower():
            is_static = True
            line = re.sub(r'\{static\}|<<static>>', '', line, flags=re.IGNORECASE).strip()

        match = re.match(r'([A-Za-z0-9_]+)\s*\((.*?)\)(?:\s*:\s*([A-Za-z0-9_]+))?', line)
        if not match:
            return None

        op_name = self._sanitize_identifier(match.group(1))
        params_str = match.group(2) or ""
        return_type = match.group(3) or "void"

        params: List[UMLParameter] = []
        if params_str.strip():
            for p_chunk in params_str.split(","):
                p_chunk = p_chunk.strip()
                def_val = None
                if "=" in p_chunk:
                    p_parts = p_chunk.split("=", 1)
                    def_val = p_parts[1].strip()
                    p_chunk = p_parts[0].strip()
                if ":" in p_chunk:
                    p_name, p_type = p_chunk.split(":", 1)
                    params.append(UMLParameter(
                        name=self._sanitize_identifier(p_name.strip()),
                        type=self._sanitize_identifier(p_type.strip()) or "String",
                        default_value=def_val
                    ))
                else:
                    params.append(UMLParameter(
                        name=self._sanitize_identifier(p_chunk),
                        type="String",
                        default_value=def_val
                    ))

        return UMLOperation(
            name=op_name,
            visibility=vis,
            parameters=params,
            return_type=return_type,
            is_abstract=is_abstract,
            is_static=is_static,
        )

    def _detect_relationships(self, binary: np.ndarray, boxes: List[DetectedBox]) -> List[DetectedLine]:
        """Detecta líneas conectando las cajas de clases e identifica tipos de relación.

        Pipeline:
        1. HoughLinesP detecta segmentos de línea
        2. Se agrupan segmentos colineales para formar conexiones box-a-box
        3. Se clasifican endpoints: flecha simple (asociación dirigida), triángulo
           hueco (herencia), rombo relleno (composición), rombo hueco (agregación)
        4. Se buscan multiplicidades con OCR en vecindad de cada endpoint
        5. Fallback: inferencia por proximidad espacial
        """
        if len(boxes) < 2:
            return []

        lines: List[DetectedLine] = []

        # Crear máscara que excluya el interior de las cajas detectadas
        box_mask = np.zeros_like(binary)
        for b in boxes:
            cv2.rectangle(box_mask, (b.x, b.y), (b.x + b.w, b.y + b.h), 255, -1)
        lines_only = cv2.bitwise_and(binary, cv2.bitwise_not(box_mask))

        # Usar HoughLinesP para detectar segmentos de línea recta
        hough_lines = cv2.HoughLinesP(
            lines_only, 1, np.pi / 180, threshold=30,
            minLineLength=20, maxLineGap=20
        )

        if hough_lines is None:
            # Fallback: inferencia por proximidad espacial
            return self._infer_closest_connections(boxes)

        # Agrupar segmentos colineales que conectan las mismas cajas
        raw_connections: Dict[tuple, List[Tuple[int, int, int, int]]] = {}
        for line_seg in hough_lines:
            coords = line_seg.flatten()
            if len(coords) < 4:
                continue
            x1, y1, x2, y2 = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])

            # Filtrar segmentos muy cortos (ruido)
            seg_len = math.hypot(x2 - x1, y2 - y1)
            if seg_len < 15:
                continue

            src_box = self._find_closest_box((x1, y1), boxes, max_dist=80.0)
            dst_box = self._find_closest_box((x2, y2), boxes, max_dist=80.0)

            if src_box and dst_box and src_box.id != dst_box.id:
                key = tuple(sorted([src_box.id, dst_box.id]))
                if key not in raw_connections:
                    raw_connections[key] = []
                raw_connections[key].append((x1, y1, x2, y2))

        crossings = self._detect_line_crossings(hough_lines, boxes)
        if crossings:
            for crossing in crossings:
                self.review_notes.append(
                    f"Posible cruce de líneas en ({crossing[0]},{crossing[1]}): revisa que las relaciones detectadas sean correctas."
                )

        for (box_id_a, box_id_b), segments in raw_connections.items():
            # Tomar el segmento más largo como representativo
            best_seg = max(segments, key=lambda s: math.hypot(s[2]-s[0], s[3]-s[1]))
            x1, y1, x2, y2 = best_seg

            # Determinar cuál extremo está cerca de box_a y cuál de box_b
            box_a = next(b for b in boxes if b.id == box_id_a)
            box_b = next(b for b in boxes if b.id == box_id_b)
            dist_1a = self._point_to_box_dist((x1, y1), box_a)
            dist_1b = self._point_to_box_dist((x1, y1), box_b)

            if dist_1a <= dist_1b:
                src_pt, dst_pt = (x1, y1), (x2, y2)
                src_id, dst_id = box_id_a, box_id_b
            else:
                src_pt, dst_pt = (x2, y2), (x1, y1)
                src_id, dst_id = box_id_b, box_id_a

            # Clasificar el tipo de relación por la forma de los endpoints en ambos extremos
            rel_type_dst, dst_marker = self._classify_endpoint_detailed(binary, dst_pt, src_pt)
            rel_type_src, src_marker = self._classify_endpoint_detailed(binary, src_pt, dst_pt)

            if rel_type_dst in (RelationshipType.COMPOSITION, RelationshipType.AGGREGATION):
                rel_type = rel_type_dst
                # En composición y agregación, el rombo está en el todo/contenedor (source)
                src_id, dst_id = dst_id, src_id
                src_pt, dst_pt = dst_pt, src_pt
            elif rel_type_src in (RelationshipType.COMPOSITION, RelationshipType.AGGREGATION):
                rel_type = rel_type_src
            elif rel_type_dst == RelationshipType.GENERALIZATION:
                # Check if it's a hollow triangle (realization) by marker info
                if dst_marker == 'hollow_triangle' and self._is_dashed_line(binary, src_pt, dst_pt):
                    rel_type = RelationshipType.REALIZATION
                    self.review_notes.append(
                        f"Triángulo hueco con línea discontinua en ({dst_pt[0]},{dst_pt[1]}): interpretado como REALIZACIÓN (implementa interfaz)."
                    )
                else:
                    rel_type = RelationshipType.GENERALIZATION
            elif rel_type_src == RelationshipType.GENERALIZATION:
                # En herencia el triángulo apunta al padre: el padre debe ser el destino (target)
                src_id, dst_id = dst_id, src_id
                src_pt, dst_pt = dst_pt, src_pt
                if src_marker == 'hollow_triangle' and self._is_dashed_line(binary, dst_pt, src_pt):
                    rel_type = RelationshipType.REALIZATION
                    self.review_notes.append(
                        f"Triángulo hueco con línea discontinua: interpretado como REALIZACIÓN (implementa interfaz)."
                    )
                else:
                    rel_type = RelationshipType.GENERALIZATION
            else:
                rel_type = RelationshipType.ASSOCIATION

            # Detectar multiplicidades cerca de los endpoints (después de la orientación definitiva)
            src_mult = self._detect_multiplicity_near(binary, src_pt)
            dst_mult = self._detect_multiplicity_near(binary, dst_pt)

            detected = DetectedLine(
                start_pt=src_pt,
                end_pt=dst_pt,
                source_box_id=src_id,
                target_box_id=dst_id,
                rel_type=rel_type,
                confidence=0.80 if rel_type != RelationshipType.ASSOCIATION else 0.75,
                source_multiplicity=src_mult,
                target_multiplicity=dst_mult,
            )

            # Build detailed annotation with multiplicities
            annotation_parts = []
            if src_mult:
                annotation_parts.append(f"src={src_mult}")
            if dst_mult:
                annotation_parts.append(f"dst={dst_mult}")
            if annotation_parts:
                detected.raw_annotation = ' '.join(annotation_parts)
                # Find class names for the review note
                src_name = next((b.parsed_class.name for b in boxes if b.id == src_id and b.parsed_class), src_id)
                dst_name = next((b.parsed_class.name for b in boxes if b.id == dst_id and b.parsed_class), dst_id)
                self.review_notes.append(
                    f"Multiplicidad detectada en {src_name}→{dst_name}: origen={src_mult or '?'}, destino={dst_mult or '?'} — confirmar manualmente."
                )

            # Check if this connection passes through a crossing zone
            for cx, cy in crossings:
                if self._segment_near_point(src_pt, dst_pt, (cx, cy), threshold=25):
                    detected.confidence = max(0.50, detected.confidence - 0.20)
                    src_name = next((b.parsed_class.name for b in boxes if b.id == src_id and b.parsed_class), src_id)
                    dst_name = next((b.parsed_class.name for b in boxes if b.id == dst_id and b.parsed_class), dst_id)
                    self.review_notes.append(
                        f"La relación {src_name}↔{dst_name} pasa por una zona de cruce — verificar que no sea una relación diferente."
                    )
                    break

            lines.append(detected)

        # Detectar conexiones ramificadas (ej: herencia con bifurcación en T)
        branched_lines = self._detect_branched_connections(hough_lines, boxes, binary)
        existing_pairs = {(line.source_box_id, line.target_box_id) for line in lines} | {(line.target_box_id, line.source_box_id) for line in lines}
        for br in branched_lines:
            if (br.source_box_id, br.target_box_id) not in existing_pairs and (br.target_box_id, br.source_box_id) not in existing_pairs:
                lines.append(br)
                existing_pairs.add((br.source_box_id, br.target_box_id))

        # Si HoughLines no encontró conexiones, usar proximidad
        if not lines:
            lines = self._infer_closest_connections(boxes)

        return lines

    def _detect_branched_connections(
        self,
        hough_lines: np.ndarray,
        boxes: List[DetectedBox],
        binary: np.ndarray
    ) -> List[DetectedLine]:
        """Detecta conexiones ramificadas (ej: herencia en T donde varias subclases
        se conectan a través de una barra horizontal o unión con un triángulo apuntando al padre)."""
        if len(boxes) < 2 or hough_lines is None:
            return []

        segments = []
        for line_seg in hough_lines:
            coords = line_seg.flatten()
            if len(coords) >= 4:
                x1, y1, x2, y2 = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
                if math.hypot(x2 - x1, y2 - y1) >= 12:
                    segments.append((x1, y1, x2, y2))

        if not segments:
            return []

        def pts_near(p1, p2, dist=25.0):
            return math.hypot(p1[0] - p2[0], p1[1] - p2[1]) <= dist

        def seg_near_point(s, pt, threshold=20.0):
            return self._segment_near_point((s[0], s[1]), (s[2], s[3]), pt, threshold=threshold)

        # Construir grafo de adyacencia entre segmentos conectados
        n = len(segments)
        adj: Dict[int, List[int]] = {i: [] for i in range(n)}
        for i in range(n):
            s1 = segments[i]
            p1a, p1b = (s1[0], s1[1]), (s1[2], s1[3])
            for j in range(i + 1, n):
                s2 = segments[j]
                p2a, p2b = (s2[0], s2[1]), (s2[2], s2[3])
                if (pts_near(p1a, p2a) or pts_near(p1a, p2b) or
                    pts_near(p1b, p2a) or pts_near(p1b, p2b) or
                    seg_near_point(s1, p2a) or seg_near_point(s1, p2b) or
                    seg_near_point(s2, p1a) or seg_near_point(s2, p1b)):
                    adj[i].append(j)
                    adj[j].append(i)

        # Encontrar componentes conexas de segmentos
        visited = set()
        components = []
        for i in range(n):
            if i not in visited:
                comp = []
                queue = [i]
                visited.add(i)
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)

        results = []
        for comp in components:
            if len(comp) < 2:
                continue

            # Cajas que tocan este componente conexo
            box_touches: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]] = {}
            for seg_idx in comp:
                s = segments[seg_idx]
                p1, p2 = (s[0], s[1]), (s[2], s[3])
                b1 = self._find_closest_box(p1, boxes, max_dist=70.0)
                if b1 and b1.id not in box_touches:
                    box_touches[b1.id] = (p1, p2)
                b2 = self._find_closest_box(p2, boxes, max_dist=70.0)
                if b2 and b2.id not in box_touches:
                    box_touches[b2.id] = (p2, p1)

            if len(box_touches) >= 2:
                # Comprobar si alguna caja tiene un marcador de triángulo apuntando a ella
                parent_box_id = None
                is_dashed = False
                for b_id, (pt_box, other_pt) in box_touches.items():
                    rel_type, marker = self._classify_endpoint_detailed(binary, pt_box, other_pt)
                    if rel_type == RelationshipType.GENERALIZATION or marker in ('triangle', 'hollow_triangle'):
                        parent_box_id = b_id
                        if marker == 'hollow_triangle' and self._is_dashed_line(binary, other_pt, pt_box):
                            is_dashed = True
                        break

                if parent_box_id:
                    parent_box = next((b for b in boxes if b.id == parent_box_id), None)
                    parent_name = parent_box.parsed_class.name if parent_box and parent_box.parsed_class else parent_box_id
                    rel_type = RelationshipType.REALIZATION if is_dashed else RelationshipType.GENERALIZATION

                    for child_id, (c_pt, c_other) in box_touches.items():
                        if child_id != parent_box_id:
                            child_box = next((b for b in boxes if b.id == child_id), None)
                            child_name = child_box.parsed_class.name if child_box and child_box.parsed_class else child_id

                            results.append(DetectedLine(
                                start_pt=c_pt,
                                end_pt=box_touches[parent_box_id][0],
                                source_box_id=child_id,
                                target_box_id=parent_box_id,
                                rel_type=rel_type,
                                confidence=0.82,
                                raw_annotation="branched_inheritance" if not is_dashed else "branched_realization"
                            ))
                            self.review_notes.append(
                                f"Herencia ramificada detectada: {child_name} hereda de {parent_name} a través de bifurcación en T."
                            )

        return results

    def _point_to_box_dist(self, pt: Tuple[int, int], box: DetectedBox) -> float:
        """Distancia de un punto al borde del rectángulo de la caja."""
        px, py = pt
        dx = max(box.x - px, 0, px - (box.x + box.w))
        dy = max(box.y - py, 0, py - (box.y + box.h))
        return math.hypot(dx, dy)

    def _classify_endpoint(self, binary: np.ndarray, tip_pt: Tuple[int, int],
                           origin_pt: Tuple[int, int]) -> RelationshipType:
        """Clasifica el tipo de relación analizando la forma del endpoint (punta de flecha).

        - Triángulo hueco grande → INHERITANCE (generalización)
        - Rombo relleno → COMPOSITION
        - Rombo hueco → AGGREGATION
        - Flecha simple / nada → ASSOCIATION
        """
        h, w = binary.shape[:2]
        tx, ty = tip_pt

        # Región de interés alrededor del endpoint (40x40 px)
        roi_size = 40
        rx1 = max(0, tx - roi_size)
        ry1 = max(0, ty - roi_size)
        rx2 = min(w, tx + roi_size)
        ry2 = min(h, ty + roi_size)

        if rx2 - rx1 < 10 or ry2 - ry1 < 10:
            return RelationshipType.ASSOCIATION

        roi = binary[ry1:ry2, rx1:rx2]

        # Detectar contornos en la ROI del endpoint
        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 80:
                continue  # ruido

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.06 * peri, True)
            num_vertices = len(approx)

            # Triángulo → herencia (3 vértices, área significativa)
            if num_vertices == 3 and area > 100:
                self.review_notes.append(
                    f"Triángulo detectado en ({tx},{ty}): interpretado como HERENCIA."
                )
                return RelationshipType.GENERALIZATION

            # Rombo → composición o agregación (4 vértices, rotado ~45°)
            if num_vertices == 4 and area > 80:
                # Verificar si es un rombo (ángulos internos ~90° en orientación diagonal)
                rect = cv2.minAreaRect(cnt)
                box_w, box_h = rect[1]
                if box_w > 0 and box_h > 0:
                    aspect = min(box_w, box_h) / max(box_w, box_h)
                    if aspect > 0.5:  # Forma aproximadamente cuadrada/romboidal
                        # Verificar si está relleno (ratio de píxeles blancos)
                        mask = np.zeros(roi.shape, dtype=np.uint8)
                        cv2.drawContours(mask, [cnt], -1, 255, -1)
                        fill_ratio = cv2.countNonZero(cv2.bitwise_and(roi, mask)) / max(area, 1)

                        if fill_ratio > 0.6:
                            self.review_notes.append(
                                f"Rombo relleno en ({tx},{ty}): interpretado como COMPOSICIÓN."
                            )
                            return RelationshipType.COMPOSITION
                        else:
                            self.review_notes.append(
                                f"Rombo hueco en ({tx},{ty}): interpretado como AGREGACIÓN."
                            )
                            return RelationshipType.AGGREGATION

        return RelationshipType.ASSOCIATION

    def _classify_endpoint_detailed(self, binary: np.ndarray, tip_pt: Tuple[int, int],
                                    origin_pt: Tuple[int, int]) -> Tuple[RelationshipType, str]:
        """Like _classify_endpoint but also returns the marker type string."""
        h, w = binary.shape[:2]
        tx, ty = tip_pt
        roi_size = 40
        rx1, ry1 = max(0, tx - roi_size), max(0, ty - roi_size)
        rx2, ry2 = min(w, tx + roi_size), min(h, ty + roi_size)
        if rx2 - rx1 < 10 or ry2 - ry1 < 10:
            return RelationshipType.ASSOCIATION, 'none'
        roi = binary[ry1:ry2, rx1:rx2]
        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 80:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.06 * peri, True)
            num_vertices = len(approx)
            if num_vertices == 3 and area > 100:
                # Check if filled or hollow
                mask = np.zeros(roi.shape, dtype=np.uint8)
                cv2.drawContours(mask, [cnt], -1, 255, -1)
                fill_ratio = cv2.countNonZero(cv2.bitwise_and(roi, mask)) / max(area, 1)
                marker = 'hollow_triangle' if fill_ratio < 0.55 else 'filled_triangle'
                self.review_notes.append(
                    f"Triángulo {'hueco' if marker == 'hollow_triangle' else 'relleno'} detectado en ({tx},{ty}): interpretado como HERENCIA."
                )
                return RelationshipType.GENERALIZATION, marker
            if num_vertices == 4 and area > 80:
                rect = cv2.minAreaRect(cnt)
                box_w, box_h = rect[1]
                if box_w > 0 and box_h > 0:
                    aspect = min(box_w, box_h) / max(box_w, box_h)
                    if aspect > 0.5:
                        mask = np.zeros(roi.shape, dtype=np.uint8)
                        cv2.drawContours(mask, [cnt], -1, 255, -1)
                        fill_ratio = cv2.countNonZero(cv2.bitwise_and(roi, mask)) / max(area, 1)
                        if fill_ratio > 0.6:
                            self.review_notes.append(f"Rombo relleno en ({tx},{ty}): interpretado como COMPOSICIÓN.")
                            return RelationshipType.COMPOSITION, 'filled_diamond'
                        else:
                            self.review_notes.append(f"Rombo hueco en ({tx},{ty}): interpretado como AGREGACIÓN.")
                            return RelationshipType.AGGREGATION, 'hollow_diamond'
        return RelationshipType.ASSOCIATION, 'none'

    def _is_dashed_line(self, binary: np.ndarray, pt1: Tuple[int, int], pt2: Tuple[int, int]) -> bool:
        """Checks if the line between two points appears dashed by sampling pixels along it."""
        num_samples = 30
        h, w = binary.shape[:2]
        transitions = 0
        prev_on = False
        for i in range(num_samples):
            t = i / max(num_samples - 1, 1)
            x = int(pt1[0] + t * (pt2[0] - pt1[0]))
            y = int(pt1[1] + t * (pt2[1] - pt1[1]))
            if 0 <= x < w and 0 <= y < h:
                on = binary[y, x] > 0
                if i > 0 and on != prev_on:
                    transitions += 1
                prev_on = on
        # A dashed line has many transitions (at least 4 on/off pairs)
        return transitions >= 8

    def _detect_line_crossings(self, hough_lines, boxes: List[DetectedBox]) -> List[Tuple[int, int]]:
        """Detect points where detected line segments cross each other (outside boxes)."""
        crossings = []
        if hough_lines is None:
            return crossings
        segments = []
        for line_seg in hough_lines:
            coords = line_seg.flatten()
            if len(coords) >= 4:
                segments.append((int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])))
        for i in range(len(segments)):
            for j in range(i + 1, len(segments)):
                pt = self._segment_intersection(segments[i], segments[j])
                if pt:
                    # Skip intersections inside boxes
                    inside = False
                    for b in boxes:
                        if b.x <= pt[0] <= b.x + b.w and b.y <= pt[1] <= b.y + b.h:
                            inside = True
                            break
                    if not inside:
                        crossings.append(pt)
        return crossings

    @staticmethod
    def _segment_intersection(seg1, seg2) -> Optional[Tuple[int, int]]:
        """Returns intersection point of two line segments, or None if they don't intersect."""
        x1, y1, x2, y2 = seg1
        x3, y3, x4, y4 = seg2
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
        if 0.05 <= t <= 0.95 and 0.05 <= u <= 0.95:  # Exclude near-endpoint intersections
            ix = int(x1 + t * (x2 - x1))
            iy = int(y1 + t * (y2 - y1))
            return (ix, iy)
        return None

    @staticmethod
    def _segment_near_point(seg_start, seg_end, point, threshold=25) -> bool:
        """Check if a point is within threshold distance of a line segment."""
        x1, y1 = seg_start
        x2, y2 = seg_end
        px, py = point
        dx, dy = x2 - x1, y2 - y1
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return math.hypot(px - x1, py - y1) <= threshold
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(px - proj_x, py - proj_y) <= threshold

    def _detect_multiplicity_near(self, binary: np.ndarray, pt: Tuple[int, int]) -> Optional[str]:
        """Busca texto de multiplicidad (0..1, 1..*, etc.) cerca de un endpoint de línea."""
        if not PYTESSERACT_AVAILABLE:
            return None

        h, w = binary.shape[:2]
        px, py = pt
        roi_margin = 45  # Wider search area for better OCR

        rx1 = max(0, px - roi_margin)
        ry1 = max(0, py - roi_margin)
        rx2 = min(w, px + roi_margin)
        ry2 = min(h, py + roi_margin)

        if rx2 - rx1 < 10 or ry2 - ry1 < 10:
            return None

        roi = binary[ry1:ry2, rx1:rx2]
        try:
            inv = cv2.bitwise_not(roi)
            # Scale up for better OCR of small text
            scaled = cv2.resize(inv, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            text = pytesseract.image_to_string(scaled, config="--psm 7 -c tessedit_char_whitelist=01234567890.*n").strip()
            # Patterns de multiplicidad UML: 0..1, 1..*, *, 0..*, 1, n
            mult_pattern = re.match(r'^([0-9n*]+(?:\.\.[0-9n*]+)?)$', text)
            if mult_pattern:
                return mult_pattern.group(1)
        except Exception:
            pass

        return None

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

    def _fallback_interpretation(self):
        return {"success": False, "isTemplate": False, "diagram": None,
                "confidence": None, "detectedClassCount": 0, "detectedRelationshipCount": 0,
                "detectedBoxes": [], "reviewNotes": [], "error": "No se reconocio un diagrama",
                "warnings": self.warnings + ["No se han inventado entidades. Revise la foto y la instalacion OCR."]}
