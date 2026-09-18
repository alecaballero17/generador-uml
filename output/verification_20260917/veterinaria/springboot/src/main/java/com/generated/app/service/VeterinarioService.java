package com.generated.app.service;
import com.generated.app.entity.*;
import com.generated.app.dto.VeterinarioDto;
import com.generated.app.repository.VeterinarioRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class VeterinarioService {
    private final VeterinarioRepository repository;
    @PersistenceContext private EntityManager em;
    public VeterinarioService(VeterinarioRepository repository) { this.repository = repository; }
    private Veterinario entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public VeterinarioDto toDto(Veterinario entity) {
        VeterinarioDto dto = new VeterinarioDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setNombre(entity.getNombre());
        dto.setApellido(entity.getApellido());
        dto.setEspecialidad(entity.getEspecialidad());
        dto.setMatricula(entity.getMatricula());
        dto.setTelefono(entity.getTelefono());
        dto.setCitasIds(entity.getCitas().stream().map(x -> x.getId()).toList());
        return dto;
    }
    private void apply(Veterinario entity, VeterinarioDto dto) {
        entity.setNombre(dto.getNombre());
        entity.setApellido(dto.getApellido());
        entity.setEspecialidad(dto.getEspecialidad());
        entity.setMatricula(dto.getMatricula());
        entity.setTelefono(dto.getTelefono());
    }
    @Transactional(readOnly = true)
    public List<VeterinarioDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public VeterinarioDto findById(Long id) { return toDto(entity(id)); }
    public VeterinarioDto create(VeterinarioDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        Veterinario entity = new Veterinario(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public VeterinarioDto update(Long id, VeterinarioDto dto) {
        Veterinario entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
