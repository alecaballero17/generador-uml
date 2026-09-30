package com.generador.ventas.service;
import com.generador.ventas.entity.*;
import com.generador.ventas.dto.VentaDto;
import com.generador.ventas.repository.VentaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class VentaService {
    private final VentaRepository repository;
    @PersistenceContext private EntityManager em;
    public VentaService(VentaRepository repository) { this.repository = repository; }
    private Venta entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public VentaDto toDto(Venta entity) {
        VentaDto dto = new VentaDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setFecha(entity.getFecha());
        dto.setVendedorId(entity.getVendedor() == null ? null : entity.getVendedor().getId());
        dto.setClienteId(entity.getCliente() == null ? null : entity.getCliente().getId());
        dto.setDetallesIds(entity.getDetalles().stream().map(x -> x.getId()).toList());
        return dto;
    }
    private void apply(Venta entity, VentaDto dto) {
        entity.setFecha(dto.getFecha());
        entity.setVendedor(resolve(Vendedor.class, dto.getVendedorId()));
        entity.setCliente(resolve(Cliente.class, dto.getClienteId()));
    }
    @Transactional(readOnly = true)
    public List<VentaDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public VentaDto findById(Long id) { return toDto(entity(id)); }
    public VentaDto create(VentaDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        Venta entity = new Venta(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public VentaDto update(Long id, VentaDto dto) {
        Venta entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
