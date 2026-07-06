import feedparser
import re
from typing import List, Dict, Optional
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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def parse_feed(url: str) -> Optional[List[Dict]]:
    """Parsea un feed RSS y devuelve las entradas"""
    try:
        feed = feedparser.parse(url)
        
        if feed.bozo:  # Error en el parseo
            logger.warning(f"⚠️ Problema al parsear feed {url}: {feed.bozo_exception}")
            return None
        
        entries = []
        for entry in feed.entries[:10]:  # Últimas 10 publicaciones
            # Extraer datos relevantes
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
    except Exception as e:
        logger.error(f"Error al parsear feed {url}: {e}")
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