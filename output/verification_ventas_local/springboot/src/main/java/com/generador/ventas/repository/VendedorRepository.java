package com.generador.ventas.repository;

import com.generador.ventas.entity.Vendedor;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface VendedorRepository extends JpaRepository<Vendedor, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Vendedor> findByNombreContainingIgnoreCase(String nombre);
    List<Vendedor> findByComision(Double comision);
}
