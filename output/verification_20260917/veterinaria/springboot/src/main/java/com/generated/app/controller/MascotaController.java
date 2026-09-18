package com.generated.app.controller;
import com.generated.app.dto.MascotaDto;
import com.generated.app.service.MascotaService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/mascotas")
public class MascotaController {
    private final MascotaService service;
    public MascotaController(MascotaService service) { this.service = service; }
    @GetMapping public List<MascotaDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public MascotaDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<MascotaDto> create(@Valid @RequestBody MascotaDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public MascotaDto update(@PathVariable Long id, @Valid @RequestBody MascotaDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
