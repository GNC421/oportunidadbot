from supabase import create_client, Client
from loguru import logger
from typing import Optional, List, Dict, Any
from datetime import datetime

from .config import settings

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
    try:
        # Verificar si existe
        existing = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if existing.data:
            # Actualizar
            supabase.table('users').update({
                'username': username,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            logger.info(f"📝 Usuario actualizado: {username} (ID: {user_id})")
        else:
            # Crear
            supabase.table('users').insert({
                'id': user_id,
                'username': username,
                'is_active': True
            }).execute()
            logger.info(f"👤 Nuevo usuario: {username} (ID: {user_id})")
        return True
    except Exception as e:
        logger.error(f"Error al añadir usuario: {e}")
        return False

def get_user(user_id: int) -> Optional[Dict]:
    """Obtiene un usuario por su ID"""
    try:
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al obtener usuario: {e}")
        return None

# ============ CRUD Feeds ============

def add_feed(user_id: int, url: str) -> int:
    """Añade un nuevo feed para un usuario"""
    try:
        result = supabase.table('feeds').insert({
            'user_id': user_id,
            'url': url,
            'is_active': True
        }).execute()
        feed_id = result.data[0]['id']
        logger.info(f"📡 Feed añadido: ID {feed_id} para usuario {user_id}")
        return feed_id
    except Exception as e:
        logger.error(f"Error al añadir feed: {e}")
        raise

def get_user_feeds(user_id: int) -> List[Dict]:
    """Obtiene todos los feeds activos de un usuario"""
    try:
        result = supabase.table('feeds').select('*').eq('user_id', user_id).eq('is_active', True).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error al obtener feeds: {e}")
        return []


def get_active_feeds() -> List[Dict]:
    """Obtiene todos los feeds activos de la base de datos."""
    try:
        result = supabase.table('feeds').select('*').eq('is_active', True).execute()
        return result.data
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
        return None

def get_alert_by_url(post_url: str) -> Optional[Dict]:
    """Verifica si una alerta ya existe por URL"""
    try:
        result = supabase.table('alerts').select('*').eq('post_url', post_url).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error al obtener alerta: {e}")
        return None

def mark_alert_sent(alert_id: int):
    """Marca una alerta como enviada"""
    try:
        supabase.table('alerts').update({
            'sent_at': datetime.now().isoformat()
        }).eq('id', alert_id).execute()
    except Exception as e:
        logger.error(f"Error al marcar alerta enviada: {e}")