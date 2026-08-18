from __future__ import annotations

from app.sources.milanuncios_source import MilanunciosSource


HTML_IMAGE_DATA_SRC = '''
<html>
  <body>
    <article class="ma-AdCardV2" data-id="1001">
      <a class="ma-AdCardListingV2-TitleLink" href="/foo-1001.htm">
        <h2>Title with image</h2>
      </a>
      <img data-src="/images/1001.jpg" />
      <p class="ma-AdCardV2-description">Desc</p>
    </article>
  </body>
</html>
'''

HTML_NO_PRICE_LOCATION = '''
<html>
  <body>
    <article class="ma-AdCardV2" data-id="2002">
      <a class="ma-AdCardListingV2-TitleLink" href="/bar-2002.htm">
        <h2>Title no price</h2>
      </a>
      <p class="ma-AdCardV2-description">Desc no price</p>
    </article>
  </body>
</html>
'''

HTML_ID_IN_HREF = '''
<html>
  <body>
    <article class="ma-AdCardV2">
      <a class="ma-AdCardListingV2-TitleLink" href="/something/title-99999.htm">
        <h2>Href ID</h2>
      </a>
      <p class="ma-AdCardV2-description">Desc</p>
    </article>
  </body>
</html>
'''

HTML_FALLBACK_ARTICLE = '''
<html>
  <body>
    <article data-testid="AD_CARD">
      <a href="/x-123.htm"><h2>Fallback</h2></a>
    </article>
  </body>
</html>
'''

HTML_TRACKING_PRODUCTS = '''
<html>
  <body>
    <article class="ma-AdCardV2">
      <h2>Product Title Match</h2>
      <p class="ma-AdCardV2-description">Desc</p>
    </article>
    <script>var trackingData = {"products": [{"id": 4242, "title": "Product Title Match"}]};</script>
  </body>
</html>
'''

HTML_ACCENT_TITLE = '''
<html>
  <body>
    <article class="ma-AdCardV2">
      <h2>Casa en Málaga ¡Nueva!</h2>
      <p class="ma-AdCardV2-description">Desc accent</p>
    </article>
    <script>var trackingData = {"products": [{"id": 7777, "title": "Casa en Málaga ¡Nueva!"}]};</script>
  </body>
</html>
'''


def test_extracts_image_from_data_src(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/viviendas/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: HTML_IMAGE_DATA_SRC)

    items = src.parse_items(1)
    assert items and len(items) == 1
    it = items[0].to_dict()
    assert it["image"].endswith("/images/1001.jpg")


def test_price_and_location_optional(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/viviendas/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: HTML_NO_PRICE_LOCATION)

    items = src.parse_items(2)
    assert items and len(items) == 1
    it = items[0].to_dict()
    assert it["price"] == ""  # no price
    assert it["category"] == "" or it["category"] == it["url"] or it["category"] == ""


def test_external_id_extracted_from_href(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/viviendas/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: HTML_ID_IN_HREF)

    items = src.parse_items(1)
    assert items and len(items) == 1
    it = items[0].to_dict()
    assert it["external_id"] == "99999"


def test_fallback_article_selector(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/viviendas/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: HTML_FALLBACK_ARTICLE)

    res = src.validate()
    assert res["valid"] is True


def test_tracking_products_array_mapping(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/viviendas/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: HTML_TRACKING_PRODUCTS)

    items = src.parse_items(5)
    assert items and len(items) == 1
    it = items[0].to_dict()
    assert it["external_id"] == "4242"


def test_slugify_and_construct_link_from_initial_props(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/viviendas/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: HTML_ACCENT_TITLE)

    items = src.parse_items(5)
    assert items and len(items) == 1
    it = items[0].to_dict()
    assert it["external_id"] == "7777"
    assert it["url"].endswith("casa-en-malaga-nueva-7777.htm")


def test_parse_items_returns_none_when_fetch_fails(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/viviendas/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: None)

    items = src.parse_items(5)
    assert items is None


def test_validate_returns_false_when_fetch_fails(monkeypatch):
    src = MilanunciosSource("https://www.milanuncios.com/viviendas/")
    monkeypatch.setattr(src, "_request_text", lambda *_a, **_k: None)

    res = src.validate()
    assert res["valid"] is False
