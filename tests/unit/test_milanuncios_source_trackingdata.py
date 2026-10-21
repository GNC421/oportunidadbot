from __future__ import annotations

from app.sources.milanuncios_source import MilanunciosSource

SAMPLE_TRACKING_HTML = '''
<html>
  <body>
    <article class="ma-AdCardV2">
      <h2>Busco una habitación para alquiler</h2>
      <div>
        <p class="ma-AdCardV2-description">Descripción completa del anuncio aquí</p>
      </div>
    </article>
    <script>
      window.trackingData = {
        "products": [
          {"id": 610461461, "title": "Busco una habitación para alquiler"}
        ]
      };
    </script>
  </body>
</html>
'''


def test_trackingdata_products_mapping(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/casas/?demanda=s&orden=relevance")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: SAMPLE_TRACKING_HTML)

    items = src.parse_items(limit=5)
    assert items is not None
    assert len(items) == 1
    it = items[0].to_dict()

    assert it["external_id"] == "610461461"
    assert it["url"].endswith("busco-una-habitacion-para-alquiler-610461461.htm")
    assert it["title"] == "Busco una habitación para alquiler"
    assert it["description"] == "Descripción completa del anuncio aquí"
