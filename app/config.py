from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""
    
    BOT_TOKEN: str = Field(..., description="Token del bot de Telegram")
    
    # Webhook
    USE_WEBHOOK: bool = Field(False, description="Usar webhook (True) o polling (False)")
    WEBHOOK_URL: Optional[str] = Field(None, description="URL pública del webhook (ej: https://tu-dominio.railway.app/webhook)")
    WEBHOOK_SECRET: Optional[str] = Field(None, description="Secreto para validar el webhook (opcional)")
    
    # Servidor - Railway provee PORT automáticamente
    PORT: int = Field(int(os.getenv("PORT", 8000)), description="Puerto donde corre FastAPI")
    HOST: str = Field("0.0.0.0", description="Host de escucha")
    
    # Base de datos (SQLite)
    DATABASE_URL: str = Field("sqlite+aiosqlite:///./oportunidad.db", description="URL de la base de datos")

    # Supabase
    SUPABASE_URL: Optional[str] = Field(None, description="URL del proyecto de Supabase")
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = Field(None, description="Clave publishable de Supabase")
    SUPABASE_KEY: Optional[str] = Field(None, description="Clave de servicio de Supabase")
    SUPABASE_JWKS_URL: Optional[str] = Field(None, description="URL de JWKS de Supabase")
    
    # Logging
    LOG_LEVEL: str = Field("INFO", description="Nivel de logging")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()