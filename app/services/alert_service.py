from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ContextTypes
from telegram.ext import ContextTypes
from loguru import logger
import os

from app.database import get_user

BOT_USERNAME = os.getenv("BOT_USERNAME", "OportunidadBot")

async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el mensaje de bienvenida"""
    user = update.effective_user
    
    welcome_text = f"""
👋 *¡Hola {user.first_name}!* 

Soy *OportunidadBot*, tu asistente para detectar oportunidades de negocio en tiempo real.

🔍 *¿Qué puedo hacer por ti?*

✅ Monitorizo grupos públicos de Facebook y detecto cuando alguien pregunta por servicios como los tuyos.
✅ Te envío alertas inmediatas para que puedas responder antes que tu competencia.
✅ Con un solo clic, genero una respuesta profesional con IA.

🚀 *Para empezar:*

1. Añade un grupo público de Facebook: `/addgroup [URL_del_feed_RSS]`
2. El bot comenzará a revisar el grupo cada 15 minutos.
3. Recibirás alertas cuando se detecten preguntas relevantes.

📖 Escribe /help para ver todos los comandos disponibles.

*¡Vamos a por esas oportunidades!* 💪
"""
    
    # Crear botones de acción rápida
    keyboard = [
        [InlineKeyboardButton("➕ Añadir grupo", callback_data="quick_add")],
        [InlineKeyboardButton("📖 Ver tutorial", callback_data="tutorial")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def send_alert(user_id: int, post_data: dict, feed_id: int):
    """Envía una alerta a un usuario específico"""
    from app.bot import application
    
    # Obtener información del usuario para personalizar
    user = get_user(user_id)
    if not user:
        logger.error(f"❌ Usuario {user_id} no encontrado")
        return
    
    # Preparar mensaje
    title = post_data.get('title', 'Sin título')
    content = post_data.get('summary', '')[:300]
    post_url = post_data.get('link', '')
    
    # Determinar si es una pregunta específica
    is_question = any(pattern in title.lower() or pattern in content.lower() 
                      for pattern in ['alguien sabe', 'recomendáis', '¿', '?'])
    
    emoji = "🔍" if is_question else "📢"
    
    alert_text = f"""
{emoji} *¡Nueva oportunidad detectada!*

📌 *{title[:100]}*

{content}...

👤 Publicado por: {post_data.get('author', 'Anónimo')}
"""
    
    # Botones de acción
    keyboard = [
        [InlineKeyboardButton("📝 Redactar respuesta con IA", callback_data=f"generate_alert_{feed_id}")],
        [InlineKeyboardButton("🔗 Ver publicación original", url=post_url)],
        [InlineKeyboardButton("⏰ Recordar más tarde", callback_data="remind_later")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await application.bot.send_message(
            chat_id=user_id,
            text=alert_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info(f"📨 Alerta enviada a {user_id}: {title[:50]}...")
    except Exception as e:
        logger.error(f"❌ Error al enviar alerta a {user_id}: {e}")