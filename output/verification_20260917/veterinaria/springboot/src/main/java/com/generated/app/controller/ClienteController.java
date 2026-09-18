package com.generated.app.controller;
import com.generated.app.dto.ClienteDto;
import com.generated.app.service.ClienteService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/clientes")
public class ClienteController {
    private final ClienteService service;
    public ClienteController(ClienteService service) { this.service = service; }
    @GetMapping public List<ClienteDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public ClienteDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<ClienteDto> create(@Valid @RequestBody ClienteDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public ClienteDto update(@PathVariable Long id, @Valid @RequestBody ClienteDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
