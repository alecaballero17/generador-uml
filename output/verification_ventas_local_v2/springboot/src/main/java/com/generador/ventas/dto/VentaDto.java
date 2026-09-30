package com.generador.ventas.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class VentaDto {
    private Long id;
    private Long version;
    private LocalDate fecha;
    @NotNull
    private Long vendedorId;
    @NotNull
    private Long clienteId;
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private List<Long> detallesIds;
}
