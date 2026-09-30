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
@Table(name = "producto")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Producto {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(name = "nombre")
    private String nombre;
    @Column(name = "precio")
    private Double precio;
    @Column(name = "stock")
    private Integer stock;
    @OneToMany(mappedBy = "producto", fetch = FetchType.LAZY)
    @JsonManagedReference("rel_49fa807271551c4276a4")
    private List<Detalle> detalles = new ArrayList<>();
    @Version
    private Long version;
}
