import asyncio
import time
from collections import OrderedDict
from typing import Optional
import inspect

from app.services.prompts import REAL_ESTATE_CLASSIFIER_PROMPT

from loguru import logger

from app.config import settings
from app.debug.trace_service import get_trace_service
from app.debug.trace_models import EventType

# Require OpenAI SDK for the classifier
try:
    from openai import OpenAI  # type: ignore
except Exception as exc:  # pragma: no cover - installation environment dependent
    OpenAI = None
    logger.error("OpenAI SDK no está instalado: %s", exc)


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
        # Enforce SDK usage
        if not OpenAI:
            raise ImportError("El paquete 'openai' no está instalado. Instálalo con 'pip install openai'.")

        try:
            self._sdk_client = OpenAI(base_url=self._base_url, api_key=self._api_key)
            logger.debug("OpenAI SDK client initialized", base_url=self._base_url)
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.exception(f"No se pudo inicializar OpenAI SDK: {exc}")
            raise

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

    async def _call_nvidia(self, title: str, summary: str) -> Optional[str]:
        """Realiza la llamada a la API de NVIDIA usando exclusivamente el SDK OpenAI y devuelve el texto generado."""
        if not self._api_key:
            logger.warning("No hay API key de NVIDIA configurada; se omite la llamada")
            return None

        messages = [
            {"role": "system", "content": REAL_ESTATE_CLASSIFIER_PROMPT},
            {"role": "user", "content": f"Título: {title}\n\nContenido: {summary}"},
        ]

        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries):
            try:
                # Llamada directa siguiendo tu ejemplo (OpenAI library)
                completion = self._sdk_client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=0.2,
                    top_p=0.7,
                    max_tokens=1024,
                    stream=True,
                )

                if inspect.isawaitable(completion):
                    completion = await completion

                content_parts: list[str] = []

                # Iterar los chunks como en tu snippet
                for chunk in completion:
                    try:
                        if getattr(chunk.choices[0].delta, "content", None) is not None:
                            content_parts.append(chunk.choices[0].delta.content)
                    except Exception:
                        # Fallback best-effort when chunk is a mapping
                        try:
                            if isinstance(chunk, dict):
                                choices = chunk.get("choices") or []
                                if choices and choices[0].get("delta", {}).get("content"):
                                    content_parts.append(choices[0]["delta"]["content"])
                        except Exception:
                            pass

                if content_parts:
                    return "".join(str(p) for p in content_parts).strip()

                # Fallback: tratar completion como respuesta no-stream
                resp = completion
                choices = None
                try:
                    choices = resp.get("choices") if hasattr(resp, "get") else getattr(resp, "choices", None)
                except Exception:
                    choices = getattr(resp, "choices", None)

                if not choices:
                    logger.warning("La respuesta SDK de NVIDIA no contiene choices")
                    return None

                first = choices[0]
                message = first.get("message") if isinstance(first, dict) else getattr(first, "message", None)
                content = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
                return str(content).strip()
            except Exception as exc:
                last_error = exc
                logger.warning(f"Intento {attempt + 1}/{self._max_retries} fallido con OpenAI SDK: {exc}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))

        logger.exception(f"Error final al llamar a NVIDIA via SDK: {last_error}")
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
