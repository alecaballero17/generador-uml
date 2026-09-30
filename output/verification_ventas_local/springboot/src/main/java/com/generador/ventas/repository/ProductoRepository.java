package com.generador.ventas.repository;

import com.generador.ventas.entity.Producto;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface ProductoRepository extends JpaRepository<Producto, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Producto> findByNombreContainingIgnoreCase(String nombre);
    List<Producto> findByPrecio(Double precio);
    List<Producto> findByStock(Integer stock);
}
