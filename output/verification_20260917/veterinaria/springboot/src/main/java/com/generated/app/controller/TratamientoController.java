package com.generated.app.controller;
import com.generated.app.dto.TratamientoDto;
import com.generated.app.service.TratamientoService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/tratamientos")
public class TratamientoController {
    private final TratamientoService service;
    public TratamientoController(TratamientoService service) { this.service = service; }
    @GetMapping public List<TratamientoDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public TratamientoDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<TratamientoDto> create(@Valid @RequestBody TratamientoDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public TratamientoDto update(@PathVariable Long id, @Valid @RequestBody TratamientoDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
