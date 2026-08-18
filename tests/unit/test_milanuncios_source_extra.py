from __future__ import annotations

from app.sources.milanuncios_source import MilanunciosSource


def test_normalize_and_slugify_edge_cases():
    src = MilanunciosSource("https://www.milanuncios.com/viviendas/")
    s = "  Ático en Málaga -- ¡Bonito!  "
    norm = src._normalize_for_match(s)
    slug = src._slugify(s)
    assert "atico en malaga bonito" in norm
    assert "atico-en-malaga-bonito" == slug


def test_extract_products_from_initial_props_jsonparse(monkeypatch):
    # create an HTML where __INITIAL_PROPS__ is assigned using JSON.parse('...')
    inner = '{"adListPagination":{"adList":{"ads":[{"id":5555,"title":"Prop Inicial"}]}}}'
    # escape quotes for embedding inside JSON.parse string
    escaped = inner.replace('\\', '\\\\').replace('"', '\\"')
    html = f"""
    <html>
      <body>
        <article class="ma-AdCardV2">
          <h2>Prop Inicial</h2>
        </article>
        <script>window.__INITIAL_PROPS__ = JSON.parse('{escaped}')</script>
      </body>
    </html>
    """

    src = MilanunciosSource("https://milanuncios.local/search/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: html)

    items = src.parse_items(limit=3)
    assert items and len(items) == 1
    it = items[0].to_dict()
    assert it["external_id"] == "5555"


def test_constructed_link_keeps_href_when_contains_id(monkeypatch):
    html = '''
    <html>
      <body>
        <article class="ma-AdCardV2">
          <a href="/path/mi-anuncio-3210.htm"><h2>Titulo</h2></a>
        </article>
      </body>
    </html>
    '''
    src = MilanunciosSource("https://milanuncios.local/search/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: html)

    items = src.parse_items(2)
    assert items and len(items) == 1
    it = items[0].to_dict()
    assert it["external_id"] == "3210"
    assert it["url"].endswith("mi-anuncio-3210.htm")


def test_constructed_link_when_no_href_uses_feed_domain(monkeypatch):
    html = '''
    <html>
      <body>
        <article class="ma-AdCardV2">
          <h2>Sin href noticia</h2>
        </article>
        <script>var trackingData = {"products": [{"id": 8080, "title": "Sin href noticia"}]};</script>
      </body>
    </html>
    '''
    src = MilanunciosSource("https://milanuncios.local/search/results/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: html)

    items = src.parse_items(3)
    assert items and len(items) == 1
    it = items[0].to_dict()
    # constructed path should include slug and id
    assert it["url"].endswith("sin-href-noticia-8080.htm")
