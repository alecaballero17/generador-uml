package com.generated.app.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class MascotaDto {
    private Long id;
    private Long version;
    private String nombre;
    private String especie;
    private String raza;
    private LocalDate fechaNacimiento;
    private Double peso;
    private String sexo;
    @NotNull
    private Long dueñoId;
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private List<Long> citasIds;
}
