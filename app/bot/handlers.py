from typing import Any, Dict, Optional
from urllib.parse import urlparse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from loguru import logger

from app import database
from app.config import settings
from app.services import feed_parser

MAX_FEEDS_PER_USER = getattr(settings, "MAX_FEEDS_PER_USER", 10)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /start."""
    user = update.effective_user
    welcome_text = (
        f"¡Hola {user.first_name}! 👋\n\n"
        "Soy **OportunidadBot**, tu asistente para encontrar oportunidades.\n"
        "Usa /help para ver qué puedo hacer."
    )
    keyboard = [[InlineKeyboardButton("Visitar sitio", url="https://tusitio.com")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /help."""
    help_text = (
        "📋 **Lista de comandos disponibles:**\n\n"
        "/start - Mensaje de bienvenida\n"
        "/help - Mostrar esta ayuda\n"
        "/addgroup [URL] - Añadir un feed RSS\n"
        "/groups - Listar tus feeds\n"
        "/removegroup [ID] - Eliminar un feed\n"
        "/pausegroup [ID] - Pausar un feed\n"
        "/resumegroup [ID] - Reanudar un feed\n"
        "/ping - Verificar latencia (para pruebas)"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


def _get_user_id(update: Update) -> Optional[int]:
    """Obtiene el ID del usuario desde la actualización."""
    user = update.effective_user
    return user.id if user else None


def _normalize_feed_url(raw_url: str) -> str:
    """Normaliza una URL de feed para evitar errores de formato."""
    cleaned = raw_url.strip()
    if not cleaned:
        return cleaned
    parsed = urlparse(cleaned)
    if parsed.scheme and parsed.netloc:
        return cleaned
    if "://" not in cleaned:
        return f"https://{cleaned}"
    return cleaned


def _fetch_user_feeds(user_id: int) -> list[Dict[str, Any]]:
    """Obtiene todos los feeds de un usuario desde la capa de persistencia."""
    return database.get_user_feeds(user_id)


def _delete_user_feed(user_id: int, feed_id: int) -> None:
    """Elimina un feed del usuario mediante la capa de persistencia."""
    database.supabase.table("feeds").delete().eq("id", feed_id).eq("user_id", user_id).execute()


def _update_user_feed_status(user_id: int, feed_id: int, is_active: bool) -> None:
    """Actualiza el estado de un feed del usuario mediante la capa de persistencia."""
    database.supabase.table("feeds").update({"is_active": is_active}).eq("id", feed_id).eq("user_id", user_id).execute()


def _find_user_feed(user_id: int, feed_id: int) -> Optional[Dict[str, Any]]:
    """Busca un feed del usuario por su identificador."""
    for feed in _fetch_user_feeds(user_id):
        if feed.get("id") == feed_id:
            return feed
    return None


async def addgroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Añade un feed RSS para el usuario actual."""
    user_id = _get_user_id(update)
    if not user_id:
        await update.message.reply_text("No pude identificar tu usuario. Inténtalo de nuevo.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /addgroup [URL_del_feed_RSS]")
        return

    raw_url = " ".join(context.args).strip()
    if not raw_url:
        await update.message.reply_text("La URL del feed no puede estar vacía.")
        return

    normalized_url = _normalize_feed_url(raw_url)
    parsed = urlparse(normalized_url)
    if not parsed.scheme or not parsed.netloc:
        logger.warning("URL de feed inválida recibida: {}", raw_url)
        await update.message.reply_text("La URL no tiene un formato válido. Prueba con una dirección completa como https://ejemplo.com/feed")
        return

    try:
        existing_feeds = _fetch_user_feeds(user_id)
        existing_urls = {
            _normalize_feed_url(str(feed.get("url", "")))
            for feed in existing_feeds
            if feed.get("url")
        }

        if normalized_url in existing_urls:
            await update.message.reply_text("Este feed ya está registrado en tus grupos.")
            return

        if len(existing_feeds) >= MAX_FEEDS_PER_USER:
            await update.message.reply_text(
                f"Has alcanzado el límite de {MAX_FEEDS_PER_USER} feeds por usuario. Elimina uno antes de añadir otro."
            )
            return

        validation = feed_parser.validate_feed_source(normalized_url)
        if not validation.get("valid", False):
            logger.warning("El feed no pudo validarse: {normalized_url} - {error}")
            await update.message.reply_text(
                "No pude validar ese RSS. " + (validation.get("error") or "Comprueba que la URL sea un feed válido y accesible.")
            )
            return

        feed_id = database.add_feed(user_id=user_id, url=normalized_url)
        logger.info("Feed añadido por usuario %s: %s", user_id, normalized_url)
        await update.message.reply_text(
            f"✅ Feed añadido correctamente.\nID: {feed_id}\nURL: {normalized_url}"
        )
    except Exception as exc:
        logger.exception("Error al añadir un feed para el usuario %s", user_id)
        await update.message.reply_text("No se pudo guardar el feed en este momento. Inténtalo más tarde.")


async def groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista los feeds del usuario actual."""
    user_id = _get_user_id(update)
    if not user_id:
        await update.message.reply_text("No pude identificar tu usuario. Inténtalo de nuevo.")
        return

    try:
        feeds = _fetch_user_feeds(user_id)
        if not feeds:
            await update.message.reply_text("No tienes feeds registrados aún. Usa /addgroup para añadir uno.")
            return

        lines = ["📡 Tus feeds:"]
        for feed in feeds:
            status = "🟢 Activo" if feed.get("is_active", True) else "🟡 Pausado"
            lines.append(f"- ID {feed.get('id')}: {status}\n  {feed.get('url', 'Sin URL')}")

        await update.message.reply_text("\n".join(lines))
    except Exception as exc:
        logger.exception("Error al listar feeds del usuario %s", user_id)
        await update.message.reply_text("No se pudieron cargar tus feeds en este momento.")


async def removegroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Elimina un feed RSS del usuario actual."""
    user_id = _get_user_id(update)
    if not user_id:
        await update.message.reply_text("No pude identificar tu usuario. Inténtalo de nuevo.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /removegroup [ID_del_feed]")
        return

    try:
        feed_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("El identificador del feed debe ser un número.")
        return

    try:
        feed = _find_user_feed(user_id, feed_id)
        if not feed:
            await update.message.reply_text("No encontré ese feed entre tus grupos.")
            return

        _delete_user_feed(user_id, feed_id)
        logger.info("Feed eliminado por usuario %s: %s", user_id, feed_id)
        await update.message.reply_text("🗑️ Feed eliminado correctamente.")
    except Exception as exc:
        logger.exception("Error al eliminar el feed %s del usuario %s", feed_id, user_id)
        await update.message.reply_text("No se pudo eliminar el feed en este momento.")


async def pausegroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pausa un feed RSS del usuario actual."""
    user_id = _get_user_id(update)
    if not user_id:
        await update.message.reply_text("No pude identificar tu usuario. Inténtalo de nuevo.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /pausegroup [ID_del_feed]")
        return

    try:
        feed_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("El identificador del feed debe ser un número.")
        return

    try:
        feed = _find_user_feed(user_id, feed_id)
        if not feed:
            await update.message.reply_text("No encontré ese feed entre tus grupos.")
            return

        _update_user_feed_status(user_id, feed_id, False)
        logger.info("Feed pausado por usuario %s: %s", user_id, feed_id)
        await update.message.reply_text("⏸️ Feed pausado correctamente.")
    except Exception as exc:
        logger.exception("Error al pausar el feed %s del usuario %s", feed_id, user_id)
        await update.message.reply_text("No se pudo pausar el feed en este momento.")


async def resumegroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reanuda un feed RSS del usuario actual."""
    user_id = _get_user_id(update)
    if not user_id:
        await update.message.reply_text("No pude identificar tu usuario. Inténtalo de nuevo.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /resumegroup [ID_del_feed]")
        return

    try:
        feed_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("El identificador del feed debe ser un número.")
        return

    try:
        feed = _find_user_feed(user_id, feed_id)
        if not feed:
            await update.message.reply_text("No encontré ese feed entre tus grupos.")
            return

        _update_user_feed_status(user_id, feed_id, True)
        logger.info("Feed reactivado por usuario %s: %s", user_id, feed_id)
        await update.message.reply_text("▶️ Feed reactivado correctamente.")
    except Exception as exc:
        logger.exception("Error al reactivar el feed %s del usuario %s", feed_id, user_id)
        await update.message.reply_text("No se pudo reactivar el feed en este momento.")


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde con el mismo texto que el usuario (solo para pruebas)."""
    text = update.message.text
    await update.message.reply_text(f"Echo: {text}")


async def handle_quick_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al botón de añadir un grupo o feed."""
    query = update.callback_query
    await query.answer("Puedes añadir un feed con /addgroup [URL_del_feed_RSS].")
    await query.message.reply_text(
        "Para añadir un grupo o feed, usa:\n\n/addgroup [URL_del_feed_RSS]\n\nEjemplo:\n/addgroup https://example.com/feed"
    )


async def handle_tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra un tutorial breve para el usuario."""
    query = update.callback_query
    await query.answer()
    tutorial_text = (
        "📚 Tutorial rápido\n\n"
        "1. Añade un feed con /addgroup [URL_del_feed_RSS].\n"
        "2. El bot revisará el contenido cada 15 minutos.\n"
        "3. Cuando detecte una oportunidad, te enviará una alerta.\n"
        "4. Puedes usar los botones de cada alerta para actuar."
    )
    await query.message.reply_text(tutorial_text)


async def handle_remind_later(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al botón de recordar más tarde."""
    query = update.callback_query
    await query.answer("Te recordaremos más tarde.")
    await query.message.reply_text(
        "Perfecto. Te avisaremos de nuevo más tarde cuando haya una oportunidad relevante."
    )


async def handle_generate_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja la generación de respuesta para una alerta concreta."""
    query = update.callback_query
    feed_id = None
    if context.matches:
        feed_id = context.matches[0].group(1)

    await query.answer("Esta acción aún no está implementada.")
    message = (
        "La generación automática de respuestas con IA aún no está activa. "
        "Puedes seguir la alerta manualmente o esperar a una próxima versión."
    )
    if feed_id:
        message += f"\n\nFeed asociado: {feed_id}"
    await query.message.reply_text(message)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra errores y notifica al desarrollador (opcional)."""
    logger.error(f"Excepción mientras se manejaba una actualización: {context.error}")
    if update and hasattr(update, "message") and update.message:
        await update.message.reply_text("Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde.")


def register_handlers(application: Application) -> None:
    """Registra los handlers del bot en la aplicación."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addgroup", addgroup_command))
    application.add_handler(CommandHandler("groups", groups_command))
    application.add_handler(CommandHandler("removegroup", removegroup_command))
    application.add_handler(CommandHandler("pausegroup", pausegroup_command))
    application.add_handler(CommandHandler("resumegroup", resumegroup_command))
    application.add_handler(CallbackQueryHandler(handle_quick_add, pattern="^quick_add$"))
    application.add_handler(CallbackQueryHandler(handle_tutorial, pattern="^tutorial$"))
    application.add_handler(CallbackQueryHandler(handle_remind_later, pattern="^remind_later$"))
    application.add_handler(CallbackQueryHandler(handle_generate_alert, pattern=r"^generate_alert_(\d+)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    application.add_error_handler(error_handler)
