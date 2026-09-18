package com.generated.app.repository;

import com.generated.app.entity.Mascota;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface MascotaRepository extends JpaRepository<Mascota, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Mascota> findByNombreContainingIgnoreCase(String nombre);
    List<Mascota> findByEspecieContainingIgnoreCase(String especie);
    List<Mascota> findByRazaContainingIgnoreCase(String raza);
    List<Mascota> findByFechaNacimiento(LocalDate fechaNacimiento);
    List<Mascota> findByPeso(Double peso);
    List<Mascota> findBySexoContainingIgnoreCase(String sexo);
}
