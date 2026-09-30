package com.generador.ventas.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class DetalleDto {
    private Long id;
    private Long version;
    private Integer cantidad;
    private Double precioUnitario;
    @NotNull
    private Long ventaId;
    @NotNull
    private Long productoId;
}
