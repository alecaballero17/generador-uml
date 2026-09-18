"""Typed REST DTO contract. Entity graphs never cross the HTTP boundary."""
from ..models.uml_model import RelationshipType


def relation_specs(gen, cls):
    specs = []
    for rel in gen.diagram.get_relationships_for_class(cls.id):
        if rel.type in (RelationshipType.GENERALIZATION, RelationshipType.REALIZATION, RelationshipType.DEPENDENCY):
            continue
        side = 'source' if rel.source.class_id == cls.id else 'target'
        own, other = (rel.source, rel.target) if side == 'source' else (rel.target, rel.source)
        many = other.multiplicity in ('*', '0..*', '1..*')
        own_many = own.multiplicity in ('*', '0..*', '1..*')
        field = gen._compute_field_name_for_side(rel, side)
        target = gen.diagram.get_class(other.class_id)
        if not target:
            continue
        # Owner is the many side for 1:N, source for 1:1 and N:M.
        owner = (side == 'source') if many == own_many else not many
        if rel.type in (RelationshipType.COMPOSITION, RelationshipType.AGGREGATION):
            owner = side == 'target' if many or own_many else side == 'source'
        specs.append(dict(field=field, key=field + ('Ids' if many else 'Id'),
                          target=target.name, many=many, owner=owner,
                          required=other.multiplicity in ('1', '1..*'),
                          set=many and own_many, relationship=rel.id))
    return specs


def attributes(diagram, cls, seen=None):
    seen = set() if seen is None else seen
    if cls.id in seen:
        return []
    seen.add(cls.id)
    inherited = [a for parent in diagram.get_parent_classes(cls.id) for a in attributes(diagram, parent, seen)]
    by_name = {a.name: a for a in inherited + cls.attributes if a.name != 'id'}
    return list(by_name.values())


def generate_rest(gen):
    from .springboot_generator import get_java_type, to_pascal_case, to_camel_case
    files = {}; base = f'src/main/java/{gen.package_path}'; pkg = gen.base_package
    for cls in gen.diagram.classes:
        if cls.is_interface or cls.is_abstract:
            continue
        name = to_pascal_case(cls.name); specs = relation_specs(gen, cls)
        attrs = attributes(gen.diagram, cls)
        fields = ['    private Long id;', '    private Long version;']
        reads = ['        dto.setId(entity.getId());', '        dto.setVersion(entity.getVersion());']
        writes = []
        for attr in attrs:
            field = to_camel_case(attr.name); cap = field[0].upper() + field[1:]
            jtype = get_java_type(attr.type, gen.diagram)
            required = attr.multiplicity == '1' or any('NotNull' in c or 'required' in c.lower() for c in attr.constraints)
            if required:
                fields.append('    @NotBlank' if jtype == 'String' else '    @NotNull')
            fields.append(f'    private {jtype} {field};')
            reads.append(f'        dto.set{cap}(entity.get{cap}());')
            writes.append(f'        entity.set{cap}(dto.get{cap}());')
        for spec in specs:
            cap = spec['field'][0].upper() + spec['field'][1:]
            dcap = spec['key'][0].upper() + spec['key'][1:]
            target = spec['target']; key = spec['key']
            if not spec['owner']:
                fields.append('    @JsonProperty(access = JsonProperty.Access.READ_ONLY)')
            elif spec['required']:
                fields.append('    @NotEmpty' if spec['many'] else '    @NotNull')
            fields.append(f"    private {'List<Long>' if spec['many'] else 'Long'} {key};")
            if spec['many']:
                reads.append(f'        dto.set{dcap}(entity.get{cap}().stream().map(x -> x.getId()).toList());')
            else:
                reads.append(f'        dto.set{dcap}(entity.get{cap}() == null ? null : entity.get{cap}().getId());')
            if spec['owner']:
                if spec['many']:
                    writes.extend([f'        entity.get{cap}().clear();', f'        if (dto.get{dcap}() != null) for (Long ref : dto.get{dcap}()) entity.get{cap}().add(resolve({target}.class, ref));'])
                else:
                    writes.append(f'        entity.set{cap}(resolve({target}.class, dto.get{dcap}()));')
        files[f'{base}/dto/{name}Dto.java'] = f'''package {pkg}.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class {name}Dto {{
{chr(10).join(fields)}
}}
'''
        files[f'{base}/service/{name}Service.java'] = f'''package {pkg}.service;
import {pkg}.entity.*;
import {pkg}.dto.{name}Dto;
import {pkg}.repository.{name}Repository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class {name}Service {{
    private final {name}Repository repository;
    @PersistenceContext private EntityManager em;
    public {name}Service({name}Repository repository) {{ this.repository = repository; }}
    private {name} entity(Long id) {{ return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }}
    private <T> T resolve(Class<T> type, Long id) {{
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }}
    public {name}Dto toDto({name} entity) {{
        {name}Dto dto = new {name}Dto();
{chr(10).join(reads)}
        return dto;
    }}
    private void apply({name} entity, {name}Dto dto) {{
{chr(10).join(writes)}
    }}
    @Transactional(readOnly = true)
    public List<{name}Dto> findAll() {{ return repository.findAll().stream().map(this::toDto).toList(); }}
    @Transactional(readOnly = true)
    public {name}Dto findById(Long id) {{ return toDto(entity(id)); }}
    public {name}Dto create({name}Dto dto) {{
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        {name} entity = new {name}(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }}
    public {name}Dto update(Long id, {name}Dto dto) {{
        {name} entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }}
    public void delete(Long id) {{ repository.delete(entity(id)); repository.flush(); }}
    public long count() {{ return repository.count(); }}
}}
'''
        endpoint = gen._get_endpoint_path(cls.name)
        files[f'{base}/controller/{name}Controller.java'] = f'''package {pkg}.controller;
import {pkg}.dto.{name}Dto;
import {pkg}.service.{name}Service;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/{endpoint}")
public class {name}Controller {{
    private final {name}Service service;
    public {name}Controller({name}Service service) {{ this.service = service; }}
    @GetMapping public List<{name}Dto> all() {{ return service.findAll(); }}
    @GetMapping("/{{id}}") public {name}Dto one(@PathVariable Long id) {{ return service.findById(id); }}
    @PostMapping public ResponseEntity<{name}Dto> create(@Valid @RequestBody {name}Dto dto) {{ return ResponseEntity.status(201).body(service.create(dto)); }}
    @PutMapping("/{{id}}") public {name}Dto update(@PathVariable Long id, @Valid @RequestBody {name}Dto dto) {{ return service.update(id, dto); }}
    @DeleteMapping("/{{id}}") public Map<String,Boolean> delete(@PathVariable Long id) {{ service.delete(id); return Map.of("deleted",true); }}
    @GetMapping("/count") public Map<String,Long> count() {{ return Map.of("count",service.count()); }}
}}
'''
    # Explicitly preserve HTTP status and classify persistence conflicts.
    files[f'{base}/exception/ContractExceptionHandler.java'] = f'''package {pkg}.exception;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.*;
import org.springframework.core.annotation.Order;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import java.util.Map;
@RestControllerAdvice @Order(-100)
public class ContractExceptionHandler {{
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<?> status(ResponseStatusException e) {{ return ResponseEntity.status(e.getStatusCode()).body(Map.of("message", e.getReason()==null?"Solicitud rechazada":e.getReason())); }}
    @ExceptionHandler({{DataIntegrityViolationException.class,ObjectOptimisticLockingFailureException.class}})
    public ResponseEntity<?> conflict(Exception e) {{ return ResponseEntity.status(409).body(Map.of("message","Conflicto: el registro cambio o tiene relaciones que impiden la operacion")); }}
}}
'''
    return files