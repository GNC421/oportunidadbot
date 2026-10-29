# Scraping Sources Skill

## Propósito

Esta skill define cómo trabajar con las fuentes externas de OportunidadBot.

Debe utilizarse cuando una tarea implique crear, modificar, revisar o depurar:

- Fuentes RSS.
- Fuentes Reddit.
- Fuentes Tablón de Anuncios.
- Nuevos adaptadores de fuentes.
- Scraping.
- Parsing de contenido externo.
- Normalización de publicaciones.
- Detección de errores en fuentes.
- Requests HTTP hacia fuentes externas.
- Extracción de datos.
- Deduplicación relacionada con fuentes.
- Tests de fuentes.

La skill debe complementar las reglas generales definidas en:

- `.github/copilot-instructions.md`
- `.github/context/architecture.md`
- `.github/context/backend.md`
- `.github/context/security.md`
- `.github/context/qa.md`
- `.github/context/ai.md`

No duplicar aquí reglas generales que ya estén definidas en esos documentos.

---

## Contexto del proyecto

OportunidadBot obtiene publicaciones desde diferentes fuentes externas.

Actualmente existen fuentes para:

- RSS.
- Reddit.
- Tablón de Anuncios.

Las fuentes se encuentran principalmente en:

- `app/sources/`
- `app/sources/base.py`
- `app/sources/factory.py`
- `app/sources/item.py`
- `app/sources/rss_source.py`
- `app/sources/reddit_source.py`
- `app/sources/tablon_source.py`

El parsing y procesamiento posterior utiliza principalmente:

- `feedparser`
- `BeautifulSoup`
- `lxml`
- `httpx`

La obtención de publicaciones forma parte del pipeline principal:

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
Optional AI classification
    ↓
Persistence
    ↓
Alert

No introducir una arquitectura distribuida o microservicios como consecuencia de una modificación relacionada con fuentes.

---

## Principios generales

Al trabajar con fuentes externas:

1. Reutilizar las abstracciones existentes.
2. Mantener las fuentes independientes entre sí.
3. Separar obtención, parsing y normalización cuando corresponda.
4. Tratar todo contenido externo como no confiable.
5. Gestionar correctamente errores y timeouts.
6. Evitar requests innecesarios.
7. Mantener un comportamiento predecible ante cambios de una fuente.
8. No acoplar el resto del sistema a una fuente concreta.
9. Evitar duplicar lógica común.
10. Mantener los cambios localizados.
11. No realizar refactors no relacionados con la tarea.

---

## Arquitectura de fuentes

Las fuentes deben seguir la abstracción existente en `app/sources/base.py`.

Antes de crear una nueva fuente:

1. Revisar `BaseSource`.
2. Revisar `SourceItem`.
3. Revisar `SourceFactory`.
4. Revisar fuentes existentes.
5. Revisar cómo el orquestador consume las fuentes.
6. Revisar tests existentes.
7. Reutilizar los contratos existentes siempre que sea posible.

Una nueva fuente debería integrarse con el sistema existente sin obligar al resto del pipeline a conocer detalles específicos de la fuente.

Flujo conceptual:

SourceFactory
    ↓
BaseSource
    ↓
Concrete Source
    ↓
SourceItem
    ↓
Orchestrator

---

## Contrato de una fuente

Una fuente concreta debe centrarse en:

- Obtener publicaciones.
- Interpretar el formato específico de la fuente.
- Convertirlas al modelo común.
- Devolver resultados consistentes.

No debe encargarse de:

- Clasificación mediante IA.
- Envío de alertas.
- Gestión de suscripciones.
- Lógica de Stripe.
- Orquestación completa del pipeline.
- Persistencia global de usuarios.
- Decidir qué usuario recibe una alerta.

Estas responsabilidades pertenecen a otras partes del sistema.

---

## SourceItem

`SourceItem` representa la abstracción común de una publicación obtenida de una fuente.

Al trabajar con nuevas fuentes:

- Utilizar `SourceItem`.
- Mantener los campos comunes.
- No introducir estructuras específicas que obliguen al pipeline a conocer la fuente.
- Normalizar los datos antes de devolverlos.

Los datos deben ser suficientemente consistentes para que el procesamiento posterior sea independiente de la fuente.

---

## Normalización

Las fuentes externas pueden utilizar formatos diferentes.

La fuente debe normalizar, cuando corresponda:

- Título.
- URL.
- Descripción/contenido.
- Fecha.
- Identificador externo.
- Autor.
- Metadatos relevantes.

La normalización debe producir una representación común.

Evitar que cada consumidor tenga que conocer:

- HTML específico.
- Campos concretos de Reddit.
- Estructuras concretas de RSS.
- Selectores HTML de Tablón.
- Formatos particulares de una fuente.

---

## Nuevas fuentes

Cuando se solicite añadir una nueva fuente:

1. Inspeccionar las abstracciones existentes.
2. Determinar el mecanismo de acceso.
3. Implementar el adaptador específico.
4. Convertir los resultados al modelo común.
5. Registrar la fuente en el mecanismo de factory existente si corresponde.
6. Añadir tests.
7. Comprobar errores y casos límite.
8. Verificar integración con el orquestador.

No modificar el pipeline completo para introducir una nueva fuente si la abstracción existente permite integrarla.

---

## SourceFactory

Cuando exista una factory para seleccionar fuentes:

- Reutilizar `SourceFactory`.
- Mantener la selección de fuentes centralizada.
- Evitar instanciar fuentes concretas directamente en múltiples partes del sistema.
- Mantener identificadores consistentes.
- Gestionar tipos de fuente desconocidos de forma explícita.

Al añadir una nueva fuente, revisar también:

- Configuración.
- Factory.
- Tests.
- Documentación.
- Cualquier catálogo de fuentes existente.

---

## HTTP requests

Las requests externas deben realizarse de forma segura y controlada.

Siempre que corresponda:

- Utilizar `httpx`.
- Definir timeouts razonables.
- Gestionar errores de conexión.
- Gestionar respuestas HTTP inesperadas.
- Evitar descargar contenido ilimitado.
- Evitar requests innecesarias.
- Reutilizar clientes o mecanismos existentes cuando corresponda.

No utilizar timeouts infinitos.

No realizar requests a URLs arbitrarias sin validar su procedencia cuando exista entrada controlada por usuarios.

---

## Timeouts

Toda integración externa debe considerar timeouts.

Los timeouts deben evitar que una fuente bloqueada detenga indefinidamente el procesamiento.

Al establecer o modificar timeouts:

1. Revisar los valores existentes.
2. Mantener consistencia entre fuentes.
3. Considerar el comportamiento del scheduler.
4. Considerar el número de fuentes procesadas.
5. Evitar valores excesivamente agresivos que provoquen falsos fallos.

---

## Errores de red

Las fuentes externas pueden fallar por:

- Timeout.
- DNS.
- Conexión rechazada.
- Error HTTP.
- Rate limiting.
- Cambios en el formato.
- Servicio temporalmente no disponible.

Una fuente con problemas no debería provocar automáticamente el fallo de todo el pipeline si el diseño existente permite continuar con las demás.

Gestionar el error en el nivel adecuado.

Registrar información suficiente para diagnóstico sin exponer información sensible.

---

## HTTP status codes

Tratar correctamente respuestas como:

- `2xx`: respuesta válida.
- `3xx`: evaluar redirecciones.
- `4xx`: problema de petición, acceso o rate limiting.
- `5xx`: error del servidor remoto.

No asumir que cualquier respuesta HTTP contiene el formato esperado.

Validar el contenido antes de procesarlo.

---

## Rate limiting

Las fuentes externas pueden aplicar límites de requests.

Evitar:

- Polling excesivamente frecuente.
- Requests duplicadas.
- Retries agresivos.
- Paralelismo innecesario.

Cuando exista información suficiente para detectar rate limiting:

1. Respetar las señales proporcionadas por la fuente.
2. Utilizar backoff cuando corresponda.
3. Evitar repetir inmediatamente una operación fallida.
4. Mantener el scheduler bajo control.

No intentar eludir deliberadamente mecanismos de rate limiting.

---

## Retries

No añadir retries indiscriminadamente.

Antes de implementar retries:

1. Determinar el tipo de error.
2. Determinar si la operación es segura para repetir.
3. Evaluar el impacto sobre la fuente.
4. Evaluar la posibilidad de duplicados.
5. Establecer un número máximo de intentos.
6. Utilizar backoff cuando corresponda.

No utilizar retries infinitos.

---

## Scraping HTML

Cuando una fuente requiera scraping HTML:

- Utilizar el parser existente cuando sea adecuado.
- Mantener los selectores lo más claros posible.
- Aislar la lógica específica de la estructura HTML.
- Gestionar HTML incompleto o inesperado.
- No asumir que todos los elementos existen.
- Evitar selectores excesivamente frágiles cuando exista una alternativa estable.

Los selectores específicos de una web deben permanecer dentro del adaptador correspondiente.

No distribuir selectores HTML por servicios generales.

---

## Cambios en páginas externas

Las páginas externas pueden cambiar sin previo aviso.

Cuando el scraping deje de funcionar:

1. Identificar exactamente qué estructura cambió.
2. Revisar el HTML real.
3. Modificar únicamente el parser afectado.
4. Añadir o actualizar tests de regresión.
5. Comprobar que el formato normalizado continúa siendo correcto.

Evitar reescribir completamente la fuente si un cambio localizado es suficiente.

---

## RSS

Para fuentes RSS:

- Utilizar `feedparser` cuando corresponda.
- Gestionar feeds malformados.
- Validar entradas.
- Normalizar URLs.
- Gestionar entradas sin fecha.
- Gestionar entradas sin descripción.
- Gestionar identificadores ausentes.
- Evitar asumir que todos los campos RSS están presentes.

Reutilizar el comportamiento existente de `rss_source.py` y `feed_parser.py`.

No duplicar parsing RSS en otros servicios.

---

## Reddit

Para Reddit:

- Mantener la lógica específica dentro de `reddit_source.py`.
- Tratar el contenido recibido como externo/no confiable.
- Validar los campos esperados.
- Gestionar publicaciones eliminadas o incompletas.
- Gestionar cambios en la respuesta externa.
- Evitar asumir que todos los posts contienen los mismos campos.

Si se modifica la integración, actualizar los tests específicos de Reddit.

---

## Tablón de Anuncios

Para Tablón de Anuncios:

- Mantener el scraping específico dentro de `tablon_source.py`.
- Aislar los selectores HTML.
- Gestionar cambios de estructura.
- Validar los campos extraídos.
- Normalizar los resultados mediante `SourceItem`.
- Evitar propagar detalles HTML al resto del sistema.

Cualquier cambio en selectores debe incluir tests de regresión cuando sea posible.

---

## URLs

Las URLs procedentes de fuentes o usuarios deben tratarse cuidadosamente.

Comprobar cuando corresponda:

- Esquema.
- Host.
- Redirecciones.
- URL válida.
- URL absoluta frente a relativa.
- Posibles URLs malformadas.

Si una URL procede directamente de un usuario y posteriormente se utiliza para realizar requests, aplicar las reglas de seguridad relacionadas con SSRF definidas en `security.md`.

No confiar en que una URL externa es segura simplemente porque tenga formato válido.

---

## SSRF

Si el sistema permite que un usuario configure una URL que posteriormente será consultada por el backend:

- Tratar la URL como input no confiable.
- Restringir esquemas permitidos.
- Evaluar hosts privados.
- Evaluar localhost.
- Evaluar rangos internos.
- Evaluar redirecciones.
- Evitar acceso a servicios internos.
- Evitar acceso a metadata services.
- Aplicar timeouts.

No deshabilitar las protecciones SSRF para facilitar una integración.

---

## Contenido no confiable

Todo contenido obtenido de una fuente externa debe considerarse no confiable.

Esto incluye:

- Títulos.
- Descripciones.
- Autores.
- URLs.
- HTML.
- Texto de Reddit.
- Texto de anuncios.
- Contenido que posteriormente se envía a IA.
- Contenido que posteriormente se envía a Telegram.

No ejecutar ni interpretar contenido externo como código.

No insertar HTML externo directamente en interfaces sin sanitización apropiada.

No asumir que el contenido externo es benigno.

---

## Parsing

El parsing debe ser tolerante ante datos incompletos.

Cuando falte un campo:

- Utilizar un fallback razonable si existe.
- Omitir el elemento si no puede procesarse correctamente.
- No provocar un crash global innecesario.

Evitar excepciones genéricas que oculten el motivo real del fallo.

Cuando un elemento concreto sea inválido, evaluar si puede omitirse sin descartar el resto de la fuente.

---

## Deduplicación

La detección de novedades debe utilizar los mecanismos existentes del proyecto.

No implementar una segunda estrategia de deduplicación dentro de cada fuente salvo que sea necesario.

Cuando exista:

- Identificador externo.
- GUID.
- URL canónica.
- Hash.
- Identificador de publicación.

utilizar el mecanismo común existente siempre que sea posible.

La fuente debe proporcionar información suficiente para que el pipeline pueda determinar si una publicación es nueva.

---

## Fechas

Las fechas procedentes de fuentes externas pueden:

- Faltar.
- Tener formatos diferentes.
- Contener zonas horarias.
- Ser inválidas.
- Tener formatos locales.

Normalizar las fechas al formato utilizado por el proyecto.

No asumir que una fecha externa está en la zona horaria local.

Si no puede determinarse una fecha correctamente, utilizar el comportamiento existente del parser.

---

## Contenido HTML

Cuando una fuente proporciona HTML:

- Extraer el texto necesario.
- Evitar conservar HTML innecesario.
- Limpiar contenido cuando corresponda.
- Evitar enviar HTML arbitrario a consumidores que no lo esperan.
- Mantener una representación normalizada.

No realizar sanitización duplicada en múltiples capas sin necesidad.

---

## Rendimiento

Las fuentes externas pueden ser numerosas.

Evitar:

- Requests duplicadas.
- Parsing repetido.
- Descargas innecesarias.
- Procesamiento secuencial cuando el diseño existente permita una mejora segura.
- Cargar contenido que no sea necesario.

Sin embargo, no introducir concurrencia compleja únicamente por una optimización hipotética.

Antes de optimizar:

1. Identificar el cuello de botella.
2. Medir o analizar el comportamiento.
3. Evaluar impacto sobre fuentes externas.
4. Mantener control sobre rate limiting.
5. Mantener la simplicidad del código.

---

## Concurrencia

Si varias fuentes se procesan de forma concurrente:

- Asegurar que las operaciones compartidas sean seguras.
- Evitar condiciones de carrera.
- Evitar duplicar requests.
- Respetar límites de las fuentes.
- Mantener errores aislados cuando sea posible.

No introducir paralelismo ilimitado.

El número de requests simultáneas debe ser razonable para las fuentes externas y para el sistema.

---

## Logging

Los logs deben permitir diagnosticar problemas de fuentes.

Puede ser útil registrar:

- Nombre de la fuente.
- Tipo de fuente.
- Resultado.
- Número de elementos obtenidos.
- Número de elementos válidos.
- Duración.
- Tipo de error.
- Código HTTP cuando corresponda.

Evitar registrar:

- Tokens.
- API keys.
- Cookies sensibles.
- Credenciales.
- Payloads completos innecesarios.
- Información privada del usuario.

Utilizar el sistema de logging existente.

---

## Observabilidad

Cuando una fuente falle repetidamente, el sistema debería permitir identificar:

- Qué fuente falla.
- Cuándo falla.
- Tipo de fallo.
- Frecuencia.
- Duración.
- Si el fallo afecta a todo el pipeline o únicamente a esa fuente.

No introducir un sistema de observabilidad nuevo si el proyecto ya proporciona mecanismos suficientes.

---

## Testing

Toda modificación de una fuente debe incluir o actualizar tests.

Utilizar la infraestructura existente:

- `pytest`
- `pytest-asyncio`
- `pytest-mock`
- Fixtures.
- Mocks/fakes.

Tests relevantes existentes incluyen:

- `tests/unit/test_base_source.py`
- `tests/unit/test_source_factory.py`
- `tests/unit/test_reddit_source.py`
- `tests/unit/test_tablon_source.py`
- Tests relacionados con parsing y feeds.

Antes de crear nuevos fixtures:

1. Revisar los existentes.
2. Reutilizarlos cuando sea posible.
3. Extenderlos cuando sea necesario.
4. Evitar duplicación.

---

## Tests de nuevas fuentes

Una nueva fuente debería tener tests para:

- Creación correcta.
- Configuración válida.
- Configuración inválida.
- Obtención correcta.
- Respuesta vacía.
- Respuesta incompleta.
- Error HTTP.
- Timeout.
- Error de parsing.
- Datos malformados.
- Normalización.
- Identificador externo.
- URL.
- Fecha.
- Duplicados cuando corresponda.

Las llamadas reales a servicios externos no deben utilizarse en tests unitarios.

---

## Tests de regresión

Cuando una fuente deja de funcionar debido a un cambio externo:

1. Reproducir el caso con un fixture controlado.
2. Añadir un test que represente el problema.
3. Corregir el parser.
4. Verificar el caso original.
5. Ejecutar la suite relacionada.

No eliminar un test que falla simplemente porque el comportamiento externo ha cambiado.

Actualizar el test únicamente si el nuevo comportamiento es realmente el esperado.

---

## Dependencias

No añadir una dependencia nueva para una fuente si la funcionalidad puede implementarse con las librerías ya utilizadas.

Antes de añadir una dependencia:

1. Revisar `requirements.txt`.
2. Comprobar si ya existe una librería equivalente.
3. Evaluar si Python estándar puede resolver el problema.
4. Evaluar mantenimiento.
5. Evaluar seguridad.
6. Evaluar impacto en Docker/deployment.
7. Explicar la razón de la dependencia.

No añadir una librería de scraping pesada cuando un parser existente sea suficiente.

---

## Cambios en contratos

No modificar silenciosamente:

- `BaseSource`.
- `SourceItem`.
- `SourceFactory`.
- Interfaces utilizadas por el orquestador.

Un cambio en estos contratos puede afectar a múltiples fuentes.

Antes de modificar una abstracción compartida:

1. Buscar todos sus consumidores.
2. Evaluar impacto.
3. Actualizar tests.
4. Determinar si existe una alternativa localizada.
5. Solicitar aprobación si el cambio es arquitectónicamente relevante.

---

## Documentación

Actualizar documentación cuando una modificación añada o cambie:

- Una fuente.
- Configuración de una fuente.
- Requisitos externos.
- Formato de datos.
- Comportamiento del parser.
- Limitaciones conocidas.
- Identificadores de configuración.

Cuando corresponda, mantener actualizado:

- `app/sources/README.md`

No documentar detalles internos triviales que puedan quedar claros en el código.

---

## Cambios arquitectónicos

Los siguientes cambios requieren especial precaución y normalmente aprobación previa:

- Sustituir la abstracción `BaseSource`.
- Cambiar completamente `SourceFactory`.
- Crear una nueva arquitectura de scraping.
- Introducir microservicios.
- Introducir una cola externa únicamente para fuentes.
- Sustituir las librerías principales de HTTP/parsing.
- Cambiar globalmente el pipeline de procesamiento.
- Introducir un sistema de crawling distribuido.
- Modificar la estrategia global de deduplicación.

El objetivo es integrar y mejorar las fuentes existentes manteniendo el modular monolith.

---

## Checklist antes de finalizar

Antes de considerar terminada una modificación relacionada con fuentes:

- [ ] Se ha revisado la abstracción existente.
- [ ] Se reutiliza `BaseSource` cuando corresponde.
- [ ] Se utiliza `SourceItem` para normalizar resultados.
- [ ] La fuente concreta contiene únicamente lógica específica de esa fuente.
- [ ] No se ha introducido lógica de negocio en el scraper.
- [ ] Los datos externos se tratan como no confiables.
- [ ] Las requests tienen timeouts adecuados.
- [ ] Los errores de red están gestionados.
- [ ] Los retries están limitados.
- [ ] Se respetan los límites de las fuentes externas.
- [ ] Las URLs se validan cuando corresponde.
- [ ] Se consideran riesgos SSRF cuando existe input controlado por usuarios.
- [ ] El parsing tolera datos incompletos.
- [ ] Los resultados están correctamente normalizados.
- [ ] La deduplicación utiliza los mecanismos existentes.
- [ ] Las fechas se gestionan correctamente.
- [ ] Los logs no contienen información sensible.
- [ ] Se han actualizado los tests relevantes.
- [ ] Se han añadido tests de regresión cuando corresponde.
- [ ] No se han añadido dependencias innecesarias.
- [ ] No se han realizado cambios arquitectónicos innecesarios.
- [ ] La documentación se ha actualizado si corresponde.
- [ ] El cambio está limitado al alcance de la tarea.

---

## Regla principal

Las fuentes deben actuar como **adaptadores aislados entre sistemas externos y el modelo interno de OportunidadBot**.

Cada fuente debe encargarse de conocer las particularidades del sistema externo y convertir sus datos a una representación común.

El resto del sistema no debería necesitar conocer cómo funciona internamente RSS, Reddit, Tablón de Anuncios u otra fuente.

Priorizar siempre:

**aislamiento > acoplamiento**

**normalización > formatos específicos**

**robustez > suposiciones**

**reutilización > duplicación**

**simplicidad > complejidad**

**seguridad > comodidad**

**cambios pequeños > refactors masivos**