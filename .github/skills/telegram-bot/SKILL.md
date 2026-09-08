# Telegram Bot Skill

## Propósito

Esta skill define cómo trabajar con la integración de Telegram dentro del proyecto OportunidadBot.

Debe utilizarse cuando una tarea implique crear, modificar, revisar o depurar:

- Handlers de Telegram.
- Comandos.
- Mensajes y respuestas.
- Callbacks.
- Botones y keyboards.
- Webhooks de Telegram.
- Integración entre Telegram y los servicios internos.
- Gestión del contexto de usuario.
- Envío de alertas.
- Manejo de errores relacionados con Telegram.
- Tests relacionados con el bot.

La skill debe complementar las reglas generales definidas en:

- `.github/copilot-instructions.md`
- `.github/context/architecture.md`
- `.github/context/backend.md`
- `.github/context/security.md`
- `.github/context/qa.md`

No duplicar aquí reglas generales que ya estén definidas en esos documentos.

---

## Contexto del proyecto

OportunidadBot utiliza Telegram como uno de sus principales canales de interacción con los usuarios.

La integración utiliza:

- `python-telegram-bot`
- Handlers de Telegram.
- Servicios internos para ejecutar la lógica de negocio.
- Telegram para enviar alertas sobre oportunidades detectadas.
- Webhook de Telegram para recibir actualizaciones cuando corresponda.

La integración forma parte del mismo **modular monolith** que el resto de la aplicación.

El bot no debe convertirse en una segunda capa de negocio independiente.

Flujo conceptual:

Telegram
    ↓
Handler
    ↓
Service
    ↓
Database / external integration
    ↓
Service result
    ↓
Telegram response

---

## Estructura actual relevante

La integración principal se encuentra actualmente en:

- `app/bot.py`
- `app/bot/handlers.py`
- `app/services/alert_service.py`
- `app/database.py`
- `app/main.py`

Los handlers deben delegar la lógica de negocio en los servicios existentes cuando corresponda.

Antes de crear nuevas funciones:

1. Inspeccionar los handlers existentes.
2. Buscar servicios reutilizables.
3. Buscar helpers existentes.
4. Revisar cómo se gestionan actualmente los errores.
5. Revisar los tests existentes.
6. Mantener el patrón actual si continúa siendo adecuado.

No reorganizar todo el bot únicamente por preferencias arquitectónicas.

---

## Principios generales

Al trabajar con Telegram:

1. Mantener los handlers pequeños.
2. No colocar lógica de negocio compleja directamente en los handlers.
3. Reutilizar servicios existentes.
4. Validar siempre los datos recibidos.
5. Mantener una experiencia consistente para el usuario.
6. Evitar duplicar lógica entre comandos.
7. Mantener las respuestas claras y predecibles.
8. Gestionar correctamente errores e integraciones externas.
9. No exponer información sensible.
10. Mantener los cambios localizados.
11. No realizar refactors no relacionados con la tarea.

---

## Handlers

Los handlers deben actuar como una capa de entrada para Telegram.

Responsabilidades apropiadas:

- Recibir la actualización.
- Extraer los datos necesarios.
- Validar el input.
- Obtener el usuario/contexto.
- Invocar servicios.
- Construir la respuesta de Telegram.
- Gestionar errores conocidos.

Evitar dentro de los handlers:

- Consultas complejas a base de datos.
- Lógica de negocio extensa.
- Scraping.
- Clasificación mediante IA.
- Lógica compleja de suscripciones.
- Procesamiento de Stripe.
- Algoritmos de detección de oportunidades.
- Lógica reutilizable que pueda pertenecer a un servicio.

Flujo recomendado:

Update
    ↓
Handler
    ↓
Service
    ↓
Result
    ↓
Telegram response

---

## Reutilización de servicios

Antes de implementar lógica dentro de un handler:

1. Buscar si existe un servicio que ya resuelva la operación.
2. Reutilizarlo si existe.
3. Si el servicio necesita una pequeña extensión, modificar el servicio.
4. Evitar duplicar la misma operación en varios handlers.

Ejemplo conceptual:

Handler
    ↓
subscription_service
    ↓
database

en lugar de:

Handler
    ↓
direct database manipulation
    ↓
custom business logic

Los handlers no deben convertirse en repositorios improvisados.

---

## Gestión de usuarios

Las operaciones relacionadas con usuarios deben utilizar las estructuras y servicios existentes.

Cuando un usuario interactúe con el bot:

- Identificar correctamente el usuario de Telegram.
- No asumir que existe en la base de datos.
- Gestionar correctamente usuarios nuevos.
- Evitar crear registros duplicados.
- Mantener consistencia con el modelo de usuarios existente.

No crear un sistema paralelo de identificación de usuarios.

---

## Comandos

Los comandos deben tener una responsabilidad clara.

Ejemplos conceptuales:

- `/start`
- `/help`
- `/settings`
- `/subscribe`

No asumir que estos ejemplos representan necesariamente todos los comandos existentes.

Antes de crear un nuevo comando:

1. Revisar los comandos actuales.
2. Comprobar posibles conflictos.
3. Mantener una nomenclatura consistente.
4. Comprobar si la funcionalidad puede integrarse en un comando existente.
5. Actualizar tests y documentación cuando corresponda.

Los comandos deben proporcionar feedback claro al usuario.

---

## Mensajes

Los mensajes enviados por el bot deben ser:

- Claros.
- Breves cuando la información lo permita.
- Consistentes con el estilo existente.
- Fáciles de leer en dispositivos móviles.
- Adecuados al contexto de la acción.

Evitar mensajes excesivamente técnicos al usuario final.

No exponer:

- Stack traces.
- Excepciones internas.
- SQL.
- Secrets.
- API keys.
- Tokens.
- Información interna de infraestructura.

Los detalles técnicos deben quedar en logs, no en el mensaje de Telegram.

---

## Alertas

Telegram es utilizado para enviar alertas de oportunidades detectadas.

La lógica de generación de oportunidades no debe vivir en el handler de Telegram.

Flujo conceptual:

Source
    ↓
Parser / normalization
    ↓
Novelty detection
    ↓
AI classification
    ↓
Persistence
    ↓
Alert service
    ↓
Telegram

La responsabilidad de Telegram debe centrarse en la entrega y presentación del mensaje.

Cuando se modifique el formato de las alertas:

1. Mantener la información esencial.
2. Evitar romper el formato existente sin necesidad.
3. Comprobar mensajes largos.
4. Comprobar caracteres especiales.
5. Actualizar los tests relacionados.

---

## Telegram formatting

Cuando se utilice formato enriquecido de Telegram, prestar atención a:

- Markdown/MarkdownV2.
- HTML.
- Caracteres especiales.
- Escape de contenido dinámico.
- URLs.
- Texto generado por usuarios.
- Texto procedente de fuentes externas.
- Texto generado por IA.

No asumir que contenido externo puede insertarse directamente en un mensaje formateado.

Si el proyecto utiliza una estrategia concreta de escaping, reutilizarla.

No mezclar diferentes mecanismos de formatting sin una razón clara.

---

## Contenido externo

Los mensajes pueden contener información procedente de:

- RSS.
- Reddit.
- Tablón de Anuncios.
- IA.
- Otros servicios externos.

Ese contenido debe considerarse **no confiable**.

Antes de enviarlo a Telegram:

- Sanitizar cuando sea necesario.
- Escapar caracteres especiales según el formato utilizado.
- Controlar longitud.
- Evitar contenido que pueda romper el formato del mensaje.
- No introducir contenido ejecutable.
- No confiar en HTML o Markdown procedente de fuentes externas.

---

## Longitud de mensajes

Telegram impone límites de longitud en los mensajes.

Cuando un mensaje pueda contener contenido variable:

1. Evaluar su longitud.
2. Evitar asumir que el contenido cabe siempre en un único mensaje.
3. Implementar truncado o división cuando sea necesario.
4. Mantener la información más relevante.
5. No truncar silenciosamente información crítica cuando pueda evitarse.

Si ya existe una utilidad para dividir mensajes, reutilizarla.

---

## Callbacks y botones

Para botones inline y callback queries:

- Mantener callbacks claros.
- Validar los datos recibidos.
- No confiar en valores enviados por el cliente.
- Evitar incluir información sensible en callback data.
- Mantener las acciones delegadas en servicios.
- Responder correctamente al callback cuando corresponda.

Si la callback data contiene identificadores:

1. Validar el formato.
2. Verificar que el recurso existe.
3. Verificar que pertenece al usuario cuando corresponda.
4. Ejecutar únicamente la acción autorizada.

No asumir que un usuario puede ejecutar una acción simplemente porque conoce el callback data.

---

## Autorización

La identidad de Telegram no implica automáticamente autorización para cualquier operación.

Para acciones sensibles:

- Comprobar el usuario.
- Comprobar el recurso solicitado.
- Comprobar permisos.
- Comprobar propiedad cuando corresponda.

Flujo conceptual:

Telegram user
    ↓
Authenticated identity
    ↓
Authorization check
    ↓
Business operation

No permitir acceso a datos de otro usuario únicamente porque se proporcione su identificador.

---

## Webhook de Telegram

El webhook debe tratarse como una superficie de entrada externa.

Debe:

1. Validar la autenticidad/configuración de seguridad existente.
2. Validar el payload.
3. Delegar el procesamiento al bot.
4. Gestionar errores correctamente.
5. Evitar exponer información interna.
6. Mantener un comportamiento seguro ante payloads inesperados.

No eliminar ni debilitar las validaciones existentes para simplificar el desarrollo o los tests.

Cualquier cambio relevante en el webhook debe incluir tests.

---

## Seguridad

La integración de Telegram debe seguir las reglas de seguridad generales del proyecto.

Nunca:

- Hardcodear el bot token.
- Registrar el bot token.
- Exponer tokens en mensajes.
- Incluir secrets en callback data.
- Confiar ciegamente en datos de Telegram.
- Permitir acceso a recursos de otros usuarios.
- Exponer excepciones internas.
- Deshabilitar validaciones de seguridad para facilitar pruebas.

La configuración sensible debe proceder del sistema de configuración existente.

---

## Bot token y configuración

El token de Telegram debe obtenerse desde la configuración de la aplicación.

No:

- Hardcodear el token.
- Añadirlo a código fuente.
- Añadirlo a tests reales.
- Registrarlo en logs.
- Incluirlo en mensajes de error.

Los tests deben utilizar mocks/fakes o configuración de prueba.

---

## Errores de Telegram

Las excepciones de la API de Telegram deben gestionarse de forma adecuada.

Distinguir entre:

- Errores recuperables.
- Errores temporales.
- Errores de configuración.
- Usuario bloqueando el bot.
- Chat inexistente.
- Mensaje inválido.
- Errores de red.
- Errores inesperados.

No convertir cualquier error en un retry infinito.

Si existe una estrategia de retry en el proyecto, reutilizarla.

---

## Retries

Antes de añadir retries:

1. Determinar si la operación es segura para repetir.
2. Determinar si puede provocar mensajes duplicados.
3. Comprobar si Telegram ya gestiona parte del comportamiento.
4. Utilizar backoff cuando sea necesario.
5. Establecer un límite razonable.

No realizar retries infinitos.

Especial atención a:

- Envío de alertas.
- Operaciones que puedan duplicar mensajes.
- Errores de red.
- Timeouts.

---

## Idempotencia

Las operaciones relacionadas con eventos externos deben considerar la posibilidad de duplicación.

Cuando corresponda:

- Detectar eventos repetidos.
- Evitar duplicar registros.
- Evitar duplicar alertas.
- Utilizar identificadores de evento o recurso existentes.
- Mantener el procesamiento seguro ante reintentos.

No introducir mecanismos de idempotencia duplicados si ya existe uno en el sistema.

---

## Rate limiting y abuso

Las acciones iniciadas por usuarios pueden necesitar protección contra abuso.

Prestar especial atención a operaciones que:

- Realicen requests externos.
- Ejecuten scraping.
- Ejecuten clasificación mediante IA.
- Generen muchas alertas.
- Modifiquen configuraciones.
- Generen costes externos.

Antes de introducir rate limiting específico:

1. Comprobar si ya existe una protección.
2. Determinar el coste de la operación.
3. Evaluar el impacto sobre usuarios legítimos.
4. Mantener una solución simple.

---

## Rendimiento

Los handlers no deben realizar operaciones costosas innecesariamente.

Evitar:

- Requests externos secuenciales innecesarios.
- Consultas repetidas.
- Procesamiento pesado dentro del handler.
- Operaciones bloqueantes innecesarias.
- Ejecución de IA si no es necesaria para la acción.

Si una operación larga no debe bloquear la interacción:

1. Evaluar el mecanismo existente de jobs/background processing.
2. Comprobar si APScheduler ya cubre la necesidad.
3. No introducir una infraestructura paralela sin necesidad.

---

## Concurrencia

Telegram puede generar múltiples actualizaciones.

Las operaciones compartidas deben ser seguras frente a concurrencia cuando corresponda.

Prestar atención a:

- Creación de usuarios.
- Suscripciones.
- Configuración de fuentes.
- Estados temporales.
- Alertas.
- Operaciones que modifican datos.

No asumir que dos handlers nunca se ejecutarán simultáneamente.

---

## Testing

Toda modificación relevante del bot debe incluir o actualizar tests.

Utilizar la infraestructura existente:

- `pytest`
- `pytest-asyncio`
- `pytest-mock`
- Fixtures.
- Mocks/fakes.

El proyecto ya dispone de infraestructura específica para Telegram, incluyendo:

- `tests/fixtures/telegram.py`
- `tests/mocks/fake_telegram.py`
- Tests de handlers existentes.

Antes de crear nuevos mocks:

1. Revisar los existentes.
2. Reutilizarlos cuando sea posible.
3. Extenderlos si la nueva funcionalidad lo requiere.
4. Evitar duplicar infraestructura de testing.

---

## Tests de handlers

Los tests deben comprobar cuando corresponda:

- Comando válido.
- Input inválido.
- Usuario inexistente.
- Usuario existente.
- Acción autorizada.
- Acción no autorizada.
- Error del servicio.
- Error de Telegram.
- Respuesta correcta.
- Mensaje correcto.
- Callback válido.
- Callback inválido.
- Casos límite.

No realizar llamadas reales a Telegram desde tests unitarios.

---

## Tests de alertas

Las modificaciones relacionadas con alertas deben comprobar:

- Alertas correctamente construidas.
- Destinatario correcto.
- Contenido correcto.
- Formato correcto.
- Contenido externo correctamente escapado.
- Mensajes largos.
- Errores de envío.
- Reintentos cuando corresponda.
- Prevención de duplicados cuando corresponda.

---

## Cambios en comportamiento

Modificar el comportamiento visible del bot requiere especial cuidado.

Antes de cambiar:

- Texto de comandos.
- Formato de alertas.
- Comportamiento de botones.
- Flujo de interacción.
- Comandos existentes.
- Respuestas ante errores.

Comprobar:

1. Tests existentes.
2. Dependencias internas.
3. Compatibilidad con usuarios actuales.
4. Documentación.
5. Posibles efectos secundarios.

Si el cambio es significativo, explicarlo antes de implementarlo.

---

## Dependencias

No añadir una nueva dependencia únicamente para simplificar una operación que puede resolverse con:

- Python estándar.
- FastAPI.
- `python-telegram-bot`.
- Librerías ya existentes.

Si una dependencia es necesaria:

1. Explicar qué problema resuelve.
2. Comprobar que no existe una solución existente.
3. Evaluar mantenimiento.
4. Evaluar seguridad.
5. Evaluar impacto en despliegue.
6. Actualizar la configuración correspondiente.

---

## Logging

Registrar información suficiente para diagnosticar problemas sin exponer información sensible.

Puede ser útil registrar:

- Tipo de actualización.
- Tipo de operación.
- Identificador interno no sensible.
- Resultado.
- Categoría del error.
- Duración.

Evitar registrar:

- Bot token.
- Authorization headers.
- Payloads completos innecesarios.
- Información sensible del usuario.
- Tokens externos.
- Credenciales.

Utilizar el sistema de logging existente del proyecto.

---

## Documentación

Actualizar documentación cuando una modificación cambie:

- Comandos.
- Flujos de interacción.
- Webhook.
- Configuración.
- Integración con Telegram.
- Formato de alertas.
- Comportamiento público del bot.

No crear documentación adicional para cambios internos triviales.

---

## Cambios arquitectónicos

Los siguientes cambios requieren especial precaución y normalmente aprobación previa:

- Sustituir `python-telegram-bot`.
- Cambiar completamente el mecanismo de webhook.
- Introducir otra librería de bots.
- Separar Telegram en un microservicio.
- Crear una nueva capa arquitectónica únicamente para Telegram.
- Cambiar el mecanismo global de autenticación.
- Cambiar la estrategia de procesamiento de actualizaciones.
- Introducir una nueva infraestructura de colas.
- Modificar significativamente el flujo de alertas.

El objetivo es mejorar la implementación existente, no rediseñar el sistema sin necesidad.

---

## Checklist antes de finalizar

Antes de considerar terminada una modificación relacionada con Telegram:

- [ ] El handler tiene una responsabilidad clara.
- [ ] La lógica de negocio está delegada al servicio correspondiente.
- [ ] Se reutiliza código existente cuando corresponde.
- [ ] Los inputs están validados.
- [ ] Las acciones sensibles comprueban autorización.
- [ ] No se exponen secretos.
- [ ] El bot token permanece fuera del código.
- [ ] El contenido externo se trata como no confiable.
- [ ] El formato de Telegram se escapa correctamente.
- [ ] Se consideran límites de longitud.
- [ ] Los errores están gestionados.
- [ ] No existen retries infinitos.
- [ ] Se considera la idempotencia cuando corresponde.
- [ ] No se bloquea innecesariamente el procesamiento.
- [ ] Se han actualizado los tests relevantes.
- [ ] Se reutilizan fixtures/mocks existentes.
- [ ] No se han realizado cambios arquitectónicos innecesarios.
- [ ] La documentación se ha actualizado si el contrato o comportamiento lo requiere.
- [ ] El cambio está limitado al alcance de la tarea.

---

## Regla principal

Telegram debe funcionar como una **capa de interacción y entrega**, no como una segunda capa de negocio.

Los handlers deben recibir y validar las actualizaciones, delegar el trabajo a los servicios apropiados y presentar los resultados al usuario de forma clara y segura.

Priorizar siempre:

**claridad > abstracción**

**reutilización > duplicación**

**simplicidad > complejidad**

**seguridad > comodidad**

**compatibilidad > cambios innecesarios**

**cambios pequeños > refactors masivos**