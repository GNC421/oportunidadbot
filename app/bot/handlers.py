from typing import Any, Dict, Optional
from urllib.parse import urlparse

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from loguru import logger

from app import database
from app.config import settings
from app.services import feed_parser, rsshub_resolver

MAX_FEEDS_PER_USER = getattr(settings, "MAX_FEEDS_PER_USER", 10)

MENU_ADD_SOURCE = "menu_add_source"
MENU_MY_SOURCES = "menu_my_sources"
MENU_HELP = "menu_help"

WAITING_URL = 1


def _log_command_entry(command_name: str, update: Update, args: Optional[list[str]] = None) -> None:
    """Registra una traza uniforme al entrar en comandos y callbacks."""
    user = update.effective_user
    logger.debug(
        "Entering handler",
        handler=command_name,
        user_id=user.id if user else None,
        username=user.username if user else None,
        args=args or [],
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /start."""
    _log_command_entry("start_command", update, context.args)
    await update.message.reply_text(
        _get_main_menu_text(),
        reply_markup=_build_main_menu_markup(),
    )


def _get_main_menu_text() -> str:
    """Texto principal mostrado al usuario al iniciar el bot."""
    return "🏠 OportunidadBot\n\n¿Qué quieres hacer?"


def _build_main_menu_markup() -> InlineKeyboardMarkup:
    """Construye el menú principal de navegación del bot."""
    keyboard = [
        [InlineKeyboardButton("➕ Añadir fuente", callback_data=MENU_ADD_SOURCE)],
        [InlineKeyboardButton("📂 Mis fuentes", callback_data=MENU_MY_SOURCES)],
        [InlineKeyboardButton("❓ Ayuda", callback_data=MENU_HELP)],
    ]
    return InlineKeyboardMarkup(keyboard)


def _get_add_source_prompt_text() -> str:
    """Texto guía para solicitar una URL al usuario."""
    return (
        "Pega la URL que deseas monitorizar.\n\n"
        "Ejemplos:\n\n"
        "https://reddit.com/r/murcia\n\n"
        "https://reddit.com/r/alicante\n\n"
        "Escribe /cancel para cancelar."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /help."""
    _log_command_entry("help_command", update, context.args)
    await update.message.reply_text(_get_help_text(), parse_mode="Markdown")


def _get_help_text() -> str:
    """Texto de ayuda con los comandos actualmente soportados."""
    return (
        "📋 **Lista de comandos disponibles:**\n\n"
        "/start - Mostrar menú principal\n"
        "/help - Mostrar esta ayuda\n"
        "/addgroup [URL] - Añadir un feed a partir de una URL soportada"
    )


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
    """Añade un feed para el usuario actual a partir de una URL soportada."""
    _log_command_entry("addgroup_command", update, context.args)
    if not context.args:
        await update.message.reply_text("Uso: /addgroup [URL]")
        return

    raw_url = " ".join(context.args).strip()
    await _addgroup_from_raw_url(update, raw_url)


async def _addgroup_from_raw_url(update: Update, raw_url: str) -> None:
    """Ejecuta el flujo de alta de feed desde una URL en texto plano."""
    user_id = _get_user_id(update)
    if not user_id:
        await update.message.reply_text("No pude identificar tu usuario. Inténtalo de nuevo.")
        return

    if not raw_url:
        await update.message.reply_text("La URL del feed no puede estar vacía.")
        return

    normalized_url = _normalize_feed_url(raw_url)
    logger.debug("URL normalized for addgroup", raw_url=raw_url, normalized_url=normalized_url)
    parsed = urlparse(normalized_url)
    if not parsed.scheme or not parsed.netloc:
        logger.warning("URL de feed inválida recibida: {}", raw_url)
        await update.message.reply_text("La URL no tiene un formato válido. Prueba con una dirección completa como https://ejemplo.com/feed")
        return

    resolved_feed_url = rsshub_resolver.resolve(normalized_url)
    if resolved_feed_url is None:
        logger.warning("No se pudo resolver una URL RSSHub para: {}", normalized_url)
        await update.message.reply_text("La plataforma aún no está soportada para convertirla a RSS automáticamente.")
        return

    logger.info("URL resolved to RSSHub", original_url=normalized_url, resolved_feed_url=resolved_feed_url)

    try:
        existing_feeds = _fetch_user_feeds(user_id)
        existing_urls = {
            _normalize_feed_url(str(feed.get("url", "")))
            for feed in existing_feeds
            if feed.get("url")
        }

        if resolved_feed_url in existing_urls:
            logger.info("Feed already registered", user_id=user_id, feed_url=resolved_feed_url)
            await update.message.reply_text("Este feed ya está registrado en tus grupos.")
            return

        if len(existing_feeds) >= MAX_FEEDS_PER_USER:
            await update.message.reply_text(
                f"Has alcanzado el límite de {MAX_FEEDS_PER_USER} feeds por usuario. Elimina uno antes de añadir otro."
            )
            return

        validation = feed_parser.validate_feed_source(resolved_feed_url)
        if not validation.get("valid", False):
            logger.warning("El feed no pudo validarse: {} - {}", resolved_feed_url, validation.get("error"))
            await update.message.reply_text(
                "No pude validar ese RSS. " + (validation.get("error") or "Comprueba que la URL sea un feed válido y accesible.")
            )
            return

        database.add_user(user_id, update.effective_user.username or "")
        feed_id = database.add_feed(user_id=user_id, url=resolved_feed_url)
        if not feed_id:
            logger.error(
                "No se pudo guardar el feed en Supabase para el usuario {user_id}: {normalized_url}",
                user_id=user_id,
                normalized_url=resolved_feed_url,
            )
            await update.message.reply_text("No se pudo guardar el feed en este momento. Inténtalo más tarde.")
            return

        logger.info(
            "Feed añadido por usuario {user_id}: {normalized_url}",
            user_id=user_id,
            normalized_url=resolved_feed_url,
        )
        await update.message.reply_text(
            f"✅ Feed añadido correctamente.\nID: {feed_id}\nURL: {resolved_feed_url}"
        )
    except Exception as exc:
        logger.exception(
            "Error al añadir un feed para el usuario {user_id}",
            user_id=user_id,
        )
        await update.message.reply_text("No se pudo guardar el feed en este momento. Inténtalo más tarde.")


async def cancel_add_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela el flujo guiado para alta de fuente."""
    _log_command_entry("cancel_add_source", update, context.args)
    await update.message.reply_text("Operación cancelada. Puedes volver al menú con /start.")
    return ConversationHandler.END


async def waiting_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe y procesa la URL pegada por el usuario en el flujo guiado."""
    _log_command_entry("waiting_url_message", update)
    raw_url = (update.message.text or "").strip()
    await _addgroup_from_raw_url(update, raw_url)
    return ConversationHandler.END


async def groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista los feeds del usuario actual."""
    _log_command_entry("groups_command", update, context.args)
    user_id = _get_user_id(update)
    if not user_id:
        await update.message.reply_text("No pude identificar tu usuario. Inténtalo de nuevo.")
        return

    try:
        feeds = _fetch_user_feeds(user_id)
        logger.debug("User feeds loaded", user_id=user_id, feed_count=len(feeds))
        if not feeds:
            await update.message.reply_text("No tienes feeds registrados aún. Usa /addgroup para añadir uno.")
            return

        lines = ["📡 Tus feeds:"]
        for feed in feeds:
            status = "🟢 Activo" if feed.get("is_active", True) else "🟡 Pausado"
            lines.append(f"- ID {feed.get('id')}: {status}\n  {feed.get('url', 'Sin URL')}")

        await update.message.reply_text("\n".join(lines))
    except Exception as exc:
        logger.exception(
            "Error al listar feeds del usuario {user_id}",
            user_id=user_id,
        )
        await update.message.reply_text("No se pudieron cargar tus feeds en este momento.")


async def removegroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Elimina un feed RSS del usuario actual."""
    _log_command_entry("removegroup_command", update, context.args)
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
        logger.info(
            "Feed eliminado por usuario {user_id}: {feed_id}",
            user_id=user_id,
            feed_id=feed_id,
        )
        await update.message.reply_text("🗑️ Feed eliminado correctamente.")
    except Exception as exc:
        logger.exception(
            "Error al eliminar el feed {feed_id} del usuario {user_id}",
            feed_id=feed_id,
            user_id=user_id,
        )
        await update.message.reply_text("No se pudo eliminar el feed en este momento.")


async def pausegroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pausa un feed RSS del usuario actual."""
    _log_command_entry("pausegroup_command", update, context.args)
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
        logger.info(
            "Feed pausado por usuario {user_id}: {feed_id}",
            user_id=user_id,
            feed_id=feed_id,
        )
        await update.message.reply_text("⏸️ Feed pausado correctamente.")
    except Exception as exc:
        logger.exception(
            "Error al pausar el feed {feed_id} del usuario {user_id}",
            feed_id=feed_id,
            user_id=user_id,
        )
        await update.message.reply_text("No se pudo pausar el feed en este momento.")


async def resumegroup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reanuda un feed RSS del usuario actual."""
    _log_command_entry("resumegroup_command", update, context.args)
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
        logger.info(
            "Feed reactivado por usuario {user_id}: {feed_id}",
            user_id=user_id,
            feed_id=feed_id,
        )
        await update.message.reply_text("▶️ Feed reactivado correctamente.")
    except Exception as exc:
        logger.exception(
            "Error al reactivar el feed {feed_id} del usuario {user_id}",
            feed_id=feed_id,
            user_id=user_id,
        )
        await update.message.reply_text("No se pudo reactivar el feed en este momento.")


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde con el mismo texto que el usuario (solo para pruebas)."""
    _log_command_entry("echo_message", update)
    text = update.message.text
    await update.message.reply_text(f"Echo: {text}")


async def handle_quick_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Responde al botón de añadir un grupo o feed."""
    _log_command_entry("handle_quick_add", update)
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(_get_add_source_prompt_text())
    return WAITING_URL


async def handle_tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra un tutorial breve para el usuario."""
    _log_command_entry("handle_tutorial", update)
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
    _log_command_entry("handle_remind_later", update)
    query = update.callback_query
    await query.answer("Te recordaremos más tarde.")
    await query.message.reply_text(
        "Perfecto. Te avisaremos de nuevo más tarde cuando haya una oportunidad relevante."
    )


async def handle_generate_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja la generación de respuesta para una alerta concreta."""
    _log_command_entry("handle_generate_alert", update)
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


async def handle_menu_add_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la acción del menú principal para añadir una fuente."""
    _log_command_entry("handle_menu_add_source", update)
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(_get_add_source_prompt_text())
    return WAITING_URL


async def handle_menu_my_sources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja la acción del menú principal para listar fuentes del usuario."""
    _log_command_entry("handle_menu_my_sources", update)
    query = update.callback_query
    await query.answer("Función en preparación")
    await query.message.reply_text("La opción Mis fuentes desde menú estará disponible pronto.")


async def handle_menu_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja la acción de ayuda desde el menú principal."""
    _log_command_entry("handle_menu_help", update)
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(_get_help_text(), parse_mode="Markdown")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra errores y notifica al desarrollador (opcional)."""
    logger.debug("Entering error_handler")
    logger.error(f"Excepción mientras se manejaba una actualización: {context.error}")
    if update and hasattr(update, "message") and update.message:
        await update.message.reply_text("Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde.")


def register_handlers(application: Application) -> None:
    """Registra los handlers del bot en la aplicación."""
    logger.info("Registering Telegram handlers")
    add_source_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_menu_add_source, pattern=f"^{MENU_ADD_SOURCE}$"),
            CallbackQueryHandler(handle_quick_add, pattern="^quick_add$"),
        ],
        states={
            WAITING_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, waiting_url_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add_source)],
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addgroup", addgroup_command))
    application.add_handler(add_source_conversation)
    application.add_handler(CallbackQueryHandler(handle_menu_my_sources, pattern=f"^{MENU_MY_SOURCES}$"))
    application.add_handler(CallbackQueryHandler(handle_menu_help, pattern=f"^{MENU_HELP}$"))
    application.add_handler(CallbackQueryHandler(handle_tutorial, pattern="^tutorial$"))
    application.add_handler(CallbackQueryHandler(handle_remind_later, pattern="^remind_later$"))
    application.add_handler(CallbackQueryHandler(handle_generate_alert, pattern=r"^generate_alert_(\d+)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    application.add_error_handler(error_handler)
    logger.info("Telegram handlers registered successfully")
