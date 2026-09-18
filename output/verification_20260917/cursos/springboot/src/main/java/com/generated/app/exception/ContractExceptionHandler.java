package com.generated.app.exception;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.*;
import org.springframework.core.annotation.Order;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import java.util.Map;
@RestControllerAdvice @Order(-100)
public class ContractExceptionHandler {
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<?> status(ResponseStatusException e) { return ResponseEntity.status(e.getStatusCode()).body(Map.of("message", e.getReason()==null?"Solicitud rechazada":e.getReason())); }
    @ExceptionHandler({DataIntegrityViolationException.class,ObjectOptimisticLockingFailureException.class})
    public ResponseEntity<?> conflict(Exception e) { return ResponseEntity.status(409).body(Map.of("message","Conflicto: el registro cambio o tiene relaciones que impiden la operacion")); }
}
