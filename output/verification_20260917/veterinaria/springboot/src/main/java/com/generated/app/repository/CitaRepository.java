package com.generated.app.repository;

import com.generated.app.entity.Cita;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface CitaRepository extends JpaRepository<Cita, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Cita> findByFecha(LocalDateTime fecha);
    List<Cita> findByMotivoContainingIgnoreCase(String motivo);
    List<Cita> findByDiagnosticoContainingIgnoreCase(String diagnostico);
    List<Cita> findByEstadoContainingIgnoreCase(String estado);
    List<Cita> findByObservacionesContainingIgnoreCase(String observaciones);
}
