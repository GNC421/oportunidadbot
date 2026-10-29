# AI Context

## Propósito

Este documento define el contexto técnico actual relacionado con Inteligencia Artificial en OportunidadBot.

Su objetivo es proporcionar a los agentes de GitHub Copilot una referencia común sobre:

- Arquitectura de la integración con IA.
- Responsabilidades del clasificador.
- Uso de NVIDIA API.
- Prompts.
- Procesamiento de respuestas.
- Uso de IA dentro del pipeline.
- Manejo de errores.
- Testing.
- Seguridad.
- Cache.
- Cambios de comportamiento.
- Criterios para modificar componentes relacionados con IA.

Este documento describe la implementación y criterios actuales. No debe interpretarse como una propuesta para rediseñar el sistema de IA.

---

## 1. Papel de la IA en el sistema

La Inteligencia Artificial es una capacidad del backend utilizada para analizar y clasificar elementos obtenidos desde fuentes externas.

La IA forma parte del pipeline principal, pero es una capacidad **opcional**.

El sistema no debe asumir que el proveedor de IA estará siempre disponible.

La ausencia, fallo o indisponibilidad temporal del proveedor debe gestionarse de forma controlada según el comportamiento definido por el servicio.

---

## 2. Ubicación

La integración principal con IA se encuentra en:

`app/services/ai_classifier.py`

Los prompts se encuentran en:

`app/services/prompts.py`

Existe además infraestructura de testing relacionada con IA en:

`tests/fixtures/nvidia.py`

y:

`tests/mocks/fake_nvidia.py`

Existe también una prueba de integración que utiliza el proveedor real:

`tests/integration/test_ai_classifier_live.py`

---

## 3. Proveedor actual

La integración actual utiliza la API de NVIDIA.

El acceso se realiza mediante una interfaz compatible con OpenAI.

El código de aplicación debe abstraerse de los detalles específicos del proveedor siempre que sea razonablemente posible.

La lógica de negocio no debería depender directamente de detalles específicos del SDK o cliente utilizado para comunicarse con NVIDIA.

---

## 4. Responsabilidad de `ai_classifier.py`

`app/services/ai_classifier.py` es responsable de la lógica relacionada con la clasificación mediante IA.

Entre sus responsabilidades conceptuales pueden encontrarse:

- Preparar la información necesaria para la clasificación.
- Construir o utilizar los prompts correspondientes.
- Invocar el proveedor de IA.
- Procesar la respuesta.
- Validar el resultado.
- Gestionar errores de la integración.
- Devolver al resto de la aplicación un resultado utilizable.

El clasificador no debe asumir responsabilidades pertenecientes a:

- Persistencia.
- Telegram.
- Stripe.
- Scheduler.
- Scraping específico de una fuente.

---

## 5. Separación entre IA y pipeline

El pipeline principal debe tratar al clasificador como un componente especializado.

Conceptualmente:

`orchestrator -> ai_classifier -> proveedor de IA`

El orquestador coordina cuándo debe utilizarse IA.

El clasificador se ocupa de cómo se realiza la clasificación.

El proveedor externo se ocupa de ejecutar el modelo.

Esta separación debe mantenerse siempre que sea razonablemente posible.

---

## 6. IA como componente opcional

La IA no debe convertirse accidentalmente en una dependencia obligatoria para funcionalidades que puedan funcionar sin ella.

El código debe contemplar escenarios como:

- Proveedor no configurado.
- API key ausente.
- Servicio temporalmente no disponible.
- Timeout.
- Error de autenticación.
- Respuesta inválida.
- Respuesta incompleta.
- Error inesperado del proveedor.

La aplicación debe manejar estos escenarios de forma controlada.

---

## 7. Configuración de IA

Las credenciales y configuración del proveedor deben proceder de variables de entorno mediante la configuración centralizada de la aplicación.

No deben incluirse en:

- Código fuente.
- Prompts.
- Tests.
- Fixtures.
- Logs.
- Documentación versionada.

Los cambios en la configuración del proveedor deben evaluarse teniendo en cuenta desarrollo local y producción.

---

## 8. Prompts

Los prompts relacionados con IA se centralizan en:

`app/services/prompts.py`

Los prompts deben mantenerse separados de la lógica de integración con el proveedor cuando sea posible.

Esto facilita:

- Mantenimiento.
- Testing.
- Revisión.
- Evolución del comportamiento.
- Identificación de cambios en clasificación.

No duplicar prompts en diferentes servicios si representan la misma operación.

---

## 9. Cambios en prompts

Un cambio aparentemente pequeño en un prompt puede modificar significativamente el comportamiento del sistema.

Por ello, antes de modificar un prompt importante:

1. Identificar quién lo utiliza.
2. Determinar qué comportamiento pretende conseguir.
3. Revisar los tests relacionados.
4. Identificar posibles efectos secundarios.
5. Comprobar el formato esperado de salida.
6. Validar ejemplos representativos.

Los cambios relevantes deben seguir el workflow de cambios de IA.

---

## 10. Datos enviados al modelo

Los datos procedentes de fuentes externas deben considerarse no confiables.

Esto incluye:

- RSS.
- Reddit.
- Tablón de Anuncios.
- HTML.
- Títulos.
- Descripciones.
- Texto de publicaciones.

El modelo debe recibir estos contenidos como **datos para analizar**, no como instrucciones confiables.

Los prompts deben separar claramente:

- Instrucciones de la aplicación.
- Datos proporcionados para análisis.
- Formato de salida esperado.

---

## 11. Prompt injection

El contenido externo puede intentar manipular el comportamiento del modelo.

Ejemplos conceptuales:

- Intentar cambiar las instrucciones.
- Solicitar información privada.
- Intentar modificar el criterio de clasificación.
- Introducir instrucciones dentro de una publicación.
- Intentar provocar acciones no relacionadas con el análisis.

Los agentes deben considerar siempre esta posibilidad cuando modifiquen prompts o el flujo de IA.

La información procedente de una fuente externa nunca debe considerarse una instrucción de confianza.

---

## 12. Principio de mínimo contexto

El modelo debe recibir únicamente la información necesaria para realizar la tarea.

Evitar enviar:

- Secretos.
- Tokens.
- Credenciales.
- Información interna innecesaria.
- Datos personales que no sean necesarios.
- Información de otros usuarios.
- Información de infraestructura.

Reducir el contexto innecesario también ayuda a:

- Reducir costes.
- Reducir latencia.
- Mejorar precisión.
- Reducir superficie de exposición.

---

## 13. Salida del modelo

Nunca asumir que el modelo devolverá exactamente el formato solicitado.

La respuesta puede:

- Tener texto adicional.
- Tener campos ausentes.
- Contener valores inesperados.
- Tener JSON inválido.
- Estar vacía.
- Contener errores semánticos.

El clasificador debe validar la respuesta antes de utilizarla en lógica posterior.

---

## 14. Validación de resultados

La validación debe comprobar como mínimo los aspectos necesarios para que el resultado pueda ser utilizado de forma segura por el resto del pipeline.

Cuando se espere una estructura concreta, comprobar:

- Existencia de campos obligatorios.
- Tipos.
- Valores permitidos.
- Estructura.
- Consistencia mínima.

No confiar en que el modelo cumple el contrato únicamente porque el prompt lo solicite.

---

## 15. Clasificación

La clasificación generada por IA debe considerarse una entrada para la lógica de aplicación, no una autoridad absoluta.

El sistema debe poder manejar resultados:

- Válidos.
- Ambiguos.
- Incompletos.
- Inválidos.
- No disponibles.

Cuando un resultado no pueda validarse correctamente, debe aplicarse el comportamiento de fallback definido por la aplicación.

No inventar silenciosamente valores cuando hacerlo pueda afectar al comportamiento de negocio.

---

## 16. Errores del proveedor

Los errores de NVIDIA deben tratarse de forma controlada.

Entre los escenarios posibles:

- Timeout.
- Error HTTP.
- Error de autenticación.
- Rate limit.
- Servicio no disponible.
- Respuesta inesperada.
- Error de parsing.
- Error interno del cliente.

El sistema debe evitar que un error externo provoque un fallo innecesario de todo el pipeline cuando exista una estrategia de recuperación razonable.

---

## 17. Timeouts y disponibilidad

Las llamadas a servicios de IA son llamadas externas y deben considerarse potencialmente lentas o fallidas.

Deben existir límites razonables de tiempo.

No permitir que una llamada al proveedor bloquee indefinidamente el procesamiento.

Los cambios relacionados con timeouts o reintentos deben evaluar:

- Latencia.
- Coste.
- Duplicación de operaciones.
- Efectos sobre el scheduler.
- Efectos sobre el pipeline.

---

## 18. Reintentos

Los reintentos deben utilizarse únicamente cuando tengan sentido.

No repetir automáticamente una operación ante cualquier excepción.

Antes de introducir reintentos considerar:

- Si el error es transitorio.
- Si el proveedor puede haber procesado ya la petición.
- Si la operación es idempotente.
- Cuántos reintentos son razonables.
- El impacto en costes.
- El impacto en rate limits.
- El impacto en tiempo de procesamiento.

No implementar reintentos infinitos.

---

## 19. Rate limits

Los proveedores de IA pueden imponer límites de uso.

El código debe estar preparado para recibir errores de rate limiting.

No realizar llamadas adicionales innecesarias.

Antes de aumentar frecuencia, concurrencia o reintentos, evaluar el impacto sobre:

- Límites del proveedor.
- Costes.
- Scheduler.
- Tiempo de procesamiento.
- Experiencia del usuario.

---

## 20. Cache

El proyecto dispone de mecanismos relacionados con cache de IA y existe el script:

`scripts/clear_ai_cache.py`

La cache debe considerarse parte del comportamiento técnico de la integración.

Antes de modificarla, comprobar:

- Qué resultados almacena.
- Cuándo se reutilizan.
- Qué identifica una entrada.
- Qué ocurre cuando cambia el prompt.
- Qué ocurre cuando cambia el modelo.
- Cómo se invalida.
- Qué impacto tiene sobre tests.

No asumir que eliminar la cache es equivalente a desactivar IA.

---

## 21. Cambios de modelo

Cambiar el modelo utilizado por la IA puede alterar:

- Resultados.
- Costes.
- Latencia.
- Formato de respuestas.
- Calidad de clasificación.
- Consumo de tokens.
- Comportamiento de edge cases.

Por tanto, un cambio de modelo debe considerarse un cambio relevante de comportamiento.

Debe validarse antes de darse por terminado.

---

## 22. Cambios de proveedor

Sustituir NVIDIA por otro proveedor debe tratarse como un cambio arquitectónico relevante.

No debe introducirse directamente durante una modificación funcional pequeña.

Debe evaluarse:

- Compatibilidad de API.
- Coste.
- Latencia.
- Calidad.
- Formato de respuestas.
- Límites.
- Seguridad.
- Gestión de credenciales.
- Impacto en tests.
- Impacto en cache.

La lógica de negocio debería permanecer lo suficientemente desacoplada para facilitar esta posibilidad sin introducir una abstracción innecesaria prematuramente.

---

## 23. Testing de IA

Los tests de IA deben dividirse conceptualmente en:

- Tests unitarios.
- Tests de integración.
- Tests live.

La mayoría de escenarios deberían poder probarse sin realizar llamadas reales al proveedor.

---

## 24. Tests unitarios de IA

Los tests unitarios deben validar aspectos como:

- Construcción de entradas.
- Procesamiento de respuestas.
- Validación.
- Manejo de errores.
- Comportamiento ante respuestas inválidas.
- Casos límite.

Utilizar mocks o fakes cuando sea posible.

---

## 25. Fake NVIDIA

Existe un fake específico en:

`tests/mocks/fake_nvidia.py`

Antes de crear otro mock para NVIDIA:

1. Revisar el fake existente.
2. Reutilizarlo si cubre el escenario.
3. Extenderlo si resulta apropiado.
4. Crear uno nuevo únicamente si representa un comportamiento realmente diferente.

El fake no debe depender de la API real.

---

## 26. Fixture NVIDIA

Existe una fixture relacionada con NVIDIA en:

`tests/fixtures/nvidia.py`

Debe utilizarse para construir escenarios de testing reproducibles cuando sea apropiado.

No introducir credenciales reales en fixtures.

---

## 27. Tests live

Existe:

`tests/integration/test_ai_classifier_live.py`

Este tipo de test puede depender de:

- Credenciales.
- Disponibilidad del proveedor.
- Red.
- Rate limits.
- Coste.
- Modelo configurado.

No debe utilizarse como sustituto de los tests deterministas.

Los cambios importantes deberían mantener una cobertura suficiente sin depender exclusivamente de este test.

---

## 28. Testing de prompts

Los prompts deben probarse indirectamente cuando el comportamiento esperado pueda determinarse de forma estable.

Cuando sea necesario validar cambios de prompt, utilizar casos representativos.

No hacer tests excesivamente frágiles que dependan de una respuesta textual exacta del modelo si el contrato no exige dicha respuesta exacta.

Preferir validar:

- Estructura.
- Campos.
- Clasificación.
- Reglas importantes.
- Comportamiento esperado.

---

## 29. Variabilidad del modelo

Las respuestas de un modelo pueden variar.

Por ello, evitar tests excesivamente acoplados a:

- Redacción exacta.
- Orden irrelevante de información.
- Explicaciones textuales.
- Tokens concretos.
- Formulaciones que no formen parte del contrato.

Los tests deben validar el comportamiento relevante para la aplicación.

---

## 30. IA dentro del pipeline

La integración con IA debe permanecer compatible con el pipeline principal:

`fuentes -> parsing/normalización -> detección de novedad -> IA opcional -> persistencia -> alerta`

La IA no debe modificar silenciosamente las etapas anteriores o posteriores.

Si una modificación de IA requiere cambiar:

- Persistencia.
- Reglas de alertas.
- Contratos de fuentes.
- Orquestación.
- API.

debe considerarse el impacto más allá de `ai_classifier.py`.

---

## 31. Fallos de IA y continuidad

Un fallo del proveedor no debería provocar automáticamente la pérdida de información si el sistema puede continuar de forma segura.

Cuando sea compatible con las reglas actuales, deben considerarse estrategias como:

- Registrar el error.
- Marcar el elemento para tratamiento posterior.
- Continuar con otros elementos.
- Utilizar un resultado de fallback definido.
- Evitar enviar una clasificación inválida.

No inventar una estrategia de fallback que cambie las reglas de negocio sin aprobación.

---

## 32. Rendimiento

Las llamadas a IA pueden ser una de las partes más costosas y lentas del pipeline.

Antes de optimizar, identificar el problema real.

Las posibles áreas de optimización incluyen:

- Evitar llamadas duplicadas.
- Cachear resultados cuando sea correcto.
- Reducir contexto innecesario.
- Reducir tamaño de prompts.
- Evitar clasificar elementos que no lo necesitan.
- Controlar concurrencia.

No sacrificar corrección por reducir unas pocas llamadas.

---

## 33. Costes

Las llamadas a proveedores de IA pueden tener coste asociado.

Antes de incrementar:

- Número de llamadas.
- Tamaño de prompts.
- Número de reintentos.
- Concurrencia.
- Frecuencia del scheduler.

debe evaluarse el impacto económico.

Los cambios que puedan multiplicar significativamente el consumo requieren revisión.

---

## 34. Observabilidad de IA

Los errores y métricas relacionadas con IA deben poder diagnosticarse.

Cuando sea útil, registrar información técnica como:

- Estado de la llamada.
- Duración.
- Modelo utilizado.
- Resultado general.
- Tipo de error.

No registrar:

- API keys.
- Tokens.
- Credenciales.
- Payloads sensibles innecesarios.
- Información privada no necesaria.

El logging debe proporcionar información suficiente para diagnosticar problemas sin exponer datos sensibles.

---

## 35. Privacidad

Los datos enviados a proveedores externos deben limitarse a lo estrictamente necesario.

Antes de enviar información a IA comprobar:

- Qué datos contiene.
- Si contienen información personal.
- Si existe una necesidad real de enviarlos.
- Si pueden minimizarse.
- Si contienen información de otros usuarios.

No utilizar datos de usuarios como contexto de otro usuario salvo que exista una justificación explícita y segura.

---

## 36. Seguridad

Los agentes deben considerar especialmente:

- Prompt injection.
- Exfiltración de información.
- Secretos en prompts.
- Datos externos no confiables.
- Respuestas manipuladas.
- Respuestas inválidas.
- Logs sensibles.
- Dependencias del proveedor.

La IA nunca debe recibir autoridad implícita para ejecutar acciones del sistema simplemente porque genere una respuesta.

---

## 37. La IA no ejecuta acciones directamente

El resultado de la IA debe pasar por la lógica de aplicación correspondiente.

El modelo no debe tener autoridad directa para:

- Ejecutar comandos.
- Modificar la base de datos arbitrariamente.
- Enviar mensajes arbitrarios.
- Modificar configuración.
- Acceder a secretos.
- Ejecutar código.

La IA debe actuar como componente de análisis/clasificación, salvo que exista explícitamente una arquitectura aprobada que otorgue capacidades adicionales.

---

## 38. Cambios de comportamiento

Cualquier modificación que pueda cambiar la clasificación de oportunidades debe considerarse un cambio funcional.

Ejemplos:

- Cambio de prompt.
- Cambio de modelo.
- Cambio de criterios.
- Cambio de campos enviados.
- Cambio de parsing previo.
- Cambio de validación de respuesta.
- Cambio de fallback.
- Cambio de cache.

Estos cambios deben acompañarse de validación y tests adecuados.

---

## 39. Workflow para cambios de IA

Los cambios relevantes de IA deben seguir:

`.github/workflows/ai-change.md`

El objetivo es garantizar que los cambios se realizan de forma controlada y que no se modifica el comportamiento del clasificador accidentalmente.

Cuando un cambio sea pequeño y no modifique comportamiento, puede aplicarse el flujo normal correspondiente.

---

## 40. Cuándo solicitar aprobación

Los agentes deben solicitar aprobación antes de:

- Cambiar de proveedor.
- Cambiar significativamente de modelo.
- Introducir una dependencia relevante.
- Cambiar contratos de entrada/salida.
- Modificar persistencia relacionada con resultados de IA.
- Cambiar significativamente la arquitectura.
- Incrementar sustancialmente el consumo.
- Introducir nuevas capacidades de ejecución.
- Modificar aspectos relevantes de seguridad.
- Cambiar comportamiento funcional de forma significativa.

---

## 41. Reutilización

Antes de crear:

- Un nuevo cliente.
- Un nuevo clasificador.
- Un nuevo parser de respuesta.
- Un nuevo sistema de cache.
- Un nuevo mock.
- Un nuevo conjunto de prompts.

buscar primero si ya existe una implementación reutilizable.

La duplicación de integraciones de IA debe evitarse.

---

## 42. Documentación

Cuando cambie de forma relevante:

- El proveedor.
- El modelo.
- El formato de respuesta.
- Los prompts.
- El flujo de clasificación.
- El sistema de cache.
- Los requisitos de configuración.

debe actualizarse la documentación correspondiente.

Los cambios arquitectónicos duraderos deben documentarse según las reglas generales del proyecto.

---

## 43. Checklist para cambios de IA

Antes de finalizar un cambio relacionado con IA, comprobar:

- ¿Qué comportamiento modifica?
- ¿Qué componente es responsable?
- ¿Existe código reutilizable?
- ¿Se ha modificado un prompt?
- ¿Se ha modificado el modelo?
- ¿Se ha modificado el proveedor?
- ¿Se valida la respuesta?
- ¿Se gestionan errores?
- ¿Se mantiene el fallback existente?
- ¿Se han actualizado los tests?
- ¿Se necesitan tests de integración?
- ¿Se necesitan tests live?
- ¿Se ha revisado la cache?
- ¿Se ha revisado el coste?
- ¿Se ha revisado la latencia?
- ¿Se han revisado posibles prompt injections?
- ¿Se han evitado secretos en prompts y logs?
- ¿Se ha evaluado el impacto sobre el pipeline?

---

## 44. Relación con otros contextos

Este documento debe utilizarse junto con:

- `.github/copilot-instructions.md`
- `.github/context/architecture.md`
- `.github/context/backend.md`
- `.github/context/qa.md`
- `.github/context/security.md`

Y con los agentes especializados de:

`.github/agents/`

Los workflows definen el proceso operativo para implementar cambios.

---

## 45. Regla principal

La IA debe tratarse como un componente externo, no determinista y potencialmente costoso.

Por tanto:

**datos externos → contexto controlado → modelo → respuesta validada → lógica de aplicación**

Nunca:

**datos externos → modelo → acción directa**

La prioridad es mantener una integración de IA:

**controlada → validada → observable → segura → mantenible → eficiente**