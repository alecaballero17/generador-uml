package com.generated.app.service;
import com.generated.app.entity.*;
import com.generated.app.dto.InstructorDto;
import com.generated.app.repository.InstructorRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class InstructorService {
    private final InstructorRepository repository;
    @PersistenceContext private EntityManager em;
    public InstructorService(InstructorRepository repository) { this.repository = repository; }
    private Instructor entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public InstructorDto toDto(Instructor entity) {
        InstructorDto dto = new InstructorDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setNombre(entity.getNombre());
        dto.setCursosIds(entity.getCursos().stream().map(x -> x.getId()).toList());
        return dto;
    }
    private void apply(Instructor entity, InstructorDto dto) {
        entity.setNombre(dto.getNombre());
    }
    @Transactional(readOnly = true)
    public List<InstructorDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public InstructorDto findById(Long id) { return toDto(entity(id)); }
    public InstructorDto create(InstructorDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        Instructor entity = new Instructor(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public InstructorDto update(Long id, InstructorDto dto) {
        Instructor entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
