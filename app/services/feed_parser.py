import asyncio
import feedparser
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Dict, Optional
from urllib.parse import urlparse
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.ai_classifier import classifier
from app.sources import SourceFactory

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
        return {"valid": False, "error": "Error inesperado al validar el feed", "title": "", "entry_count": 0}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def parse_feed(url: str) -> Optional[List[Dict]]:
    """Parsea un feed RSS y devuelve las entradas."""
    logger.debug("parse_feed called", url=url)
    try:
        source = SourceFactory.from_url(url, parse_feed_fn=_parse_feed_source)
        items = source.parse_items(limit=10)
        if items is None:
            return None

        return [item.to_dict() for item in items]
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
    logger.info("🔄 Iniciando revisión de feed...")
    logger.debug("check_user_feeds called", feed_id=feed.get("id"), user_id=feed.get("user_id"))

    try:
        url = feed.get("url")
        if not url:
            logger.warning("Feed sin URL, se omite")
            return []

        entries = parse_feed(url)
        if not entries:
            logger.info("No entries parsed for feed", url=url)
            return []

        results: List[Dict] = []
        for entry in entries:
            full_text = f"{entry.get('title', '')} {entry.get('summary', '')}".strip()
            if detect_question(full_text):
                results.append(
                    {
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", ""),
                        "url": entry.get("link", ""),
                        "author": entry.get("author", ""),
                        "published": entry.get("published", ""),
                        "question": full_text,
                    }
                )

        logger.info(f"✅ Revisión completada. {len(results)} entradas relevantes encontradas.")
        return results

    except Exception as e:
        logger.error(f"❌ Error en check_user_feeds: {e}")
        return []


def check_user_source_entries(feed: Dict) -> List[Dict]:
    """Alias semántico para mantener el scheduler/orchestrator agnóstico al tipo de fuente."""
    return check_user_feeds(feed)