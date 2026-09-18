package com.generated.app.controller;
import com.generated.app.dto.InstructorDto;
import com.generated.app.service.InstructorService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;
import jakarta.validation.Valid;
import java.util.*;
@RestController @RequestMapping("/api/instructors")
public class InstructorController {
    private final InstructorService service;
    public InstructorController(InstructorService service) { this.service = service; }
    @GetMapping public List<InstructorDto> all() { return service.findAll(); }
    @GetMapping("/{id}") public InstructorDto one(@PathVariable Long id) { return service.findById(id); }
    @PostMapping public ResponseEntity<InstructorDto> create(@Valid @RequestBody InstructorDto dto) { return ResponseEntity.status(201).body(service.create(dto)); }
    @PutMapping("/{id}") public InstructorDto update(@PathVariable Long id, @Valid @RequestBody InstructorDto dto) { return service.update(id, dto); }
    @DeleteMapping("/{id}") public Map<String,Boolean> delete(@PathVariable Long id) { service.delete(id); return Map.of("deleted",true); }
    @GetMapping("/count") public Map<String,Long> count() { return Map.of("count",service.count()); }
}
