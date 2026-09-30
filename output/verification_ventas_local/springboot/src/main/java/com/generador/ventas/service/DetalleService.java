package com.generador.ventas.service;
import com.generador.ventas.entity.*;
import com.generador.ventas.dto.DetalleDto;
import com.generador.ventas.repository.DetalleRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class DetalleService {
    private final DetalleRepository repository;
    @PersistenceContext private EntityManager em;
    public DetalleService(DetalleRepository repository) { this.repository = repository; }
    private Detalle entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public DetalleDto toDto(Detalle entity) {
        DetalleDto dto = new DetalleDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setCantidad(entity.getCantidad());
        dto.setPrecioUnitario(entity.getPrecioUnitario());
        dto.setVentaId(entity.getVenta() == null ? null : entity.getVenta().getId());
        dto.setProductoId(entity.getProducto() == null ? null : entity.getProducto().getId());
        return dto;
    }
    private void apply(Detalle entity, DetalleDto dto) {
        entity.setCantidad(dto.getCantidad());
        entity.setPrecioUnitario(dto.getPrecioUnitario());
        entity.setVenta(resolve(Venta.class, dto.getVentaId()));
        entity.setProducto(resolve(Producto.class, dto.getProductoId()));
    }
    @Transactional(readOnly = true)
    public List<DetalleDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public DetalleDto findById(Long id) { return toDto(entity(id)); }
    public DetalleDto create(DetalleDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        Detalle entity = new Detalle(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public DetalleDto update(Long id, DetalleDto dto) {
        Detalle entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
