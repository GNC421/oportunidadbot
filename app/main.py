import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from telegram import Update
from telegram.ext import Application
import os

from .config import settings
from .bot import create_application
from .database import init_db
from .jobs.scheduler import start_scheduler, stop_scheduler

# Variable global para mantener la aplicación del bot
bot_app: Application = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan de FastAPI: se ejecuta al iniciar y al cerrar la aplicación.
    Inicializa el bot, configura webhook o polling, y programa tareas.
    """
    global bot_app
    logger.info("🚀 Iniciando OportunidadBot...")
    logger.debug("FastAPI lifespan startup entered")

    # 1. Crear la aplicación del bot
    bot_app = create_application()
    logger.debug("Telegram application created in lifespan")

    # 2. Verificar conexión con Supabase
    if not init_db():
        raise RuntimeError("No se pudo conectar a Supabase")
    logger.info("📦 Conexión a Supabase lista")

    # 3. Configurar modo de operación (webhook o polling)
    if settings.USE_WEBHOOK:
        # Modo webhook (producción)
        if not settings.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL es requerido cuando USE_WEBHOOK=True")
        # Iniciar la aplicación (necesario para el webhook)
        await bot_app.initialize()
        await bot_app.start()
        logger.debug("Telegram application initialized in webhook mode")
        # Configurar webhook en Telegram
        webhook_url = f"{settings.WEBHOOK_URL}/webhook"
        await bot_app.bot.set_webhook(
            url=webhook_url,
            secret_token=settings.WEBHOOK_SECRET,  # opcional, para validar
        )
        logger.info(f"🔗 Webhook configurado en {webhook_url}")
    else:
        # Modo polling (desarrollo)
        # Iniciar la aplicación y el polling como tarea en segundo plano
        await bot_app.initialize()
        await bot_app.start()
        logger.debug("Telegram application initialized in polling mode")
        # Iniciar polling en una tarea asíncrona para no bloquear el servidor
        asyncio.create_task(bot_app.updater.start_polling())
        logger.info("📡 Polling iniciado en segundo plano")

    # 4. Programar tareas periódicas (ejemplo)
    # La JobQueue se inicia automáticamente con bot_app.start()
    # Podemos añadir un trabajo de ejemplo:
    # async def ejemplo_job(context):
    #     logger.info("Tarea programada ejecutada")
    # bot_app.job_queue.run_repeating(ejemplo_job, interval=60, first=10)

    # 4. Iniciar scheduler si está disponible
    start_scheduler()
    logger.debug("Scheduler start requested from lifespan")

    logger.info("✅ Bot listo y funcionando")
    yield  # Aquí se ejecuta la aplicación FastAPI

    # Limpieza al apagar
    logger.info("🛑 Apagando OportunidadBot...")
    logger.debug("FastAPI lifespan shutdown entered")
    if bot_app:
        if settings.USE_WEBHOOK:
            await bot_app.bot.delete_webhook()
        await bot_app.stop()
        await bot_app.shutdown()

    stop_scheduler()
    logger.debug("Scheduler stop requested from lifespan")
    logger.info("👋 Bot detenido correctamente")

# Crear la aplicación FastAPI con el lifespan
app = FastAPI(
    title="OportunidadBot",
    description="Bot de Telegram para oportunidades",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Endpoint para healthchecks (Railway, etc.)"""
    logger.debug("health_check endpoint called")
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook_endpoint(request: Request) -> JSONResponse:
    """
    Endpoint que recibe las actualizaciones de Telegram (webhook).
    Verifica el secret_token y procesa la actualización.
    """
    global bot_app
    logger.debug("webhook_endpoint called")

    # Validar secret_token si está configurado
    if settings.WEBHOOK_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if token != settings.WEBHOOK_SECRET:
            logger.warning("Secret token inválido")
            raise HTTPException(status_code=403, detail="Invalid secret token")

    try:
        # Obtener el cuerpo de la solicitud
        data = await request.json()
        logger.debug("Webhook payload received", keys=list(data.keys()) if isinstance(data, dict) else [])
        # Crear el objeto Update
        update = Update.de_json(data, bot_app.bot)
        # Procesar la actualización
        await bot_app.process_update(update)
        logger.debug("Webhook update processed successfully")
        return JSONResponse(content={"ok": True})
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

# Opcional: endpoint para pruebas
@app.get("/ping")
async def ping():
    logger.debug("ping endpoint called")
    return {"ping": "pong"}

# Punto de entrada para ejecutar con uvicorn directamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=not settings.USE_WEBHOOK,  # recarga solo en desarrollo
    )