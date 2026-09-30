package com.generador.ventas.entity;

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
@Table(name = "venta")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
public class Venta {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(name = "fecha")
    private LocalDate fecha;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "vendedor_id")
    @JsonBackReference("rel_cac9d2daea42e012aca9")
    private Vendedor vendedor;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cliente_id")
    @JsonBackReference("rel_39a76d7f236bc9e06073")
    private Cliente cliente;
    @OneToMany(mappedBy = "venta", fetch = FetchType.LAZY)
    @JsonManagedReference("rel_376288ba5ecb2fcfd242")
    private List<Detalle> detalles = new ArrayList<>();
    @Version
    private Long version;
}
