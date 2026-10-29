from supabase import create_client, Client
from loguru import logger
from typing import Optional, List, Dict, Any
from datetime import datetime

from .config import settings
from app.debug.trace_service import get_trace_service
from app.debug.trace_models import EventType
import asyncio


def _maybe_run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
        return ""
    except RuntimeError:
        return asyncio.run(coro)

if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
    logger.error("❌ Supabase URL o KEY no configuradas")
    raise ValueError("Supabase credentials are required")

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def init_db():
    """Verifica la conexión a la base de datos"""
    try:
        # Hacer una consulta simple para verificar conexión
        result = supabase.table('users').select('count').limit(1).execute()
        logger.info(f"✅ Conexión a Supabase exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a Supabase: {e}")
        return False

# ============ CRUD Usuarios ============

def add_user(user_id: int, username: str) -> bool:
    """Añade un nuevo usuario o actualiza si existe"""
    trace = get_trace_service()
    event_id = _maybe_run_async(trace.start(type=EventType.DATABASE, name="Add/Update user", input_payload={"user_id": user_id, "username": username}))
    try:
        # Verificar si existe
        existing = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if existing.data:
            current = existing.data[0]
            # Actualizar
            supabase.table('users').update({
                'username': username,
                'plan': current.get('plan', 'starter'),
                'subscription_status': current.get('subscription_status', 'active'),
                'stripe_customer_id': current.get('stripe_customer_id'),
                'stripe_subscription_id': current.get('stripe_subscription_id'),
                'current_period_end': current.get('current_period_end'),
                'cancel_at_period_end': bool(current.get('cancel_at_period_end', False)),
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            logger.info(f"📝 Usuario actualizado: {username} (ID: {user_id})")
        else:
            # Crear
            supabase.table('users').insert({
                'id': user_id,
                'username': username,
                'is_active': True,
                'plan': 'starter',
                'subscription_status': 'active',
                'stripe_customer_id': None,
                'stripe_subscription_id': None,
                'current_period_end': None,
                'cancel_at_period_end': False,
            }).execute()
            logger.info(f"👤 Nuevo usuario: {username} (ID: {user_id})")
        return True
    except Exception as e:
        logger.error(f"Error al añadir usuario: {e}")
        _maybe_run_async(trace.error(event_id, error=str(e)))
        return False

def get_user(user_id: int) -> Optional[Dict]:
    """Obtiene un usuario por su ID"""
    try:
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al obtener usuario: {e}")
        return None


def get_user_by_stripe_customer_id(stripe_customer_id: str) -> Optional[Dict]:
    """Obtiene un usuario por su stripe_customer_id."""
    try:
        result = supabase.table('users').select('*').eq('stripe_customer_id', stripe_customer_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al obtener usuario por stripe_customer_id {stripe_customer_id}: {e}")
        return None


def update_user_subscription(
    user_id: int,
    plan: str,
    subscription_status: str,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
    current_period_end: Optional[str] = None,
    cancel_at_period_end: bool = False,
) -> bool:
    """Actualiza los campos de suscripción de un usuario."""
    trace = get_trace_service()
    event_id = _maybe_run_async(trace.start(type=EventType.DATABASE, name="Update subscription", input_payload={"user_id": user_id, "plan": plan}))
    try:
        result = supabase.table('users').update({
            'plan': plan,
            'subscription_status': subscription_status,
            'stripe_customer_id': stripe_customer_id,
            'stripe_subscription_id': stripe_subscription_id,
            'current_period_end': current_period_end,
            'cancel_at_period_end': cancel_at_period_end,
            'updated_at': datetime.now().isoformat(),
        }).eq('id', user_id).execute()
        return bool(getattr(result, 'data', None) is not None)
    except Exception as e:
        logger.error(f"Error al actualizar suscripción del usuario {user_id}: {e}")
        _maybe_run_async(trace.error(event_id, error=str(e)))
        return False


def register_stripe_webhook_event(event_id: str, event_type: str, payload: Dict[str, Any]) -> bool:
    """Registra un evento de Stripe para idempotencia. Devuelve False si ya existe."""
    try:
        existing = supabase.table('stripe_webhook_events').select('id').eq('event_id', event_id).execute()
        if existing.data:
            return False

        supabase.table('stripe_webhook_events').insert({
            'event_id': event_id,
            'event_type': event_type,
            'status': 'received',
            'payload': payload,
            'created_at': datetime.now().isoformat(),
            'processed_at': None,
            'error_message': None,
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Error al registrar evento de Stripe {event_id}: {e}")
        return False


def mark_stripe_webhook_event_status(event_id: str, status: str, error_message: Optional[str] = None) -> bool:
    """Actualiza el estado de procesamiento de un evento de Stripe."""
    try:
        result = supabase.table('stripe_webhook_events').update({
            'status': status,
            'processed_at': datetime.now().isoformat(),
            'error_message': error_message,
        }).eq('event_id', event_id).execute()
        return bool(getattr(result, 'data', None) is not None)
    except Exception as e:
        logger.error(f"Error al actualizar estado del evento de Stripe {event_id}: {e}")
        return False

# ============ CRUD Feeds ============

def add_feed(user_id: int, url: str) -> Optional[int]:
    """Añade un nuevo feed para un usuario."""
    trace = get_trace_service()
    event_id = _maybe_run_async(trace.start(type=EventType.DATABASE, name="Add feed", input_payload={"user_id": user_id, "url": url}))
    try:
        from app.services.subscription_service import get_subscription_service

        if not get_subscription_service().can_add_source(user_id):
            logger.warning(f"Usuario {user_id} alcanzó el límite de fuentes para su suscripción")
            return None

        result = supabase.table('feeds').insert({
            'user_id': user_id,
            'url': url,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
        }).execute()
        feed_id = result.data[0]['id'] if result.data else None
        logger.info(f"📡 Feed añadido: ID {feed_id} para usuario {user_id}")
        return feed_id
    except Exception as e:
        logger.error(f"Error al añadir feed: {e}")
        _maybe_run_async(trace.error(event_id, error=str(e)))
        return None


def get_user_feeds(user_id: int) -> List[Dict[str, Any]]:
    """Obtiene todos los feeds de un usuario."""
    try:
        result = supabase.table('feeds').select('*').eq('user_id', user_id).execute()
        return result.data if result.data is not None else []
    except Exception as e:
        logger.error(f"Error al obtener feeds del usuario {user_id}: {e}")
        return []


def delete_feed(user_id: int, feed_id: int) -> bool:
    """Elimina un feed de un usuario."""
    try:
        result = supabase.table('feeds').delete().eq('id', feed_id).eq('user_id', user_id).execute()
        success = bool(getattr(result, 'data', None) is not None)
        logger.info(f"🗑️ Feed eliminado: ID {feed_id} para usuario {user_id}")
        return success
    except Exception as e:
        logger.error(f"Error al eliminar feed {feed_id}: {e}")
        return False


def enable_feed(user_id: int, feed_id: int) -> bool:
    """Activa un feed de un usuario."""
    try:
        result = supabase.table('feeds').update({
            'is_active': True,
        }).eq('id', feed_id).eq('user_id', user_id).execute()
        success = bool(getattr(result, 'data', None) is not None)
        logger.info(f"▶️ Feed activado: ID {feed_id} para usuario {user_id}")
        return success
    except Exception as e:
        logger.error(f"Error al activar feed {feed_id}: {e}")
        return False


def disable_feed(user_id: int, feed_id: int) -> bool:
    """Desactiva un feed de un usuario."""
    try:
        result = supabase.table('feeds').update({
            'is_active': False,
        }).eq('id', feed_id).eq('user_id', user_id).execute()
        success = bool(getattr(result, 'data', None) is not None)
        logger.info(f"⏸️ Feed desactivado: ID {feed_id} para usuario {user_id}")
        return success
    except Exception as e:
        logger.error(f"Error al desactivar feed {feed_id}: {e}")
        return False


def feed_exists(user_id: int, url: str) -> bool:
    """Comprueba si un usuario ya tiene un feed con la misma URL."""
    try:
        result = supabase.table('feeds').select('id').eq('user_id', user_id).eq('url', url).execute()
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error al comprobar existencia del feed {url}: {e}")
        return False


def user_feed_count(user_id: int) -> int:
    """Cuenta los feeds de un usuario."""
    try:
        result = supabase.table('feeds').select('id', count='exact').eq('user_id', user_id).execute()
        return int(getattr(result, 'count', 0) or 0)
    except Exception as e:
        logger.error(f"Error al contar feeds del usuario {user_id}: {e}")
        return 0


def get_active_feeds() -> List[Dict[str, Any]]:
    """Obtiene todos los feeds activos de la base de datos."""
    try:
        result = supabase.table('feeds').select('*').eq('is_active', True).execute()
        return result.data if result.data is not None else []
    except Exception as e:
        logger.error(f"Error al obtener feeds activos: {e}")
        return []


def update_feed_last_check(feed_id: int):
    """Actualiza la última revisión de un feed"""
    try:
        supabase.table('feeds').update({
            'last_check': datetime.now().isoformat()
        }).eq('id', feed_id).execute()
    except Exception as e:
        logger.error(f"Error al actualizar last_check: {e}")

# ============ CRUD Alertas ============

def save_alert(user_id: int, feed_id: int, post_data: Dict) -> Optional[int]:
    """Guarda una alerta en la base de datos"""
    trace = get_trace_service()
    event_id = _maybe_run_async(trace.start(type=EventType.DATABASE, name="Save alert", input_payload={"user_id": user_id, "feed_id": feed_id, "post_url": post_data.get("link")}))
    try:
        result = supabase.table('alerts').insert({
            'user_id': user_id,
            'feed_id': feed_id,
            'post_title': post_data.get('title', ''),
            'post_content': post_data.get('summary', ''),
            'post_url': post_data.get('link'),
            'post_author': post_data.get('author', ''),
            'detected_at': datetime.now().isoformat()
        }).execute()
        return result.data[0]['id'] if result.data else None
    except Exception as e:
        logger.error(f"Error al guardar alerta: {e}")
        _maybe_run_async(trace.error(event_id, error=str(e)))
        return None

def get_alert_by_url(post_url: str) -> Optional[Dict]:
    """Verifica si una alerta ya existe por URL"""
    try:
        result = supabase.table('alerts').select('*').eq('post_url', post_url).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al obtener alerta: {e}")
        return None


def get_user_alerts(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene alertas de un usuario sin exponer registros de otros usuarios."""
    try:
        safe_limit = max(1, min(limit, 100))
        result = supabase.table('alerts').select('*').eq('user_id', user_id).limit(safe_limit).execute()
        return result.data if result.data is not None else []
    except Exception as e:
        logger.error(f"Error al obtener alertas del usuario {user_id}: {e}")
        return []

def mark_alert_sent(alert_id: int):
    """Marca una alerta como enviada"""
    trace = get_trace_service()
    event_id = _maybe_run_async(trace.start(type=EventType.DATABASE, name="Mark alert sent", input_payload={"alert_id": alert_id}))
    try:
        supabase.table('alerts').update({
            'sent_at': datetime.now().isoformat()
        }).eq('id', alert_id).execute()
        _maybe_run_async(trace.success(event_id, output_payload={"alert_id": alert_id}))
    except Exception as e:
        logger.error(f"Error al marcar alerta enviada: {e}")
        _maybe_run_async(trace.error(event_id, error=str(e)))


def list_alerts_for_users(user_ids: List[int]) -> List[Dict[str, Any]]:
    """Obtiene las alertas de un conjunto de usuarios (uso interno Enterprise)."""
    try:
        wanted = set(user_ids)
        if not wanted:
            return []
        result = supabase.table('alerts').select('*').execute()
        rows = result.data if result.data is not None else []
        return [row for row in rows if row.get('user_id') in wanted]
    except Exception as e:
        logger.error(f"Error al obtener alertas para usuarios {user_ids}: {e}")
        return []


def list_feeds_for_users(user_ids: List[int]) -> List[Dict[str, Any]]:
    """Obtiene los feeds de un conjunto de usuarios (uso interno Enterprise)."""
    try:
        wanted = set(user_ids)
        if not wanted:
            return []
        result = supabase.table('feeds').select('*').execute()
        rows = result.data if result.data is not None else []
        return [row for row in rows if row.get('user_id') in wanted]
    except Exception as e:
        logger.error(f"Error al obtener feeds para usuarios {user_ids}: {e}")
        return []


def list_users_by_ids(user_ids: List[int]) -> List[Dict[str, Any]]:
    """Obtiene los datos públicos básicos de un conjunto de usuarios."""
    try:
        wanted = set(user_ids)
        if not wanted:
            return []
        result = supabase.table('users').select('*').execute()
        rows = result.data if result.data is not None else []
        return [row for row in rows if row.get('id') in wanted]
    except Exception as e:
        logger.error(f"Error al obtener usuarios {user_ids}: {e}")
        return []


# ============ CRUD Enterprise: organizaciones ============

def create_enterprise_organization(owner_user_id: int, name: str, seats_purchased: int = 1) -> Optional[Dict[str, Any]]:
    """Crea una organización Enterprise y su membresía OWNER en una única operación."""
    try:
        existing = supabase.table('enterprise_organizations').select('*').eq('owner_user_id', owner_user_id).execute()
        if existing.data:
            logger.warning(f"El usuario {owner_user_id} ya tiene una organización Enterprise")
            return None

        result = supabase.table('enterprise_organizations').insert({
            'owner_user_id': owner_user_id,
            'name': name,
            'seats_purchased': seats_purchased,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }).execute()
        organization = result.data[0] if result.data else None
        if not organization:
            return None

        membership = create_enterprise_membership(
            organization_id=organization['id'],
            user_id=owner_user_id,
            parent_user_id=None,
            role='OWNER',
        )
        if not membership:
            logger.error(f"No se pudo crear la membresía OWNER para la organización {organization['id']}")
            return None
        return organization
    except Exception as e:
        logger.error(f"Error al crear organización Enterprise para {owner_user_id}: {e}")
        return None


def get_enterprise_organization(organization_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una organización Enterprise por su ID."""
    try:
        result = supabase.table('enterprise_organizations').select('*').eq('id', organization_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al obtener la organización Enterprise {organization_id}: {e}")
        return None


def update_enterprise_organization(organization_id: int, **fields: Any) -> bool:
    """Actualiza campos de una organización Enterprise."""
    try:
        payload = dict(fields)
        payload['updated_at'] = datetime.now().isoformat()
        result = supabase.table('enterprise_organizations').update(payload).eq('id', organization_id).execute()
        return bool(getattr(result, 'data', None) is not None)
    except Exception as e:
        logger.error(f"Error al actualizar la organización Enterprise {organization_id}: {e}")
        return False


# ============ CRUD Enterprise: miembros ============

def create_enterprise_membership(
    organization_id: int,
    user_id: int,
    parent_user_id: Optional[int],
    role: str,
    status: str = 'active',
) -> Optional[Dict[str, Any]]:
    """Crea la fila de pertenencia/jerarquía de un usuario dentro de una organización."""
    try:
        result = supabase.table('enterprise_members').insert({
            'organization_id': organization_id,
            'user_id': user_id,
            'parent_user_id': parent_user_id,
            'role': role,
            'status': status,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al crear membresía Enterprise para usuario {user_id}: {e}")
        return None


def get_enterprise_membership(user_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene la membresía Enterprise (de cualquier estado) de un usuario."""
    try:
        result = supabase.table('enterprise_members').select('*').eq('user_id', user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al obtener la membresía Enterprise del usuario {user_id}: {e}")
        return None


def list_enterprise_members(organization_id: int) -> List[Dict[str, Any]]:
    """Obtiene todas las filas de pertenencia (activas e inactivas) de una organización."""
    try:
        result = supabase.table('enterprise_members').select('*').eq('organization_id', organization_id).execute()
        return result.data if result.data is not None else []
    except Exception as e:
        logger.error(f"Error al listar miembros de la organización {organization_id}: {e}")
        return []


def update_enterprise_membership(organization_id: int, user_id: int, **fields: Any) -> bool:
    """Actualiza la fila de pertenencia de un usuario (rol, responsable o estado)."""
    try:
        payload = dict(fields)
        payload['updated_at'] = datetime.now().isoformat()
        result = (
            supabase.table('enterprise_members')
            .update(payload)
            .eq('organization_id', organization_id)
            .eq('user_id', user_id)
            .execute()
        )
        return bool(getattr(result, 'data', None) is not None)
    except Exception as e:
        logger.error(f"Error al actualizar la membresía Enterprise del usuario {user_id}: {e}")
        return False


# ============ CRUD Enterprise: invitaciones ============

def create_enterprise_invitation(
    organization_id: int,
    invited_by_user_id: int,
    parent_user_id: int,
    role: str,
    token: str,
    expires_at: str,
    telegram_username: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Crea una invitación pendiente para unirse a una organización Enterprise."""
    try:
        result = supabase.table('enterprise_invitations').insert({
            'organization_id': organization_id,
            'invited_by_user_id': invited_by_user_id,
            'parent_user_id': parent_user_id,
            'telegram_username': telegram_username,
            'invited_user_id': None,
            'role': role,
            'token': token,
            'status': 'pending',
            'expires_at': expires_at,
            'created_at': datetime.now().isoformat(),
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al crear invitación Enterprise para la organización {organization_id}: {e}")
        return None


def get_enterprise_invitation_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Obtiene una invitación Enterprise por su token."""
    try:
        result = supabase.table('enterprise_invitations').select('*').eq('token', token).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al obtener la invitación Enterprise {token}: {e}")
        return None


def list_pending_enterprise_invitations(organization_id: int) -> List[Dict[str, Any]]:
    """Lista las invitaciones pendientes de una organización."""
    try:
        result = (
            supabase.table('enterprise_invitations')
            .select('*')
            .eq('organization_id', organization_id)
            .eq('status', 'pending')
            .execute()
        )
        return result.data if result.data is not None else []
    except Exception as e:
        logger.error(f"Error al listar invitaciones pendientes de la organización {organization_id}: {e}")
        return []


def update_enterprise_invitation(invitation_id: int, **fields: Any) -> bool:
    """Actualiza el estado/datos de una invitación Enterprise."""
    try:
        result = supabase.table('enterprise_invitations').update(fields).eq('id', invitation_id).execute()
        return bool(getattr(result, 'data', None) is not None)
    except Exception as e:
        logger.error(f"Error al actualizar la invitación Enterprise {invitation_id}: {e}")
        return False


def get_pending_invitation_for_username(username: Optional[str]) -> Optional[Dict[str, Any]]:
    """Busca una invitación Enterprise pendiente y no caducada dirigida a este @usuario de Telegram.

    Permite que un empleado invitado pueda iniciar sesión en la webapp por primera vez
    aunque su plan personal (Starter) no le daría acceso por sí solo.
    """
    if not username:
        return None
    try:
        result = (
            supabase.table('enterprise_invitations')
            .select('*')
            .eq('status', 'pending')
            .eq('telegram_username', username)
            .execute()
        )
        rows = result.data if result.data is not None else []
        now = datetime.now()
        for row in rows:
            expires_at = row.get('expires_at')
            if not expires_at:
                continue
            try:
                parsed = datetime.fromisoformat(str(expires_at).replace('Z', '+00:00')).replace(tzinfo=None)
            except ValueError:
                continue
            if parsed >= now:
                return row
        return None
    except Exception as e:
        logger.error(f"Error al buscar invitación pendiente para @{username}: {e}")
        return None