import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.orchestrator import run_feed_checks

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():

    logger.debug("start_scheduler called")
    logger.info("Configurando scheduler")

    scheduler.add_job(
        run_feed_checks,
        trigger=IntervalTrigger(minutes=15),
        id="feed_check_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    logger.info("Scheduler iniciado")
    logger.info("Comprobación automática de fuentes cada 15 minutos")


def stop_scheduler():

    logger.debug("stop_scheduler called")
    logger.info("Deteniendo scheduler")

    scheduler.shutdown(wait=False)

    logger.info("Scheduler detenido")