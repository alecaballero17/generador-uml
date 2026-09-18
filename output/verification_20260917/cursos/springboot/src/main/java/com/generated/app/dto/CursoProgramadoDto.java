package com.generated.app.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class CursoProgramadoDto {
    private Long id;
    private Long version;
    @NotBlank
    private String titulo;
    private LocalDate fechaInicio;
    private Boolean activo;
    @NotNull
    private Long instructorId;
}
