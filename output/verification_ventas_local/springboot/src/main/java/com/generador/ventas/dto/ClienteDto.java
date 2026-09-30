package com.generador.ventas.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class ClienteDto {
    private Long id;
    private Long version;
    private String nombre;
    private String email;
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private List<Long> ventasIds;
}
