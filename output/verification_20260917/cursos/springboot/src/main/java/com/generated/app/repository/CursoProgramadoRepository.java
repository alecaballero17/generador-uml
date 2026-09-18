package com.generated.app.repository;

import com.generated.app.entity.CursoProgramado;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface CursoProgramadoRepository extends JpaRepository<CursoProgramado, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<CursoProgramado> findByTituloContainingIgnoreCase(String titulo);
    List<CursoProgramado> findByFechaInicio(LocalDate fechaInicio);
    List<CursoProgramado> findByActivo(Boolean activo);
}
