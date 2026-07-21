from __future__ import annotations

import importlib

from types import SimpleNamespace

from app.services import rsshub_resolver


def test_rss_resolver_module_reload_for_import_coverage():
    module = importlib.import_module("app.services.rsshub_resolver")
    reloaded = importlib.reload(module)
    assert hasattr(reloaded, "resolve")


def test_resolve_valid_supported_platform(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    resolved = rsshub_resolver.resolve("https://reddit.com/r/python")

    assert resolved == "https://rsshub.local/reddit/r/python"


def test_resolve_invalid_url_returns_none(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    assert rsshub_resolver.resolve("not-a-url") is None


def test_resolve_unknown_platform_returns_none(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    assert rsshub_resolver.resolve("https://unknown.example.com/path") is None


def test_resolve_missing_base_url_returns_none(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL=""))

    assert rsshub_resolver.resolve("https://reddit.com/r/python") is None


def test_resolve_reddit_user(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    resolved = rsshub_resolver.resolve("https://reddit.com/user/guillermo")

    assert resolved == "https://rsshub.local/reddit/user/guillermo"


def test_resolve_milanuncios(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    resolved = rsshub_resolver.resolve("https://www.milanuncios.com/pisos-en-alquiler/madrid.htm")

    assert resolved == "https://rsshub.local/milanuncios/pisos-en-alquiler/madrid.htm"


def test_resolve_tablondeanuncios(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    resolved = rsshub_resolver.resolve("https://tablondeanuncios.com/inmobiliaria/venta")

    assert resolved == "https://rsshub.local/tablondeanuncios/inmobiliaria/venta"


def test_resolve_tablondeanuncios_keeps_demanda_query(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    resolved = rsshub_resolver.resolve("https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1")

    assert resolved == "https://rsshub.local/tablondeanuncios/inmobiliaria-en-murcia?demanda=1"


def test_resolve_rejects_non_string(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    assert rsshub_resolver.resolve(123) is None


def test_resolve_rejects_empty_string(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    assert rsshub_resolver.resolve("   ") is None


def test_matches_host_subdomain():
    assert rsshub_resolver._matches_host("www.reddit.com", ("reddit.com",)) is True


def test_resolve_reddit_without_resource(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    assert rsshub_resolver.resolve("https://reddit.com/") is None


def test_resolve_path_based_without_segments(monkeypatch):
    monkeypatch.setattr(rsshub_resolver, "settings", SimpleNamespace(RSSHUB_BASE_URL="https://rsshub.local"))

    assert rsshub_resolver.resolve("https://milanuncios.com/") is None
