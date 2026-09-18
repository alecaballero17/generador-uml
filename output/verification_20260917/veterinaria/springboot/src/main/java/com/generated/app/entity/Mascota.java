package com.generated.app.entity;

import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import lombok.*;
import java.time.LocalDate;

import java.util.List;
import java.util.ArrayList;
import java.util.Set;
import java.util.HashSet;

@Entity
@Table(name = "mascota")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Mascota {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "nombre")
    private String nombre;
    @Column(name = "especie")
    private String especie;
    @Column(name = "raza")
    private String raza;
    @Column(name = "fecha_nacimiento")
    private LocalDate fechaNacimiento;
    @Column(name = "peso")
    private Double peso;
    @Column(name = "sexo")
    private String sexo;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cliente_id", nullable = false)
    @JsonBackReference("rel_71c221cdf2e7a196e3b8")
    private Cliente dueño;
    @OneToMany(mappedBy = "mascota", fetch = FetchType.LAZY)
    @JsonManagedReference("rel_603d549800bcba023213")
    private List<Cita> citas = new ArrayList<>();
    @Version
    private Long version;
}
