package com.generador.ventas.controller;
import com.generador.ventas.dto.VentaDto;
import com.generador.ventas.service.VentaService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/ventas")
public class VentaController {
    private final VentaService service;
    public VentaController(VentaService service) { this.service = service; }
    @GetMapping public List<VentaDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public VentaDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<VentaDto> create(@Valid @RequestBody VentaDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public VentaDto update(@PathVariable Long id, @Valid @RequestBody VentaDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
