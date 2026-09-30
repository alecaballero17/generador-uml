package com.generador.ventas.service;
import com.generador.ventas.entity.*;
import com.generador.ventas.dto.ProductoDto;
import com.generador.ventas.repository.ProductoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import jakarta.persistence.*;
import java.util.*;
@Service @Transactional
public class ProductoService {
    private final ProductoRepository repository;
    @PersistenceContext private EntityManager em;
    public ProductoService(ProductoRepository repository) { this.repository = repository; }
    private Producto entity(Long id) { return repository.findById(id).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Registro inexistente")); }
    private <T> T resolve(Class<T> type, Long id) {
        if (id == null) return null;
        T result = em.find(type, id);
        if (result == null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Referencia inexistente: " + type.getSimpleName());
        return result;
    }
    public ProductoDto toDto(Producto entity) {
        ProductoDto dto = new ProductoDto();
        dto.setId(entity.getId());
        dto.setVersion(entity.getVersion());
        dto.setNombre(entity.getNombre());
        dto.setPrecio(entity.getPrecio());
        dto.setStock(entity.getStock());
        dto.setDetallesIds(entity.getDetalles().stream().map(x -> x.getId()).toList());
        return dto;
    }
    private void apply(Producto entity, ProductoDto dto) {
        entity.setNombre(dto.getNombre());
        entity.setPrecio(dto.getPrecio());
        entity.setStock(dto.getStock());
    }
    @Transactional(readOnly = true)
    public List<ProductoDto> findAll() { return repository.findAll().stream().map(this::toDto).toList(); }
    @Transactional(readOnly = true)
    public ProductoDto findById(Long id) { return toDto(entity(id)); }
    public ProductoDto create(ProductoDto dto) {
        if (dto.getId() != null) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "El ID lo asigna el servidor");
        Producto entity = new Producto(); apply(entity, dto);
        return toDto(repository.saveAndFlush(entity));
    }
    public ProductoDto update(Long id, ProductoDto dto) {
        Producto entity = entity(id);
        if (dto.getVersion() == null || !Objects.equals(dto.getVersion(), entity.getVersion()))
            throw new ResponseStatusException(HttpStatus.CONFLICT, "El registro cambio; recargue antes de guardar");
        apply(entity, dto); return toDto(repository.saveAndFlush(entity));
    }
    public void delete(Long id) { repository.delete(entity(id)); repository.flush(); }
    public long count() { return repository.count(); }
}
