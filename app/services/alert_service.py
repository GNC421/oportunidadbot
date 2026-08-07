from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
import os

from app.database import get_user
from app.debug.trace_service import get_trace_service
from app.debug.trace_models import EventType
try:
    from telegram.utils.helpers import escape_markdown  # type: ignore
except Exception:
    # Fallback simple escaper to avoid dependency in tests
    def escape_markdown(text: str, version: int = 1) -> str:
        if text is None:
            return ""
        esc_chars = '\\_*[]()~`>#+-=|{}.!'
        out = []
        for ch in str(text):
            if ch in esc_chars:
                out.append(f"\\{ch}")
            else:
                out.append(ch)
        return ''.join(out)

BOT_USERNAME = os.getenv("BOT_USERNAME", "OportunidadBot")

async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envía el mensaje de bienvenida"""
    logger.debug("send_welcome_message called")
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
    logger.debug("send_alert called", user_id=user_id, feed_id=feed_id, post_url=post_data.get("link"))
    from app.bot import application

    trace = get_trace_service()
    event_id = await trace.start(type=EventType.TELEGRAM, name="Send alert", input_payload={"user_id": user_id, "feed_id": feed_id, "post": {"title": post_data.get("title")}})
    
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

    # Construir mensaje usando helper reutilizable
    def format_opportunity_message(item: dict, limit: int = 4000) -> tuple[str, InlineKeyboardMarkup]:
        title = item.get('title') or 'Sin título'
        category = item.get('category')
        price = item.get('price')
        location = item.get('location')
        description = item.get('summary') or ''
        post_url = item.get('link') or ''

        esc = lambda s: escape_markdown(str(s), version=1) if s is not None else ''

        parts: list[str] = []
        parts.append("🚨 NUEVA OPORTUNIDAD")
        parts.append("")
        parts.append(f"🏠 {esc(title)}")

        if category:
            parts.append(f"🏷️ {esc(category)}")

        if price:
            parts.append(f"💰 {esc(price)}")

        if description:
            parts.append("")
            parts.append("📄 Descripción:")
            parts.append(esc(description))

        if location:
            parts.append("")
            parts.append(f"📍 {esc(location)}")

        text = "\n".join(parts)

        if len(text) > limit and description:
            try:
                desc_index = parts.index(esc(description))
            except ValueError:
                desc_index = None

            if desc_index is not None:
                label_index = desc_index - 1 if desc_index - 1 >= 0 else desc_index
                prefix = parts[:label_index]
                footer = parts[desc_index+1:]
                # Reserve length for prefix + label + footer + ellipsis
                reserved = len("\n".join(prefix + ["", "📄 Descripción:"] + footer)) + 3
                allowed_desc = max(0, limit - reserved)
                if allowed_desc <= 0:
                    text = "\n".join(["🚨 NUEVA OPORTUNIDAD", "", f"🏠 {esc(title)}"])
                else:
                    short_desc = esc(description)[:allowed_desc]
                    if " " in short_desc:
                        short_desc = short_desc.rsplit(' ', 1)[0]
                    text = "\n".join(prefix + ["", "📄 Descripción:", short_desc + "..."] + footer)

        keyboard = []
        if post_url:
            keyboard = [[InlineKeyboardButton("🔗 Ver anuncio", url=post_url)]]

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        return text, reply_markup

    alert_text, reply_markup = format_opportunity_message(post_data)

    # reply_markup ya proviene de format_opportunity_message (solo botón Ver anuncio)
    
    try:
        await application.bot.send_message(
            chat_id=user_id,
            text=alert_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info(f"📨 Alerta enviada a {user_id}: {title[:50]}...")
        await trace.success(event_id, output_payload={"sent_to": user_id, "title": title})
    except Exception as e:
        logger.error(f"❌ Error al enviar alerta a {user_id}: {e}")
        await trace.error(event_id, error=str(e))