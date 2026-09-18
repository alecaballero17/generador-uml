package com.generated.app.repository;

import com.generated.app.entity.Cliente;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface ClienteRepository extends JpaRepository<Cliente, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Cliente> findByNombreContainingIgnoreCase(String nombre);
    List<Cliente> findByApellidoContainingIgnoreCase(String apellido);
    List<Cliente> findByTelefonoContainingIgnoreCase(String telefono);
    List<Cliente> findByEmailContainingIgnoreCase(String email);
    List<Cliente> findByDireccionContainingIgnoreCase(String direccion);
}
