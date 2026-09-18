"""
GeneradorUML — Generador de Spring Boot

Genera un proyecto Spring Boot 3.x completo y compilable a partir de un diagrama UML.
Incluye: entidades JPA, repositorios, servicios, controladores REST, DTOs,
manejo de errores, configuración PostgreSQL, y colección Postman.

Decisión de arquitectura: Se utiliza Spring Data JPA con Hibernate como ORM.
Esta es una decisión del equipo de desarrollo, no una exigencia del docente.
"""

from __future__ import annotations
import os
import re
from typing import Optional
from ..models.uml_model import (
    UMLDiagram, UMLClass, UMLAttribute, UMLRelationship,
    RelationshipType, Visibility, UMLOperation
)


# Type mapping from UML/common types to Java types
UML_TO_JAVA_TYPE = {
    "String": "String",
    "Integer": "Integer",
    "int": "int",
    "Long": "Long",
    "long": "long",
    "Float": "Float",
    "float": "float",
    "Double": "Double",
    "double": "double",
    "Boolean": "Boolean",
    "boolean": "Boolean",
    "Date": "LocalDate",
    "LocalDate": "LocalDate",
    "LocalDateTime": "LocalDateTime",
    "BigDecimal": "BigDecimal",
    "Byte": "Byte",
    "byte": "byte",
    "Short": "Short",
    "short": "short",
    "Character": "Character",
    "char": "char",
    "Real": "Double",
    "void": "void",
    "Object": "Object",
}

# Imports needed for specific Java types
JAVA_TYPE_IMPORTS = {
    "LocalDate": "java.time.LocalDate",
    "LocalDateTime": "java.time.LocalDateTime",
    "BigDecimal": "java.math.BigDecimal",
    "List": "java.util.List",
    "Set": "java.util.Set",
    "ArrayList": "java.util.ArrayList",
    "HashSet": "java.util.HashSet",
}


def to_pascal_case(name: str) -> str:
    """Convert a name to PascalCase."""
    if not name:
        return name
    # Already PascalCase
    if name[0].isupper() and "_" not in name:
        return name
    # snake_case to PascalCase
    return "".join(word[:1].upper() + word[1:] for word in name.split("_") if word)


def to_camel_case(name: str) -> str:
    """Convert a name to camelCase."""
    pascal = to_pascal_case(name)
    if not pascal:
        return pascal
    return pascal[0].lower() + pascal[1:]


def to_snake_case(name: str) -> str:
    """Convert PascalCase or camelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def pluralize(name: str) -> str:
    """Simple English pluralization."""
    if name.endswith("s") or name.endswith("x") or name.endswith("z"):
        return name + "es"
    if name.endswith("y") and name[-2:] not in ("ay", "ey", "oy", "uy"):
        return name[:-1] + "ies"
    return name + "s"


def get_java_type(uml_type: str, diagram: UMLDiagram) -> str:
    """Convert a UML type to its Java equivalent."""
    if uml_type in UML_TO_JAVA_TYPE:
        return UML_TO_JAVA_TYPE[uml_type]
    # Check if it's a class in the diagram
    for cls in diagram.classes:
        if cls.name == uml_type:
            return to_pascal_case(uml_type)
    # Default: use as-is
    return uml_type


def get_java_imports_for_type(java_type: str) -> list[str]:
    """Get required imports for a Java type."""
    imports = []
    if java_type in JAVA_TYPE_IMPORTS:
        imports.append(JAVA_TYPE_IMPORTS[java_type])
    return imports


class SpringBootGenerator:
    """Generates a complete Spring Boot project from a UML diagram."""

    def __init__(self, diagram: UMLDiagram, base_package: str = "com.generated.app",
                 output_dir: str = "generated-springboot"):
        self.diagram = diagram
        self.base_package = base_package
        self.output_dir = output_dir
        self.package_path = base_package.replace(".", "/")
        self._relationship_map: dict[str, list[tuple[UMLRelationship, str]]] = {}
        self._build_relationship_map()

    def _build_relationship_map(self):
        """Build a map of class_id -> [(relationship, role)] for quick lookup."""
        for rel in self.diagram.relationships:
            if rel.source.class_id not in self._relationship_map:
                self._relationship_map[rel.source.class_id] = []
            self._relationship_map[rel.source.class_id].append((rel, "source"))

            if rel.target.class_id not in self._relationship_map:
                self._relationship_map[rel.target.class_id] = []
            self._relationship_map[rel.target.class_id].append((rel, "target"))

    def generate(self) -> dict[str, str]:
        """Generate all files and return a dict of filepath -> content."""
        files = {}

        # POM
        files["pom.xml"] = self._generate_pom()

        # Application class
        src_base = f"src/main/java/{self.package_path}"
        files[f"{src_base}/Application.java"] = self._generate_application()

        # Config
        files[f"{src_base}/config/CorsConfig.java"] = self._generate_cors_config()
        files[f"{src_base}/config/SwaggerConfig.java"] = self._generate_swagger_config()

        # Exception handling
        files[f"{src_base}/exception/ResourceNotFoundException.java"] = self._generate_not_found_exception()
        files[f"{src_base}/exception/GlobalExceptionHandler.java"] = self._generate_global_exception_handler()
        files[f"{src_base}/exception/BadRequestException.java"] = self._generate_bad_request_exception()

        # Health
        files[f"{src_base}/controller/HealthController.java"] = self._generate_health_controller()

        # Generate per-entity files
        for cls in self.diagram.classes:
            if cls.is_interface:
                files[f"{src_base}/entity/{to_pascal_case(cls.name)}.java"] = self._generate_interface(cls)
                continue

            class_name = to_pascal_case(cls.name)

            files[f"{src_base}/entity/{class_name}.java"] = self._generate_entity(cls)
            files[f"{src_base}/repository/{class_name}Repository.java"] = self._generate_repository(cls)
            files[f"{src_base}/dto/{class_name}Dto.java"] = self._generate_dto(cls)
            files[f"{src_base}/service/{class_name}Service.java"] = self._generate_service(cls)
            files[f"{src_base}/controller/{class_name}Controller.java"] = self._generate_controller(cls)

        # Application properties
        files["src/main/resources/application.properties"] = self._generate_application_properties()
        files["src/main/resources/application-dev.properties"] = self._generate_dev_properties()
        files["src/test/resources/application-test.properties"] = "spring.datasource.url=jdbc:h2:mem:uml;DB_CLOSE_DELAY=-1\nspring.datasource.driver-class-name=org.h2.Driver\nspring.datasource.username=sa\nspring.datasource.password=\nspring.jpa.database-platform=org.hibernate.dialect.H2Dialect\nspring.jpa.hibernate.ddl-auto=create-drop\n"

        # Database schema SQL (PostgreSQL DDL)
        files["schema.sql"] = self._generate_sql_schema()
        files["src/main/resources/schema.sql"] = files["schema.sql"]

        # Tests
        test_base = f"src/test/java/{self.package_path}"
        files[f"{test_base}/ApplicationTests.java"] = self._generate_application_test()
        for cls in self.diagram.classes:
            if not cls.is_interface:
                class_name = to_pascal_case(cls.name)
                files[f"{test_base}/controller/{class_name}ControllerTest.java"] = self._generate_controller_test(cls)

        from .rest_contract import generate_rest
        files.update(generate_rest(self))
        # Old mock-controller tests used entity bodies; REST now exposes typed DTOs.
        files = {p: c for p, c in files.items() if not p.endswith("ControllerTest.java")}
        for cls in self.diagram.classes:
            if cls.is_abstract:
                name = to_pascal_case(cls.name)
                files.pop(f"{src_base}/controller/{name}Controller.java", None)
                files.pop(f"{src_base}/service/{name}Service.java", None)
        return files

    def generate_to_disk(self, base_path: str = None) -> list[str]:
        """Generate all files to disk. Returns list of created file paths."""
        if base_path is None:
            base_path = self.output_dir

        files = self.generate()
        created_files = []

        for filepath, content in files.items():
            full_path = os.path.join(base_path, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_files.append(full_path)

        return created_files

    # ─── POM ───────────────────────────────────────────────────────────────

    def _generate_pom(self) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>

    <groupId>{self.base_package}</groupId>
    <artifactId>{to_snake_case(self.diagram.name).replace(' ', '-')}</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <name>{self.diagram.name}</name>
    <description>Aplicación generada por GeneradorUML a partir del diagrama: {self.diagram.name}</description>

    <properties>
        <java.version>17</java.version>
        <lombok.version>1.18.36</lombok.version>
    </properties>

    <dependencies>
        <!-- Spring Boot Starters -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>

        <!-- PostgreSQL Driver -->
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Swagger/OpenAPI -->
        <dependency>
            <groupId>org.springdoc</groupId>
            <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
            <version>2.3.0</version>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>

        <!-- H2 for testing -->
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>test</scope>
        </dependency>

        <!-- Test -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <configuration>
                    <annotationProcessorPaths>
                        <path>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                            <version>${{lombok.version}}</version>
                        </path>
                    </annotationProcessorPaths>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
"""

    # ─── Application ───────────────────────────────────────────────────────

    def _generate_application(self) -> str:
        return f"""package {self.base_package};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {{

    public static void main(String[] args) {{
        SpringApplication.run(Application.class, args);
    }}
}}
"""

    # ─── Config ────────────────────────────────────────────────────────────

    def _generate_cors_config(self) -> str:
        return f"""package {self.base_package}.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

import java.util.Arrays;

@Configuration
public class CorsConfig {{

    @Bean
    public CorsFilter corsFilter() {{
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowCredentials(true);
        config.setAllowedOriginPatterns(Arrays.asList("*"));
        config.setAllowedHeaders(Arrays.asList("*"));
        config.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return new CorsFilter(source);
    }}
}}
"""

    def _generate_swagger_config(self) -> str:
        return f"""package {self.base_package}.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {{

    @Bean
    public OpenAPI customOpenAPI() {{
        return new OpenAPI()
            .info(new Info()
                .title("{self.diagram.name} API")
                .version("1.0.0")
                .description("API generada por GeneradorUML a partir del diagrama: {self.diagram.name}"));
    }}
}}
"""

    def _generate_health_controller(self) -> str:
        return f"""package {self.base_package}.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class HealthController {{

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {{
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "message", "Backend Spring Boot en línea",
            "timestamp", Instant.now().toString()
        ));
    }}
}}
"""

    # ─── Exceptions ────────────────────────────────────────────────────────

    def _generate_not_found_exception(self) -> str:
        return f"""package {self.base_package}.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(HttpStatus.NOT_FOUND)
public class ResourceNotFoundException extends RuntimeException {{

    public ResourceNotFoundException(String message) {{
        super(message);
    }}

    public ResourceNotFoundException(String resourceName, String fieldName, Object fieldValue) {{
        super(String.format("%s no encontrado con %s: '%s'", resourceName, fieldName, fieldValue));
    }}
}}
"""

    def _generate_bad_request_exception(self) -> str:
        return f"""package {self.base_package}.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(HttpStatus.BAD_REQUEST)
public class BadRequestException extends RuntimeException {{

    public BadRequestException(String message) {{
        super(message);
    }}
}}
"""

    def _generate_global_exception_handler(self) -> str:
        return f"""package {self.base_package}.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {{

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<Map<String, Object>> handleResourceNotFound(ResourceNotFoundException ex) {{
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now().toString());
        body.put("status", 404);
        body.put("error", "Not Found");
        body.put("message", ex.getMessage());
        return new ResponseEntity<>(body, HttpStatus.NOT_FOUND);
    }}

    @ExceptionHandler(BadRequestException.class)
    public ResponseEntity<Map<String, Object>> handleBadRequest(BadRequestException ex) {{
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now().toString());
        body.put("status", 400);
        body.put("error", "Bad Request");
        body.put("message", ex.getMessage());
        return new ResponseEntity<>(body, HttpStatus.BAD_REQUEST);
    }}

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidation(MethodArgumentNotValidException ex) {{
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now().toString());
        body.put("status", 400);
        body.put("error", "Validation Error");

        Map<String, String> errors = new HashMap<>();
        for (FieldError error : ex.getBindingResult().getFieldErrors()) {{
            errors.put(error.getField(), error.getDefaultMessage());
        }}
        body.put("errors", errors);
        return new ResponseEntity<>(body, HttpStatus.BAD_REQUEST);
    }}

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGeneral(Exception ex) {{
        Map<String, Object> body = new HashMap<>();
        body.put("timestamp", LocalDateTime.now().toString());
        body.put("status", 500);
        body.put("error", "Internal Server Error");
        body.put("message", ex.getMessage());
        return new ResponseEntity<>(body, HttpStatus.INTERNAL_SERVER_ERROR);
    }}
}}
"""

    # ─── Entity ────────────────────────────────────────────────────────────

    def _generate_interface(self, cls):
        methods = []
        for op in cls.operations:
            params = ", ".join(get_java_type(p.type, self.diagram) + " " + p.name for p in op.parameters)
            methods.append(f'    default {get_java_type(op.return_type, self.diagram)} {op.name}({params}) {{ throw new UnsupportedOperationException("Operacion UML sin regla de negocio implementada"); }}')
        return f"package {self.base_package}.entity;\nimport java.util.*;\nimport java.time.*;\nimport java.math.*;\npublic interface {to_pascal_case(cls.name)} {{\n" + "\n".join(methods) + "\n}\n"

    def _generate_entity(self, cls: UMLClass) -> str:
        class_name = to_pascal_case(cls.name)
        table_name = to_snake_case(cls.name)

        imports = set()
        imports.add("jakarta.persistence.*")
        imports.add("jakarta.validation.constraints.*")
        imports.add("lombok.*")
        imports.add("com.fasterxml.jackson.annotation.JsonManagedReference")
        imports.add("com.fasterxml.jackson.annotation.JsonBackReference")
        imports.add("com.fasterxml.jackson.annotation.JsonIgnoreProperties")

        fields = []
        extra_imports = set()

        # ID field (always add if not explicitly in attributes)
        has_id = any(a.name.lower() == "id" for a in cls.attributes)

        # Process attributes
        for attr in cls.attributes:
            java_type = get_java_type(attr.type, self.diagram)
            field_name = to_camel_case(attr.name)

            for imp in get_java_imports_for_type(java_type):
                extra_imports.add(imp)

            annotations = []
            if attr.name.lower() == "id":
                annotations.append("    @Id")
                annotations.append("    @GeneratedValue(strategy = GenerationType.IDENTITY)")
            else:
                col_parts = [f'name = "{to_snake_case(attr.name)}"']
                if "NotNull" in str(attr.constraints) or attr.multiplicity == "1":
                    col_parts.append("nullable = false")
                annotations.append(f"    @Column({', '.join(col_parts)})")

            # Validation annotations
            if java_type == "String":
                if any("NotNull" in c or "required" in c.lower() for c in attr.constraints):
                    annotations.append("    @NotBlank(message = \"" + attr.name + " es obligatorio\")")
                if any("Size" in c for c in attr.constraints):
                    annotations.append("    @Size(max = 255)")

            visibility_kw = "private"
            static_kw = "static " if attr.is_static else ""
            final_kw = "final " if attr.is_final else ""

            field_line = f"    {visibility_kw} {static_kw}{final_kw}{java_type} {field_name};"
            fields.append("\n".join(annotations) + "\n" + field_line if annotations else field_line)

        # Process relationships
        rel_fields = self._generate_relationship_fields(cls, extra_imports)
        fields.extend(rel_fields)

        # Build imports string
        import_lines = []
        for imp in sorted(imports):
            import_lines.append(f"import {imp};")
        for imp in sorted(extra_imports):
            import_lines.append(f"import {imp};")
        import_lines.append("")

        # Inheritance
        parent_classes = self.diagram.get_parent_classes(cls.id)
        extends_clause = ""
        if parent_classes:
            parent_name = to_pascal_case(parent_classes[0].name)
            extends_clause = f" extends {parent_name}"

        # Interface implementations
        implements_list = []
        for rel in self.diagram.relationships:
            if (rel.type == RelationshipType.REALIZATION and
                    rel.source.class_id == cls.id):
                iface = self.diagram.get_class(rel.target.class_id)
                if iface:
                    implements_list.append(to_pascal_case(iface.name))

        implements_clause = ""
        if implements_list:
            implements_clause = f" implements {', '.join(implements_list)}"

        abstract_kw = "abstract " if cls.is_abstract else ""

        # Inheritance strategy
        inheritance_annotation = ""
        children = self.diagram.get_child_classes(cls.id)
        if children and not parent_classes:
            inheritance_annotation = "@Inheritance(strategy = InheritanceType.JOINED)\n"

        # Add @Id field if not present
        id_field = ""
        if not has_id and not parent_classes:
            id_field = """
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
"""

        if not parent_classes:
            fields.append("    @Version\n    private Long version;")

        return f"""package {self.base_package}.entity;

{chr(10).join(import_lines)}
import java.util.List;
import java.util.ArrayList;
import java.util.Set;
import java.util.HashSet;

@Entity
@Table(name = "{table_name}")
{inheritance_annotation}@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties({{"hibernateLazyInitializer", "handler"}})
public {abstract_kw}class {class_name}{extends_clause}{implements_clause} {{
{id_field}
{chr(10).join(fields)}
}}
"""

    def _compute_field_name_for_side(self, rel: UMLRelationship, side: str) -> str:
        """Compute the Java field name that will be generated for a given side of a relationship.

        This is the single source of truth for field naming, used both for generating
        the field itself and for computing mappedBy values.
        """
        if side == "source":
            # When processing from the source side, the field points to the target
            target_cls = self.diagram.get_class(rel.target.class_id)
            if not target_cls:
                return "unknown"
            is_collection = (rel.target.multiplicity in ("*", "0..*", "1..*") or
                             rel.type in (RelationshipType.COMPOSITION, RelationshipType.AGGREGATION))
            return to_camel_case(rel.target.role or (pluralize(target_cls.name) if is_collection else target_cls.name))
        else:
            # When processing from the target side, the field points to the source
            source_cls = self.diagram.get_class(rel.source.class_id)
            if not source_cls:
                return "unknown"
            is_collection = rel.source.multiplicity in ("*", "0..*", "1..*")
            return to_camel_case(rel.source.role or (pluralize(source_cls.name) if is_collection else source_cls.name))

    def _generate_relationship_fields(self, cls: UMLClass, extra_imports: set) -> list[str]:
        """Generate JPA relationship fields for an entity."""
        fields = []

        for rel in self.diagram.relationships:
            if rel.type in (RelationshipType.GENERALIZATION, RelationshipType.REALIZATION,
                            RelationshipType.DEPENDENCY):
                continue

            if rel.source.class_id == cls.id:
                target_cls = self.diagram.get_class(rel.target.class_id)
                if not target_cls:
                    continue
                target_name = to_pascal_case(target_cls.name)
                field_name = self._compute_field_name_for_side(rel, "source")

                field = self._build_jpa_field(
                    rel, "source", target_name, field_name,
                    rel.source.multiplicity, rel.target.multiplicity, extra_imports
                )
                if field:
                    fields.append(field)

            elif rel.target.class_id == cls.id:
                source_cls = self.diagram.get_class(rel.source.class_id)
                if not source_cls:
                    continue
                source_name = to_pascal_case(source_cls.name)
                field_name = self._compute_field_name_for_side(rel, "target")

                field = self._build_jpa_field(
                    rel, "target", source_name, field_name,
                    rel.target.multiplicity, rel.source.multiplicity, extra_imports
                )
                if field:
                    fields.append(field)

        return fields

    @staticmethod
    def _reference_name(rel):
        import hashlib
        return "rel_" + hashlib.sha256(rel.id.encode()).hexdigest()[:20]

    def _build_jpa_field(self, rel: UMLRelationship, side: str,
                         related_class: str, field_name: str,
                         this_mult: str, other_mult: str,
                         extra_imports: set) -> Optional[str]:
        """Build a JPA annotated field for a relationship.

        The mappedBy value is computed by calling _compute_field_name_for_side
        for the OPPOSITE side, ensuring it always matches the actual field name.
        """
        this_many = this_mult in ("*", "0..*", "1..*")
        other_many = other_mult in ("*", "0..*", "1..*")

        annotations = []

        # mappedBy must reference the field name on the INVERSE entity that points back
        # to this entity. We compute it using the same logic used to generate that field.
        inverse_side = "target" if side == "source" else "source"
        inverse_field_name = self._compute_field_name_for_side(rel, inverse_side)

        if rel.type == RelationshipType.COMPOSITION:
            if side == "source":
                annotations = [
                    f'    @OneToMany(mappedBy = "{inverse_field_name}", '
                    f'cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)',
                    f'    @JsonManagedReference("{self._reference_name(rel)}")',
                ]
                return "\n".join(annotations) + f"\n    private List<{related_class}> {field_name} = new ArrayList<>();"
            else:
                annotations.append(f'    @ManyToOne(fetch = FetchType.LAZY)')
                annotations.append(f'    @JoinColumn(name = "{to_snake_case(related_class)}_id", nullable = false)')
                annotations.append(f'    @JsonBackReference("{self._reference_name(rel)}")')
                return "\n".join(annotations) + f"\n    private {related_class} {field_name};"

        elif rel.type == RelationshipType.AGGREGATION:
            if side == "source":
                annotations = [
                    f'    @OneToMany(mappedBy = "{inverse_field_name}", '
                    f'cascade = {{CascadeType.PERSIST, CascadeType.MERGE}}, fetch = FetchType.LAZY)',
                    f'    @JsonManagedReference("{self._reference_name(rel)}")',
                ]
                return "\n".join(annotations) + f"\n    private List<{related_class}> {field_name} = new ArrayList<>();"
            else:
                annotations.append(f'    @ManyToOne(fetch = FetchType.LAZY)')
                annotations.append(f'    @JoinColumn(name = "{to_snake_case(related_class)}_id")')
                annotations.append(f'    @JsonBackReference("{self._reference_name(rel)}")')
                return "\n".join(annotations) + f"\n    private {related_class} {field_name};"

        else:  # ASSOCIATION
            if not this_many and not other_many:
                # OneToOne
                if side == "source":
                    annotations.append(f'    @OneToOne(fetch = FetchType.LAZY)')
                    annotations.append(f'    @JoinColumn(name = "{to_snake_case(related_class)}_id")')
                    return "\n".join(annotations) + f"\n    private {related_class} {field_name};"
                else:
                    annotations.append(f'    @OneToOne(mappedBy = "{inverse_field_name}", fetch = FetchType.LAZY)')
                    return "\n".join(annotations) + f"\n    private {related_class} {field_name};"

            elif this_many and other_many:
                # ManyToMany
                if side == "source":
                    join_table = f"{to_snake_case(self.diagram.get_class(rel.source.class_id).name)}_{to_snake_case(related_class)}"
                    annotations.append(f'    @ManyToMany(fetch = FetchType.LAZY)')
                    annotations.append(f'    @JoinTable(name = "{join_table}",')
                    annotations.append(f'        joinColumns = @JoinColumn(name = "{to_snake_case(self.diagram.get_class(rel.source.class_id).name)}_id"),')
                    annotations.append(f'        inverseJoinColumns = @JoinColumn(name = "{to_snake_case(related_class)}_id"))')
                    return "\n".join(annotations) + f"\n    private Set<{related_class}> {field_name} = new HashSet<>();"
                else:
                    # For ManyToMany inverse, mappedBy references the field name on the SOURCE entity
                    source_field_name = self._compute_field_name_for_side(rel, "source")
                    annotations.append(f'    @ManyToMany(mappedBy = "{source_field_name}", fetch = FetchType.LAZY)')
                    return "\n".join(annotations) + f"\n    private Set<{related_class}> {field_name} = new HashSet<>();"

            elif other_many:
                # This side is "one", other side is "many" -> OneToMany on this side
                annotations.append(f'    @OneToMany(mappedBy = "{inverse_field_name}", fetch = FetchType.LAZY)')
                annotations.append(f'    @JsonManagedReference("{self._reference_name(rel)}")')
                return "\n".join(annotations) + f"\n    private List<{related_class}> {field_name} = new ArrayList<>();"

            else:
                # This side is "many", other side is "one" -> ManyToOne on this side
                annotations.append(f'    @ManyToOne(fetch = FetchType.LAZY)')
                annotations.append(f'    @JoinColumn(name = "{to_snake_case(related_class)}_id")')
                annotations.append(f'    @JsonBackReference("{self._reference_name(rel)}")')
                return "\n".join(annotations) + f"\n    private {related_class} {field_name};"

        return None

    # ─── Repository ────────────────────────────────────────────────────────

    def _generate_repository(self, cls: UMLClass) -> str:
        class_name = to_pascal_case(cls.name)
        return f"""package {self.base_package}.repository;

import {self.base_package}.entity.{class_name};
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface {class_name}Repository extends JpaRepository<{class_name}, Long> {{

    // Métodos de búsqueda generados automáticamente según atributos
{self._generate_finder_methods(cls)}
}}
"""

    def _generate_finder_methods(self, cls: UMLClass) -> str:
        """Generate Spring Data JPA finder methods for searchable attributes."""
        methods = []
        class_name = to_pascal_case(cls.name)

        for attr in cls.attributes:
            if attr.name.lower() == "id":
                continue
            java_type = get_java_type(attr.type, self.diagram)
            method_name = f"findBy{to_pascal_case(attr.name)}"
            param_name = to_camel_case(attr.name)

            if java_type == "String":
                methods.append(
                    f"    List<{class_name}> findBy{to_pascal_case(attr.name)}ContainingIgnoreCase({java_type} {param_name});"
                )
            else:
                methods.append(
                    f"    List<{class_name}> {method_name}({java_type} {param_name});"
                )

        return "\n".join(methods) if methods else "    // No se encontraron atributos para generar buscadores"

    # ─── DTO ───────────────────────────────────────────────────────────────

    def _generate_dto(self, cls: UMLClass) -> str:
        class_name = to_pascal_case(cls.name)

        dto_fields = []
        extra_imports = set()

        for attr in cls.attributes:
            java_type = get_java_type(attr.type, self.diagram)
            field_name = to_camel_case(attr.name)
            for imp in get_java_imports_for_type(java_type):
                extra_imports.add(imp)

            validation = ""
            if java_type == "String" and attr.name.lower() != "id":
                validation = "\n    @NotBlank(message = \"" + attr.name + " es obligatorio\")"

            dto_fields.append(f"{validation}\n    private {java_type} {field_name};")

        # Add relationship IDs
        for rel in self.diagram.relationships:
            if rel.type in (RelationshipType.GENERALIZATION, RelationshipType.REALIZATION,
                            RelationshipType.DEPENDENCY):
                continue

            if rel.source.class_id == cls.id:
                target = self.diagram.get_class(rel.target.class_id)
                if target:
                    other_mult = rel.target.multiplicity
                    if other_mult in ("*", "0..*", "1..*"):
                        dto_fields.append(f"\n    private List<Long> {to_camel_case(target.name)}Ids;")
                        extra_imports.add("java.util.List")
                    else:
                        dto_fields.append(f"\n    private Long {to_camel_case(target.name)}Id;")

            elif rel.target.class_id == cls.id:
                source = self.diagram.get_class(rel.source.class_id)
                if source:
                    other_mult = rel.source.multiplicity
                    if other_mult in ("*", "0..*", "1..*"):
                        dto_fields.append(f"\n    private List<Long> {to_camel_case(source.name)}Ids;")
                        extra_imports.add("java.util.List")
                    else:
                        dto_fields.append(f"\n    private Long {to_camel_case(source.name)}Id;")

        import_lines = [f"import {imp};" for imp in sorted(extra_imports)]

        return f"""package {self.base_package}.dto;

import jakarta.validation.constraints.*;
import lombok.*;
{chr(10).join(import_lines)}

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class {class_name}Dto {{
{chr(10).join(dto_fields)}
}}
"""

    # ─── Service ───────────────────────────────────────────────────────────

    def _generate_service(self, cls: UMLClass) -> str:
        class_name = to_pascal_case(cls.name)
        var_name = to_camel_case(cls.name)

        return f"""package {self.base_package}.service;

import {self.base_package}.entity.{class_name};
import {self.base_package}.dto.{class_name}Dto;
import {self.base_package}.repository.{class_name}Repository;
import {self.base_package}.exception.ResourceNotFoundException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional
public class {class_name}Service {{

    @Autowired
    private {class_name}Repository {var_name}Repository;

    public List<{class_name}> findAll() {{
        return {var_name}Repository.findAll();
    }}

    public {class_name} findById(Long id) {{
        return {var_name}Repository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("{class_name}", "id", id));
    }}

    public {class_name} create({class_name} {var_name}) {{
        return {var_name}Repository.save({var_name});
    }}

    public {class_name} update(Long id, {class_name} updated{class_name}) {{
        {class_name} existing = findById(id);
{self._generate_update_fields(cls)}
        return {var_name}Repository.save(existing);
    }}

    public void delete(Long id) {{
        {class_name} {var_name} = findById(id);
        {var_name}Repository.delete({var_name});
    }}

    public long count() {{
        return {var_name}Repository.count();
    }}
}}
"""

    def _generate_update_fields(self, cls: UMLClass) -> str:
        """Generate field-by-field update logic."""
        lines = []
        var_name = to_camel_case(cls.name)
        for attr in cls.attributes:
            if attr.name.lower() == "id":
                continue
            getter = f"get{to_pascal_case(attr.name)}()"
            setter = f"set{to_pascal_case(attr.name)}"
            lines.append(f"        existing.{setter}(updated{to_pascal_case(cls.name)}.{getter});")

        return "\n".join(lines) if lines else f"        // No hay atributos para actualizar"

    # ─── Controller ────────────────────────────────────────────────────────

    @staticmethod
    def _get_endpoint_path(class_name: str) -> str:
        """Compute the REST endpoint path for a class name.

        This is the single source of truth for endpoint naming.
        Uses snake_case pluralized converted to kebab-case.
        Example: OrdenCompra -> orden-compras
        """
        return to_snake_case(pluralize(class_name)).replace("_", "-")

    def _generate_controller(self, cls: UMLClass) -> str:
        class_name = to_pascal_case(cls.name)
        var_name = to_camel_case(cls.name)
        path = self._get_endpoint_path(cls.name)

        return f"""package {self.base_package}.controller;

import {self.base_package}.entity.{class_name};
import {self.base_package}.service.{class_name}Service;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/{path}")
public class {class_name}Controller {{

    @Autowired
    private {class_name}Service {var_name}Service;

    @GetMapping
    public ResponseEntity<List<{class_name}>> getAll() {{
        return ResponseEntity.ok({var_name}Service.findAll());
    }}

    @GetMapping("/{{id}}")
    public ResponseEntity<{class_name}> getById(@PathVariable Long id) {{
        return ResponseEntity.ok({var_name}Service.findById(id));
    }}

    @PostMapping
    public ResponseEntity<{class_name}> create(@Valid @RequestBody {class_name} {var_name}) {{
        {class_name} created = {var_name}Service.create({var_name});
        return new ResponseEntity<>(created, HttpStatus.CREATED);
    }}

    @PutMapping("/{{id}}")
    public ResponseEntity<{class_name}> update(@PathVariable Long id,
                                               @Valid @RequestBody {class_name} {var_name}) {{
        {class_name} updated = {var_name}Service.update(id, {var_name});
        return ResponseEntity.ok(updated);
    }}

    @DeleteMapping("/{{id}}")
    public ResponseEntity<Map<String, Boolean>> delete(@PathVariable Long id) {{
        {var_name}Service.delete(id);
        return ResponseEntity.ok(Map.of("deleted", true));
    }}

    @GetMapping("/count")
    public ResponseEntity<Map<String, Long>> count() {{
        return ResponseEntity.ok(Map.of("count", {var_name}Service.count()));
    }}
}}
"""

    # ─── Properties ────────────────────────────────────────────────────────

    def _generate_application_properties(self) -> str:
        db_name = to_snake_case(self.diagram.name).replace(" ", "_")
        return f"""# Configuración de la aplicación generada por GeneradorUML
spring.application.name={self.diagram.name}

# PostgreSQL
spring.datasource.url=${{DB_URL:jdbc:postgresql://localhost:5432/{db_name}}}
spring.datasource.username=${{DB_USER:postgres}}
spring.datasource.password=${{DB_PASSWORD:}}
spring.datasource.driver-class-name=org.postgresql.Driver

# JPA / Hibernate
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect

# Server
server.port=8080

# Swagger
springdoc.api-docs.path=/api-docs
springdoc.swagger-ui.path=/swagger-ui.html
"""

    def _generate_dev_properties(self) -> str:
        return """# Configuración de desarrollo
spring.jpa.hibernate.ddl-auto=create-drop
spring.jpa.show-sql=true
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.type.descriptor.sql.BasicBinder=TRACE
"""

    def _generate_sql_schema(self) -> str:
        """Genera el script SQL de creación de tablas PostgreSQL (DDL)."""
        sql_types = {
            "String": "VARCHAR(255)",
            "Integer": "INTEGER",
            "int": "INTEGER",
            "Long": "BIGINT",
            "long": "BIGINT",
            "Float": "REAL",
            "float": "REAL",
            "Double": "DOUBLE PRECISION",
            "double": "DOUBLE PRECISION",
            "Boolean": "BOOLEAN",
            "boolean": "BOOLEAN",
            "Date": "DATE",
            "LocalDate": "DATE",
            "LocalDateTime": "TIMESTAMP",
            "BigDecimal": "NUMERIC(12, 2)",
            "Byte": "SMALLINT",
            "byte": "SMALLINT",
            "Short": "SMALLINT",
            "short": "SMALLINT",
            "Character": "CHAR(1)",
            "char": "CHAR(1)",
        }

        db_name = to_snake_case(self.diagram.name).replace(" ", "_")
        lines = [
            f"-- ============================================================================",
            f"-- GeneradorUML — Script DDL PostgreSQL para '{self.diagram.name}'",
            f"-- Generado automáticamente",
            f"-- ============================================================================",
            f"",
            f"-- Descomentar si se ejecuta como superusuario:",
            f"-- CREATE DATABASE {db_name};",
            f"-- \\c {db_name};",
            f"",
        ]

        class_map = {c.id: c for c in self.diagram.classes}

        # First generate tables
        for cls in self.diagram.classes:
            if cls.is_interface:
                continue
            table_name = to_snake_case(cls.name)
            lines.append(f"-- Tabla: {table_name}")
            lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")
            col_defs = ["    id BIGSERIAL PRIMARY KEY"]

            for attr in cls.attributes:
                if attr.name.lower() == "id":
                    continue
                col_name = to_snake_case(attr.name)
                col_type = sql_types.get(attr.type, "VARCHAR(255)")
                col_defs.append(f"    {col_name} {col_type}")

            # Foreign keys from relationships where this class is target (child/dependent)
            for rel in self.diagram.relationships:
                if rel.target.class_id == cls.id and rel.type in (
                    RelationshipType.COMPOSITION,
                    RelationshipType.ASSOCIATION,
                    RelationshipType.AGGREGATION,
                ):
                    src_cls = class_map.get(rel.source.class_id)
                    if src_cls:
                        fk_col = f"{to_snake_case(src_cls.name)}_id"
                        on_delete = "CASCADE" if rel.type == RelationshipType.COMPOSITION else "SET NULL"
                        col_defs.append(f"    {fk_col} BIGINT REFERENCES {to_snake_case(src_cls.name)}(id) ON DELETE {on_delete}")

            lines.append(",\n".join(col_defs))
            lines.append(");")
            lines.append("")

        # Create indexes for foreign keys
        lines.append("-- Índices de optimización para Claves Foráneas")
        for rel in self.diagram.relationships:
            if rel.type in (RelationshipType.COMPOSITION, RelationshipType.ASSOCIATION, RelationshipType.AGGREGATION):
                src_cls = class_map.get(rel.source.class_id)
                tgt_cls = class_map.get(rel.target.class_id)
                if src_cls and tgt_cls and not tgt_cls.is_interface:
                    fk_col = f"{to_snake_case(src_cls.name)}_id"
                    tgt_table = to_snake_case(tgt_cls.name)
                    idx_name = f"idx_{tgt_table}_{fk_col}"
                    lines.append(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {tgt_table}({fk_col});")

        lines.append("")
        return "\n".join(lines)


    # ─── Tests ─────────────────────────────────────────────────────────────

    def _generate_application_test(self) -> str:
        return f"""package {self.base_package};

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("test")
class ApplicationTests {{

    @Test
    void contextLoads() {{
    }}
}}
"""

    def _generate_controller_test(self, cls: UMLClass) -> str:
        class_name = to_pascal_case(cls.name)
        var_name = to_camel_case(cls.name)
        path = self._get_endpoint_path(cls.name)

        return f"""package {self.base_package}.controller;

import {self.base_package}.entity.{class_name};
import {self.base_package}.service.{class_name}Service;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest({class_name}Controller.class)
class {class_name}ControllerTest {{

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private {class_name}Service {var_name}Service;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void shouldGetAll{class_name}s() throws Exception {{
        when({var_name}Service.findAll()).thenReturn(List.of());
        mockMvc.perform(get("/api/{path}"))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }}

    @Test
    void shouldReturn404WhenNotFound() throws Exception {{
        when({var_name}Service.findById(999L))
            .thenThrow(new {self.base_package}.exception.ResourceNotFoundException("{class_name}", "id", 999L));
        mockMvc.perform(get("/api/{path}/999"))
            .andExpect(status().isNotFound());
    }}
}}
"""
