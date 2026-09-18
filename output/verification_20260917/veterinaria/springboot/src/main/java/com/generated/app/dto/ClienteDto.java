package com.generated.app.dto;
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
    private String apellido;
    private String telefono;
    private String email;
    private String direccion;
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private List<Long> mascotasIds;
}
