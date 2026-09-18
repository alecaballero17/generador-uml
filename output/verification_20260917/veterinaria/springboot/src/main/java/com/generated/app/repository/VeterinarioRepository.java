package com.generated.app.repository;

import com.generated.app.entity.Veterinario;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface VeterinarioRepository extends JpaRepository<Veterinario, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Veterinario> findByNombreContainingIgnoreCase(String nombre);
    List<Veterinario> findByApellidoContainingIgnoreCase(String apellido);
    List<Veterinario> findByEspecialidadContainingIgnoreCase(String especialidad);
    List<Veterinario> findByMatriculaContainingIgnoreCase(String matricula);
    List<Veterinario> findByTelefonoContainingIgnoreCase(String telefono);
}
