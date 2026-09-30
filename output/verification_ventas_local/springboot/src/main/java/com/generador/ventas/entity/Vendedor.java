package com.generador.ventas.entity;

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
@Table(name = "vendedor")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Vendedor {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(name = "nombre")
    private String nombre;
    @Column(name = "comision")
    private Double comision;
    @OneToMany(mappedBy = "vendedor", fetch = FetchType.LAZY)
    @JsonManagedReference("rel_cac9d2daea42e012aca9")
    private List<Venta> ventas = new ArrayList<>();
    @Version
    private Long version;
}
