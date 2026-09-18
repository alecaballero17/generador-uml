package com.generated.app.service;
import com.generated.app.entity.*;
import com.generated.app.dto.CitaDto;
import com.generated.app.repository.CitaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class CitaService {
    private final CitaRepository repository;
    @PersistenceContext private EntityManager em;
    public CitaService(CitaRepository repository) { this.repository = repository; }
    private Cita entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public CitaDto toDto(Cita entity) {
        CitaDto dto = new CitaDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setFecha(entity.getFecha());
        dto.setMotivo(entity.getMotivo());
        dto.setDiagnostico(entity.getDiagnostico());
        dto.setEstado(entity.getEstado());
        dto.setObservaciones(entity.getObservaciones());
        dto.setMascotaId(entity.getMascota() == null ? null : entity.getMascota().getId());
        dto.setVeterinarioId(entity.getVeterinario() == null ? null : entity.getVeterinario().getId());
        dto.setTratamientosIds(entity.getTratamientos().stream().map(x -> x.getId()).toList());
        return dto;
    }
    private void apply(Cita entity, CitaDto dto) {
        entity.setFecha(dto.getFecha());
        entity.setMotivo(dto.getMotivo());
        entity.setDiagnostico(dto.getDiagnostico());
        entity.setEstado(dto.getEstado());
        entity.setObservaciones(dto.getObservaciones());
        entity.setMascota(resolve(Mascota.class, dto.getMascotaId()));
        entity.setVeterinario(resolve(Veterinario.class, dto.getVeterinarioId()));
    }
    @Transactional(readOnly = true)
    public List<CitaDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public CitaDto findById(Long id) { return toDto(entity(id)); }
    public CitaDto create(CitaDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        Cita entity = new Cita(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public CitaDto update(Long id, CitaDto dto) {
        Cita entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
