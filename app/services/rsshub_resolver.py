from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
from urllib.parse import ParseResult, urlparse

try:
    from app.config import settings
except Exception:  # pragma: no cover - fallback defensivo si la configuración no está completa
    settings = None


@dataclass(frozen=True)
class PlatformResolver:
    """Describe una estrategia de resolución para una plataforma concreta."""

    name: str
    hosts: tuple[str, ...]
    resolver: Callable[[ParseResult], str | None]


def resolve(url: str) -> str | None:
    """Convierte una URL de una plataforma soportada en una URL RSSHub.

    El flujo principal solo valida la entrada y delega en la estrategia
    adecuada de acuerdo con el host detectado.
    """
    if not isinstance(url, str):
        return None

    normalized_url = url.strip()
    if not normalized_url:
        return None

    parsed_url = urlparse(normalized_url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return None

    for platform in _PLATFORM_RESOLVERS:
        if _matches_host(parsed_url.netloc, platform.hosts):
            return platform.resolver(parsed_url)

    return None


def _matches_host(host: str, domains: tuple[str, ...]) -> bool:
    """Comprueba si un host coincide con alguno de los dominios soportados."""
    normalized_host = host.lower()
    return any(
        normalized_host == domain or normalized_host.endswith(f".{domain}")
        for domain in domains
    )


def _resolve_reddit(parsed_url: ParseResult) -> str | None:
    """Transforma URLs de Reddit en rutas RSSHub de subreddit o usuario."""
    path = (parsed_url.path or "").strip("/")
    parts = [part for part in path.split("/") if part]

    if not parts:
        return None

    if parts[0] == "r" and len(parts) >= 2:
        subreddit = parts[1]
        return _build_rsshub_url(f"reddit/r/{subreddit}")

    if parts[0] == "user" and len(parts) >= 2:
        username = parts[1]
        return _build_rsshub_url(f"reddit/user/{username}")

    return None


def _resolve_milanuncios(parsed_url: ParseResult) -> str | None:
    """Transforma URLs de Milanuncios en una ruta RSSHub compatible."""
    return _resolve_path_based(parsed_url, "milanuncios")


def _resolve_tablondeanuncios(parsed_url: ParseResult) -> str | None:
    """Transforma URLs de Tablon de Anuncios en una ruta RSSHub compatible."""
    return _resolve_path_based(parsed_url, "tablondeanuncios")


def _resolve_path_based(parsed_url: ParseResult, prefix: str) -> str | None:
    """Construye una ruta RSSHub a partir de la ruta del sitio original."""
    path = (parsed_url.path or "").strip("/")
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return None

    route_path = "/".join(segments)
    return _build_rsshub_url(f"{prefix}/{route_path}")


_PLATFORM_RESOLVERS: tuple[PlatformResolver, ...] = (
    PlatformResolver("reddit", ("reddit.com",), _resolve_reddit),
    PlatformResolver("milanuncios", ("milanuncios.com",), _resolve_milanuncios),
    PlatformResolver("tablondeanuncios", ("tablondeanuncios.com",), _resolve_tablondeanuncios),
)


def _build_rsshub_url(path: str) -> str | None:
    """Construye la URL final usando la base configurada de RSSHub."""
    base_url = getattr(settings, "RSSHUB_BASE_URL", None) if settings is not None else None
    if not base_url:
        return None

    normalized_base = base_url.rstrip("/")
    normalized_path = path.lstrip("/")
    return f"{normalized_base}/{normalized_path}"