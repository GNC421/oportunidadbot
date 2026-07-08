from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from loguru import logger


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
        "/ping - Verificar latencia (para pruebas)\n\n"
        "Próximamente más funcionalidades..."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


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
    application.add_handler(CallbackQueryHandler(handle_quick_add, pattern="^quick_add$"))
    application.add_handler(CallbackQueryHandler(handle_tutorial, pattern="^tutorial$"))
    application.add_handler(CallbackQueryHandler(handle_remind_later, pattern="^remind_later$"))
    application.add_handler(CallbackQueryHandler(handle_generate_alert, pattern=r"^generate_alert_(\d+)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    application.add_error_handler(error_handler)
