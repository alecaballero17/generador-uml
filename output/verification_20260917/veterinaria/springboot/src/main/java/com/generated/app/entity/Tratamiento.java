package com.generated.app.entity;

import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import lombok.*;
import java.math.BigDecimal;

import java.util.List;
import java.util.ArrayList;
import java.util.Set;
import java.util.HashSet;

@Entity
@Table(name = "tratamiento")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Tratamiento {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "descripcion")
    private String descripcion;
    @Column(name = "medicamento")
    private String medicamento;
    @Column(name = "dosis")
    private String dosis;
    @Column(name = "duracion_dias")
    private Integer duracionDias;
    @Column(name = "costo")
    private BigDecimal costo;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cita_id")
    @JsonBackReference("rel_ae05ad6b71592f24facc")
    private Cita cita;
    @Version
    private Long version;
}
