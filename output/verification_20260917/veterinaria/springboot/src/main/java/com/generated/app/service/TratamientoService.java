package com.generated.app.service;
import com.generated.app.entity.*;
import com.generated.app.dto.TratamientoDto;
import com.generated.app.repository.TratamientoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class TratamientoService {
    private final TratamientoRepository repository;
    @PersistenceContext private EntityManager em;
    public TratamientoService(TratamientoRepository repository) { this.repository = repository; }
    private Tratamiento entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public TratamientoDto toDto(Tratamiento entity) {
        TratamientoDto dto = new TratamientoDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setDescripcion(entity.getDescripcion());
        dto.setMedicamento(entity.getMedicamento());
        dto.setDosis(entity.getDosis());
        dto.setDuracionDias(entity.getDuracionDias());
        dto.setCosto(entity.getCosto());
        dto.setCitaId(entity.getCita() == null ? null : entity.getCita().getId());
        return dto;
    }
    private void apply(Tratamiento entity, TratamientoDto dto) {
        entity.setDescripcion(dto.getDescripcion());
        entity.setMedicamento(dto.getMedicamento());
        entity.setDosis(dto.getDosis());
        entity.setDuracionDias(dto.getDuracionDias());
        entity.setCosto(dto.getCosto());
        entity.setCita(resolve(Cita.class, dto.getCitaId()));
    }
    @Transactional(readOnly = true)
    public List<TratamientoDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public TratamientoDto findById(Long id) { return toDto(entity(id)); }
    public TratamientoDto create(TratamientoDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        Tratamiento entity = new Tratamiento(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public TratamientoDto update(Long id, TratamientoDto dto) {
        Tratamiento entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
