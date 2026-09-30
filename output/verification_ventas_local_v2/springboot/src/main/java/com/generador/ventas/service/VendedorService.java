package com.generador.ventas.service;
import com.generador.ventas.entity.*;
import com.generador.ventas.dto.VendedorDto;
import com.generador.ventas.repository.VendedorRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class VendedorService {
    private final VendedorRepository repository;
    @PersistenceContext private EntityManager em;
    public VendedorService(VendedorRepository repository) { this.repository = repository; }
    private Vendedor entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public VendedorDto toDto(Vendedor entity) {
        VendedorDto dto = new VendedorDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setNombre(entity.getNombre());
        dto.setComision(entity.getComision());
        dto.setVentasIds(entity.getVentas().stream().map(x -> x.getId()).toList());
        return dto;
    }
    private void apply(Vendedor entity, VendedorDto dto) {
        entity.setNombre(dto.getNombre());
        entity.setComision(dto.getComision());
    }
    @Transactional(readOnly = true)
    public List<VendedorDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public VendedorDto findById(Long id) { return toDto(entity(id)); }
    public VendedorDto create(VendedorDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        Vendedor entity = new Vendedor(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public VendedorDto update(Long id, VendedorDto dto) {
        Vendedor entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
