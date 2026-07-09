import logging
from typing import Dict

from app.database import (
    get_active_feeds,
    get_alert_by_url,
    mark_alert_sent,
    save_alert,
    update_feed_last_check,
)
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
        """Procesa una oportunidad detectada en el orden pedido por el flujo."""
        payload = self._build_alert_payload(alert)
        post_url = payload.get("link", "")

        if not post_url:
            logger.warning("Oportunidad sin URL, se omite")
            return

        existing = get_alert_by_url(post_url)
        if existing:
            logger.info(f"Oportunidad ya registrada previamente: {post_url}")
            return

        alert_id = save_alert(
            user_id=user_id,
            feed_id=feed_id,
            post_data=payload,
        )
        logger.info(f"Alerta guardada ({alert_id})")

        await send_alert(user_id=user_id, post_data=payload, feed_id=feed_id)

        if alert_id:
            mark_alert_sent(alert_id)

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
                    logger.warning(f"Feed incompleto, se omite: {feed}")
                    continue

                logger.info(f"Procesando feed {url}")
                opportunities = check_user_feeds(feed)

                if not opportunities:
                    logger.info(f"No hay novedades para {url}")
                    update_feed_last_check(feed_id)
                    continue

                logger.info(f"Encontradas {len(opportunities)} oportunidades nuevas")

                for opportunity in opportunities:
                    try:
                        await self._handle_alert(user_id, feed_id, opportunity)
                        total_alerts += 1
                    except Exception:
                        logger.exception("Error procesando oportunidad")

                update_feed_last_check(feed_id)

            except Exception:
                logger.exception(f"Error procesando feed {feed.get('url')}")

        logger.info(f"Finalizada comprobación. Alertas enviadas: {total_alerts}")
        return total_alerts


orchestrator = Orchestrator()


async def run_feed_checks() -> int:
    return await orchestrator.run_feed_checks()