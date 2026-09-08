# Backend Context

## Propósito

Este documento describe el contexto técnico del backend actual de OportunidadBot.

Su objetivo es proporcionar a los agentes de GitHub Copilot una referencia común sobre:

- Tecnologías utilizadas.
- Organización del backend.
- Responsabilidades de los principales módulos.
- Flujo de ejecución.
- Integraciones.
- Configuración.
- Persistencia.
- Manejo de errores.
- Testing.
- Criterios para modificar el backend.

Este documento describe el sistema existente y no constituye una propuesta para rediseñarlo.

---

## 1. Stack tecnológico

El backend está desarrollado principalmente con:

- Python.
- FastAPI.
- `python-telegram-bot`.
- Supabase.
- APScheduler.
- Pydantic Settings.
- Loguru.
- Pytest.

Integraciones y librerías relevantes:

- `feedparser` para RSS.
- BeautifulSoup para parsing HTML.
- `lxml` para procesamiento HTML/XML.
- `httpx` para peticiones HTTP.
- OpenAI-compatible SDK para la integración con NVIDIA API.
- Stripe SDK para pagos y suscripciones.

---

## 2. Organización del backend

La aplicación principal se encuentra dentro de `app/`.

Estructura relevante:

- `app/main.py`
- `app/config.py`
- `app/database.py`
- `app/models.py`
- `app/bot.py`
- `app/bot/`
- `app/services/`
- `app/sources/`
- `app/jobs/`
- `app/subscriptions/`
- `app/debug/`

Cada módulo debe mantener una responsabilidad clara.

No debe utilizarse la estructura actual como justificación para introducir nuevas capas cuando no exista una necesidad real.

---

## 3. Punto de entrada

### `app/main.py`

Es el principal punto de composición de la aplicación.

Puede contener:

- Inicialización de FastAPI.
- Configuración de endpoints.
- Registro de componentes.
- Configuración de webhooks.
- Integración de diferentes servicios.

La lógica de negocio compleja debe permanecer fuera de los endpoints.

Cuando un endpoint necesite realizar una operación de negocio:

1. Validar la entrada.
2. Obtener las dependencias necesarias.
3. Delegar en el servicio correspondiente.
4. Transformar el resultado en la respuesta HTTP apropiada.

---

## 4. Configuración

### `app/config.py`

La configuración se gestiona mediante Pydantic Settings y variables de entorno.

La configuración sensible debe proceder del entorno.

No se deben introducir:

- API keys hardcodeadas.
- Tokens hardcodeados.
- Credenciales en el código.
- Secretos en archivos versionados.

Los cambios en configuración deben valorar su impacto tanto en desarrollo local como en despliegue.

---

## 5. Persistencia

### `app/database.py`

El acceso a la base de datos se realiza mediante Supabase.

Actualmente:

- Se utiliza el cliente de Supabase directamente.
- No se utiliza un ORM.
- Las operaciones de persistencia están centralizadas principalmente en `database.py`.

Antes de crear una nueva operación de acceso a datos:

1. Buscar si ya existe una operación equivalente.
2. Reutilizarla si es posible.
3. Extenderla si la nueva necesidad pertenece a la misma responsabilidad.
4. Crear una nueva función solamente cuando exista una responsabilidad claramente diferenciada.

No introducir un ORM únicamente para aplicar un patrón arquitectónico.

---

## 6. Modelos

### `app/models.py`

Contiene modelos utilizados por el backend.

Los modelos deben mantenerse coherentes con los contratos existentes.

Antes de modificar un modelo utilizado por varias partes del sistema se debe comprobar:

- Dónde se utiliza.
- Qué endpoints lo exponen.
- Qué servicios dependen de él.
- Qué tests lo utilizan.
- Si afecta a persistencia.
- Si afecta a integraciones externas.

Los cambios incompatibles deben considerarse cambios de arquitectura o contrato y requieren una revisión adecuada.

---

## 7. Servicios

La lógica de aplicación se encuentra principalmente en:

`app/services/`

Servicios actuales relevantes:

- `orchestrator.py`
- `feed_parser.py`
- `ai_classifier.py`
- `alert_service.py`
- `stripe_service.py`
- `subscription_service.py`
- `prompts.py`
- `source_display_name.py`

Cada servicio debe mantener una responsabilidad coherente.

### Regla

No introducir lógica directamente en un servicio existente simplemente porque sea el archivo más cercano.

Primero determinar cuál es la responsabilidad real de la nueva funcionalidad.

---

## 8. Orquestador

### `app/services/orchestrator.py`

Es el componente principal de coordinación del pipeline.

Coordina conceptualmente:

1. Obtención de información desde fuentes.
2. Parsing y normalización.
3. Detección de novedades.
4. Clasificación mediante IA cuando corresponde.
5. Persistencia.
6. Generación de alertas.
7. Envío de notificaciones.

El orquestador debe coordinar las etapas, no implementar todos sus detalles internos.

Si empieza a acumular demasiada lógica específica, debe evaluarse la extracción de esa responsabilidad a un servicio especializado.

No crear un segundo orquestador paralelo sin una razón arquitectónica clara.

---

## 9. Fuentes externas

Las fuentes se encuentran en:

`app/sources/`

Componentes principales:

- `base.py`
- `factory.py`
- `item.py`
- `rss_source.py`
- `reddit_source.py`
- `tablon_source.py`

Existe una abstracción común para las fuentes.

Las fuentes concretas deben encargarse de los detalles específicos de cada proveedor.

La lógica común debe mantenerse fuera de las implementaciones específicas cuando pueda reutilizarse.

---

## 10. Factory de fuentes

### `app/sources/factory.py`

Centraliza la creación o selección de implementaciones de fuentes.

Cuando se añada una nueva fuente:

1. Comprobar la abstracción existente.
2. Crear la implementación específica.
3. Integrarla mediante la factory.
4. Añadir los tests correspondientes.
5. Evitar modificar innecesariamente las fuentes existentes.

No debe introducirse lógica específica de cada proveedor dentro de la factory si puede mantenerse en su implementación correspondiente.

---

## 11. Normalización de elementos

### `app/sources/item.py`

Representa los elementos obtenidos de las fuentes.

El objetivo de esta capa es proporcionar una representación común independientemente de la fuente original.

El resto del pipeline debería trabajar preferentemente con esta representación común en lugar de depender de estructuras específicas de RSS, Reddit o Tablón de Anuncios.

---

## 12. Parsing

### `app/services/feed_parser.py`

Centraliza lógica relacionada con parsing y procesamiento de feeds.

Utiliza tecnologías como:

- `feedparser`.
- BeautifulSoup.
- `lxml`.

El parser debe encargarse de transformar información externa en estructuras que el resto de la aplicación pueda procesar.

Debe contemplarse que las fuentes externas pueden proporcionar:

- Campos ausentes.
- HTML incompleto.
- Datos malformados.
- Formatos inesperados.
- Valores nulos.
- Cambios en la estructura de origen.

Los parsers deben fallar de forma controlada y proporcionar suficiente información para diagnosticar errores sin exponer información sensible.

---

## 13. Clasificación mediante IA

### `app/services/ai_classifier.py`

Contiene la integración con el sistema de clasificación mediante IA.

La IA utiliza opcionalmente una API de NVIDIA mediante una interfaz compatible con OpenAI.

La clasificación mediante IA debe permanecer desacoplada del resto del pipeline tanto como sea razonablemente posible.

El resto de la aplicación no debería necesitar conocer detalles específicos de:

- Cliente HTTP.
- Proveedor.
- Modelo concreto.
- Formato interno de la petición.

Cuando sea posible, debe interactuar con el servicio mediante una interfaz de alto nivel.

---

## 14. Prompts

### `app/services/prompts.py`

Centraliza prompts relacionados con la IA.

Los prompts no deben duplicarse innecesariamente entre diferentes componentes.

Cuando se modifique un prompt que pueda afectar al comportamiento de clasificación:

- Identificar qué flujos lo utilizan.
- Actualizar tests relevantes.
- Comprobar posibles cambios de comportamiento.
- Validar la respuesta del modelo cuando sea necesario.

Los cambios importantes relacionados con IA deben seguir además el workflow específico de cambios de IA.

---

## 15. Alertas

### `app/services/alert_service.py`

Gestiona la generación y/o envío de alertas.

La generación de una alerta debe permanecer separada de los detalles de otras etapas del pipeline cuando sea posible.

Un cambio en las reglas de alertas debe comprobar:

- Cuándo se genera una alerta.
- Qué datos contiene.
- A qué usuario se envía.
- Cómo se comunica con Telegram.
- Qué ocurre cuando el envío falla.
- Qué tests cubren el comportamiento.

---

## 16. Telegram

Existen componentes relacionados con Telegram en:

- `app/bot.py`
- `app/bot/`
- `app/bot/handlers.py`

La integración utiliza `python-telegram-bot`.

Los handlers deben actuar como capa de entrada para las interacciones del usuario.

La lógica reutilizable debe delegarse a servicios.

Evitar implementar reglas de negocio complejas directamente dentro de handlers.

---

## 17. Webhook de Telegram

La aplicación expone un mecanismo de webhook para Telegram.

La validación del webhook debe mantenerse.

Los cambios relacionados con el webhook deben considerar:

- Autenticación/validación.
- Formato de las actualizaciones.
- Compatibilidad con Telegram.
- Manejo de errores.
- Idempotencia cuando corresponda.
- Tests.

No eliminar validaciones existentes para simplificar el flujo.

---

## 18. Stripe

### `app/services/stripe_service.py`

Centraliza la lógica relacionada con Stripe.

Actualmente se utilizan:

- Stripe Checkout.
- Customer Portal.
- Webhooks.

### Webhooks

La validación de firma del webhook debe conservarse.

Los handlers de Stripe deben evitar confiar únicamente en datos proporcionados por el cliente.

Los cambios en pagos, suscripciones o webhooks deben considerarse cambios sensibles.

---

## 19. Suscripciones

La lógica relacionada con suscripciones se encuentra principalmente en:

- `app/services/subscription_service.py`
- `app/subscriptions/catalog.py`
- `app/subscriptions/entities.py`

La separación permite diferenciar:

- Catálogo de planes.
- Entidades de suscripción.
- Lógica de aplicación.

Antes de modificar un plan o suscripción debe comprobarse si el cambio afecta a:

- Stripe.
- Usuarios existentes.
- Persistencia.
- Límites funcionales.
- Frontend.
- Tests.

---

## 20. Jobs programados

### `app/jobs/scheduler.py`

Los procesos periódicos utilizan APScheduler.

Los jobs deben ser ligeros en cuanto a responsabilidad.

Preferentemente:

`job -> service/orchestrator -> lógica de negocio`

y no:

`job -> lógica de negocio duplicada`

Esto permite que la misma lógica pueda ejecutarse desde diferentes puntos de entrada y facilita su testing.

---

## 21. Debug y trazabilidad

El backend dispone de un sistema propio de debugging en:

`app/debug/`

Componentes relevantes:

- `config.py`
- `routes.py`
- `trace_models.py`
- `trace_repository.py`
- `trace_service.py`

También existen:

- `app/logging_flow.py`
- `logs/bot.log`
- Dashboard interno.

Los cambios importantes en procesos críticos deberían mantener una trazabilidad suficiente para poder diagnosticar problemas.

Los logs deben evitar:

- Tokens.
- Secretos.
- Credenciales.
- Información sensible innecesaria.
- Payloads completos cuando no sean necesarios.

---

## 22. Manejo de errores

Los errores deben manejarse en el nivel adecuado.

### Entrada

Los datos externos o proporcionados por usuarios deben validarse antes de utilizarlos.

### Servicios

Los servicios deben manejar errores de dominio o integración cuando puedan hacerlo de forma significativa.

### Integraciones externas

Los errores de APIs externas, scraping, Telegram, Stripe o IA deben tratarse de forma controlada.

### API

Los endpoints deben traducir errores a respuestas HTTP coherentes sin exponer detalles internos innecesarios.

No utilizar excepciones genéricas como mecanismo principal de control de flujo.

---

## 23. HTTP y recursos externos

Las peticiones externas utilizan principalmente `httpx`.

Las conexiones a recursos externos deben considerar:

- Timeouts.
- Errores de red.
- Respuestas inesperadas.
- Códigos HTTP.
- Contenido malformado.
- Reintentos cuando sean apropiados.

No asumir que una fuente externa siempre está disponible o devuelve datos válidos.

---

## 24. Seguridad en backend

El backend debe mantener como mínimo:

- Secretos únicamente mediante variables de entorno.
- Validación de entradas.
- Validación de firmas de Stripe.
- Validación del webhook de Telegram.
- Protección frente a SSRF al procesar URLs externas.
- Sanitización de HTML cuando se procese contenido externo.
- No exposición de secretos en logs.
- No exposición innecesaria de información interna en errores.
- Revisión de autenticación de endpoints administrativos.
- Rate limiting cuando sea necesario para endpoints públicos.

Los cambios de seguridad deben revisarse antes de considerarse finalizados.

---

## 25. Testing

El proyecto utiliza:

- `pytest`.
- `pytest-asyncio`.
- `pytest-mock`.
- `pytest-cov`.

La estructura actual es:

- `tests/unit/`
- `tests/integration/`
- `tests/e2e/`
- `tests/fixtures/`
- `tests/mocks/`

La cobertura está configurada con un objetivo mínimo del 90%.

---

## 26. Unit tests

Los tests unitarios deben utilizarse para lógica aislada.

Ejemplos de componentes con cobertura unitaria:

- Servicios.
- Parsers.
- Sources.
- Handlers.
- Scheduler.
- Stripe.
- Suscripciones.

Los tests unitarios deben evitar depender innecesariamente de servicios externos reales.

---

## 27. Integration tests

Los tests de integración comprueban la interacción entre varios componentes.

Son especialmente relevantes para:

- Orquestador.
- Base de datos.
- Feed detector.
- Scheduler.
- Alertas.
- Clasificación IA.

Cuando una integración externa no deba ejecutarse realmente, utilizar mocks o fakes existentes.

---

## 28. E2E

Los tests E2E verifican flujos completos.

Actualmente existen pruebas para:

- Pipeline completo.
- Detección de duplicados.
- Procesamiento de múltiples feeds.

Los cambios que afecten al pipeline principal deben comprobar si requieren actualizar o añadir cobertura E2E.

---

## 29. Fixtures y mocks

Los tests disponen de fixtures y mocks reutilizables.

Entre ellos:

- `fake_nvidia.py`
- `fake_scheduler.py`
- `fake_supabase.py`
- `fake_telegram.py`

Antes de crear un mock nuevo, comprobar si existe uno reutilizable.

Los mocks deben representar el comportamiento relevante de la dependencia y no convertirse en implementaciones paralelas del sistema real.

---

## 30. Cambios funcionales

Cuando se implemente una funcionalidad:

1. Inspeccionar primero el código existente.
2. Identificar el servicio o módulo responsable.
3. Reutilizar componentes existentes.
4. Implementar el cambio mínimo necesario.
5. Añadir o modificar tests.
6. Ejecutar la validación correspondiente.
7. Revisar efectos secundarios.

No realizar refactors no relacionados dentro del mismo cambio.

---

## 31. Bug fixes

Los errores deben corregirse intentando identificar primero la causa raíz.

Un bug fix debe incluir una prueba de regresión cuando sea razonablemente posible.

La prueba debe demostrar:

- El comportamiento que fallaba.
- El comportamiento esperado después de la corrección.

No eliminar o debilitar tests existentes simplemente para hacer que la suite pase.

---

## 32. Nuevas dependencias

Antes de añadir una dependencia:

1. Comprobar si la funcionalidad puede resolverse con el código existente.
2. Comprobar si puede resolverse con la librería estándar.
3. Revisar dependencias ya instaladas.
4. Explicar qué problema resuelve.
5. Evaluar mantenimiento.
6. Evaluar seguridad.
7. Evaluar impacto en despliegue.

Las dependencias significativas requieren aprobación previa.

---

## 33. Cambios de base de datos

Los cambios relacionados con:

- Esquema.
- Tablas.
- Columnas.
- Índices.
- Constraints.
- Migraciones.
- Datos existentes.

deben considerarse cambios de alto impacto.

No deben ejecutarse automáticamente sin revisión y aprobación previa.

Antes de realizar un cambio de persistencia se debe determinar:

- Qué datos existentes se ven afectados.
- Compatibilidad hacia atrás.
- Impacto en código.
- Impacto en tests.
- Necesidad de migración.
- Estrategia de rollback.

---

## 34. Compatibilidad

Los cambios deben preservar el comportamiento existente siempre que sea posible.

Antes de cambiar una función, endpoint o servicio utilizado por múltiples componentes, buscar sus consumidores.

No asumir que una función utilizada únicamente en un archivo es realmente privada sin comprobar referencias.

Los contratos externos deben considerarse estables salvo decisión explícita de cambiarlos.

---

## 35. Código limpio

El backend debe seguir estos principios:

- KISS.
- DRY.
- SRP cuando aporte valor real.
- Funciones pequeñas y comprensibles.
- Nombres descriptivos.
- Código explícito antes que abstracciones innecesarias.
- Reutilización antes que duplicación.
- Cambios pequeños y enfocados.

No aplicar patrones de diseño automáticamente.

La complejidad debe estar justificada por una necesidad real.

---

## 36. Regla para los agentes de backend

Antes de modificar el backend:

1. Leer este contexto.
2. Leer `copilot-instructions.md`.
3. Identificar el módulo responsable.
4. Inspeccionar código y tests relacionados.
5. Buscar implementaciones existentes reutilizables.
6. Realizar el cambio mínimo necesario.
7. Añadir o actualizar tests.
8. Ejecutar las validaciones correspondientes.
9. Revisar seguridad y compatibilidad.
10. Documentar cambios importantes.

Si el cambio afecta a arquitectura, base de datos, dependencias relevantes, seguridad, contratos externos o despliegue, detenerse y solicitar aprobación antes de ejecutarlo.

---

## 37. Principio fundamental

El backend debe evolucionar de forma incremental.

La prioridad es:

**funcionalidad correcta → mantenibilidad → simplicidad → seguridad → rendimiento**

No optimizar prematuramente ni introducir complejidad arquitectónica sin evidencia de que sea necesaria.

Cuando exista una solución sencilla que cumpla correctamente los requisitos, debe preferirse frente a una solución más compleja.