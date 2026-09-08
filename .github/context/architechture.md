# Architecture Context

## Propósito

Este documento describe la arquitectura técnica actual de OportunidadBot y sirve como contexto compartido para los agentes de GitHub Copilot.

Debe utilizarse como referencia antes de realizar cambios que afecten a la estructura del sistema, responsabilidades entre módulos, integraciones externas o flujo principal de procesamiento.

Este documento describe **cómo está construido actualmente el sistema**. No debe interpretarse como una propuesta para migrarlo a otra arquitectura.

---

## 1. Arquitectura actual

OportunidadBot está construido actualmente como un **monolito modular**.

La aplicación concentra en un mismo despliegue:

- API HTTP basada en FastAPI.
- Bot de Telegram.
- Procesamiento de fuentes externas.
- Lógica de negocio.
- Persistencia.
- Tareas programadas.
- Integración con servicios de IA.
- Integración con Stripe.
- Sistema de debugging y trazabilidad.

Actualmente **no se utiliza una arquitectura de microservicios**.

No debe introducirse una separación en microservicios salvo que exista una necesidad técnica clara y se haya aprobado explícitamente.

---

## 2. Estructura principal

La estructura relevante del backend se organiza aproximadamente de la siguiente forma:

- `app/main.py`
  - Punto principal de composición de la aplicación.
  - Configuración de FastAPI.
  - Endpoints HTTP y composición de diferentes componentes.

- `app/bot/`
  - Componentes relacionados con Telegram.
  - Handlers y lógica de interacción con el bot.

- `app/services/`
  - Lógica de aplicación y servicios de negocio.
  - Orquestación del procesamiento.
  - Parsing.
  - Clasificación mediante IA.
  - Alertas.
  - Suscripciones.
  - Stripe.

- `app/sources/`
  - Abstracciones y adaptadores para las fuentes externas.
  - Implementaciones de RSS, Reddit y Tablón de Anuncios.
  - Normalización de elementos obtenidos de fuentes externas.

- `app/jobs/`
  - Tareas programadas.
  - Integración con APScheduler.
  - Ejecución periódica del procesamiento.

- `app/subscriptions/`
  - Catálogo y entidades relacionadas con suscripciones.

- `app/debug/`
  - Sistema de debugging, trazabilidad y dashboard interno.

- `app/database.py`
  - Acceso a Supabase.
  - Operaciones relacionadas con persistencia.
  - Algunas reglas relacionadas con usuarios y feeds.

- `app/models.py`
  - Modelos utilizados por la aplicación.

- `app/config.py`
  - Configuración mediante Pydantic Settings y variables de entorno.

---

## 3. Responsabilidades por capa

### API / composición

La aplicación FastAPI actúa como punto de entrada HTTP y como parte de la composición general del sistema.

Los endpoints deben delegar la lógica de negocio a servicios apropiados.

Los endpoints no deberían convertirse en contenedores de lógica de negocio compleja.

---

### Bot

La capa de bot representa la interacción con Telegram.

Su responsabilidad principal es:

- Recibir actualizaciones de Telegram.
- Interpretar comandos e interacciones.
- Validar la entrada necesaria.
- Delegar operaciones a los servicios correspondientes.
- Presentar resultados al usuario.

La lógica de negocio reutilizable no debe duplicarse entre handlers.

---

### Services

`app/services/` contiene la lógica de aplicación y negocio.

Entre los servicios actuales se encuentran:

- `orchestrator.py`
- `feed_parser.py`
- `ai_classifier.py`
- `alert_service.py`
- `stripe_service.py`
- `subscription_service.py`
- `prompts.py`
- `source_display_name.py`

Los servicios deben mantener responsabilidades claras y evitar convertirse en clases o módulos monolíticos que acumulen responsabilidades no relacionadas.

---

### Sources

`app/sources/` contiene la abstracción de las fuentes externas y sus implementaciones.

Actualmente existen fuentes para:

- RSS.
- Reddit.
- Tablón de Anuncios.

La arquitectura utiliza una abstracción común para permitir que distintas fuentes puedan integrarse en el flujo de procesamiento.

Las implementaciones específicas de una fuente deben permanecer aisladas de la lógica de negocio general siempre que sea posible.

---

### Jobs

`app/jobs/` contiene la ejecución programada de tareas.

Actualmente se utiliza APScheduler.

Los jobs deben actuar principalmente como mecanismos de disparo y coordinación, evitando duplicar la lógica de negocio que ya exista en los servicios.

---

### Database

La persistencia utiliza Supabase.

El acceso se realiza mediante el cliente de Supabase desde Python y actualmente no se utiliza un ORM.

Las operaciones de persistencia deben mantenerse centralizadas y reutilizables cuando exista una operación equivalente.

No debe introducirse un ORM únicamente por motivos de estilo o preferencia personal.

---

### Debug

`app/debug/` contiene los componentes relacionados con:

- Trazabilidad.
- Modelos de trazas.
- Persistencia de trazas.
- Servicios de debugging.
- Dashboard interno.

Los mecanismos de debugging y observabilidad no deben acoplar innecesariamente la lógica de negocio con la interfaz del dashboard.

---

## 4. Flujo principal de procesamiento

El flujo principal del sistema sigue conceptualmente esta secuencia:

1. Se consultan las fuentes configuradas.
2. Cada fuente obtiene nuevos elementos.
3. Los elementos se parsean y normalizan.
4. Se determina si el elemento es nuevo.
5. Cuando corresponde, se procesa mediante IA.
6. El resultado se persiste.
7. Cuando corresponde, se genera una alerta.
8. La alerta se envía mediante Telegram.

La orquestación principal de este flujo se encuentra en:

`app/services/orchestrator.py`

Cualquier modificación importante de este flujo debe tener en cuenta el impacto sobre:

- Fuentes.
- Persistencia.
- Clasificación mediante IA.
- Alertas.
- Tests de integración.
- Tests E2E.

---

## 5. Integraciones externas

El sistema depende de varios servicios externos.

### Supabase

Responsable de la persistencia de datos.

La aplicación utiliza el cliente de Supabase directamente.

---

### Telegram

La comunicación con Telegram se realiza mediante `python-telegram-bot`.

Telegram se utiliza para:

- Interacción con usuarios.
- Recepción de comandos.
- Envío de alertas.
- Webhook.

---

### Stripe

Stripe gestiona las funcionalidades relacionadas con pagos y suscripciones.

La aplicación utiliza:

- Stripe Checkout.
- Customer Portal.
- Webhooks.

Los webhooks deben conservar su validación de firma.

---

### NVIDIA API

La clasificación mediante IA utiliza opcionalmente una API de NVIDIA mediante una interfaz compatible con OpenAI.

La IA es una capacidad opcional del sistema y no debe asumirse como una dependencia obligatoria para todos los flujos.

---

### Fuentes externas

Actualmente se soportan diferentes mecanismos de obtención de información:

- RSS mediante `feedparser`.
- Reddit.
- Tablón de Anuncios.
- HTTP mediante `httpx`.
- Parsing HTML mediante BeautifulSoup y `lxml`.

Las fuentes externas deben integrarse mediante las abstracciones existentes en `app/sources/`.

---

## 6. Dependencias entre componentes

La dirección general de dependencias debe favorecer la separación de responsabilidades:

- Los puntos de entrada reciben solicitudes o eventos.
- Los puntos de entrada delegan en servicios.
- Los servicios utilizan las abstracciones de fuentes, persistencia e integraciones necesarias.
- Las implementaciones concretas de fuentes permanecen dentro de `app/sources/`.
- Los jobs disparan procesos existentes en lugar de duplicarlos.
- Los tests verifican cada nivel de forma apropiada.

Debe evitarse que:

- Un handler contenga lógica de negocio compleja.
- Un job replique lógica existente en `services`.
- Una fuente conozca detalles internos de Telegram.
- La lógica de negocio dependa directamente de elementos propios del dashboard de debugging.
- Se duplique lógica de persistencia en múltiples módulos.

---

## 7. Orquestación

`app/services/orchestrator.py` es actualmente el punto principal de coordinación del pipeline.

Su responsabilidad es coordinar las distintas etapas del procesamiento sin absorber innecesariamente la implementación detallada de cada etapa.

Cuando una etapa necesite nueva funcionalidad, debe evaluarse primero si corresponde modificar o reutilizar un servicio existente antes de añadir lógica directamente al orquestador.

El orquestador no debe convertirse progresivamente en un "god object".

Si una modificación incrementa significativamente su complejidad, debe considerarse extraer responsabilidades a servicios especializados.

---

## 8. Modularidad

El proyecto debe continuar evolucionando como **monolito modular**.

La modularidad se consigue mediante:

- Responsabilidades bien delimitadas.
- Servicios especializados.
- Abstracciones para fuentes.
- Separación entre entrada, negocio, infraestructura y jobs.
- Tests independientes por componente.
- Interfaces claras entre módulos.

No se debe introducir complejidad arquitectónica innecesaria para conseguir una separación teórica perfecta.

La solución preferida es la que mantenga el sistema sencillo y mantenible.

---

## 9. Cambios arquitectónicos

Los cambios locales que no alteren las fronteras principales del sistema pueden realizarse siguiendo las reglas generales de Copilot.

Requieren revisión o aprobación previa los cambios que impliquen:

- Introducción de una nueva arquitectura.
- División del monolito en servicios independientes.
- Cambios importantes en las responsabilidades de módulos.
- Cambios importantes en el flujo principal.
- Cambios en contratos de API.
- Cambios en el modelo de persistencia.
- Migraciones o cambios de esquema de base de datos.
- Introducción de dependencias estructurales importantes.
- Cambios relevantes en Docker o despliegue.
- Cambios importantes en mecanismos de autenticación o seguridad.

Antes de ejecutar uno de estos cambios debe explicarse:

1. Qué problema resuelve.
2. Por qué la arquitectura actual no es suficiente.
3. Qué alternativas se han considerado.
4. Qué impacto tendrá.
5. Qué riesgos o incompatibilidades introduce.
6. Cómo se validará el cambio.

---

## 10. Restricciones arquitectónicas actuales

### No introducir microservicios prematuramente

La aplicación debe mantenerse como monolito modular mientras esta estructura sea suficiente.

### No introducir abstracciones innecesarias

No crear capas, interfaces o patrones únicamente para seguir una arquitectura teórica.

La abstracción debe resolver una necesidad real.

### No duplicar responsabilidades

Antes de crear una nueva función o servicio, comprobar si la responsabilidad ya existe en otro componente.

### No modificar contratos sin necesidad

Los cambios deben ser compatibles con el comportamiento actual siempre que sea posible.

### No realizar refactors globales durante cambios funcionales

Un cambio funcional debe mantenerse centrado en su objetivo.

Los refactors no relacionados deben realizarse de forma independiente cuando sea necesario.

---

## 11. Configuración y despliegue

La configuración se gestiona mediante:

- Pydantic Settings.
- Variables de entorno.
- `.env` para configuración local.

Los secretos y credenciales no deben almacenarse en código.

El proyecto utiliza Docker para el despliegue y contiene configuración específica para Railway.

Actualmente existe una discrepancia conocida:

- `requirements.txt` considera Python 3.12 como versión estable.
- `Dockerfile` utiliza Python 3.11.

Esta discrepancia no debe resolverse automáticamente durante cambios no relacionados.

Si se decide corregirla, debe tratarse como un cambio explícito y validarse el impacto sobre dependencias, tests y despliegue.

---

## 12. Testing desde el punto de vista arquitectónico

La arquitectura actual dispone de tres niveles principales de pruebas:

- Unitarias.
- Integración.
- E2E.

La ubicación actual es:

- `tests/unit/`
- `tests/integration/`
- `tests/e2e/`

Los cambios arquitectónicos deben preservar la capacidad de probar componentes de forma aislada.

Cuando sea posible, las dependencias externas deben poder sustituirse mediante mocks o fakes existentes.

El pipeline crítico debe continuar cubierto mediante pruebas de integración y E2E cuando corresponda.

---

## 13. Observabilidad

El sistema utiliza:

- Loguru.
- Logging estructurado.
- Métricas internas.
- Trazabilidad personalizada.
- Dashboard interno de debugging.

Los cambios relevantes en el flujo de procesamiento deberían mantener una observabilidad equivalente a la existente.

No deben añadirse logs indiscriminados.

Especialmente no deben registrarse:

- Secretos.
- Tokens.
- Credenciales.
- Información sensible innecesaria.
- Payloads completos cuando no sean necesarios.

---

## 14. Principios de evolución

Al modificar la arquitectura existente, seguir este orden de preferencia:

1. Reutilizar componentes existentes.
2. Modificar el componente existente si su responsabilidad sigue siendo coherente.
3. Extraer una responsabilidad cuando un componente haya acumulado demasiadas funciones.
4. Crear un nuevo módulo cuando exista una responsabilidad claramente diferenciada.
5. Introducir una nueva abstracción solamente cuando aporte valor real.
6. Considerar cambios arquitectónicos mayores únicamente cuando exista una necesidad demostrable.

La arquitectura debe evolucionar de forma incremental.

---

## 15. Fuente de verdad

Este archivo representa el **contexto arquitectónico compartido** para los agentes.

Debe mantenerse actualizado cuando se produzcan cambios arquitectónicos relevantes.

No debe utilizarse como sustituto de:

- `copilot-instructions.md`, que define reglas de comportamiento.
- Los agentes especializados de `.github/agents/`, que definen responsabilidades y forma de trabajo.
- Los workflows de `.github/workflows/`, que definen procesos.
- La documentación específica de cada módulo.

Cuando exista una contradicción entre este documento y la implementación real, no asumir automáticamente que el documento es correcto.

La implementación actual debe inspeccionarse y la discrepancia debe identificarse antes de realizar cambios estructurales.

---

## 16. Decisiones arquitectónicas actuales

### Modular monolith

La aplicación permanece como monolito modular.

**Motivo:** la separación actual proporciona suficiente aislamiento entre responsabilidades sin introducir la complejidad operacional de los microservicios.

### Supabase como persistencia

Se mantiene el cliente de Supabase directamente desde Python.

**Motivo:** es la solución existente y no existe actualmente una necesidad establecida de introducir un ORM.

### APScheduler

Las tareas periódicas se gestionan mediante APScheduler.

### IA opcional

La clasificación mediante IA es una capacidad opcional y no debe convertirse accidentalmente en una dependencia obligatoria de todo el pipeline.

### Orquestación central

El pipeline principal continúa coordinado desde `app/services/orchestrator.py`, evitando distribuir prematuramente la coordinación entre múltiples procesos o servicios.

---

## 17. Regla principal para los agentes

Antes de realizar un cambio arquitectónico:

- Inspeccionar la implementación existente.
- Identificar las responsabilidades actuales.
- Reutilizar componentes existentes cuando sea posible.
- Evitar introducir patrones innecesarios.
- Mantener el monolito modular.
- Preservar los contratos existentes.
- Mantener la cobertura de tests.
- Explicar cualquier cambio estructural relevante antes de ejecutarlo.

**La prioridad es evolucionar la arquitectura existente de forma incremental, simple y mantenible, no rediseñarla por completo.**