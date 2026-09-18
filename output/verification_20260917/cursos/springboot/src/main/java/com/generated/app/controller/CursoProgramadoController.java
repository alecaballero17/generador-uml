package com.generated.app.controller;
import com.generated.app.dto.CursoProgramadoDto;
import com.generated.app.service.CursoProgramadoService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/curso-programados")
public class CursoProgramadoController {
    private final CursoProgramadoService service;
    public CursoProgramadoController(CursoProgramadoService service) { this.service = service; }
    @GetMapping public List<CursoProgramadoDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public CursoProgramadoDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<CursoProgramadoDto> create(@Valid @RequestBody CursoProgramadoDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public CursoProgramadoDto update(@PathVariable Long id, @Valid @RequestBody CursoProgramadoDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
