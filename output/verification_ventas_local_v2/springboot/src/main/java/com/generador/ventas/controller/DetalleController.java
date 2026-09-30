package com.generador.ventas.controller;
import com.generador.ventas.dto.DetalleDto;
import com.generador.ventas.service.DetalleService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/detalles")
public class DetalleController {
    private final DetalleService service;
    public DetalleController(DetalleService service) { this.service = service; }
    @GetMapping public List<DetalleDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public DetalleDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<DetalleDto> create(@Valid @RequestBody DetalleDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public DetalleDto update(@PathVariable Long id, @Valid @RequestBody DetalleDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
