import asyncio
import feedparser
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Dict, Optional
from urllib.parse import urlparse
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.ai_classifier import classifier
from app.sources import SourceFactory
from app.logging_flow import flow_log
from app.debug.trace_service import get_trace_service
from app.debug.trace_models import EventType


def _maybe_run_async(coro):
    """Run an async coro in a sync context safely.

    If an event loop is already running, schedule the task and return an
    empty id (best-effort). Otherwise run with `asyncio.run` and return
    the result.
    """
    try:
        loop = asyncio.get_running_loop()
        # running loop found — schedule task and return empty placeholder
        loop.create_task(coro)
        return ""
    except RuntimeError:
        # no running loop
        return asyncio.run(coro)

def _parse_feed_source(url: str) -> Optional[Any]:
    """Obtiene el objeto parseado por feedparser para una URL dada."""
    logger.debug("_parse_feed_source called", url=url)
    try:
        return feedparser.parse(url)
    except Exception as exc:
        logger.error(f"Error al obtener el contenido del feed {url}: {exc}")
        return None


def validate_feed_source(url: str) -> Dict[str, Any]:
    """Valida si una URL apunta a una fuente usable y devuelve un resultado estructurado."""
    logger.debug("validate_feed_source called", url=url)
    trace = get_trace_service()
    event_id = ""
    try:
        event_id = _maybe_run_async(trace.start(type=EventType.RSS, name="Validate feed", input_payload={"url": url}))
    except Exception:
        # best-effort: tracing should not break validation
        event_id = ""
    if not url or not str(url).strip():
        logger.warning("Se recibió una URL de feed vacía")
        return {"valid": False, "error": "La URL del feed está vacía", "title": "", "entry_count": 0}

    normalized_url = str(url).strip()
    parsed_url = urlparse(normalized_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        logger.warning(f"URL de feed inválida: {normalized_url}")
        return {"valid": False, "error": "La URL del feed no tiene un formato válido", "title": "", "entry_count": 0}

    logger.info(f"Validando fuente: {normalized_url}")

    try:
        source = SourceFactory.from_url(normalized_url, parse_feed_fn=_parse_feed_source)
        return source.validate()
    except Exception as exc:
        logger.exception(f"Error inesperado validando fuente {normalized_url}: {exc}")
        try:
            # record error in trace
            _maybe_run_async(trace.error(event_id, error=str(exc)))
        except Exception:
            pass
        return {"valid": False, "error": "Error inesperado al validar el feed", "title": "", "entry_count": 0}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def parse_feed(url: str) -> Optional[List[Dict]]:
    """Parsea un feed RSS y devuelve las entradas."""
    logger.debug("parse_feed called", url=url)
    trace = get_trace_service()
    event_id = ""
    try:
        # start trace (use sync helper because parse_feed is sync)
        try:
            event_id = _maybe_run_async(trace.start(type=EventType.RSS, name="Parse feed", input_payload={"url": url}))
        except Exception:
            event_id = ""
        try:
            source = SourceFactory.from_url(url, parse_feed_fn=_parse_feed_source)
            items = source.parse_items(limit=10)
            if items is None:
                # record as success with zero entries
                _maybe_run_async(trace.success(event_id, output_payload={"entries": 0}))
                return None

            res = [item.to_dict() for item in items]
            _maybe_run_async(trace.success(event_id, output_payload={"entries": len(res)}))
            return res
        except Exception as exc_inner:
            # record inner error
            try:
                _maybe_run_async(trace.error(event_id, error=str(exc_inner)))
            except Exception:
                pass
            raise
    except Exception as exc:
        logger.error(f"Error al parsear feed {url}: {exc}")
        return None

def detect_question(text: str) -> bool:
    """Detecta si un texto parece una oportunidad de negocio mediante IA."""
    logger.debug("detect_question called", text_length=len(text) if text else 0)
    if not text:
        return False

    title, summary = "", text
    if "\n" in text:
        parts = [part.strip() for part in text.split("\n", 1) if part.strip()]
        if parts:
            title = parts[0]
            summary = parts[1] if len(parts) > 1 else parts[0]

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(lambda: asyncio.run(classifier.is_business_opportunity(title, summary)))
            return future.result()
    except Exception as exc:
        logger.exception(f"Error al clasificar con IA: {exc}")
        return False

def check_user_feeds(feed: Dict) -> List[Dict]:
    """Revisa un feed y devuelve solo las entradas que parecen preguntas relevantes."""
    total_steps = 6
    # step 1 is emitted by the orchestrator; feed parser starts at step 2
    flow_log(2, total_steps, "Iniciando revisión del feed...")
    logger.debug("check_user_feeds called", feed_id=feed.get("id"), user_id=feed.get("user_id"))

    try:
        trace = get_trace_service()
        # start a trace for the feed check (sync context)
        try:
            event_id = _maybe_run_async(trace.start(type=EventType.RSS, name="Check user feed", input_payload={"feed_id": feed.get("id"), "url": url}))
        except Exception:
            event_id = ""
        url = feed.get("url")
        if not url:
            logger.warning("Feed sin URL, se omite")
            return []

        entries = parse_feed(url)
        if not entries:
            try:
                _maybe_run_async(trace.success(event_id, output_payload={"entries": 0}))
            except Exception:
                pass
            logger.info("No entries parsed for feed", url=url)
            return []

        flow_log(2, total_steps, f"Feed obtenido: {len(entries)} publicaciones")

        results: List[Dict] = []
        for entry in entries:
            title = entry.get("title", "")
            # Combine multiple possible fields to ensure the classifier receives the full message
            parts = [title]
            # summary/description fields
            for fld in ("summary", "description"):
                v = entry.get(fld)
                if v:
                    parts.append(v)

            # content may be a list of dicts (feedparser) or a string
            content = entry.get("content")
            if content:
                if isinstance(content, list):
                    try:
                        first = content[0]
                        if isinstance(first, dict):
                            val = first.get("value")
                            if val:
                                parts.append(val)
                    except Exception:
                        pass
                elif isinstance(content, str):
                    parts.append(content)

            full_text = " ".join([p for p in parts if p]).strip()
            flow_log(3, total_steps, f"Analizando publicación: \"{title}\"")
            is_question = detect_question(full_text)
            flow_log(4, total_steps, f"NVIDIA responde: {'YES' if is_question else 'NO'}")
            if is_question:
                results.append(
                    {
                        "title": title,
                        "summary": entry.get("summary", ""),
                        "url": entry.get("link", ""),
                        "author": entry.get("author", ""),
                        "published": entry.get("published", ""),
                        "question": full_text,
                    }
                )

        logger.info(f"✅ Revisión completada. {len(results)} entradas relevantes encontradas.")
        try:
            _maybe_run_async(trace.success(event_id, output_payload={"matches": len(results)}))
        except Exception:
            pass
        return results

    except Exception as e:
        logger.error(f"❌ Error en check_user_feeds: {e}")
        try:
            _maybe_run_async(trace.error(event_id, error=str(e)))
        except Exception:
            pass
        return []


def check_user_source_entries(feed: Dict) -> List[Dict]:
    """Alias semántico para mantener el scheduler/orchestrator agnóstico al tipo de fuente."""
    return check_user_feeds(feed)