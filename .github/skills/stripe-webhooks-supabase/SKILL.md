---
name: stripe-webhooks-supabase
description: "Implementa integraciones de pagos con Stripe usando webhooks, validacion server-side, StripeService centralizado y sincronizacion con Supabase. Usar cuando se creen checkout sessions, suscripciones, renovaciones, cancelaciones o reconciliacion de estado de pago."
argument-hint: "Que flujo de Stripe quieres implementar o corregir?"
user-invocable: true
---

# Stripe Webhooks + Supabase

## Resultado
Esta skill produce una integracion de Stripe segura y mantenible con estas garantias:
- Toda decision de pago ocurre en servidor.
- Nunca se confia en datos sensibles enviados por cliente.
- Toda logica Stripe queda centralizada en StripeService.
- No se hardcodea ningun price_id.
- Supabase se sincroniza exclusivamente a traves de webhooks verificados.

## Cuando Usar
- Alta de suscripcion con Checkout Session.
- Cambios de plan.
- Renovaciones o cobros periodicos.
- Cancelaciones.
- Correccion de inconsistencias entre Stripe y Supabase.
- Refactor de codigo donde Stripe este disperso en controladores/rutas.

## Reglas No Negociables
- Usar webhooks como fuente de verdad para el estado final de pago/suscripcion.
- Nunca confiar en montos, estado de pago, customer_id, subscription_id o price_id enviados por cliente.
- Centralizar interacciones con Stripe en StripeService.
- Cargar secretos y configuraciones via variables de entorno.
- No hardcodear price_id; resolverlos via mapeo por plan en configuracion.
- Sincronizar Supabase unicamente desde eventos webhook validados.

## Proceso

### 1. Preparar configuracion
1. Definir variables de entorno requeridas:
   - STRIPE_SECRET_KEY
   - STRIPE_WEBHOOK_SECRET
   - STRIPE_PRICE_BASIC
   - STRIPE_PRICE_PRO
   - STRIPE_PRICE_ENTERPRISE
2. Opcional recomendado: usar un prefijo de entorno por stage (dev/staging/prod).
3. Fallar rapido en arranque si falta alguna variable critica.

### 2. Definir contratos de dominio
1. Definir ids internos de plan (por ejemplo: basic, pro, enterprise).
2. Crear mapeo plan interno -> variable de entorno con price_id.
3. Exponer en StripeService un metodo que traduzca plan interno a price_id.
4. Si el plan solicitado no existe en el mapeo, devolver error de validacion.

### 3. Centralizar StripeService
1. Crear/usar StripeService como unico punto para:
   - crear checkout sessions
   - recuperar sesiones/suscripciones
   - verificar firmas de webhook
   - normalizar eventos Stripe a eventos de dominio
2. Evitar llamadas directas a Stripe SDK desde handlers, controladores o jobs.
3. Mantener manejo de errores y logs en StripeService para consistencia.

### 4. Flujo de Checkout seguro
1. Cliente envia solo datos no sensibles (por ejemplo: plan interno).
2. Servidor autentica usuario y obtiene user_id desde sesion/token server-side.
3. Servidor resuelve price_id por mapeo en StripeService.
4. Servidor crea Checkout Session via StripeService.
5. Guardar metadata minima para reconciliacion (user_id, plan interno, correlation_id).

### 5. Endpoint de webhook
1. Exponer endpoint dedicado para webhook de Stripe.
2. Verificar firma con STRIPE_WEBHOOK_SECRET antes de procesar.
3. Rechazar payload no verificado.
4. Aplicar idempotencia por event.id para evitar reprocesamiento.
5. Procesar solo tipos de evento permitidos.

### 6. Sincronizar Supabase desde webhooks
1. Mapear eventos Stripe relevantes a acciones de dominio:
   - checkout.session.completed
   - customer.subscription.created
   - customer.subscription.updated
   - customer.subscription.deleted
   - invoice.payment_succeeded
   - invoice.payment_failed
2. Actualizar tablas de Supabase con estado canonico derivado del webhook.
3. Registrar event.id, tipo, fecha y resultado para auditoria.
4. Si ocurre error transitorio, dejar trazabilidad y habilitar reintento seguro.

### 7. Branching y decisiones
- Si firma webhook invalida: responder 400 y no mutar estado.
- Si event.id ya procesado: responder 200 sin reprocesar.
- Si evento no soportado: responder 200 y registrar como ignorado.
- Si referencia de usuario no existe en Supabase: registrar incidente y enviar a cola de conciliacion.
- Si Stripe y Supabase divergen: priorizar estado de Stripe recibido por webhook validado.

## Criterios de Calidad (Definition of Done)
- No hay price_id hardcodeados en codigo.
- Todas las llamadas a Stripe pasan por StripeService.
- Ningun endpoint confia en estado de pago informado por cliente.
- Webhook valida firma y aplica idempotencia.
- Supabase se actualiza solo desde webhooks.
- Existen logs estructurados con event.id para trazabilidad.
- Hay pruebas para camino feliz y casos de seguridad.

## Checklist Rapido
- Variables de entorno completas y validadas al iniciar.
- Mapeo de planes a price_id implementado.
- Endpoint webhook protegido con firma.
- Tabla o mecanismo de idempotencia activo.
- Sincronizacion Supabase disparada por webhook.
- Pruebas de eventos duplicados, firma invalida y evento no soportado.

## Prompts de ejemplo
- Implementa checkout con Stripe siguiendo stripe-webhooks-supabase para plan pro.
- Refactoriza el modulo de pagos para mover toda logica Stripe a StripeService.
- Agrega endpoint webhook de Stripe con validacion de firma e idempotencia.
- Sincroniza suscripciones en Supabase usando customer.subscription.updated.
