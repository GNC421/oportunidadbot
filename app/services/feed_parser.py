import feedparser
import re
from typing import Any, List, Dict, Optional
from urllib.parse import urlparse
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

# Palabras clave para detectar preguntas
QUESTION_PATTERNS = [
    r'alguien sabe',
    r'recomend[áa]is',
    r'recomendaci[óo]n',
    r'd[óo]nde (comprar|alquilar|comer|contratar|comprar)',
    r'[¿?]',
    r'busc[oó]',
    r'necesito',
    r'me pode[íi]s',
    r'me recomend[áa]is',
    r'qu[eé] (restaurante|tienda|servicio|profesional)',
    r'tiene alg[uú]n',
    r'conoc[eé]is',
    r'sab[eé]is de',
    r'hay alg[uú]n',
    r'alg[uú]n (sitio|local|lugar)',
]

# Palabras clave para filtrado negativo (spam)
SPAM_PATTERNS = [
    r'publicidad',
    r'contrata',
    r'servicios SEO',
    r'compra seguidores',
    r'vendo seguidores',
]

def _parse_feed_source(url: str) -> Optional[Any]:
    """Obtiene el objeto parseado por feedparser para una URL dada."""
    try:
        return feedparser.parse(url)
    except Exception as exc:
        logger.error(f"Error al obtener el contenido del feed {url}: {exc}")
        return None


def validate_feed_source(url: str) -> Dict[str, Any]:
    """Valida si una URL apunta a un feed RSS usable y devuelve un resultado estructurado."""
    if not url or not str(url).strip():
        logger.warning("Se recibió una URL de feed vacía")
        return {"valid": False, "error": "La URL del feed está vacía", "title": "", "entry_count": 0}

    normalized_url = str(url).strip()
    parsed_url = urlparse(normalized_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        logger.warning(f"URL de feed inválida: {normalized_url}")
        return {"valid": False, "error": "La URL del feed no tiene un formato válido", "title": "", "entry_count": 0}

    logger.info(f"Validando feed RSS: {normalized_url}")

    try:
        parsed_feed = _parse_feed_source(normalized_url)
        if parsed_feed is None:
            return {"valid": False, "error": "No se pudo obtener el contenido del feed", "title": "", "entry_count": 0}

        if getattr(parsed_feed, "bozo", False):
            error_detail = getattr(parsed_feed, "bozo_exception", None)
            logger.warning(f"El feed no pudo procesarse como RSS válido: {normalized_url} ({error_detail})")
            return {"valid": False, "error": "No se pudo procesar como un RSS válido", "title": "", "entry_count": 0}

        entries = getattr(parsed_feed, "entries", []) or []
        if not entries:
            logger.warning(f"El feed no tiene entradas: {normalized_url}")
            return {"valid": False, "error": "El feed no tiene entradas disponibles", "title": "", "entry_count": 0}

        feed_title = ""
        feed_data = getattr(parsed_feed, "feed", {}) or {}
        if isinstance(feed_data, dict):
            feed_title = feed_data.get("title", "") or ""

        logger.info(f"Feed RSS válido: {normalized_url} ({len(entries)} entradas)")
        return {
            "valid": True,
            "error": None,
            "title": feed_title,
            "entry_count": len(entries),
        }
    except Exception as exc:
        logger.exception(f"Error inesperado validando feed RSS {normalized_url}: {exc}")
        return {"valid": False, "error": "Error inesperado al validar el feed", "title": "", "entry_count": 0}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def parse_feed(url: str) -> Optional[List[Dict]]:
    """Parsea un feed RSS y devuelve las entradas."""
    validation = validate_feed_source(url)
    if not validation.get("valid", False):
        logger.warning(f"No se parseará el feed inválido {url}: {validation.get('error')}")
        return None

    try:
        feed = _parse_feed_source(url)
        if feed is None:
            return None

        entries = []
        for entry in feed.entries[:10]:
            entry_data = {
                'title': entry.get('title', ''),
                'summary': entry.get('summary', ''),
                'link': entry.get('link', ''),
                'author': entry.get('author', ''),
                'published': entry.get('published', ''),
                'published_parsed': entry.get('published_parsed')
            }
            entries.append(entry_data)

        return entries
    except Exception as exc:
        logger.error(f"Error al parsear feed {url}: {exc}")
        return None

def detect_question(text: str) -> bool:
    """Detecta si un texto contiene una pregunta relevante"""
    if not text:
        return False
    
    # Limpiar y normalizar
    text = text.lower().strip()
    
    # Filtrar spam
    for spam in SPAM_PATTERNS:
        if re.search(spam, text, re.IGNORECASE):
            return False
    
    # Detectar preguntas
    for pattern in QUESTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def check_user_feeds(feed: Dict) -> List[Dict]:
    """Revisa un feed y devuelve solo las entradas que parecen preguntas relevantes."""
    logger.info("🔄 Iniciando revisión de feed...")

    try:
        url = feed.get("url")
        if not url:
            logger.warning("Feed sin URL, se omite")
            return []

        entries = parse_feed(url)
        if not entries:
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