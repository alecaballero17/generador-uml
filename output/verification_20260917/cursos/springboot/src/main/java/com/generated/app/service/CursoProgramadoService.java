package com.generated.app.service;
import com.generated.app.entity.*;
import com.generated.app.dto.CursoProgramadoDto;
import com.generated.app.repository.CursoProgramadoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class CursoProgramadoService {
    private final CursoProgramadoRepository repository;
    @PersistenceContext private EntityManager em;
    public CursoProgramadoService(CursoProgramadoRepository repository) { this.repository = repository; }
    private CursoProgramado entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public CursoProgramadoDto toDto(CursoProgramado entity) {
        CursoProgramadoDto dto = new CursoProgramadoDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setTitulo(entity.getTitulo());
        dto.setFechaInicio(entity.getFechaInicio());
        dto.setActivo(entity.getActivo());
        dto.setInstructorId(entity.getInstructor() == null ? null : entity.getInstructor().getId());
        return dto;
    }
    private void apply(CursoProgramado entity, CursoProgramadoDto dto) {
        entity.setTitulo(dto.getTitulo());
        entity.setFechaInicio(dto.getFechaInicio());
        entity.setActivo(dto.getActivo());
        entity.setInstructor(resolve(Instructor.class, dto.getInstructorId()));
    }
    @Transactional(readOnly = true)
    public List<CursoProgramadoDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public CursoProgramadoDto findById(Long id) { return toDto(entity(id)); }
    public CursoProgramadoDto create(CursoProgramadoDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        CursoProgramado entity = new CursoProgramado(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public CursoProgramadoDto update(Long id, CursoProgramadoDto dto) {
        CursoProgramado entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
