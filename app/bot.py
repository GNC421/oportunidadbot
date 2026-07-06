import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from .config import settings
from loguru import logger

# Configurar loguru para que también capture logs de telegram
logger.add("logs/bot.log", rotation="500 MB", level=settings.LOG_LEVEL)

_application: Optional[Application] = None
application: Optional[Application] = None


def _build_application() -> Application:
    """Construye la instancia de Application con handlers configurados."""
    app = Application.builder().token(settings.BOT_TOKEN).build()

    # --- Handlers de comandos ---
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    # --- Handler para mensajes de texto no comandos (opcional) ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))

    # --- Manejo global de errores ---
    app.add_error_handler(error_handler)

    return app


# Función para crear o recuperar la única instancia del bot
def create_application() -> Application:
    """
    Crea y devuelve la instancia única de Application del bot.
    Si ya existe, la reutiliza para evitar duplicados.
    """
    global _application, application
    if _application is None:
        _application = _build_application()
        application = _application
    return _application


def get_application() -> Application:
    """Devuelve la instancia singleton del bot."""
    return create_application()


# Crear la instancia al importar el módulo para que sea accesible globalmente.
application = create_application()


# --- Comandos ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /start."""
    user = update.effective_user
    welcome_text = (
        f"¡Hola {user.first_name}! 👋\n\n"
        "Soy **OportunidadBot**, tu asistente para encontrar oportunidades.\n"
        "Usa /help para ver qué puedo hacer."
    )
    # Ejemplo de botón inline
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


# --- Handler de mensajes de texto (ejemplo) ---

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde con el mismo texto que el usuario (solo para pruebas)."""
    text = update.message.text
    await update.message.reply_text(f"Echo: {text}")


# --- Manejador de errores ---

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra errores y notifica al desarrollador (opcional)."""
    logger.error(f"Excepción mientras se manejaba una actualización: {context.error}")
    # Opcional: enviar mensaje al usuario sobre el error
    if update and hasattr(update, "message") and update.message:
        await update.message.reply_text("Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde.")