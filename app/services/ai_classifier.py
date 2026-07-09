import asyncio
import time
from collections import OrderedDict
from typing import Optional

from app.services.prompts import REAL_ESTATE_CLASSIFIER_PROMPT

import httpx
from loguru import logger

from app.config import settings


class AIClassifier:
    """Encapsula la clasificación de oportunidades mediante IA."""

    def __init__(self) -> None:
        self._api_key: Optional[str] = settings.NVIDIA_API_KEY
        self._base_url: str = settings.NVIDIA_BASE_URL
        self._model: str = settings.NVIDIA_MODEL
        self._ai_enabled: bool = settings.AI_ENABLED
        self._timeout: float = 20.0
        self._max_retries: int = 3
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: OrderedDict[str, bool] = OrderedDict()
        self._cache_limit: int = 1000
        self._metrics = {
            "calls": 0,
            "responses_yes": 0,
            "responses_no": 0,
            "errors": 0,
        }

    async def is_business_opportunity(self, title: str, summary: str) -> bool:
        """Devuelve True si el texto parece una oportunidad de negocio relevante."""
        start_time = time.perf_counter()
        self._metrics["calls"] += 1
        try:
            if not self._ai_enabled:
                logger.info("IA deshabilitada; se devuelve True para no interrumpir el flujo")
                return True

            if not title and not summary:
                logger.warning("No se recibió contenido para clasificar")
                return False

            if not self._api_key:
                logger.warning("No hay API key de NVIDIA configurada; se devuelve False")
                return False

            cache_key = self._build_cache_key(title, summary)
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                logger.info("Clasificación IA servida desde caché", cache_key=cache_key)
                self._log_metrics(start_time, cached_result)
                return cached_result

            response = await self._call_nvidia(title, summary)
            result = self._parse_response(response)
            self._set_cached_result(cache_key, result)
            self._log_metrics(start_time, result)
            return result
        except Exception as exc:
            self._metrics["errors"] += 1
            logger.exception(f"Error clasificando oportunidad con IA: {exc}")
            self._log_metrics(start_time, False)
            return False

    def _log_metrics(self, start_time: float, result: bool) -> None:
        """Registra métricas de desempeño y resultados del clasificador."""
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
        if result:
            self._metrics["responses_yes"] += 1
        else:
            self._metrics["responses_no"] += 1

        logger.bind(
            elapsed_ms=elapsed_ms,
            calls=self._metrics["calls"],
            responses_yes=self._metrics["responses_yes"],
            responses_no=self._metrics["responses_no"],
            errors=self._metrics["errors"],
        ).info("Métrica AIClassifier")

    def _build_cache_key(self, title: str, summary: str) -> str:
        """Construye la clave de caché a partir del contenido completo."""
        return f"{title or ''}{summary or ''}"

    def _get_cached_result(self, cache_key: str) -> Optional[bool]:
        """Devuelve un resultado cacheado si existe."""
        if cache_key not in self._cache:
            return None

        self._cache.move_to_end(cache_key)
        return self._cache[cache_key]

    def _set_cached_result(self, cache_key: str, result: bool) -> None:
        """Guarda un resultado en la caché LRU."""
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
        self._cache[cache_key] = result
        if len(self._cache) > self._cache_limit:
            self._cache.popitem(last=False)

    async def _get_client(self) -> httpx.AsyncClient:
        """Reutiliza un cliente HTTP asíncrono para todas las peticiones."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self._timeout))
        return self._client

    async def close(self) -> None:
        """Cierra el cliente HTTP reutilizado."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def _call_nvidia(self, title: str, summary: str) -> Optional[str]:
        """Realiza la llamada a la API de NVIDIA y devuelve el texto generado."""
        if not self._api_key:
            logger.warning("No hay API key de NVIDIA configurada; se omite la llamada")
            return None

        url = f"{self._base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": REAL_ESTATE_CLASSIFIER_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"Título: {title}\n\nContenido: {summary}",
                },
            ],
            "temperature": 0,
            "max_tokens": 8,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        last_error: Optional[Exception] = None
        client = await self._get_client()

        for attempt in range(self._max_retries):
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    logger.warning("La respuesta de NVIDIA no contiene choices")
                    return None

                message = choices[0].get("message", {})
                content = message.get("content") or ""
                return str(content).strip()
            except Exception as exc:
                last_error = exc
                logger.warning(f"Intento {attempt + 1}/{self._max_retries} fallido al llamar a NVIDIA: {exc}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))

        logger.exception(f"Error final al llamar a NVIDIA: {last_error}")
        return None

    def _parse_response(self, response: Optional[str]) -> bool:
        """Extrae el resultado booleano del texto generado por el modelo."""
        if not response:
            return False

        try:
            content = response.strip().lower()
            return content == "true"
        except Exception as exc:
            logger.exception(f"Error parseando la respuesta de IA: {exc}")
            return False


classifier = AIClassifier()
