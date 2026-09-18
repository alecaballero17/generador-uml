package com.generated.app.entity;

import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import lombok.*;

import java.util.List;
import java.util.ArrayList;
import java.util.Set;
import java.util.HashSet;

@Entity
@Table(name = "veterinario")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Veterinario {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "nombre")
    private String nombre;
    @Column(name = "apellido")
    private String apellido;
    @Column(name = "especialidad")
    private String especialidad;
    @Column(name = "matricula")
    private String matricula;
    @Column(name = "telefono")
    private String telefono;
    @OneToMany(mappedBy = "veterinario", fetch = FetchType.LAZY)
    @JsonManagedReference("rel_9872c6df5e9f1b52e0e1")
    private List<Cita> citas = new ArrayList<>();
    @Version
    private Long version;
}
