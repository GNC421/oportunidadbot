"""Integración opcional: verifica que se recibe HTML desde una URL remota.

Esta prueba se omite por defecto. Para ejecutarla, exporta:

    SET RUN_LIVE_HTML_TEST=1    # Windows (PowerShell/CMD)
    export RUN_LIVE_HTML_TEST=1 # Linux/macOS

Opcionalmente puedes definir `LIVE_HTML_URL` para probar otra URL.
"""
from __future__ import annotations

import os

import pytest

from app.sources.base import BaseSource
from loguru import logger


class DummySource(BaseSource):
    def validate(self):
        return {"ok": True}

    def parse_items(self, limit: int = 10):
        return []


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_HTML_TEST", "0") != "1",
    reason="Live HTTP tests disabled",
)
def test_fetch_html_returns_html():
    url = os.environ.get("LIVE_HTML_URL", "https://www.example.com/")
    logger.info("Live HTML test URL: {}", url)
    src = DummySource(url)
    text = src._request_text()
    assert text is not None, "No se recibió texto HTTP"
    assert "<html" in text.lower()
