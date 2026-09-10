import asyncio
import json
import time
from collections import OrderedDict
from typing import Iterable, Optional

import httpx

from app.services.prompts import REAL_ESTATE_CLASSIFIER_PROMPT

from loguru import logger

from app.config import settings
from app.debug.trace_service import get_trace_service
from app.debug.trace_models import EventType


class AIClassifier:
    """Encapsula la clasificación de oportunidades mediante IA."""

    def __init__(self) -> None:
        self._api_key: Optional[str] = settings.NVIDIA_API_KEY
        self._base_url: str = settings.NVIDIA_BASE_URL
        self._model: str = settings.NVIDIA_MODEL
        self._ai_enabled: bool = settings.AI_ENABLED
        self._timeout: float = 20.0
        self._max_retries: int = 3
        self._cache: OrderedDict[str, bool] = OrderedDict()
        self._cache_limit: int = 1000
        self._metrics = {
            "calls": 0,
            "responses_yes": 0,
            "responses_no": 0,
            "errors": 0,
        }
        self._endpoint = f"{self._base_url.rstrip('/')}/chat/completions" if self._base_url else None

    async def is_business_opportunity(self, title: str, summary: str) -> bool:
        """Devuelve True si el texto parece una oportunidad de negocio relevante."""
        start_time = time.perf_counter()
        trace = get_trace_service()
        event_id = await trace.start(type=EventType.AI, name="AI Classification", input_payload={"title": title, "summary": summary, "model": self._model})
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
            # record outcome into trace
            await trace.success(event_id, output_payload={"full_response": response, "parsed": result}, metadata={"model": self._model, "elapsed_s": round((time.perf_counter() - start_time), 3)})
            return result
        except Exception as exc:
            self._metrics["errors"] += 1
            logger.exception(f"Error clasificando oportunidad con IA: {exc}")
            self._log_metrics(start_time, False)
            # record error into trace
            await trace.error(event_id, error=str(exc))
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

    @staticmethod
    def _extract_delta_content(chunk: dict) -> Optional[str]:
        """Extrae el texto incremental de un fragmento SSE de NVIDIA."""
        try:
            choices = chunk.get("choices") or []
            if not choices:
                return None
            delta = choices[0].get("delta") or {}
            return delta.get("content")
        except Exception:
            return None

    def _parse_sse_lines(self, lines: Iterable[object]) -> str:
        """Procesa líneas SSE (`data: ...` / `[DONE]`) y devuelve el texto concatenado."""
        content_parts: list[str] = []
        for raw_line in lines:
            if raw_line is None:
                continue
            line = raw_line.decode("utf-8", errors="ignore") if isinstance(raw_line, bytes) else str(raw_line)
            line = line.strip()
            if not line:
                continue
            if not line.startswith("data:"):
                continue
            data_str = line[len("data:"):].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                logger.warning("Fragmento SSE de NVIDIA no es JSON válido; se omite")
                continue
            delta_content = self._extract_delta_content(chunk)
            if delta_content:
                content_parts.append(delta_content)
        return "".join(content_parts).strip()

    async def _call_nvidia(self, title: str, summary: str) -> Optional[str]:
        """Realiza la llamada HTTP directa (SSE) a NVIDIA NIM y devuelve el texto generado."""
        if not self._api_key:
            logger.warning("No hay API key de NVIDIA configurada; se omite la llamada")
            return None

        if not self._endpoint:
            logger.warning("No hay NVIDIA_BASE_URL configurada; se omite la llamada")
            return None

        messages = [
            {"role": "system", "content": REAL_ESTATE_CLASSIFIER_PROMPT},
            {"role": "user", "content": f"Título: {title}\n\nContenido: {summary}"},
        ]

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }

        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries):
            request_start = time.perf_counter()
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    with client.stream("POST", self._endpoint, json=payload, headers=headers) as response:
                        if response.status_code >= 400:
                            response.read()
                            logger.warning(
                                "NVIDIA respondió con error HTTP",
                                status_code=response.status_code,
                                model=self._model,
                                endpoint=self._endpoint,
                            )
                            if response.status_code in (401, 403):
                                # Credenciales inválidas: reintentar no lo arreglará
                                return None
                            response.raise_for_status()

                        content = self._parse_sse_lines(response.iter_lines())
                        elapsed = round(time.perf_counter() - request_start, 3)
                        logger.debug(
                            "Llamada a NVIDIA completada",
                            model=self._model,
                            endpoint=self._endpoint,
                            status_code=response.status_code,
                            elapsed_s=elapsed,
                        )

                        if not content:
                            logger.warning("NVIDIA devolvió una respuesta vacía", model=self._model)
                            return None
                        return content
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning(f"Timeout llamando a NVIDIA (intento {attempt + 1}/{self._max_retries})")
            except httpx.HTTPStatusError as exc:
                last_error = exc
                logger.warning(f"Error HTTP llamando a NVIDIA (intento {attempt + 1}/{self._max_retries}): {exc}")
            except httpx.RequestError as exc:
                last_error = exc
                logger.warning(f"Error de conexión llamando a NVIDIA (intento {attempt + 1}/{self._max_retries}): {exc}")
            except Exception as exc:
                last_error = exc
                logger.warning(f"Intento {attempt + 1}/{self._max_retries} fallido llamando a NVIDIA: {exc}")

            if attempt < self._max_retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))

        logger.exception(f"Error final al llamar a NVIDIA: {last_error}")
        return None

    def _parse_response(self, response: Optional[str]) -> bool:
        """Extrae el resultado booleano del texto generado por el modelo."""
        if not response:
            return False

        try:
            import unicodedata
            import re

            content = response.strip().lower()
            # remove accents (e.g., 'sí' -> 'si')
            content = "".join(ch for ch in unicodedata.normalize("NFD", content) if unicodedata.category(ch) != "Mn")

            # canonical affirmative / negative tokens
            affirmatives = {"true", "yes", "y", "si", "s", "1", "verdadero", "v", "sí"}
            negatives = {"false", "no", "n", "0", "f", "falso"}

            # exact match
            if content in affirmatives:
                return True
            if content in negatives:
                return False

            # check first token (model may return sentences like "SI es relevante" or "No, irrelevante")
            first = content.split()[0] if content else ""
            if first in affirmatives:
                return True
            if first in negatives:
                return False

            # fallback: look for affirmative words anywhere
            for a in affirmatives:
                # match whole words only to avoid substring false-positives
                if re.search(r"\b" + re.escape(a) + r"\b", content):
                    return True
            return False
        except Exception as exc:
            logger.exception(f"Error parseando la respuesta de IA: {exc}")
            return False

    def clear_cache(self) -> int:
        """Vacía la caché en memoria y devuelve cuántas entradas había."""
        n = len(self._cache)
        try:
            self._cache.clear()
        except Exception:
            # ensure no exceptions bubble up
            pass
        return n


classifier = AIClassifier()
