from __future__ import annotations

from app.sources.milanuncios_source import MilanunciosSource


SAMPLE_HTML = '''
<html>
  <body>
    <article class="ma-AdCardV2 ma-AdCardV2--listingCard3AdsPerRow ma-AdCardV2--permanentShadow" data-testid="AD_CARD">
      <a class="ma-AdCardListingV2-TitleLink" href="/alquiler-de-casas-en-la-paca-murcia/casa-pequena-con-terremo-573733265.htm">
        <h2>Casa pequeña con terremo</h2>
      </a>
      <div>
        <p class="ma-AdCardV2-description">Casa con terreno y varias habitaciones</p>
        <span class="ma-AdPrice-value">650 €</span>
        <span class="ma-AdLocation-text">La Paca (Murcia)</span>
        <p class="ma-SharedText ma-AdCardV2-time">Hace 6 horas</p>
      </div>
    </article>
  </body>
</html>
'''


def test_milanuncios_source_validate_ok(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/casas-en-murcia/?demanda=s&vendedor=part")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: SAMPLE_HTML)

    res = src.validate()

    assert res["valid"] is True
    assert res["entry_count"] == 1


def test_milanuncios_source_parse_items_maps_fields(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/casas-en-murcia/?demanda=s&vendedor=part")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: SAMPLE_HTML)

    items = src.parse_items(limit=5)

    assert items is not None
    assert len(items) == 1
    it = items[0].to_dict()

    assert it["title"] == "Casa pequeña con terremo"
    assert it["price"] == "650 €"
    assert it["category"] == "La Paca (Murcia)"
    assert it["published_date"] == "Hace 6 horas"
    assert it["external_id"] == "573733265"
    assert it["url"].endswith("casa-pequena-con-terremo-573733265.htm")


def test_milanuncios_source_no_articles(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/casas-en-murcia/?demanda=s&vendedor=part")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: "<html><body>No results</body></html>")

    res = src.validate()
    assert res["valid"] is False
