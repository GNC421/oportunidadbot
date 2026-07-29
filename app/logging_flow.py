from loguru import logger
from typing import Optional


def flow_log(step: int, total: int, message: str, level: Optional[str] = "info") -> None:
    """Registra un mensaje con formato de flujo: [step/total] message.

    level puede ser 'info', 'debug', 'warning', 'error'.
    """
    text = f"[{step}/{total}] {message}"
    if level == "debug":
        logger.debug(text)
    elif level == "warning":
        logger.warning(text)
    elif level == "error":
        logger.error(text)
    else:
        logger.info(text)
