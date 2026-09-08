# FastAPI Skill

## Propósito

Esta skill define cómo trabajar con FastAPI dentro del proyecto OportunidadBot.

Debe utilizarse cuando una tarea implique crear, modificar, revisar o depurar:

- Endpoints HTTP.
- Routers y rutas.
- Request/response models.
- Validación de datos.
- Dependencias de FastAPI.
- Manejo de errores HTTP.
- Webhooks.
- Integración entre la API y los servicios internos.
- Tests relacionados con endpoints.
- Configuración específica de FastAPI.

La skill debe complementar las reglas generales de arquitectura, backend, seguridad y testing del proyecto.

---

## Contexto del proyecto

OportunidadBot utiliza FastAPI como framework HTTP principal.

La aplicación es actualmente un **modular monolith**. FastAPI convive dentro del mismo despliegue con:

- Bot de Telegram.
- Servicios de aplicación.
- Jobs programados.
- Integraciones externas.
- Persistencia mediante Supabase.
- Endpoints relacionados con Stripe.
- Endpoints de debugging y observabilidad.

No introducir una arquitectura distribuida o microservicios como consecuencia de una modificación de FastAPI.

---

## Principios generales

Al trabajar con FastAPI:

1. Mantener los endpoints pequeños y orientados a HTTP.
2. Evitar colocar lógica de negocio compleja directamente en los endpoints.
3. Reutilizar los servicios existentes antes de crear nueva lógica.
4. Mantener separadas las responsabilidades HTTP y las responsabilidades de negocio.
5. Validar los datos de entrada en el límite de la aplicación.
6. Mantener contratos HTTP estables salvo que exista una razón explícita para modificarlos.
7. Utilizar respuestas y errores HTTP coherentes.
8. Evitar abstracciones innecesarias.
9. Mantener los cambios localizados.
10. No realizar refactors no relacionados con la tarea.

---

## Estructura actual relevante

La aplicación contiene actualmente lógica FastAPI principalmente en:

- `app/main.py`
- `app/config.py`
- `app/services/`
- `app/debug/routes.py`

`app/main.py` contiene parte de la composición de la aplicación y varios endpoints.

Antes de crear una nueva estructura de routers:

1. Inspeccionar la estructura existente.
2. Determinar dónde está actualmente implementada la funcionalidad.
3. Mantener el patrón existente si es adecuado.
4. No introducir una reorganización global únicamente por preferencias arquitectónicas.

Si una nueva funcionalidad requiere una estructura diferente, evaluar primero el impacto y proponer el cambio antes de realizar una modificación arquitectónica relevante.

---

## Endpoints

Los endpoints deben actuar como una capa de entrada HTTP.

Responsabilidades apropiadas:

- Recibir la petición.
- Validar parámetros.
- Obtener dependencias necesarias.
- Invocar servicios.
- Transformar el resultado en una respuesta HTTP.
- Traducir errores conocidos a respuestas HTTP apropiadas.

Evitar dentro del endpoint:

- Lógica de negocio extensa.
- Acceso complejo a base de datos.
- Scraping.
- Clasificación mediante IA.
- Procesamiento complejo de feeds.
- Lógica de suscripciones.
- Lógica de Stripe.
- Lógica de Telegram.
- Algoritmos que puedan reutilizarse desde otras partes de la aplicación.

Flujo conceptual:

HTTP Request
    ↓
FastAPI endpoint
    ↓
Service
    ↓
Repository / external integration
    ↓
Service result
    ↓
HTTP Response

El endpoint no debe convertirse en el orquestador principal de la lógica de negocio si ya existe un servicio apropiado.

---

## Request validation

Validar los datos de entrada lo antes posible.

Para datos estructurados:

- Utilizar modelos Pydantic cuando corresponda.
- Definir tipos explícitos.
- Evitar aceptar estructuras arbitrarias si se conoce el contrato esperado.
- Validar campos obligatorios.
- Aplicar restricciones razonables a strings, números y listas.
- No confiar en que el cliente enviará datos válidos.

Para parámetros simples:

- Utilizar type hints.
- Utilizar validación de FastAPI cuando aporte valor.
- Mantener las validaciones relacionadas con el contrato HTTP en la capa HTTP.

La validación específica de reglas de negocio debe permanecer en la capa apropiada del servicio.

---

## Response models

Utilizar response models cuando aporten claridad, validación o estabilidad del contrato.

Los response models deben:

- Representar el contrato público del endpoint.
- Evitar exponer accidentalmente datos internos.
- Mantener una estructura estable.
- Ser suficientemente explícitos para que el consumidor conozca la respuesta.

No devolver directamente objetos internos complejos cuando eso pueda acoplar el contrato HTTP a la implementación interna.

Cuando un endpoint ya tiene un contrato establecido, evitar cambiar nombres, tipos o estructura de respuesta sin una razón justificada.

---

## Status codes

Utilizar códigos HTTP semánticamente correctos.

Como referencia:

- `200 OK` para operaciones exitosas con respuesta.
- `201 Created` cuando se crea un recurso.
- `202 Accepted` cuando una operación ha sido aceptada para procesamiento posterior.
- `204 No Content` cuando la operación tiene éxito y no requiere cuerpo de respuesta.
- `400 Bad Request` para peticiones inválidas.
- `401 Unauthorized` cuando falta autenticación válida.
- `403 Forbidden` cuando el cliente está autenticado pero no tiene permisos.
- `404 Not Found` cuando el recurso solicitado no existe.
- `409 Conflict` para conflictos de estado o duplicados cuando corresponda.
- `422 Unprocessable Entity` para errores de validación gestionados por FastAPI/Pydantic.
- `429 Too Many Requests` cuando corresponda por rate limiting.
- `500 Internal Server Error` para errores inesperados.

No utilizar códigos HTTP arbitrariamente para ocultar errores internos.

---

## Error handling

Los errores esperados deben gestionarse explícitamente.

Preferir:

known domain/application error
    ↓
appropriate HTTP response

sobre:

catch everything
    ↓
return generic response

No capturar `Exception` indiscriminadamente salvo que exista una razón clara para hacerlo.

Los errores inesperados deben registrarse adecuadamente y no revelar información sensible al cliente.

No devolver:

- Secrets.
- Tokens.
- Credenciales.
- Stack traces en producción.
- Datos internos innecesarios.
- Información sensible de otros usuarios.
- Detalles internos de infraestructura.

---

## Dependencias de FastAPI

Utilizar FastAPI dependency injection cuando simplifique responsabilidades como:

- Autenticación.
- Autorización.
- Obtención de contexto.
- Validación común.
- Recursos compartidos.
- Configuración.
- Dependencias reutilizables.

No crear dependencias únicamente para envolver una operación trivial sin aportar reutilización o separación de responsabilidades.

Antes de crear una nueva dependencia:

1. Comprobar si ya existe una equivalente.
2. Comprobar si la lógica puede reutilizarse desde un servicio existente.
3. Mantener la dependencia enfocada en una única responsabilidad.

---

## Async

Utilizar `async` cuando la operación sea realmente asíncrona o dependa de APIs async.

No convertir funciones síncronas en `async` simplemente por seguir una convención.

Prestar especial atención a:

- Requests HTTP.
- Integraciones externas.
- Telegram.
- Operaciones de I/O.
- Jobs que interactúan con servicios externos.

Evitar bloquear el event loop con operaciones síncronas costosas dentro de endpoints async.

Antes de introducir mecanismos adicionales de concurrencia, comprobar si el código existente ya proporciona una solución adecuada.

---

## Integraciones externas

Los endpoints que actúan como entrada para servicios externos deben tratar las integraciones con especial cuidado.

Especialmente:

- Stripe.
- Telegram.
- NVIDIA API.
- Fuentes externas.

El endpoint debe validar y limitar la entrada antes de pasar datos a servicios externos.

No asumir que un payload externo es confiable.

Cuando exista una firma, token o mecanismo de autenticación del proveedor, debe validarse antes de procesar el evento.

---

## Webhooks

Los webhooks son endpoints especialmente sensibles.

Para cualquier webhook:

1. Validar autenticidad antes de procesar el evento.
2. Validar el payload.
3. Evitar procesar eventos inválidos.
4. Gestionar correctamente eventos duplicados cuando corresponda.
5. Mantener el procesamiento idempotente cuando sea necesario.
6. Evitar devolver información sensible.
7. Registrar información suficiente para debugging sin exponer secretos.

### Stripe

Los webhooks de Stripe deben verificar la firma proporcionada por Stripe utilizando el mecanismo oficial correspondiente.

No confiar únicamente en datos enviados por el cliente.

No modificar la lógica de verificación existente sin entender primero su implementación y sus tests.

### Telegram

Los endpoints relacionados con webhooks de Telegram deben mantener las validaciones de seguridad existentes, incluyendo los secretos configurados para el webhook cuando corresponda.

---

## Seguridad HTTP

Toda modificación de endpoints debe considerar:

- Autenticación.
- Autorización.
- Validación de entrada.
- Rate limiting cuando sea necesario.
- Exposición de información.
- CORS si aplica.
- Webhook verification.
- SSRF cuando se acepten URLs externas.
- Inyección de contenido.
- Logging de información sensible.

Nunca:

- Hardcodear secretos.
- Registrar tokens.
- Registrar credenciales.
- Devolver secretos en respuestas.
- Confiar en URLs externas proporcionadas por usuarios sin validación cuando puedan provocar SSRF.
- Deshabilitar una validación de seguridad únicamente para facilitar un test.

---

## URLs proporcionadas por usuarios

Si un endpoint acepta URLs proporcionadas por usuarios, tratar estas URLs como input no confiable.

Evaluar:

- Esquema permitido.
- Hosts permitidos o bloqueados.
- Direcciones privadas/internas.
- Redirecciones.
- Protocolos peligrosos.
- Acceso a metadata services.
- Timeouts.
- Tamaño de respuesta.

La validación debe realizarse antes de ejecutar requests externos.

Si el proyecto ya dispone de una implementación de validación, reutilizarla.

---

## Logging

Los endpoints deben generar logs útiles para diagnosticar problemas sin exponer información sensible.

Evitar registrar directamente:

- Authorization headers.
- Tokens.
- API keys.
- Stripe secrets.
- Telegram secrets.
- Payloads completos cuando puedan contener información sensible.
- Información privada innecesaria de usuarios.

Preferir información contextual como:

- Endpoint.
- Request type.
- Resource identifier.
- Operation.
- Result.
- Error category.
- Duration.

Siempre que sea seguro hacerlo.

Utilizar el sistema de logging existente del proyecto en lugar de introducir otro mecanismo.

---

## Configuración

La configuración de FastAPI debe utilizar el sistema existente basado en configuración de aplicación y variables de entorno.

No hardcodear:

- Secrets.
- URLs de servicios.
- API keys.
- Credenciales.
- Configuración específica de producción.

Si una nueva configuración es necesaria:

1. Añadirla al mecanismo de configuración existente.
2. Documentar la nueva variable si procede.
3. Actualizar tests relacionados.
4. Evitar introducir una segunda fuente de configuración.

---

## Routers

Si la aplicación necesita incorporar routers adicionales:

1. Evaluar primero la estructura actual.
2. Agrupar rutas por responsabilidad.
3. Evitar routers excesivamente grandes.
4. Evitar crear routers artificiales para uno o dos endpoints sin necesidad.
5. Mantener los prefijos y tags coherentes.
6. Registrar el router desde el punto de composición de la aplicación.

Flujo conceptual:

main.py
    ↓
router
    ↓
service

La introducción de routers no debe implicar automáticamente una reorganización completa de `app/main.py`.

Si el cambio requiere una migración significativa de endpoints existentes, tratarlo como cambio arquitectónico y solicitar aprobación antes de ejecutarlo.

---

## Background tasks

No utilizar `BackgroundTasks` automáticamente para cualquier operación lenta.

Antes de utilizarlo:

1. Determinar si la operación realmente puede ejecutarse después de responder.
2. Determinar si necesita garantías de ejecución.
3. Determinar si debe sobrevivir a un restart.
4. Comprobar si APScheduler ya es el mecanismo adecuado.

Para trabajos programados o procesos que requieren ejecución fiable, utilizar el mecanismo de jobs existente en lugar de introducir una segunda infraestructura de scheduling.

---

## Testing

Toda modificación relevante de un endpoint debe incluir o actualizar tests.

Como mínimo, comprobar cuando corresponda:

- Happy path.
- Validación de entrada.
- Recursos inexistentes.
- Errores conocidos.
- Errores de autenticación/autorización.
- Integraciones externas mockeadas.
- Casos límite.

Utilizar la infraestructura existente de:

- `pytest`
- `pytest-asyncio`
- `pytest-mock`
- Fixtures.
- Mocks/fakes existentes.

Antes de crear un mock nuevo:

1. Comprobar si ya existe uno reutilizable.
2. Comprobar fixtures existentes.
3. Mantener el mock específico si la integración lo requiere.

No realizar llamadas reales a servicios externos en tests unitarios.

---

## Tests de webhooks

Los webhooks deben tener tests específicos para:

- Payload válido.
- Firma válida.
- Firma inválida.
- Payload inválido.
- Evento duplicado cuando corresponda.
- Errores del servicio interno.
- Respuesta HTTP esperada.

Para Stripe y Telegram, reutilizar los mocks y fixtures existentes cuando sea posible.

---

## Compatibilidad

Antes de modificar un endpoint existente comprobar:

- Tests existentes.
- Consumidores conocidos.
- Contrato de request.
- Contrato de response.
- Status codes.
- Autenticación.
- Autorización.
- Webhook configuration.
- Documentación existente.

No modificar silenciosamente un contrato público.

Si una modificación incompatible es necesaria:

1. Identificar el impacto.
2. Explicar la incompatibilidad.
3. Proponer una estrategia.
4. Solicitar aprobación cuando el cambio sea relevante.

---

## Documentación

Cuando una modificación de FastAPI cambie alguno de los siguientes aspectos, actualizar la documentación correspondiente:

- Endpoints.
- Contratos HTTP.
- Autenticación.
- Webhooks.
- Variables de configuración.
- Integraciones.
- Flujo de ejecución.

No crear documentación innecesaria para cambios internos triviales.

---

## Rendimiento

No optimizar prematuramente.

Antes de introducir una optimización:

1. Identificar el cuello de botella.
2. Confirmar que el cambio aporta una mejora real.
3. Mantener la complejidad bajo control.
4. Evitar sacrificar legibilidad sin una justificación clara.

Prestar especial atención a:

- Operaciones bloqueantes dentro de endpoints async.
- Requests externos innecesarios.
- Procesamiento repetido.
- Acceso innecesario a base de datos.
- Payloads excesivamente grandes.
- Operaciones costosas ejecutadas durante cada request.

No introducir cachés, colas o sistemas de procesamiento distribuido sin necesidad demostrable.

---

## Cambios arquitectónicos

Los siguientes cambios requieren especial precaución y, normalmente, aprobación previa:

- Migrar todos los endpoints a routers.
- Cambiar la arquitectura de la aplicación.
- Introducir nuevos frameworks HTTP.
- Introducir una capa de repository únicamente por motivos relacionados con FastAPI.
- Introducir un API gateway.
- Introducir microservicios.
- Cambiar el mecanismo global de autenticación.
- Cambiar contratos públicos.
- Introducir una nueva infraestructura de ejecución asíncrona.
- Cambiar la estrategia global de manejo de errores.

FastAPI debe integrarse en la arquitectura actual, no utilizarse como motivo para rediseñarla sin necesidad.

---

## Checklist antes de finalizar un cambio

Antes de considerar terminada una modificación relacionada con FastAPI:

- [ ] El endpoint tiene una responsabilidad clara.
- [ ] La lógica de negocio está fuera del endpoint cuando corresponde.
- [ ] Se reutilizan servicios existentes.
- [ ] Los inputs están correctamente validados.
- [ ] Los response models son adecuados cuando corresponde.
- [ ] Los status codes son correctos.
- [ ] Los errores esperados están gestionados.
- [ ] No se exponen datos sensibles.
- [ ] Los webhooks mantienen sus validaciones de seguridad.
- [ ] No se han introducido dependencias innecesarias.
- [ ] No se bloquea el event loop innecesariamente.
- [ ] Los tests existentes siguen siendo válidos.
- [ ] Se han añadido o actualizado tests relevantes.
- [ ] No se han realizado cambios arquitectónicos innecesarios.
- [ ] La documentación se ha actualizado si el contrato o comportamiento lo requiere.
- [ ] El cambio está limitado al alcance de la tarea.

---

## Regla principal

FastAPI debe funcionar como una **capa HTTP clara, ligera y predecible**.

La API debe recibir y validar las peticiones, delegar el trabajo a las capas apropiadas y convertir los resultados en respuestas HTTP.

Priorizar siempre:

**claridad > abstracción**

**reutilización > duplicación**

**simplicidad > complejidad**

**compatibilidad > cambios innecesarios**

**seguridad > comodidad**

**cambios pequeños > refactors masivos**