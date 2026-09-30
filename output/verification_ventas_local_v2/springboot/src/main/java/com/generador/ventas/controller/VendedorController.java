package com.generador.ventas.controller;
import com.generador.ventas.dto.VendedorDto;
import com.generador.ventas.service.VendedorService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/vendedors")
public class VendedorController {
    private final VendedorService service;
    public VendedorController(VendedorService service) { this.service = service; }
    @GetMapping public List<VendedorDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public VendedorDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<VendedorDto> create(@Valid @RequestBody VendedorDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public VendedorDto update(@PathVariable Long id, @Valid @RequestBody VendedorDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
