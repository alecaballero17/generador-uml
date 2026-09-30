package com.generador.ventas.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class ProductoDto {
    private Long id;
    private Long version;
    private String nombre;
    private Double precio;
    private Integer stock;
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private List<Long> detallesIds;
}
