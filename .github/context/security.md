# Security Context

## Propósito

Este documento define el contexto de seguridad actual de OportunidadBot.

Su objetivo es proporcionar a los agentes una referencia común sobre:

- Gestión de secretos.
- Validación de entradas.
- Integraciones externas.
- Webhooks.
- URLs externas y SSRF.
- HTML y contenido no confiable.
- Logging.
- Autenticación y autorización.
- Dependencias.
- Configuración y despliegue.
- Criterios para revisar cambios de seguridad.

Este documento describe el baseline de seguridad que debe conservarse y reforzarse cuando sea necesario.

---

## 1. Principios generales

La seguridad debe considerarse una propiedad transversal del backend.

Los agentes deben asumir que:

- Toda entrada externa puede ser maliciosa o estar malformada.
- Las APIs externas pueden devolver datos inesperados.
- Los secretos deben tratarse como información sensible.
- Los logs pueden terminar almacenados o accesibles por terceros.
- Los endpoints públicos pueden ser objetivo de abuso.
- Los datos procedentes de fuentes externas no son confiables.

La seguridad no debe implementarse únicamente en un punto del sistema si existe la posibilidad de que otra ruta permita saltarse la protección.

---

## 2. Gestión de secretos

Los secretos deben almacenarse mediante variables de entorno o mecanismos equivalentes de configuración segura.

No deben aparecer hardcodeados en:

- Código Python.
- Tests.
- Documentación.
- Logs.
- Mensajes de error.
- Commits.
- Configuración versionada.

Ejemplos de información que debe considerarse secreta:

- API keys.
- Tokens de Telegram.
- Secretos de webhooks.
- Credenciales de Supabase.
- Claves de Stripe.
- Credenciales de proveedores de IA.
- Tokens administrativos.

Los valores reales nunca deben incluirse en respuestas generadas por los agentes.

---

## 3. Archivo `.env`

El proyecto utiliza `.env` para configuración local.

El archivo debe permanecer fuera del control de versiones cuando contenga secretos.

Antes de modificar `.gitignore` o mecanismos de configuración, comprobar que no se está permitiendo accidentalmente el versionado de secretos.

No copiar valores reales del `.env` a:

- Código.
- Tests.
- Ejemplos.
- Documentación.
- Logs.

---

## 4. Variables de entorno

La configuración debe centralizarse mediante:

`app/config.py`

Utilizando Pydantic Settings.

Los componentes deberían obtener la configuración desde el sistema de configuración existente en lugar de leer variables de entorno directamente de forma dispersa.

Esto facilita:

- Testing.
- Validación.
- Configuración por entorno.
- Mantenimiento.

---

## 5. Validación de entradas

Toda entrada procedente de usuarios o servicios externos debe considerarse no confiable.

Esto incluye:

- Requests HTTP.
- Parámetros de endpoints.
- Datos de Telegram.
- Webhooks.
- URLs.
- Contenido RSS.
- Contenido Reddit.
- HTML externo.
- Datos recibidos de Stripe.
- Respuestas de proveedores externos.

Debe validarse:

- Tipo.
- Formato.
- Longitud.
- Valores permitidos.
- Estructura.
- Presencia de campos obligatorios.

La validación debe realizarse antes de utilizar los datos en operaciones sensibles.

---

## 6. Telegram

Telegram constituye una superficie de entrada externa.

Los handlers deben asumir que los datos recibidos pueden ser inesperados.

Debe comprobarse:

- Estructura de las actualizaciones.
- Comandos.
- Parámetros.
- Identidad del usuario cuando corresponda.
- Permisos necesarios.
- Datos proporcionados por el usuario.

No confiar únicamente en que Telegram proporciona una estructura válida.

---

## 7. Webhook de Telegram

El webhook de Telegram debe conservar sus mecanismos de validación y protección.

Los cambios relacionados con el webhook deben revisar:

- Validación del secreto configurado.
- Identificación correcta de las peticiones.
- Procesamiento de actualizaciones.
- Errores.
- Repetición de eventos.
- Exposición del endpoint.

No eliminar una validación existente para simplificar tests o desarrollo.

---

## 8. Stripe

Stripe es una integración sensible porque interviene en pagos y suscripciones.

Los webhooks de Stripe deben validar la firma utilizando el mecanismo proporcionado por Stripe.

Nunca debe confiarse únicamente en el contenido recibido por HTTP.

Antes de procesar un evento:

1. Validar autenticidad.
2. Validar estructura.
3. Determinar el tipo de evento.
4. Procesar únicamente eventos soportados.
5. Manejar errores de forma controlada.

Los cambios en esta área deben considerarse de alto riesgo.

---

## 9. Idempotencia

Los procesos que puedan recibir eventos repetidos deben considerar la posibilidad de duplicados.

Esto es especialmente importante en:

- Webhooks.
- Procesamiento de feeds.
- Alertas.
- Operaciones de persistencia.
- Jobs programados.

No asumir que un evento externo se recibirá exactamente una vez.

Antes de modificar lógica relacionada con duplicados, revisar los tests existentes del pipeline.

---

## 10. URLs externas y SSRF

Las URLs proporcionadas por usuarios o fuentes externas deben tratarse como potencialmente peligrosas.

Cuando el sistema realice peticiones HTTP a una URL externa, debe considerarse el riesgo de:

**Server-Side Request Forgery (SSRF)**

Debe evaluarse especialmente:

- Protocolos permitidos.
- Hosts permitidos o esperados.
- Redirecciones.
- Direcciones IP privadas.
- `localhost`.
- Interfaces internas.
- Rangos reservados.
- URLs manipuladas.

No realizar peticiones arbitrarias a URLs proporcionadas por usuarios sin una validación adecuada.

---

## 11. Peticiones HTTP

Las peticiones mediante `httpx` deben utilizar:

- Timeouts adecuados.
- Manejo controlado de errores.
- Validación de respuestas.
- Restricciones apropiadas sobre destinos cuando exista entrada controlable por usuarios.

No asumir que una petición externa:

- Terminará correctamente.
- Responderá rápidamente.
- Tendrá el contenido esperado.
- Devolverá JSON válido.
- Devolverá HTML válido.

---

## 12. Redirecciones

Las redirecciones externas deben considerarse parte de la superficie de seguridad.

Una URL inicialmente válida podría redirigir a un destino no permitido.

Cuando una funcionalidad dependa de URLs externas controladas por usuarios o datos externos, revisar el comportamiento de redirecciones.

No considerar una validación de URL completa si únicamente valida la URL inicial pero permite posteriormente cualquier redirección.

---

## 13. HTML externo

El sistema procesa contenido HTML mediante BeautifulSoup y `lxml`.

El HTML procedente de fuentes externas debe considerarse contenido no confiable.

Debe evitarse insertar HTML externo directamente en interfaces o respuestas sin sanitización apropiada.

Debe controlarse especialmente:

- Scripts.
- Atributos peligrosos.
- URLs externas.
- Contenido embebido.
- HTML malformado.

El parsing de HTML no implica que el contenido sea seguro.

---

## 14. Telegram y contenido generado

El contenido enviado mediante Telegram puede proceder de fuentes externas o de IA.

Antes de enviarlo debe considerarse:

- Longitud.
- Formato.
- Caracteres especiales.
- HTML/Markdown.
- Contenido inesperado.
- Datos sensibles.

No asumir que una respuesta generada por una fuente externa o IA es segura para insertar directamente en un mensaje formateado.

---

## 15. IA

La IA puede procesar contenido procedente de fuentes externas.

Por tanto:

**el contenido enviado al modelo debe considerarse no confiable.**

Debe evitarse que instrucciones incluidas dentro de un anuncio, publicación, RSS, HTML u otro contenido externo sean interpretadas como instrucciones para el sistema.

El prompt debe diferenciar claramente entre:

- Instrucciones del sistema.
- Instrucciones de la aplicación.
- Datos externos que deben analizarse.

No permitir que contenido externo modifique silenciosamente las reglas de procesamiento.

---

## 16. Prompt injection

Los datos analizados por IA pueden contener intentos de prompt injection.

Ejemplos conceptuales:

- Texto que intenta cambiar las instrucciones.
- Texto que solicita revelar información.
- Texto que intenta modificar la clasificación.
- Texto que intenta obtener secretos.
- Texto que intenta provocar acciones no relacionadas con el análisis.

El clasificador debe tratar el contenido externo como **datos**, no como instrucciones confiables.

---

## 17. Respuestas de IA

Las respuestas de IA deben validarse antes de utilizarse en lógica posterior.

No asumir que el modelo:

- Siempre devuelve JSON válido.
- Siempre respeta el formato esperado.
- Siempre incluye todos los campos.
- Nunca produce texto adicional.
- Nunca devuelve valores inesperados.

Cuando el sistema dependa de una estructura concreta, debe existir validación y manejo de errores.

---

## 18. Secretos y IA

Nunca enviar secretos al proveedor de IA salvo que exista una necesidad explícita y aprobada.

No incluir en prompts:

- API keys.
- Tokens.
- Credenciales.
- Secretos de infraestructura.
- Información interna innecesaria.

El contenido enviado al proveedor debe limitarse a la información necesaria para realizar la tarea.

---

## 19. Logging

El sistema utiliza Loguru y mecanismos de logging estructurado.

Los logs deben facilitar diagnóstico sin convertirse en una fuente de filtración de información.

Nunca registrar directamente:

- API keys.
- Tokens.
- Passwords.
- Secretos de webhook.
- Credenciales.
- Cookies sensibles.
- Authorization headers.

---

## 20. Información sensible en logs

Evitar registrar payloads completos cuando no sean necesarios.

Especialmente en:

- Telegram.
- Stripe.
- Supabase.
- IA.
- Requests HTTP.
- Usuarios.

Preferir información técnica mínima, por ejemplo:

- Identificador interno.
- Tipo de evento.
- Estado.
- Duración.
- Resultado.
- Error sanitizado.

No registrar datos sensibles únicamente porque faciliten temporalmente el debugging.

---

## 21. Errores y excepciones

Los errores expuestos al cliente no deben revelar detalles internos innecesarios.

Evitar devolver:

- Stack traces.
- Credenciales.
- Variables de entorno.
- SQL interno.
- Información de infraestructura.
- Paths internos.
- Respuestas completas de servicios externos.

Los detalles técnicos pueden registrarse internamente de forma segura cuando sean necesarios para diagnóstico.

---

## 22. Autenticación y autorización

Los endpoints que proporcionen acceso a información administrativa o sensible deben disponer de controles apropiados.

El proyecto ya contempla mecanismos de protección para el dashboard privado y determinados endpoints.

No asumir que un endpoint es seguro únicamente porque no aparezca enlazado públicamente.

Cada endpoint debe evaluarse según:

- Quién puede acceder.
- Qué datos devuelve.
- Qué operaciones permite.
- Qué impacto tendría un acceso no autorizado.

---

## 23. Dashboard de debugging

El dashboard interno de debugging puede contener información especialmente útil para diagnóstico.

Por tanto:

- Debe permanecer protegido.
- No debe exponerse innecesariamente.
- No debe mostrar secretos.
- No debe mostrar información sensible sin necesidad.
- Los endpoints internos deben revisarse como endpoints reales de seguridad.

No eliminar autenticación para facilitar el desarrollo local sin evaluar el impacto.

---

## 24. Rate limiting

Los endpoints públicos pueden estar expuestos a:

- Abuso.
- Brute force.
- Spam.
- Requests excesivas.
- Agotamiento de recursos.

Cuando el riesgo lo justifique debe considerarse rate limiting.

Antes de introducir un mecanismo nuevo, comprobar si ya existe infraestructura para ello.

No añadir una dependencia únicamente para un caso trivial si puede resolverse correctamente con las herramientas existentes.

---

## 25. Denial of Service

Las entradas externas no deben poder provocar un consumo desproporcionado de recursos.

Considerar límites sobre:

- Tamaño de requests.
- Tamaño de contenido descargado.
- Número de elementos procesados.
- Longitud de textos enviados a IA.
- Número de peticiones externas.
- Tiempo de ejecución.
- Concurrencia.

Las optimizaciones de seguridad deben mantener el comportamiento funcional esperado.

---

## 26. Fuentes externas

Las fuentes RSS, Reddit y Tablón de Anuncios deben tratarse como proveedores externos no confiables.

No asumir que:

- Siempre estarán disponibles.
- Mantendrán el mismo formato.
- Los datos estarán limpios.
- Las URLs serán seguras.
- El contenido será benigno.

Las implementaciones de `app/sources/` deben validar y normalizar los datos antes de entregarlos al resto del pipeline.

---

## 27. Persistencia

Los datos almacenados en Supabase deben validarse antes de persistirse.

Evitar:

- Persistir entradas sin validar.
- Construir consultas de forma insegura.
- Exponer datos innecesarios.
- Confiar en identificadores proporcionados directamente por usuarios.

Utilizar las APIs y mecanismos existentes del cliente de Supabase en lugar de construir manualmente operaciones potencialmente inseguras.

---

## 28. Control de acceso a datos

Cuando una operación acceda a datos asociados a un usuario, debe comprobarse que el usuario tiene derecho a acceder a esos datos.

No confiar únicamente en un identificador proporcionado por el cliente.

Especialmente importante para:

- Usuarios.
- Feeds.
- Suscripciones.
- Alertas.
- Datos administrativos.

---

## 29. Dependencias

Las dependencias externas representan una superficie adicional de seguridad.

Antes de añadir una dependencia significativa:

1. Comprobar si ya existe una solución.
2. Evaluar su mantenimiento.
3. Evaluar vulnerabilidades conocidas.
4. Evaluar su origen.
5. Evaluar su impacto en el despliegue.
6. Evaluar si realmente es necesaria.

No añadir paquetes sin justificación.

---

## 30. Docker y despliegue

El backend se despliega mediante Docker y Railway.

Los cambios relacionados con:

- `Dockerfile`
- `railway.json`
- Variables de entorno.
- Puertos.
- Comandos de arranque.
- Permisos.
- Usuario del contenedor.
- Dependencias del sistema.

deben considerarse cambios potencialmente sensibles.

No modificar configuración de despliegue automáticamente como parte de un cambio funcional no relacionado.

---

## 31. Configuración de producción

La configuración de producción debe evitar:

- Debug innecesario.
- Secretos hardcodeados.
- Endpoints administrativos expuestos.
- Logs excesivamente verbosos.
- Configuración insegura heredada de desarrollo.

Los cambios que afecten a producción deben revisarse explícitamente.

---

## 32. Seguridad en tests

Los tests también deben seguir buenas prácticas de seguridad.

No incluir secretos reales en:

- Fixtures.
- Mocks.
- Tests.
- Snapshots.
- Logs generados.
- Ejemplos.

Utilizar valores ficticios.

Los tests que necesiten credenciales reales deben tratarse como casos especiales y nunca deben provocar que dichas credenciales terminen versionadas.

---

## 33. Seguridad en mocks y fakes

Los mocks deben representar el comportamiento necesario sin contener credenciales reales.

Los fakes de:

- NVIDIA.
- Supabase.
- Telegram.
- Scheduler.

deben permanecer deterministas y seguros.

No copiar respuestas reales que contengan datos sensibles para construir fixtures.

---

## 34. Cambios de seguridad

Cualquier modificación que afecte a:

- Autenticación.
- Autorización.
- Webhooks.
- Secretos.
- URLs externas.
- SSRF.
- Validación de entradas.
- Dependencias de seguridad.
- Exposición de endpoints.
- Datos sensibles.
- Infraestructura.

debe considerarse de alto riesgo.

Antes de implementarla debe analizarse:

1. Amenaza que se intenta mitigar.
2. Punto de entrada.
3. Superficie afectada.
4. Solución propuesta.
5. Posibles bypass.
6. Impacto funcional.
7. Tests necesarios.

---

## 35. Revisión de seguridad

El agente de seguridad debe revisar especialmente:

- Nuevos endpoints.
- Nuevas integraciones.
- Nuevas entradas externas.
- Cambios en autenticación.
- Cambios en webhooks.
- Cambios de configuración.
- Nuevas dependencias.
- Procesamiento de URLs.
- Procesamiento de HTML.
- Prompts y datos enviados a IA.
- Logs.
- Persistencia.

La revisión debe centrarse en riesgos reales y no en introducir complejidad innecesaria.

---

## 36. Principio de mínimo privilegio

Cada componente debe disponer únicamente de los permisos necesarios para cumplir su función.

Evitar:

- Credenciales más amplias de lo necesario.
- Endpoints administrativos accesibles sin necesidad.
- Exposición innecesaria de datos.
- Acceso indiscriminado a recursos.

Cuando una integración permita diferentes niveles de permisos, utilizar el mínimo necesario.

---

## 37. Defensa en profundidad

No depender de una única validación cuando varias capas puedan proteger un recurso crítico.

Ejemplo conceptual:

- Validación de entrada.
- Autenticación.
- Autorización.
- Validación de datos.
- Control de acceso a persistencia.
- Logging seguro.

Cada capa debe aportar una protección real.

---

## 38. Principio de fail-safe

Cuando una validación de seguridad crítica falle, el sistema debe preferir rechazar la operación antes que continuar con datos no confiables.

Ejemplos:

- Firma de webhook inválida.
- Credenciales ausentes.
- URL no permitida.
- Usuario no autorizado.
- Datos con formato inválido.

No degradar silenciosamente una protección crítica.

---

## 39. Compatibilidad con la funcionalidad existente

La seguridad no debe romper funcionalidades existentes sin una razón justificada.

Cuando una protección pueda introducir incompatibilidades:

1. Identificar el comportamiento actual.
2. Evaluar el riesgo.
3. Diseñar una transición cuando sea necesario.
4. Añadir tests.
5. Documentar el cambio.

Las protecciones críticas, sin embargo, no deben eliminarse simplemente para preservar un comportamiento inseguro.

---

## 40. Checklist de seguridad para cambios

Antes de finalizar un cambio, comprobar:

- ¿Se han introducido secretos?
- ¿Se ha añadido una nueva entrada externa?
- ¿Se valida esa entrada?
- ¿Se han introducido nuevas URLs?
- ¿Existe riesgo de SSRF?
- ¿Se procesa HTML no confiable?
- ¿Se ha modificado un webhook?
- ¿Se mantiene la validación de firma?
- ¿Se han añadido logs?
- ¿Los logs pueden contener información sensible?
- ¿Se ha añadido una dependencia?
- ¿Se han modificado permisos o autenticación?
- ¿Se han creado nuevos endpoints?
- ¿Se ha revisado autorización?
- ¿Se han actualizado los tests de seguridad relevantes?

---

## 41. Relación con otros contextos

Este documento debe utilizarse junto con:

- `.github/copilot-instructions.md`
- `.github/context/architecture.md`
- `.github/context/backend.md`
- `.github/context/qa.md`
- `.github/context/ai.md`

Y con los agentes especializados de:

`.github/agents/`

Los workflows determinan el proceso de trabajo que debe seguirse en cada tipo de cambio.

---

## 42. Regla principal

La seguridad debe formar parte del diseño de cada cambio, no ser una revisión posterior.

Ante cualquier dato externo:

**no confiar → validar → limitar → procesar → registrar de forma segura**

Ante cualquier cambio sensible:

**identificar riesgo → analizar impacto → implementar protección → añadir tests → revisar**

La prioridad es mantener un backend funcional sin sacrificar la confidencialidad, integridad y disponibilidad del sistema.