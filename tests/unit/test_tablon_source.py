from __future__ import annotations

from app.sources.tablon_source import TablonSource


SAMPLE_HTML = """
<html>
  <body>
    <article class=\"result-item\" id=\"5236281\">
      <h2><a href=\"/inmobiliaria/venta-piso.htm\">Venta piso en Murcia</a></h2>
      <p class=\"description\">Piso reformado, buena zona</p>
      <img src=\"/images/piso.jpg\" />
      <span class=\"price\">150.000 EUR</span>
      <time datetime=\"2026-07-22\">22/07/2026</time>
      <span class=\"category\">Inmobiliaria</span>
    </article>
  </body>
</html>
"""


def test_tablon_source_validate_ok(monkeypatch):
    source = TablonSource("https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1")

    monkeypatch.setattr(source, "_request_text", lambda *_a, **_k: SAMPLE_HTML)

    result = source.validate()

    assert result["valid"] is True
    assert result["entry_count"] == 1


def test_tablon_source_parse_items_maps_fields(monkeypatch):
    source = TablonSource("https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1")

    monkeypatch.setattr(source, "_request_text", lambda *_a, **_k: SAMPLE_HTML)

    items = source.parse_items(limit=10)

    assert items is not None
    assert len(items) == 1
    item = items[0]
    as_dict = item.to_dict()

    assert as_dict["external_id"] == "5236281"
    assert as_dict["title"] == "Venta piso en Murcia"
    assert as_dict["url"] == "https://www.tablondeanuncios.com/inmobiliaria/venta-piso.htm"
    assert as_dict["description"] == "Piso reformado, buena zona"
    assert as_dict["image"] == "https://www.tablondeanuncios.com/images/piso.jpg"
    assert as_dict["price"] == "150.000 EUR"
    assert as_dict["published_date"] == "22/07/2026"
    assert as_dict["category"] == "Inmobiliaria"


def test_tablon_source_validate_error_when_no_articles(monkeypatch):
    source = TablonSource("https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1")

    monkeypatch.setattr(source, "_request_text", lambda *_a, **_k: "<html><body><div>sin resultados</div></body></html>")

    result = source.validate()

    assert result["valid"] is False


def test_tablon_source_detects_html_structure_fallback(monkeypatch):
    source = TablonSource("https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1")
    html_with_fallback_only = """
    <html><body>
      <article id=\"42\">
        <a href=\"/anuncio.htm\">Anuncio fallback</a>
        <p>texto</p>
      </article>
    </body></html>
    """
    monkeypatch.setattr(source, "_request_text", lambda *_a, **_k: html_with_fallback_only)

    items = source.parse_items(limit=10)

    assert items is not None
    assert len(items) == 1
    metrics = source.get_metrics()
    assert metrics["html_structure_fallbacks"] >= 1
