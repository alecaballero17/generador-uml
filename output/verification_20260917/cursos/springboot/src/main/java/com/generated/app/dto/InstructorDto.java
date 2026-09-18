package com.generated.app.dto;
import lombok.*;
import jakarta.validation.constraints.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;
import java.time.*;
import java.math.*;
@Getter @Setter @NoArgsConstructor
public class InstructorDto {
    private Long id;
    private Long version;
    @NotBlank
    private String nombre;
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private List<Long> cursosIds;
}
