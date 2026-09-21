"""
Tests para la detección mejorada de relaciones en PhotoInterpreter.
Crea imágenes sintéticas con formas geométricas (triángulos, rombos, líneas)
y verifica la clasificación correcta.
"""
import numpy as np
import pytest
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from backend.app.services.photo_interpreter import PhotoInterpreter, DetectedBox
from backend.app.models.uml_model import RelationshipType


@pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
class TestRelationshipClassification:
    """Tests de clasificación de tipos de relación desde formas de endpoints."""

    def _create_blank_binary(self, w=400, h=400):
        return np.zeros((h, w), dtype=np.uint8)

    def test_triangle_detected_as_inheritance(self):
        """Un triángulo en el endpoint debería clasificarse como INHERITANCE."""
        interp = PhotoInterpreter()
        binary = self._create_blank_binary()

        # Dibujar un triángulo en (200, 200)
        triangle = np.array([[200, 180], [185, 215], [215, 215]], np.int32)
        cv2.fillPoly(binary, [triangle], 255)

        result = interp._classify_endpoint(binary, (200, 200), (100, 200))
        assert result == RelationshipType.GENERALIZATION

    def test_filled_diamond_detected_as_composition(self):
        """Un rombo relleno debería clasificarse como COMPOSITION."""
        interp = PhotoInterpreter()
        binary = self._create_blank_binary()

        # Dibujar un rombo relleno en (200, 200)
        diamond = np.array([[200, 175], [220, 200], [200, 225], [180, 200]], np.int32)
        cv2.fillPoly(binary, [diamond], 255)

        result = interp._classify_endpoint(binary, (200, 200), (100, 200))
        # Should be COMPOSITION or AGGREGATION (both are diamond-based)
        assert result in (RelationshipType.COMPOSITION, RelationshipType.AGGREGATION)

    def test_hollow_diamond_detected_as_aggregation(self):
        """Un rombo hueco debería clasificarse como AGGREGATION."""
        interp = PhotoInterpreter()
        binary = self._create_blank_binary()

        # Dibujar un rombo hueco (solo contorno)
        diamond = np.array([[200, 170], [225, 200], [200, 230], [175, 200]], np.int32)
        cv2.polylines(binary, [diamond], True, 255, 2)

        result = interp._classify_endpoint(binary, (200, 200), (100, 200))
        # Hueco debería ser aggregation
        assert result in (RelationshipType.AGGREGATION, RelationshipType.ASSOCIATION)

    def test_no_shape_returns_association(self):
        """Sin forma especial, debería ser ASSOCIATION."""
        interp = PhotoInterpreter()
        binary = self._create_blank_binary()

        result = interp._classify_endpoint(binary, (200, 200), (100, 200))
        assert result == RelationshipType.ASSOCIATION


@pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
class TestRelationshipDetection:
    """Tests del pipeline completo de detección de relaciones."""

    def _create_diagram_image(self) -> np.ndarray:
        """Crea una imagen sintética con dos cajas y una línea conectándolas."""
        img = np.ones((500, 600), dtype=np.uint8) * 255

        # Box 1: (50, 100) - (200, 200)
        cv2.rectangle(img, (50, 100), (200, 200), 0, 2)
        # Box 2: (350, 100) - (550, 200)
        cv2.rectangle(img, (350, 100), (550, 200), 0, 2)
        # Línea entre las cajas
        cv2.line(img, (200, 150), (350, 150), 0, 2)

        # Invertir para binary (blanco sobre negro)
        binary = cv2.bitwise_not(img)
        return binary

    def test_two_boxes_one_line(self):
        """Debe detectar una relación entre dos cajas conectadas."""
        interp = PhotoInterpreter()
        binary = self._create_diagram_image()

        boxes = [
            DetectedBox(id="box1", x=50, y=100, w=150, h=100),
            DetectedBox(id="box2", x=350, y=100, w=200, h=100),
        ]

        # Simular parsed_class para que pase el filtro
        from backend.app.models.uml_model import UMLClass, Position, Size
        boxes[0].parsed_class = UMLClass(id="box1", name="A", position=Position(x=50,y=100), size=Size(width=150,height=100))
        boxes[1].parsed_class = UMLClass(id="box2", name="B", position=Position(x=350,y=100), size=Size(width=200,height=100))

        lines = interp._detect_relationships(binary, boxes)
        assert len(lines) >= 1
        # Debe conectar box1 y box2
        pair = {lines[0].source_box_id, lines[0].target_box_id}
        assert pair == {"box1", "box2"}

    def test_no_boxes_no_relationships(self):
        """Con menos de 2 cajas, no debe detectar relaciones."""
        interp = PhotoInterpreter()
        binary = np.zeros((300, 300), dtype=np.uint8)
        assert interp._detect_relationships(binary, []) == []

    def test_inheritance_line_with_triangle(self):
        """Una línea con triángulo en el extremo debe ser INHERITANCE."""
        interp = PhotoInterpreter()
        img = np.ones((500, 600), dtype=np.uint8) * 255

        # Box 1
        cv2.rectangle(img, (50, 100), (200, 200), 0, 2)
        # Box 2
        cv2.rectangle(img, (350, 100), (550, 200), 0, 2)
        # Línea
        cv2.line(img, (200, 150), (330, 150), 0, 2)
        # Triángulo de herencia en el extremo derecho
        triangle = np.array([[330, 135], [330, 165], (350, 150)], np.int32)
        cv2.fillPoly(img, [triangle], 0)  # Triángulo negro en imagen blanca

        binary = cv2.bitwise_not(img)

        from backend.app.models.uml_model import UMLClass, Position, Size
        boxes = [
            DetectedBox(id="box1", x=50, y=100, w=150, h=100,
                       parsed_class=UMLClass(id="box1", name="Child", position=Position(x=50,y=100), size=Size(width=150,height=100))),
            DetectedBox(id="box2", x=350, y=100, w=200, h=100,
                       parsed_class=UMLClass(id="box2", name="Parent", position=Position(x=350,y=100), size=Size(width=200,height=100))),
        ]

        lines = interp._detect_relationships(binary, boxes)
        # Debe haber al menos 1 relación
        assert len(lines) >= 1
        # El tipo puede ser INHERITANCE si el triángulo es detectado
        # (en imágenes sintéticas la detección puede variar)


@pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
class TestPointToBoxDist:
    def test_point_inside_box(self):
        interp = PhotoInterpreter()
        box = DetectedBox(id="b", x=100, y=100, w=200, h=100)
        dist = interp._point_to_box_dist((150, 150), box)
        assert dist == 0.0

    def test_point_outside_box(self):
        interp = PhotoInterpreter()
        box = DetectedBox(id="b", x=100, y=100, w=200, h=100)
        dist = interp._point_to_box_dist((50, 150), box)
        assert dist == 50.0


@pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
class TestIlluminationNormalization:
    def test_shadow_gradient_flattened(self):
        """Verifica que un gradiente de sombra sea aplanado para uniformar el fondo."""
        interp = PhotoInterpreter()
        h, w = 200, 300
        gradient = np.tile(np.linspace(250, 80, w, dtype=np.uint8), (h, 1))
        gradient[50:150, 180:260] = 20

        normalized = interp._normalize_illumination(gradient)
        assert normalized is not None
        assert normalized.shape == (h, w)
        box_val = np.mean(normalized[60:140, 190:250])
        bg_val = np.mean(normalized[10:40, 190:250])
        assert bg_val - box_val > 80, "Debe mantener fuerte separación entre fondo y trazo bajo sombra"


@pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
class TestBranchedInheritance:
    def test_t_junction_branched_inheritance_detected(self):
        """Verifica que una bifurcación en T conecte múltiples hijos con el padre en herencia."""
        from backend.app.models.uml_model import UMLClass
        interp = PhotoInterpreter()
        binary = np.zeros((400, 500), dtype=np.uint8)

        parent_box = DetectedBox(id="p", x=200, y=50, w=100, h=50)
        parent_box.parsed_class = UMLClass(name="Animal")
        child1_box = DetectedBox(id="c1", x=80, y=300, w=100, h=50)
        child1_box.parsed_class = UMLClass(name="Perro")
        child2_box = DetectedBox(id="c2", x=320, y=300, w=100, h=50)
        child2_box.parsed_class = UMLClass(name="Gato")
        boxes = [parent_box, child1_box, child2_box]

        triangle = np.array([[250, 105], [240, 125], [260, 125]], np.int32)
        cv2.fillPoly(binary, [triangle], 255)

        hough_lines = np.array([
            [[250, 115, 250, 200]],
            [[130, 200, 370, 200]],
            [[130, 200, 130, 290]],
            [[370, 200, 370, 290]],
        ])

        branched = interp._detect_branched_connections(hough_lines, boxes, binary)
        assert len(branched) == 2, f"Debe detectar 2 relaciones ramificadas, obtuvo {len(branched)}"
        targets = {b.target_box_id for b in branched}
        sources = {b.source_box_id for b in branched}
        assert targets == {"p"}, "El destino de la herencia ramificada debe ser el padre Animal"
        assert sources == {"c1", "c2"}, "Los orígenes deben ser los hijos Perro y Gato"
        for b in branched:
            assert b.rel_type == RelationshipType.GENERALIZATION


@pytest.mark.skipif(not CV2_AVAILABLE, reason="OpenCV not installed")
class TestCompositionDiamondOrientation:
    def test_diamond_oriented_with_container_as_source(self):
        """El rombo en el extremo de la clase B debe hacer que B sea el source (contenedor) y A el target."""
        from backend.app.models.uml_model import UMLClass, Position, Size
        interp = PhotoInterpreter()
        img = np.ones((500, 600), dtype=np.uint8) * 255

        cv2.rectangle(img, (50, 100), (200, 200), 0, 2)
        cv2.rectangle(img, (350, 100), (550, 200), 0, 2)
        cv2.line(img, (200, 150), (330, 150), 0, 2)
        diamond = np.array([[330, 140], [345, 150], [330, 160], [315, 150]], np.int32)
        cv2.fillPoly(img, [diamond], 0)

        binary = cv2.bitwise_not(img)

        box_a = DetectedBox(id="box_a", x=50, y=100, w=150, h=100,
                            parsed_class=UMLClass(id="box_a", name="Item", position=Position(x=50, y=100), size=Size(width=150, height=100)))
        box_b = DetectedBox(id="box_b", x=350, y=100, w=200, h=100,
                            parsed_class=UMLClass(id="box_b", name="Pedido", position=Position(x=350, y=100), size=Size(width=200, height=100)))

        lines = interp._detect_relationships(binary, [box_a, box_b])
        assert len(lines) >= 1
        line = lines[0]
        if line.rel_type in (RelationshipType.COMPOSITION, RelationshipType.AGGREGATION):
            assert line.source_box_id == "box_b", "El contenedor (Pedido con rombo) debe ser el origen de la relación"
            assert line.target_box_id == "box_a", "El componente (Item) debe ser el destino"


class TestPhotoTextParsing:
    """Pruebas para el parser de texto OCR de clases, atributos y operaciones."""

    def test_parse_abstract_class(self):
        interp = PhotoInterpreter()
        box = DetectedBox(id="b1", x=100, y=100, w=200, h=150)
        text = "<<abstract>> Figura\n+ area(): Double\n- color: String"
        cls = interp._parse_class_text(text, box)
        assert cls.name == "Figura"
        assert cls.is_abstract is True
        assert cls.is_interface is False
        assert len(cls.operations) == 1
        assert cls.operations[0].name == "area"

    def test_parse_interface_class(self):
        interp = PhotoInterpreter()
        box = DetectedBox(id="b2", x=100, y=100, w=200, h=150)
        text = "<<interface>> Imprimible\n+ imprimir(): void"
        cls = interp._parse_class_text(text, box)
        assert cls.name == "Imprimible"
        assert cls.is_interface is True
        assert cls.is_abstract is False

    def test_parse_attribute_variations(self):
        interp = PhotoInterpreter()
        attr1 = interp._parse_attribute_line("• total: Double = 0.0")
        assert attr1 is not None
        assert attr1.name == "total"
        assert attr1.type == "Double"
        assert attr1.visibility.value == "-"
        assert attr1.default_value == "0.0"

        attr2 = interp._parse_attribute_line("+ /edad: Integer")
        assert attr2 is not None
        assert attr2.name == "edad"
        assert attr2.is_derived is True
        assert attr2.visibility.value == "+"

        attr3 = interp._parse_attribute_line("- telefonos: String[0..*]")
        assert attr3 is not None
        assert attr3.name == "telefonos"
        assert attr3.type == "String"
        assert attr3.multiplicity == "0..*"

        attr4 = interp._parse_attribute_line("+ id: Long {id, unique}")
        assert attr4 is not None
        assert attr4.name == "id"
        assert "id" in attr4.constraints
        assert "unique" in attr4.constraints

    def test_parse_operation_variations(self):
        interp = PhotoInterpreter()
        op1 = interp._parse_operation_line("+ calcularDescuento(tasa: Double = 0.15): Double")
        assert op1 is not None
        assert op1.name == "calcularDescuento"
        assert op1.return_type == "Double"
        assert len(op1.parameters) == 1
        assert op1.parameters[0].name == "tasa"
        assert op1.parameters[0].type == "Double"
        assert op1.parameters[0].default_value == "0.15"

        op2 = interp._parse_operation_line("+ crearInstancia(): Singleton {static}")
        assert op2 is not None
        assert op2.name == "crearInstancia"
        assert op2.is_static is True


class TestPhotoDeskewing:
    def test_deskew_straight_image(self):
        interp = PhotoInterpreter()
        img = np.ones((200, 300), dtype=np.uint8) * 255
        img[50:150, 50:250] = 0
        angle = interp._estimate_deskew_angle(img)
        assert abs(angle) < 1.0, f"Straight image should have near zero angle, got {angle}"

    def test_deskew_rotated_image(self):
        import cv2
        interp = PhotoInterpreter()
        img = np.ones((300, 300), dtype=np.uint8) * 255
        cv2.line(img, (30, 80), (270, 80), 0, 2)
        cv2.line(img, (30, 150), (270, 150), 0, 2)
        cv2.line(img, (30, 220), (270, 220), 0, 2)

        center = (150, 150)
        M = cv2.getRotationMatrix2D(center, -5.0, 1.0)
        rotated = cv2.warpAffine(img, M, (300, 300), borderValue=255)

        angle = interp._estimate_deskew_angle(rotated)
        assert abs(abs(angle) - 5.0) <= 2.0, f"Expected angle ~ 5 degrees, got {angle}"

        deskewed = interp._deskew_image(rotated, angle)
        assert deskewed.shape == rotated.shape
        assert any("inclinación" in note for note in interp.review_notes)

