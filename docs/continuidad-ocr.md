# Continuidad: OCR web y Android (19 septiembre)

Cambios guardados en este proyecto, sin commit ni push.

- Lector local compartido Tesseract: separa compartimentos de cajas rectangulares antes del OCR. No depende del color verde ni del contenido del ejemplo.
- Caso real suministrado: usuario confirmó en Android 7 clases, 20 atributos y 10 métodos importados. Conserva +, -, #, ~. Tipos ausentes usan String y void; no son inferidos de la imagen.
- Detecta candidatos de conexiones mediante componentes de píxeles fuera de las cajas. Caso real: cuatro pares y dos grupos ambiguos. No interpreta aún puntas, dirección ni multiplicidad; se revisan manualmente. Android muestra candidatos que abren Conectar clases para clases ya importadas.
- Importador web ahora usa recognizeLocalPhoto y reviewPhotoText compartidos, en vez del endpoint Python de OCR. Mantiene revisión antes de aceptar. La aceptación web reemplaza el diagrama actual (comportamiento anterior); evitar usar con trabajo ajeno sin revisar.
- Métodos: por ahora solo firmas sin parámetros. Una firma no compatible bloquea el bloque con error; no se debe declarar cobertura UML completa.
- Pruebas: test_photo_segmentation.cjs, test_photo_visibility.cjs y test_mobile_relationship.cjs pasan. Prueba OCR real en .runtime/test-photo-boxes.cjs (imagen temporal del usuario, no fixture versionado).
- APK instalada con conexiones candidatas. Cambio posterior del importador web aún requiere próxima compilación para igualar todos los assets empaquetados.
- Pendientes: reconocimiento semántico de relaciones, imágenes inclinadas/pizarras reales, parámetros de métodos, prueba offline integral, validación externa StarUML/Enterprise Architect. No presentar como terminado.
- Verificación posterior real en navegador integrado: seleccionar original, ejecutar OCR local, revisar y aceptar. Lienzo muestra 7 clases, 20 atributos públicos y 10 métodos, con mensaje de importación exitosa. Se usó un proyecto nuevo de prueba; no el diagrama del teléfono.
- Nueva verificación: tras aceptar en web abre revisión compartida de conexiones; Bank-ATM selecciona extremos correctos y permite guardar Agregación. Probado en navegador real. APK recompilada e instalada con assets actuales. El tipo fue elegido manualmente; no es reconocimiento automático.
