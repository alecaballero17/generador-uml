package com.generated.app.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class CitaDto {
    private Long id;
    private Long version;
    private LocalDateTime fecha;
    private String motivo;
    private String diagnostico;
    private String estado;
    private String observaciones;
    @NotNull
    private Long mascotaId;
    @NotNull
    private Long veterinarioId;
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private List<Long> tratamientosIds;
}
