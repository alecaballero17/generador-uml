package com.generador.ventas.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class VendedorDto {
    private Long id;
    private Long version;
    private String nombre;
    private Double comision;
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private List<Long> ventasIds;
}
