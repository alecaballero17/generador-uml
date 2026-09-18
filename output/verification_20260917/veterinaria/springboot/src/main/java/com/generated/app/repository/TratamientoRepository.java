package com.generated.app.repository;

import com.generated.app.entity.Tratamiento;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface TratamientoRepository extends JpaRepository<Tratamiento, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Tratamiento> findByDescripcionContainingIgnoreCase(String descripcion);
    List<Tratamiento> findByMedicamentoContainingIgnoreCase(String medicamento);
    List<Tratamiento> findByDosisContainingIgnoreCase(String dosis);
    List<Tratamiento> findByDuracionDias(Integer duracionDias);
    List<Tratamiento> findByCosto(BigDecimal costo);
}
