import logging
from typing import Dict, List, Optional

from app.database import get_active_feeds, save_alert
from app.services.alert_service import send_alert
from app.services.feed_parser import check_user_feeds

logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordina el flujo RSS -> parser -> alerta."""

    def _build_alert_payload(self, alert: Dict) -> Dict:
        """Normaliza la salida del parser a un formato compatible con el resto del sistema."""
        return {
            "title": alert.get("title", ""),
            "summary": alert.get("summary", ""),
            "link": alert.get("url", ""),
            "author": alert.get("author", ""),
            "question": alert.get("question", ""),
        }

    async def _handle_alert(self, user_id: int, feed_id: int, alert: Dict) -> None:
        """Guarda y envía una alerta para una entrada detectada."""
        payload = self._build_alert_payload(alert)

        alert_id = save_alert(
            user_id=user_id,
            feed_id=feed_id,
            post_data=payload,
        )
        logger.info("Alerta guardada (%s)", alert_id)

        await send_alert(user_id=user_id, post_data=payload, feed_id=feed_id)

    async def run_feed_checks(self) -> int:
        logger.info("=" * 60)
        logger.info("Iniciando comprobación de feeds")
        logger.info("=" * 60)

        feeds = []
        try:
            feeds = get_active_feeds()
        except Exception:
            logger.exception("No se pudieron obtener los feeds")
            return 0

        if not feeds:
            logger.info("No hay feeds disponibles para revisar")
            return 0

        total_alerts = 0

        for feed in feeds:
            try:
                feed_id = feed.get("id")
                user_id = feed.get("user_id")
                url = feed.get("url")

                if not feed_id or not user_id or not url:
                    logger.warning("Feed incompleto, se omite: %s", feed)
                    continue

                logger.info("Procesando feed %s", url)
                alerts = check_user_feeds(feed)

                if not alerts:
                    logger.info("No hay novedades para %s", url)
                    continue

                logger.info("Encontradas %s alertas nuevas", len(alerts))

                for alert in alerts:
                    try:
                        await self._handle_alert(user_id, feed_id, alert)
                        total_alerts += 1
                    except Exception:
                        logger.exception("Error procesando alerta")

            except Exception:
                logger.exception("Error procesando feed %s", feed.get("url"))

        logger.info("Finalizada comprobación. Alertas enviadas: %s", total_alerts)
        return total_alerts


orchestrator = Orchestrator()


async def run_feed_checks() -> int:
    return await orchestrator.run_feed_checks()