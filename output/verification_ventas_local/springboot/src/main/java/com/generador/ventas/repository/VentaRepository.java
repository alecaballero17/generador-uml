package com.generador.ventas.repository;

import com.generador.ventas.entity.Venta;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface VentaRepository extends JpaRepository<Venta, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Venta> findByFecha(LocalDate fecha);
}
