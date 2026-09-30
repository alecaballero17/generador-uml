package com.cursos.app.repository;

import com.cursos.app.entity.Instructor;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.math.BigDecimal;

@Repository
public interface InstructorRepository extends JpaRepository<Instructor, Long> {

    // Métodos de búsqueda generados automáticamente según atributos
    List<Instructor> findByNombreContainingIgnoreCase(String nombre);
}
