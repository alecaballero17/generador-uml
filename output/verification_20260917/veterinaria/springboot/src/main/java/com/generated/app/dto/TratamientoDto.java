package com.generated.app.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class TratamientoDto {
    private Long id;
    private Long version;
    private String descripcion;
    private String medicamento;
    private String dosis;
    private Integer duracionDias;
    private BigDecimal costo;
    @NotNull
    private Long citaId;
}
