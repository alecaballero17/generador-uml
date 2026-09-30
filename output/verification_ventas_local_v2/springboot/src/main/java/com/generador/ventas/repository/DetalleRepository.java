package com.generador.ventas.repository;

import com.generador.ventas.entity.Detalle;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface DetalleRepository extends JpaRepository<Detalle, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Detalle> findByCantidad(Integer cantidad);
    List<Detalle> findByPrecioUnitario(Double precioUnitario);
}
