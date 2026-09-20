# Avance estimado del producto — 20 septiembre de 2026

Estimación orientativa sobre los requisitos expresados por el usuario, no porcentaje medido de líneas de código ni garantía de aprobación académica. Los pesos son una propuesta de seguimiento y pueden cambiar al contrastar casos de aceptación más exigentes. No representan el tiempo restante.

| Bloque | Peso | Implementación estimada | Validación estimada |
|---|---:|---:|---:|
| Editor UML web y modelo | 20% | 90% | 85% |
| Colaboración, invitaciones y recuperación | 15% | 85% | 65% |
| APK e interacción móvil | 10% | 85% | 75% |
| Voz y asistente contextual | 15% | 70% | 45% |
| Foto a diagrama editable | 15% | 60% | 60% |
| Operación offline y sincronización integral | 10% | 60% | 35% |
| Generación backend y aplicación | 10% | 85% | 60% |
| Intercambio StarUML y Enterprise Architect | 5% | 70% | 40% |

Promedio ponderado aproximado: 78% de implementación y 63% de validación. Comunicar como rangos: 75–80% implementado y 60–65% comprobado. La validación no equivale a que el 63% de las pruebas pase: la batería actual pasa, pero su cobertura de requisitos es incompleta.

## Evidencia nueva

- Compilación real de backend generado: `mvn test-compile` completado con `BUILD SUCCESS` (33 clases Java compiladas con `javac [release 17]` bajo JDK 23). Se garantizó compatibilidad JPA unificando `@Id` a tipo `Long` y evitando duplicación de IDs/versiones en subclases.
- Generador móvil Flutter: corregida la generación de formularios en `flutter_generator.py` agregando declaración explícita de `TextEditingController` y liberación en `dispose()`.
- Interoperabilidad: soporte ampliado en `XMIAdapter` para variantes de namespace de Sparx Enterprise Architect y resolución de tipos vía `xmi:idref`, verificado con prueba unitaria automatizada.
- Revisión OCR web comprobada en navegador real: se cambió deposit() por deposit(amount: Double): Boolean antes de importar. El lienzo mostró el método con parámetro y retorno (la etiqueta visual se trunca por ancho).
- Importación bloquea atributos duplicados y errores de interpretación, evitando omitirlos silenciosamente.
- Casos reales previos: Android y web importaron siete clases, veinte atributos y diez métodos del ejemplo bancario.
- Pruebas de colaboración con dos clientes y reconexión; todavía no equivalen al flujo completo con voz/foto offline en dos dispositivos.

## Criterios aún necesarios para cerrar

1. Fotos: resolver o revisar explícitamente todas las relaciones, con dirección, tipo, multiplicidades y cruces; corpus variado de pizarras, no solo el ejemplo digital.
2. Voz: medir errores con frases y hablantes reales y probar captura/transcripción/interpretación sin red en Android.
3. Offline: edición, cierre, reapertura y sincronización con conflictos sin pérdidas entre web y Android.
4. Generación: compilar y ejecutar varias aplicaciones representativas con relaciones, herencia y validaciones.
5. Interoperabilidad: abrir y reexportar archivos dentro de StarUML y Enterprise Architect; comprobar fidelidad.
6. Documentación final: evidencias y límites consistentes con el comportamiento real.

Estado: incompleto. No declarar entrega final ni convertir estos rangos en una promesa de tiempo.
