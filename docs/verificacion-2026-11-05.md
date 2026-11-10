# Registro de verificación — 5 de noviembre de 2026

Estado: revisión en curso; no declarar aceptación completa de las cinco preguntas.

## Evidencia ejecutada

- Python: `python -m pytest -q`: 119 pruebas aprobadas. Una advertencia de deprecación de TestClient.
- JavaScript: todos los archivos `tests/test_*.cjs` finalizaron correctamente.
- IA: solicitud real de creación de Cliente con nombre String devolvió la acción correspondiente.
- Backend generado de ventas: Maven package y prueba de contexto aprobados.
- Flutter generado: prueba de carga inicial aprobada y APK debug compilada.
- Botón local del editor: inició y completó el trabajo `f7911a72a0d04b2ab5fc095367661c3f`.
- Artefactos: `output/build_f7911a72a0d04b2ab5fc095367661c3f/aplicacion.apk` y `entrega.zip`.
- Postman/Newman contra backend de ventas en 8087: 31 peticiones, 57 aserciones, cero fallos.
  Reporte: `output/build_4c17e0cd738041ec8b25df042e786417/postman-results.json`.
  Ese primer trabajo compiló, pero su supervisor de consola terminó por un error de
  codificación al imprimir el log; su empaquetado no se considera válido. Usar la entrega
  del segundo trabajo, ejecutado desde el botón web.
- `git diff --check`: sin errores de espacios; avisos de conversión LF/CRLF.

## Pendiente antes de aceptación

- Comprobar respuestas negativas del backend en ejecución: referencia inexistente,
  versión obsoleta y borrado de un registro referenciado. Revisar especialmente la
  interacción de ResponseStatusException con el manejador general de excepciones.
- Instalar y probar CRUD en teléfono físico. No hay evidencia de esta prueba todavía.
- Comparar manualmente el modelo completo con una foto nueva; OCR puede requerir corrección.
- Revisar equivalencia de multiplicidades en Enterprise Architect para el modelo de defensa.
- Cerrar la revisión documental y anexar capturas de aceptación sin inventar resultados.

No se desplegaron estos cambios en Render. Los cambios permanecen locales.
Guía operativa: [primera parte](primera-parte.md). Metodología y trazabilidad:
[Proceso Unificado](proceso_unificado_pud.md).
