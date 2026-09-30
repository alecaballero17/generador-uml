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
@Table(name = "detalle")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Detalle {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(name = "cantidad")
    private Integer cantidad;
    @Column(name = "precio_unitario")
    private Double precioUnitario;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "venta_id")
    @JsonBackReference("rel_b5e2f0a64bd38e91fcb0")
    private Venta venta;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "producto_id")
    @JsonBackReference("rel_49fa807271551c4276a4")
    private Producto producto;
    @Version
    private Long version;
}
