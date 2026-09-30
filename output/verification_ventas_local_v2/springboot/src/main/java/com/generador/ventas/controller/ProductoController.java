package com.generador.ventas.controller;
import com.generador.ventas.dto.ProductoDto;
import com.generador.ventas.service.ProductoService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/productos")
public class ProductoController {
    private final ProductoService service;
    public ProductoController(ProductoService service) { this.service = service; }
    @GetMapping public List<ProductoDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public ProductoDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<ProductoDto> create(@Valid @RequestBody ProductoDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public ProductoDto update(@PathVariable Long id, @Valid @RequestBody ProductoDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
