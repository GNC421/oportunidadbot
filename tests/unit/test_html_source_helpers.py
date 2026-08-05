from pathlib import Path

from bs4 import BeautifulSoup


def test_to_tuple():
    from app.sources.html_source import HTMLSource

    assert HTMLSource._to_tuple(None) == ()
    assert HTMLSource._to_tuple("a") == ("a",)
    assert HTMLSource._to_tuple(("a", "b")) == ("a", "b")


def test_find_articles_and_fallback(monkeypatch):
    from app.sources.html_source import HTMLSelectors

    class DSRC:
        selectors = HTMLSelectors(item_selector=(".primary", "article[id]"), title_selector="h2")

    # create a minimal instance by subclassing HTMLSource dynamically
    from app.sources.html_source import HTMLSource

    class Dummy(HTMLSource):
        selectors = DSRC.selectors

        def build_item(self, article, extracted):
            from app.sources.item import Item

            return Item(title=extracted.get("title", ""), summary="", link=extracted.get("link", ""), author="", published="")

    src = Dummy(url="https://example.com")

    html_primary = "<div class=\"primary\"><h2>One</h2></div>"
    soup = src._soup_from_html(html_primary)
    articles, used_fallback = src._find_articles(soup)
    assert len(articles) == 1
    assert used_fallback is False

    html_second = "<article id=\"42\"><h2>Fallback</h2></article>"
    soup = src._soup_from_html(html_second)
    articles, used_fallback = src._find_articles(soup)
    assert len(articles) == 1
    assert used_fallback is True

    html_none = "<html><body><p>no items here</p></body></html>"
    soup = src._soup_from_html(html_none)
    articles, used_fallback = src._find_articles(soup)
    assert articles == []


def test_extract_link_image_and_text_normalization(monkeypatch):
    from app.sources.html_source import HTMLSelectors

    from app.sources.html_source import HTMLSource

    class Dummy(HTMLSource):
        selectors = HTMLSelectors(item_selector=("article",), title_selector=("h2 a",))

        def build_item(self, article, extracted):
            from app.sources.item import Item

            return Item(title=extracted.get("title", ""), summary="", link=extracted.get("link", ""), author="", published="")

    src = Dummy(url="https://example.com/base/")
    html = "<article><h2><a href=\"/path/page.html\">Title</a></h2><img src=\"/img/pic.jpg\"></article>"
    soup = src._soup_from_html(html)
    article = soup.select_one("article")

    title = src._extract_text(article, src.selectors.title_selector)
    assert title == "Title"

    link = src._extract_link(article, src.selectors.link_selector)
    # default link_selector is None so anchor fallback should be used and normalized
    assert link.startswith("https://example.com/")

    img = src._extract_image(article, src.selectors.image_selector)
    assert img.startswith("https://example.com/")


def test_extract_date_and_external_id():
    from app.sources.html_source import HTMLSelectors, HTMLSource

    class Dummy(HTMLSource):
        selectors = HTMLSelectors(item_selector=("article",), title_selector=("h2",))

        def build_item(self, article, extracted):
            from app.sources.item import Item

            return Item(title=extracted.get("title", ""), summary="", link=extracted.get("link", ""), author="", published="")

    src = Dummy(url="https://x/")
    html = "<article id=\"abc123\"><time datetime=\"2026-01-02T03:04:05Z\"></time></article>"
    soup = src._soup_from_html(html)
    art = soup.select_one("article")
    assert src._extract_external_id(art) == "abc123"
    assert src._extract_date(art, None) == "2026-01-02T03:04:05Z"


def test_parse_items_handles_build_item_errors(monkeypatch):
    from app.sources.html_source import HTMLSelectors, HTMLSource
    from app.sources.item import Item

    class DummyErr(HTMLSource):
        selectors = HTMLSelectors(item_selector=("article",), title_selector=("h2",))

        def build_item(self, article, extracted):
            # raise for first, succeed for second
            if extracted.get("title") == "BAD":
                raise RuntimeError("boom")
            return Item(title=extracted.get("title"), summary="", link="/ok", author="", published="")

    html = "<article><h2>BAD</h2></article><article><h2>GOOD</h2></article>"
    src = DummyErr(url="https://host/")
    monkeypatch.setattr(DummyErr, "_fetch_html", lambda self: html)

    items = src.parse_items(limit=10)
    assert items is not None
    # only GOOD should be returned
    assert len(items) == 1
    assert items[0].title == "GOOD"
    metrics = src.get_metrics()
    assert metrics.get("parse_runs", 0) >= 1
    assert metrics.get("items_extracted", 0) >= 1


def test_validate_no_html_or_no_entries(monkeypatch):
    from app.sources.html_source import HTMLSelectors, HTMLSource

    class Dummy(HTMLSource):
        selectors = HTMLSelectors(item_selector=("article",), title_selector=("h2",))

        def build_item(self, article, extracted):
            from app.sources.item import Item

            return Item(title=extracted.get("title", ""), summary="", link=extracted.get("link", ""), author="", published="")

    src = Dummy(url="https://host/")
    monkeypatch.setattr(Dummy, "_fetch_html", lambda self: None)
    res = src.validate()
    assert res["valid"] is False

    monkeypatch.setattr(Dummy, "_fetch_html", lambda self: "<html><body><p>no articles</p></body></html>")
    res2 = src.validate()
    assert res2["valid"] is False


def test_parse_items_fallback_and_no_html(monkeypatch):
    from app.sources.html_source import HTMLSelectors, HTMLSource

    class Dummy(HTMLSource):
        selectors = HTMLSelectors(item_selector=(".primary", "article[id]"), title_selector=("h2",))

        def build_item(self, article, extracted):
            from app.sources.item import Item

            return Item(title=extracted.get("title", ""), summary="", link=extracted.get("link", ""), author="", published="")

    src = Dummy(url="https://host/")
    # Case: parse_items with no HTML
    monkeypatch.setattr(Dummy, "_fetch_html", lambda self: None)
    assert src.parse_items() is None

    # Case: second selector matches -> fallback should be recorded
    html = "<article id=\"1\"><h2>X</h2></article>"
    monkeypatch.setattr(Dummy, "_fetch_html", lambda self: html)
    items = src.parse_items()
    assert items is not None
    metrics = src.get_metrics()
    assert metrics.get("html_structure_fallbacks", 0) >= 1


def test_validate_uses_running_loop(monkeypatch):
    import asyncio

    from app.sources.html_source import HTMLSelectors, HTMLSource

    class Dummy(HTMLSource):
        selectors = HTMLSelectors(item_selector=("article",), title_selector=("h2",))

        def build_item(self, article, extracted):
            from app.sources.item import Item

            return Item(title=extracted.get("title", ""), summary="", link=extracted.get("link", ""), author="", published="")

    src = Dummy(url="https://host/")
    html = "<article><h2>OK</h2></article>"
    monkeypatch.setattr(Dummy, "_fetch_html", lambda self: html)

    class DummyLoop:
        def __init__(self):
            self.tasks = []

        def create_task(self, coro):
            # store the coroutine; do not run
            self.tasks.append(coro)

    loop = DummyLoop()
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    res = src.validate()
    assert res.get("valid") is True

