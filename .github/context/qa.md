# QA Context

## Propósito

Este documento define el contexto técnico actual relacionado con calidad y testing en OportunidadBot.

Su objetivo es proporcionar a los agentes una referencia común sobre:

- Estrategia de testing.
- Estructura de tests.
- Tipos de pruebas.
- Fixtures y mocks.
- Cobertura.
- Criterios para añadir o modificar tests.
- Validación de cambios.
- Reglas para evitar regresiones.

Este documento describe la estrategia existente y no pretende sustituir los workflows específicos de desarrollo, bug fixing o code review.

---

## 1. Stack de testing

El proyecto utiliza principalmente:

- `pytest`
- `pytest-asyncio`
- `pytest-mock`
- `pytest-cov`

La configuración principal de pytest se encuentra en:

`pytest.ini`

La configuración de cobertura se encuentra en:

`.coveragerc`

El proyecto mantiene como objetivo una cobertura mínima del **90%**.

La cobertura no debe conseguirse eliminando, debilitando o ignorando tests relevantes.

---

## 2. Estructura de tests

Los tests se encuentran en:

`tests/`

La estructura principal es:

- `tests/unit/`
- `tests/integration/`
- `tests/e2e/`
- `tests/fixtures/`
- `tests/mocks/`

Cada nivel tiene una finalidad diferente y debe utilizarse según el tipo de comportamiento que se quiera validar.

---

## 3. Unit tests

Los tests unitarios se encuentran en:

`tests/unit/`

Su objetivo es comprobar unidades aisladas de comportamiento.

Entre los componentes actualmente cubiertos existen:

- Servicios.
- Parsers.
- Sources.
- Handlers.
- Scheduler.
- Orquestador.
- Stripe.
- Suscripciones.
- Factory de fuentes.
- Clasificación mediante IA.
- Utilidades.

Ejemplos actuales:

- `test_ai_classifier.py`
- `test_alert_service.py`
- `test_base_source.py`
- `test_database.py`
- `test_detector.py`
- `test_feed_parser.py`
- `test_handlers.py`
- `test_orchestrator.py`
- `test_scheduler.py`
- `test_source_factory.py`
- `test_stripe_service.py`
- `test_subscription_service.py`

---

## 4. Cuándo crear un unit test

Debe añadirse o modificarse un test unitario cuando se:

- Añade lógica nueva.
- Modifica una condición existente.
- Añade una nueva rama de ejecución.
- Corrige un bug localizado en una unidad.
- Cambia el comportamiento de una función.
- Añade validaciones.
- Modifica el tratamiento de errores.

Siempre que sea posible, el test debe centrarse en el comportamiento observable y no en detalles internos innecesarios.

---

## 5. Integration tests

Los tests de integración se encuentran en:

`tests/integration/`

Comprueban la interacción entre varios componentes.

Ejemplos actuales:

- `test_ai_classifier_live.py`
- `test_alert_database.py`
- `test_feed_detector.py`
- `test_orchestrator_database.py`
- `test_scheduler_orchestrator.py`

Son especialmente importantes cuando una modificación afecta a la comunicación entre:

- Servicios.
- Persistencia.
- Scheduler.
- Orquestador.
- Clasificación IA.
- Alertas.

---

## 6. Cuándo crear un integration test

Debe considerarse un test de integración cuando la funcionalidad depende de la interacción real entre varios componentes y un unit test aislado no proporciona suficiente confianza.

Ejemplos:

- Orquestador + base de datos.
- Scheduler + orquestador.
- Servicio + persistencia.
- Pipeline de detección + persistencia.
- Clasificador + infraestructura de IA.

No convertir automáticamente todos los tests en integración.

Los tests unitarios deben seguir siendo la primera opción para lógica aislada.

---

## 7. End-to-End tests

Los tests E2E se encuentran en:

`tests/e2e/`

Actualmente existen pruebas relacionadas con:

- Pipeline completo.
- Detección de duplicados.
- Procesamiento de múltiples feeds.

Ejemplos:

- `test_full_pipeline.py`
- `test_duplicate_pipeline.py`
- `test_multi_feed_pipeline.py`

Los tests E2E deben utilizarse para comprobar flujos completos y críticos.

No deben utilizarse para validar cada pequeña función del backend.

---

## 8. Pipeline crítico

El flujo principal de procesamiento debe conservar cobertura suficiente a través de los distintos niveles de testing.

El pipeline conceptual es:

1. Obtener información desde fuentes.
2. Parsear y normalizar.
3. Detectar novedades.
4. Clasificar mediante IA cuando corresponda.
5. Persistir.
6. Generar alertas.
7. Enviar notificaciones.

Los cambios en cualquiera de estas etapas deben considerar el impacto sobre los tests del pipeline completo.

---

## 9. Fixtures

Las fixtures se encuentran en:

`tests/fixtures/`

Actualmente existen fixtures relacionadas con:

- Base de datos.
- Feeds.
- NVIDIA.
- Telegram.
- Usuarios.
- RSS entries.

Antes de crear una fixture nueva:

1. Buscar si existe una equivalente.
2. Reutilizarla si cubre la necesidad.
3. Extenderla si es apropiado.
4. Crear una nueva únicamente cuando represente un escenario diferente.

Las fixtures deben ser fáciles de entender y reutilizar.

---

## 10. Mocks y fakes

Los mocks y fakes se encuentran en:

`tests/mocks/`

Actualmente existen:

- `fake_nvidia.py`
- `fake_scheduler.py`
- `fake_supabase.py`
- `fake_telegram.py`

Su objetivo es aislar los tests de dependencias externas o controlar escenarios difíciles de reproducir.

Antes de crear un mock nuevo, comprobar los existentes.

No duplicar implementaciones de mocks para la misma dependencia sin una razón clara.

---

## 11. Dependencias externas en tests

Las pruebas no deben depender innecesariamente de servicios externos reales.

Siempre que sea posible:

- Unit tests → dependencias aisladas.
- Integration tests → mocks/fakes cuando corresponda.
- E2E → entorno controlado.

Un test que dependa de Internet, Telegram, Stripe, NVIDIA o Supabase debe tener una razón explícita para hacerlo.

Los tests externos o live deben identificarse claramente.

---

## 12. Tests live

Existe al menos una prueba relacionada con la clasificación IA real:

`tests/integration/test_ai_classifier_live.py`

Los tests que acceden a servicios reales pueden:

- Ser más lentos.
- Ser menos deterministas.
- Requerir credenciales.
- Fallar por disponibilidad externa.
- Generar costes.

No deben utilizarse como sustituto de una suite unitaria o de integración determinista.

---

## 13. Determinismo

Los tests deben ser lo más deterministas posible.

Evitar depender de:

- Hora actual sin controlar.
- Orden accidental de datos.
- Internet.
- Servicios externos inestables.
- Datos aleatorios no controlados.
- Estado persistente entre tests.

Cuando un comportamiento dependa de tiempo, aleatoriedad o estado externo, debe buscarse una forma de controlarlo dentro del test.

---

## 14. Testing asíncrono

El backend utiliza código asíncrono en diferentes componentes.

Para las pruebas asíncronas se utiliza:

`pytest-asyncio`

Los tests async deben utilizar las herramientas de pytest adecuadas y evitar bloquear innecesariamente el event loop.

Cuando una función sea asíncrona, comprobar tanto:

- Resultado correcto.
- Comportamiento ante excepciones.

---

## 15. Cobertura

La cobertura objetivo del proyecto es:

**90% o superior**

La cobertura debe utilizarse como indicador de calidad, no como único criterio de calidad.

Un test que únicamente ejecuta líneas sin comprobar comportamiento significativo no aporta suficiente valor.

Cuando se añada una funcionalidad:

- Añadir tests representativos.
- Cubrir caminos relevantes.
- Cubrir errores importantes.
- Cubrir límites y casos extremos cuando tengan impacto.

---

## 16. Branch coverage

Cuando una función contiene condiciones relevantes, se deben considerar las diferentes ramas.

Ejemplos:

- Entrada válida.
- Entrada inválida.
- Valor ausente.
- Resultado vacío.
- Error externo.
- Resultado exitoso.
- Comportamiento alternativo.

No es necesario crear un test para cada línea si varias líneas forman parte del mismo comportamiento, pero sí deben cubrirse las decisiones relevantes.

---

## 17. Tests de errores

Los tests deben cubrir errores importantes cuando formen parte del comportamiento esperado.

Ejemplos:

- Fuente externa no disponible.
- Respuesta inválida.
- Elemento duplicado.
- Error de persistencia.
- Error de Telegram.
- Error de Stripe.
- Error de IA.
- Datos de entrada inválidos.

No basta con comprobar únicamente el happy path.

---

## 18. Tests de regresión

Todo bug relevante debería incorporar una prueba de regresión cuando sea razonablemente posible.

La prueba debe reproducir el problema anterior a la corrección y demostrar el comportamiento esperado después de ella.

Patrón recomendado:

1. Reproducir el escenario defectuoso.
2. Comprobar el resultado incorrecto esperado antes del fix conceptualmente.
3. Aplicar la corrección.
4. Mantener el test como protección futura.

El test debe permanecer aunque el bug quede solucionado.

---

## 19. Cambios funcionales

Cuando se implemente una nueva funcionalidad:

1. Identificar el componente afectado.
2. Buscar tests existentes.
3. Determinar qué comportamiento cambia.
4. Añadir o modificar tests.
5. Ejecutar la suite relevante.
6. Ejecutar la suite completa cuando corresponda.
7. Comprobar cobertura.

No considerar terminada una funcionalidad simplemente porque el código compile o el endpoint responda.

---

## 20. Cambios de refactor

Un refactor que no debería modificar comportamiento debe mantener los tests existentes funcionando sin cambios sustanciales.

Si un refactor requiere modificar muchos tests únicamente porque estaban acoplados a detalles internos, revisar si los tests están validando implementación en lugar de comportamiento.

No modificar tests para ocultar una regresión funcional.

---

## 21. Tests de API

Cuando se añadan o modifiquen endpoints:

Debe comprobarse al menos cuando sea relevante:

- Request válido.
- Response esperado.
- Parámetros obligatorios.
- Datos inválidos.
- Errores.
- Códigos HTTP.
- Autenticación/autorización cuando aplique.

Los cambios en contratos API deben considerar también consumidores existentes.

---

## 22. Tests de fuentes

Cuando se añada o modifique una fuente:

Comprobar:

- Creación correcta.
- Parsing.
- Normalización.
- Datos incompletos.
- Respuestas inesperadas.
- Errores de conexión cuando sean relevantes.
- Integración con la factory.
- Comportamiento del elemento normalizado.

La implementación específica de una fuente no debe romper el contrato común.

---

## 23. Tests del parser

Los parsers deben probar casos reales y casos problemáticos.

Entre los escenarios relevantes:

- Contenido válido.
- Campos opcionales ausentes.
- HTML.
- Texto vacío.
- Formatos inesperados.
- Datos incompletos.
- Elementos malformados.

Los tests deben proteger especialmente contra cambios en formatos externos.

---

## 24. Tests del orquestador

El orquestador es una pieza crítica.

Los tests deben considerar:

- Flujo exitoso.
- Elementos nuevos.
- Elementos duplicados.
- Fuentes múltiples.
- Fallos de una etapa.
- Clasificación IA cuando corresponda.
- Persistencia.
- Generación de alertas.

Los cambios en `app/services/orchestrator.py` deben revisarse especialmente porque pueden afectar a múltiples componentes.

---

## 25. Tests de Telegram

Cuando se modifiquen handlers o alertas:

Comprobar:

- Entrada esperada.
- Parámetros inválidos.
- Respuesta correcta.
- Errores.
- Integración con servicios.
- Comportamiento ante fallos de Telegram.

Utilizar `fake_telegram.py` cuando sea apropiado.

No depender de Telegram real para tests unitarios.

---

## 26. Tests de Stripe

Los cambios en Stripe deben comprobar especialmente:

- Creación de Checkout.
- Customer Portal.
- Procesamiento de eventos.
- Validación de firma.
- Eventos inválidos.
- Errores.
- Estados de suscripción.

La validación de firma no debe eliminarse para facilitar los tests.

Debe utilizarse mocking/faking apropiado.

---

## 27. Tests de IA

Los tests relacionados con IA deben distinguir entre:

- Lógica del clasificador.
- Construcción de prompts.
- Procesamiento de respuestas.
- Manejo de errores.
- Integración real con el proveedor.

La mayoría de escenarios deben poder probarse sin consumir una API real.

Los cambios en prompts deben comprobar si modifican el comportamiento esperado.

---

## 28. Tests del scheduler

Cuando se modifique `app/jobs/scheduler.py`, comprobar:

- Registro de tareas.
- Ejecución.
- Integración con el orquestador.
- Manejo de errores.
- Evitar ejecuciones duplicadas cuando sea relevante.

Utilizar `fake_scheduler.py` cuando sea suficiente.

---

## 29. Tests de base de datos

Las operaciones de persistencia deben disponer de cobertura adecuada.

Los tests deben considerar:

- Inserciones.
- Consultas.
- Actualizaciones.
- Duplicados.
- Datos inexistentes.
- Errores.

Los cambios de esquema o migraciones requieren una revisión adicional y no deben ejecutarse automáticamente.

---

## 30. Naming

Los nombres de tests deben describir el comportamiento que verifican.

Preferir nombres que indiquen:

- Qué componente se prueba.
- Qué escenario se ejecuta.
- Qué resultado se espera.

Evitar nombres genéricos como:

- `test_works`
- `test_basic`
- `test_function`

cuando el comportamiento puede expresarse de forma más precisa.

---

## 31. Organización

Mantener los tests organizados según su nivel:

`unit`

para lógica aislada.

`integration`

para interacción entre componentes.

`e2e`

para flujos completos.

No mover tests entre niveles únicamente para hacer que una suite sea más cómoda.

La clasificación debe representar el tipo real de prueba.

---

## 32. No debilitar tests

Está prohibido solucionar un fallo de la suite mediante:

- Eliminar un test válido.
- Comentar un test.
- Reducir assertions relevantes.
- Ignorar una excepción inesperada.
- Aumentar artificialmente tolerancias.
- Reducir la cobertura requerida.
- Mockear tanto una funcionalidad que el test deje de validar su comportamiento real.

Si un test falla después de un cambio, determinar primero si:

1. El código tiene un bug.
2. El comportamiento cambió intencionadamente.
3. El test necesita actualizarse porque el contrato cambió realmente.
4. Existe un problema en el entorno de testing.

---

## 33. Validación antes de finalizar un cambio

Antes de considerar un cambio terminado:

1. Ejecutar los tests relacionados.
2. Ejecutar tests adicionales afectados indirectamente.
3. Ejecutar la suite completa cuando sea apropiado.
4. Comprobar cobertura.
5. Revisar errores y warnings relevantes.
6. Confirmar que no existen regresiones.

Para cambios pequeños puede bastar inicialmente con una ejecución focalizada, pero antes de finalizar debe determinarse si es necesaria una validación más amplia.

---

## 34. Prioridad de validación

La prioridad recomendada es:

1. Tests directamente afectados.
2. Tests del módulo afectado.
3. Tests de integración relacionados.
4. Tests E2E si el flujo crítico está afectado.
5. Suite completa.
6. Cobertura.

La profundidad debe ajustarse al riesgo del cambio.

---

## 35. Cambios de alto riesgo

Requieren especial atención los cambios relacionados con:

- Orquestador.
- Persistencia.
- Detección de duplicados.
- Alertas.
- Stripe.
- Telegram.
- Autenticación.
- Seguridad.
- Scheduler.
- IA.
- Contratos API.

Estos cambios deberían tener una estrategia de testing explícita.

---

## 36. QA y agentes especializados

El agente de QA debe:

- Revisar cobertura.
- Identificar escenarios no cubiertos.
- Crear tests cuando corresponda.
- Revisar regresiones.
- Ejecutar validaciones.
- Identificar problemas de determinismo.
- Comprobar que los tests realmente validan comportamiento.

El agente de QA no debe modificar producción únicamente para hacer pasar una prueba sin entender primero la causa del fallo.

---

## 37. Relación con otros contextos

Este archivo debe utilizarse junto con:

- `.github/copilot-instructions.md`
- `.github/context/architecture.md`
- `.github/context/backend.md`
- `.github/context/security.md`
- `.github/context/ai.md`

Y con los agentes especializados de:

`.github/agents/`

Los workflows de desarrollo y QA determinan el proceso que debe seguirse en cada tipo de cambio.

---

## 38. Regla principal

Cada cambio funcional debe responder a estas preguntas:

1. ¿Qué comportamiento cambia?
2. ¿Qué test demuestra el comportamiento esperado?
3. ¿Qué comportamiento anterior podría romperse?
4. ¿Qué tests existentes protegen ese comportamiento?
5. ¿Necesitamos un test unitario, de integración o E2E?
6. ¿La cobertura sigue siendo suficiente?

La calidad no consiste únicamente en tener muchos tests.

La prioridad es mantener una suite:

**fiable → determinista → significativa → mantenible → suficientemente completa.**