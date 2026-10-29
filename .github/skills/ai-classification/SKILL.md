# AI Classification Skill

## Propósito

Esta skill define cómo trabajar con la integración de Inteligencia Artificial utilizada para analizar y clasificar publicaciones en OportunidadBot.

Debe utilizarse cuando una tarea implique crear, modificar, revisar o depurar:

- Clasificación mediante IA.
- `app/services/ai_classifier.py`.
- Prompts.
- `app/services/prompts.py`.
- Integración con NVIDIA API.
- Clientes compatibles con la interfaz OpenAI.
- Caching de resultados de IA.
- Parseo de respuestas del modelo.
- Validación de resultados generados por IA.
- Gestión de errores y timeouts de IA.
- Costes y eficiencia de llamadas.
- Tests relacionados con IA.

La skill debe complementar las reglas generales definidas en:

- `.github/copilot-instructions.md`
- `.github/context/architecture.md`
- `.github/context/backend.md`
- `.github/context/security.md`
- `.github/context/qa.md`
- `.github/context/ai.md`

No duplicar innecesariamente reglas generales ya definidas en esos documentos.

---

## Contexto del proyecto

OportunidadBot utiliza IA como parte opcional del pipeline de procesamiento de publicaciones.

La IA se utiliza para analizar publicaciones y determinar si pueden representar una oportunidad relevante.

La integración actual utiliza:

- NVIDIA API.
- Una interfaz compatible con OpenAI.
- `app/services/ai_classifier.py`.
- `app/services/prompts.py`.
- Caching de resultados cuando corresponde.

La IA es una parte del pipeline, no el centro de la arquitectura.

Flujo conceptual:

Source
    ↓
Fetch
    ↓
Parse
    ↓
Normalize
    ↓
Novelty detection
    ↓
AI classification
    ↓
Persistence
    ↓
Alert

La clasificación mediante IA debe permanecer desacoplada de:

- Telegram.
- Stripe.
- Gestión de usuarios.
- Scraping específico de fuentes.
- API HTTP.
- Scheduler.

---

## Principios generales

Al trabajar con IA:

1. Utilizar la integración existente antes de crear una nueva.
2. Mantener la IA como una dependencia opcional del pipeline cuando corresponda.
3. Separar construcción de prompts, llamada al modelo y procesamiento de respuestas.
4. Validar las respuestas del modelo.
5. No confiar ciegamente en contenido generado por IA.
6. Gestionar errores y timeouts.
7. Evitar llamadas innecesarias.
8. Utilizar caching cuando sea apropiado.
9. Mantener los costes bajo control.
10. Mantener los cambios localizados.
11. No introducir complejidad innecesaria.
12. No realizar refactors no relacionados con la tarea.

---

## Estructura actual relevante

La integración principal se encuentra actualmente en:

- `app/services/ai_classifier.py`
- `app/services/prompts.py`
- `app/config.py`

También existen tests relacionados con IA, incluyendo:

- `tests/unit/test_ai_classifier.py`
- `tests/integration/test_ai_classifier_live.py`
- `tests/fixtures/nvidia.py`
- `tests/mocks/fake_nvidia.py`

Existe además un script relacionado con el cache:

- `scripts/clear_ai_cache.py`

Antes de modificar la integración:

1. Revisar `ai_classifier.py`.
2. Revisar `prompts.py`.
3. Revisar la configuración existente.
4. Revisar el sistema de caching.
5. Revisar los tests.
6. Revisar cómo el orquestador utiliza el clasificador.

No asumir que la arquitectura descrita aquí sustituye a la implementación actual. El código existente es la fuente de verdad para detalles concretos.

---

## Separación de responsabilidades

La integración de IA debe mantener responsabilidades diferenciadas.

Conceptualmente:

Prompt construction
    ↓
AI client
    ↓
Model response
    ↓
Response validation/parsing
    ↓
Classification result

Evitar mezclar en una única función:

- Construcción del prompt.
- Requests HTTP.
- Parsing.
- Persistencia.
- Envío de alertas.
- Lógica de usuarios.

Si una función existente realiza varias responsabilidades, evitar ampliar aún más su alcance. Considerar una refactorización únicamente si es necesaria para la tarea.

---

## ai_classifier.py

`app/services/ai_classifier.py` es la pieza principal de integración con el modelo.

Al modificarlo:

- Reutilizar el cliente existente.
- Mantener la interfaz utilizada por el resto de la aplicación.
- Evitar acoplar el código a detalles innecesarios del proveedor.
- Gestionar errores de forma explícita.
- Validar respuestas.
- Evitar introducir llamadas adicionales no justificadas.

Antes de cambiar la interfaz pública del clasificador:

1. Buscar todos sus consumidores.
2. Revisar tests.
3. Evaluar impacto.
4. Mantener compatibilidad cuando sea posible.

---

## Proveedor de IA

La integración actual utiliza NVIDIA API mediante una interfaz compatible con OpenAI.

No sustituir el proveedor ni introducir otro cliente sin una razón explícita.

Antes de cambiar la integración del proveedor:

1. Revisar configuración existente.
2. Revisar cliente utilizado.
3. Revisar tests y mocks.
4. Evaluar compatibilidad.
5. Evaluar impacto en configuración y deployment.

No introducir dependencias adicionales si la interfaz existente permite resolver la necesidad.

---

## Configuración

Las credenciales y configuración del proveedor deben proceder del sistema de configuración existente.

Nunca:

- Hardcodear API keys.
- Hardcodear tokens.
- Registrar API keys.
- Incluir credenciales en prompts.
- Incluir credenciales en tests.
- Exponer credenciales en errores.

La configuración debe utilizar variables de entorno y el mecanismo existente de `app/config.py`.

Si se añade una nueva configuración:

1. Añadirla al sistema existente.
2. Documentarla cuando corresponda.
3. Actualizar tests.
4. Evitar crear una segunda fuente de configuración.

---

## Prompts

Los prompts deben mantenerse separados de la lógica de infraestructura cuando sea posible.

La ubicación actual para prompts es:

- `app/services/prompts.py`

Al modificar prompts:

1. Revisar los prompts existentes.
2. Reutilizar instrucciones comunes.
3. Evitar duplicación.
4. Mantenerlos claros y deterministas.
5. Evitar introducir información innecesaria.
6. Definir claramente el formato esperado de respuesta.
7. Considerar cómo afectará el cambio a los tests y al parsing.

No cambiar simultáneamente el prompt y el parser sin necesidad.

---

## Diseño de prompts

Un prompt debe especificar claramente:

- Qué tarea debe realizar el modelo.
- Qué información recibe.
- Qué criterios debe utilizar.
- Qué formato debe devolver.
- Qué hacer cuando la información sea insuficiente.
- Qué campos son obligatorios.

Cuando se espere una respuesta estructurada, preferir un formato fácilmente validable.

Evitar depender de texto libre si el sistema necesita una clasificación concreta.

---

## Contenido externo en prompts

Las publicaciones procedentes de fuentes externas deben considerarse contenido no confiable.

Esto es especialmente importante porque pueden contener instrucciones diseñadas para manipular al modelo.

No tratar el contenido de una publicación como instrucciones del sistema.

Conceptualmente:

System instructions
    ↓
Classification task
    ↓
Untrusted external content
    ↓
Structured result

El contenido analizado debe permanecer claramente separado de las instrucciones que definen el comportamiento esperado del modelo.

---

## Prompt injection

Considerar ataques de prompt injection cuando el modelo procese contenido externo.

Una publicación podría contener texto como:

- Instrucciones dirigidas al modelo.
- Intentos de cambiar la tarea.
- Peticiones para ignorar las instrucciones originales.
- Contenido diseñado para alterar la clasificación.
- Información que intenta provocar una salida no válida.

El modelo debe tratar el contenido de la publicación como **datos a analizar**, no como instrucciones con autoridad.

No confiar en frases procedentes del contenido externo como instrucciones de ejecución.

---

## Datos enviados al modelo

Enviar únicamente la información necesaria para realizar la clasificación.

Evitar incluir:

- Secrets.
- API keys.
- Tokens.
- Información privada innecesaria.
- Datos de otros usuarios.
- Información de infraestructura.
- Campos que no aporten valor a la clasificación.

Aplicar el principio de mínimo privilegio también al contexto enviado al modelo.

---

## Privacidad

Antes de enviar información al proveedor de IA:

1. Determinar qué datos se están enviando.
2. Evaluar si contienen información privada.
3. Evitar enviar información innecesaria.
4. Mantener las credenciales fuera del contenido.
5. Seguir la configuración y políticas existentes del proyecto.

No ampliar el conjunto de datos enviado al proveedor sin una razón clara.

---

## Respuestas del modelo

Nunca asumir que la respuesta del modelo es válida únicamente porque la request haya tenido éxito.

Validar:

- Existencia de la respuesta.
- Formato.
- Campos esperados.
- Tipos.
- Valores permitidos.
- Estructura.
- Contenido necesario para continuar el pipeline.

Si el modelo devuelve información inválida:

1. Gestionar el error.
2. Evitar persistir datos corruptos.
3. Evitar enviar una alerta incorrecta.
4. Registrar información útil para diagnóstico sin exponer contenido sensible.

---

## Clasificaciones

Cuando el modelo produzca una clasificación:

- Utilizar valores controlados siempre que sea posible.
- Validar que el resultado pertenece al conjunto esperado.
- No depender de variaciones arbitrarias de texto.
- Normalizar valores cuando corresponda.

Si el proyecto utiliza un enum o estructura equivalente, reutilizarlo.

No introducir nuevos valores de clasificación sin revisar sus consumidores.

---

## Incertidumbre

La IA puede no disponer de información suficiente.

El sistema debe contemplar:

- Respuesta ambigua.
- Información insuficiente.
- Clasificación desconocida.
- Respuesta incompleta.
- Error del modelo.

No forzar una clasificación arbitraria únicamente para evitar un estado desconocido.

Si existe un estado `UNKNOWN` u otro mecanismo equivalente, utilizar el mecanismo existente.

---

## Timeouts

Las llamadas al proveedor de IA deben tener timeouts adecuados.

Nunca asumir que el proveedor responderá inmediatamente.

Los timeouts deben:

- Evitar bloquear indefinidamente el pipeline.
- Ser compatibles con el scheduler.
- Ser razonables para el modelo utilizado.
- Permitir distinguir fallo temporal de respuesta válida.

No utilizar timeouts infinitos.

---

## Errores del proveedor

Gestionar correctamente errores como:

- Timeout.
- Error de conexión.
- Rate limiting.
- Error de autenticación.
- Error del proveedor.
- Respuesta inválida.
- Servicio no disponible.

No convertir todos los errores en una clasificación válida.

El pipeline debe distinguir entre:

Successful classification
    ↓
Valid result

y:

AI failure
    ↓
Controlled failure / fallback

---

## Fallback

Antes de implementar un fallback:

1. Revisar el comportamiento existente.
2. Determinar qué debe ocurrir si la IA no está disponible.
3. Evitar inventar una clasificación.
4. Evitar enviar alertas incorrectas.
5. Mantener el comportamiento consistente con el pipeline.

La IA es opcional dentro de la arquitectura; un fallo de IA no debería provocar necesariamente un fallo global si el diseño existente permite continuar de forma segura.

---

## Retries

No realizar retries indiscriminados.

Antes de añadir retries:

1. Identificar el tipo de error.
2. Determinar si la request es segura para repetir.
3. Evaluar el coste.
4. Evaluar rate limits.
5. Establecer un máximo de intentos.
6. Utilizar backoff cuando corresponda.

No realizar retries infinitos.

Especial atención a llamadas que puedan generar costes externos.

---

## Rate limiting

El proveedor puede aplicar límites de uso.

Evitar:

- Llamadas innecesarias.
- Clasificar repetidamente el mismo contenido.
- Retries agresivos.
- Paralelismo ilimitado.
- Procesamiento de publicaciones que no necesitan clasificación.

Respetar los límites del proveedor.

---

## Coste

Las llamadas a IA pueden generar costes o consumir cuotas.

Antes de aumentar el número de llamadas:

1. Evaluar si realmente son necesarias.
2. Comprobar si el resultado puede reutilizarse.
3. Revisar caching.
4. Evitar clasificar contenido duplicado.
5. Evaluar el impacto sobre el volumen habitual.

No añadir llamadas de IA únicamente para simplificar una decisión que puede resolverse localmente.

---

## Caching

El proyecto dispone de mecanismos relacionados con caching de resultados de IA.

Antes de implementar un nuevo cache:

1. Revisar el mecanismo existente.
2. Revisar cómo se generan las claves.
3. Revisar cómo se invalida.
4. Revisar `scripts/clear_ai_cache.py`.
5. Reutilizarlo si es adecuado.

El cache debe evitar llamadas repetidas para contenido equivalente cuando sea seguro hacerlo.

---

## Cache keys

Las claves del cache deben ser:

- Deterministas.
- Estables.
- Suficientemente específicas.
- Independientes de datos sensibles innecesarios.

Si el resultado depende del prompt, modelo o configuración, considerar estos factores en la estrategia de cache.

No reutilizar un resultado de IA cuando las condiciones de clasificación hayan cambiado de forma relevante.

---

## Invalidation

Cuando se modifique de forma significativa:

- Prompt.
- Modelo.
- Parámetros relevantes.
- Criterios de clasificación.
- Formato de salida.

evaluar si los resultados cacheados siguen siendo válidos.

No asumir que un resultado antiguo sigue siendo correcto después de cambiar la lógica de clasificación.

---

## Determinismo

Cuando la tarea requiera resultados consistentes:

- Mantener prompts estables.
- Mantener formato de salida estructurado.
- Configurar parámetros del modelo de forma apropiada.
- Evitar depender de texto libre innecesario.

La IA no debe considerarse completamente determinista.

Los tests deben validar comportamiento esperado sin depender excesivamente de una respuesta exacta del modelo real.

---

## Modelos

Si se cambia el modelo utilizado:

1. Evaluar compatibilidad.
2. Evaluar formato de salida.
3. Evaluar calidad de clasificación.
4. Evaluar coste.
5. Evaluar latencia.
6. Revisar prompts.
7. Revisar cache.
8. Actualizar tests.

No cambiar el modelo únicamente porque exista uno más reciente sin evaluar el impacto.

---

## Tests unitarios

Los tests unitarios deben utilizar mocks/fakes.

El proyecto dispone de:

- `tests/mocks/fake_nvidia.py`
- `tests/fixtures/nvidia.py`

Antes de crear infraestructura nueva:

1. Revisar los mocks existentes.
2. Reutilizarlos.
3. Extenderlos si es necesario.
4. Evitar llamadas reales al proveedor.

Los tests unitarios deben ser rápidos y reproducibles.

---

## Tests de clasificación

Comprobar al menos cuando corresponda:

- Clasificación válida.
- Respuesta vacía.
- Respuesta malformada.
- Campo obligatorio ausente.
- Valor desconocido.
- Error de proveedor.
- Timeout.
- Rate limiting.
- Error de parsing.
- Contenido incompleto.
- Contenido malicioso o con prompt injection.
- Cache hit.
- Cache miss.

---

## Tests de integración

Los tests de integración deben comprobar la interacción entre el clasificador y el resto del sistema cuando sea necesario.

El proyecto dispone de:

- `tests/integration/test_ai_classifier_live.py`

Los tests que dependan de un proveedor externo deben estar claramente diferenciados de los tests unitarios.

No hacer que la suite unitaria dependa de la disponibilidad de NVIDIA API.

---

## Tests live

Los tests reales contra el proveedor:

- No deben ejecutarse accidentalmente como tests unitarios normales si requieren credenciales.
- No deben contener credenciales reales.
- Deben manejar correctamente la indisponibilidad del proveedor.
- Deben tener un coste controlado.

No añadir llamadas live simplemente para comprobar lógica que puede cubrirse mediante mocks.

---

## Logging

Registrar suficiente información para diagnosticar problemas de IA sin exponer información sensible.

Puede ser útil registrar:

- Operación.
- Resultado general.
- Modelo utilizado cuando sea seguro.
- Duración.
- Error categorizado.
- Cache hit/miss.
- Número de elementos procesados.

Evitar registrar:

- API keys.
- Tokens.
- Secrets.
- Prompts completos si contienen información sensible.
- Contenido privado completo.
- Respuestas completas del modelo cuando puedan contener datos sensibles.

Utilizar el sistema de logging existente.

---

## Observabilidad

Cuando sea necesario diagnosticar el comportamiento de IA, considerar:

- Número de clasificaciones.
- Éxitos.
- Fallos.
- Timeouts.
- Cache hits.
- Cache misses.
- Latencia.
- Errores del proveedor.

No introducir un sistema de métricas nuevo si el proyecto ya dispone de mecanismos suficientes.

---

## Rendimiento

La IA puede ser una de las operaciones más costosas del pipeline.

Evitar:

- Clasificar duplicados.
- Llamar al modelo antes de comprobar novedad.
- Llamar al modelo cuando la clasificación local sea suficiente.
- Enviar contextos excesivamente grandes.
- Realizar llamadas secuenciales innecesarias.
- Repetir requests por errores mal gestionados.

El pipeline debería comprobar primero si una publicación necesita realmente ser procesada.

---

## Integración con el orquestador

El orquestador es responsable del flujo general.

La IA debe permanecer como una etapa del pipeline:

Novelty detection
    ↓
AI classification
    ↓
Persistence
    ↓
Alert

No trasladar al clasificador responsabilidades del orquestador.

El clasificador no debe decidir:

- Qué fuentes ejecutar.
- Qué usuarios procesar.
- Qué alertas enviar.
- Cuándo ejecutar el scheduler.
- Cómo gestionar Stripe.

---

## Seguridad

Toda modificación relacionada con IA debe considerar:

- Protección de API keys.
- Privacidad.
- Prompt injection.
- Validación de outputs.
- Información enviada a terceros.
- Logging seguro.
- Control de costes.
- Rate limiting.

No utilizar contenido generado por IA como fuente de autoridad para decisiones de seguridad.

La IA puede asistir en clasificación, pero las validaciones críticas deben permanecer deterministas cuando corresponda.

---

## Dependencias

No añadir una nueva librería de IA si la integración existente puede resolver la necesidad.

Antes de introducir una dependencia:

1. Revisar `requirements.txt`.
2. Comprobar el cliente existente.
3. Evaluar si la interfaz compatible con OpenAI ya es suficiente.
4. Evaluar mantenimiento.
5. Evaluar seguridad.
6. Evaluar impacto en deployment.
7. Explicar el beneficio concreto.

No introducir frameworks completos de agentes, chains o pipelines de IA sin una necesidad demostrable.

---

## Cambios en prompts o modelo

Los cambios en prompts o modelos pueden modificar el comportamiento del producto incluso aunque no cambie ninguna API.

Por ello, tratarlos como cambios funcionales.

Antes de finalizar:

1. Ejecutar tests.
2. Revisar el formato de salida.
3. Revisar casos límite.
4. Evaluar cache.
5. Evaluar impacto en clasificación.
6. Documentar cambios relevantes.

Si el cambio altera significativamente el comportamiento esperado, comunicarlo antes de aplicarlo.

---

## Cambios arquitectónicos

Los siguientes cambios requieren especial precaución y normalmente aprobación previa:

- Sustituir completamente el proveedor de IA.
- Introducir un nuevo framework de agentes.
- Introducir un sistema de RAG.
- Introducir vector databases.
- Introducir múltiples modelos especializados.
- Separar la IA en un microservicio.
- Cambiar globalmente el pipeline de clasificación.
- Introducir una cola específica para IA.
- Cambiar el contrato público del clasificador.
- Eliminar el mecanismo de caching existente.
- Introducir una infraestructura de observabilidad independiente.

El objetivo es mejorar la integración existente, no convertir OportunidadBot en una plataforma de IA más compleja sin necesidad.

---

## Checklist antes de finalizar

Antes de considerar terminada una modificación relacionada con IA:

- [ ] Se ha revisado `ai_classifier.py`.
- [ ] Se ha revisado `prompts.py`.
- [ ] Se ha revisado la configuración existente.
- [ ] Se reutiliza el cliente de IA existente.
- [ ] No se han añadido dependencias innecesarias.
- [ ] Las API keys permanecen fuera del código.
- [ ] No se registran secrets.
- [ ] Los datos enviados al modelo son los mínimos necesarios.
- [ ] El contenido externo se trata como no confiable.
- [ ] Se considera prompt injection.
- [ ] La respuesta del modelo se valida.
- [ ] Los valores de clasificación están controlados.
- [ ] Los errores están gestionados.
- [ ] Los timeouts están controlados.
- [ ] Los retries están limitados.
- [ ] Se respetan los rate limits.
- [ ] Se ha considerado el coste.
- [ ] Se reutiliza el caching existente.
- [ ] Se ha evaluado la invalidación del cache.
- [ ] Se han actualizado los tests relevantes.
- [ ] Los tests unitarios no dependen del proveedor real.
- [ ] Los tests live están correctamente aislados.
- [ ] Los logs no contienen información sensible.
- [ ] No se ha introducido complejidad arquitectónica innecesaria.
- [ ] La documentación se ha actualizado si corresponde.
- [ ] El cambio está limitado al alcance de la tarea.

---

## Regla principal

La IA debe actuar como **un componente especializado de clasificación dentro del pipeline**, no como una autoridad sobre el resto de la aplicación.

El sistema debe controlar qué información recibe el modelo, cómo se construye la petición, cómo se valida la respuesta y qué ocurre cuando el proveedor falla.

Priorizar siempre:

**validación > confianza ciega**

**datos mínimos > contexto innecesario**

**resultados estructurados > texto libre**

**reutilización > duplicación**

**cache > llamadas repetidas**

**robustez > dependencia del proveedor**

**simplicidad > complejidad**

**seguridad > comodidad**

**cambios pequeños > refactors masivos**