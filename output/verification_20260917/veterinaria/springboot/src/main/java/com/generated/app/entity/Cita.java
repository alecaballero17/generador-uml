package com.generated.app.entity;

import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import lombok.*;
import java.time.LocalDateTime;

import java.util.List;
import java.util.ArrayList;
import java.util.Set;
import java.util.HashSet;

@Entity
@Table(name = "cita")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Cita {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "fecha")
    private LocalDateTime fecha;
    @Column(name = "motivo")
    private String motivo;
    @Column(name = "diagnostico")
    private String diagnostico;
    @Column(name = "estado")
    private String estado;
    @Column(name = "observaciones")
    private String observaciones;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "mascota_id")
    @JsonBackReference("rel_603d549800bcba023213")
    private Mascota mascota;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "veterinario_id")
    @JsonBackReference("rel_9872c6df5e9f1b52e0e1")
    private Veterinario veterinario;
    @OneToMany(mappedBy = "cita", fetch = FetchType.LAZY)
    @JsonManagedReference("rel_ae05ad6b71592f24facc")
    private List<Tratamiento> tratamientos = new ArrayList<>();
    @Version
    private Long version;
}
