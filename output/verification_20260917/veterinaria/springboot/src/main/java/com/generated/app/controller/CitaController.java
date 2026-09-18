package com.generated.app.controller;
import com.generated.app.dto.CitaDto;
import com.generated.app.service.CitaService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/citas")
public class CitaController {
    private final CitaService service;
    public CitaController(CitaService service) { this.service = service; }
    @GetMapping public List<CitaDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public CitaDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<CitaDto> create(@Valid @RequestBody CitaDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public CitaDto update(@PathVariable Long id, @Valid @RequestBody CitaDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
