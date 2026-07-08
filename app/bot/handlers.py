from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
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


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra errores y notifica al desarrollador (opcional)."""
    logger.error(f"Excepción mientras se manejaba una actualización: {context.error}")
    if update and hasattr(update, "message") and update.message:
        await update.message.reply_text("Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde.")


def register_handlers(application: Application) -> None:
    """Registra los handlers del bot en la aplicación."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    application.add_error_handler(error_handler)
