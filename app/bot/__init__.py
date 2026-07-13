from typing import Optional

from telegram.ext import Application
from loguru import logger

from ..config import settings
from .handlers import register_handlers

logger.add("logs/bot.log", rotation="500 MB", level=settings.LOG_LEVEL)

_application: Optional[Application] = None
application: Optional[Application] = None


def _build_application() -> Application:
    """Construye la instancia de Application con handlers configurados."""
    logger.debug("Building Telegram Application instance")
    app = Application.builder().token(settings.BOT_TOKEN).build()
    register_handlers(app)
    logger.info("Telegram Application instance built")
    return app


def create_application() -> Application:
    """
    Crea y devuelve la instancia única de Application del bot.
    Si ya existe, la reutiliza para evitar duplicados.
    """
    global _application, application
    if _application is None:
        logger.info("Creating singleton Telegram Application")
        _application = _build_application()
        application = _application
    else:
        logger.debug("Reusing existing Telegram Application singleton")
    return _application


def get_application() -> Application:
    """Devuelve la instancia singleton del bot."""
    logger.debug("get_application called")
    return create_application()


application = create_application()
