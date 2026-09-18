package com.generated.app.service;
import com.generated.app.entity.*;
import com.generated.app.dto.MascotaDto;
import com.generated.app.repository.MascotaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class MascotaService {
    private final MascotaRepository repository;
    @PersistenceContext private EntityManager em;
    public MascotaService(MascotaRepository repository) { this.repository = repository; }
    private Mascota entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public MascotaDto toDto(Mascota entity) {
        MascotaDto dto = new MascotaDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setNombre(entity.getNombre());
        dto.setEspecie(entity.getEspecie());
        dto.setRaza(entity.getRaza());
        dto.setFechaNacimiento(entity.getFechaNacimiento());
        dto.setPeso(entity.getPeso());
        dto.setSexo(entity.getSexo());
        dto.setDueñoId(entity.getDueño() == null ? null : entity.getDueño().getId());
        dto.setCitasIds(entity.getCitas().stream().map(x -> x.getId()).toList());
        return dto;
    }
    private void apply(Mascota entity, MascotaDto dto) {
        entity.setNombre(dto.getNombre());
        entity.setEspecie(dto.getEspecie());
        entity.setRaza(dto.getRaza());
        entity.setFechaNacimiento(dto.getFechaNacimiento());
        entity.setPeso(dto.getPeso());
        entity.setSexo(dto.getSexo());
        entity.setDueño(resolve(Cliente.class, dto.getDueñoId()));
    }
    @Transactional(readOnly = true)
    public List<MascotaDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public MascotaDto findById(Long id) { return toDto(entity(id)); }
    public MascotaDto create(MascotaDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        Mascota entity = new Mascota(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public MascotaDto update(Long id, MascotaDto dto) {
        Mascota entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
