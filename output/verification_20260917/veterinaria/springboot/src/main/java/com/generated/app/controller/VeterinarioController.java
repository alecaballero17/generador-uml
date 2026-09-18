package com.generated.app.controller;
import com.generated.app.dto.VeterinarioDto;
import com.generated.app.service.VeterinarioService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/veterinarios")
public class VeterinarioController {
    private final VeterinarioService service;
    public VeterinarioController(VeterinarioService service) { this.service = service; }
    @GetMapping public List<VeterinarioDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public VeterinarioDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<VeterinarioDto> create(@Valid @RequestBody VeterinarioDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public VeterinarioDto update(@PathVariable Long id, @Valid @RequestBody VeterinarioDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
