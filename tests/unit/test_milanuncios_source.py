from pathlib import Path


def test_milanuncios_parse(monkeypatch):
    from app.sources import MilanunciosSource

    fixture = Path(__file__).parent.parent / "fixtures" / "milanuncions.html"
    html = fixture.read_text(encoding="utf-8")

    # Ensure the source uses our fixture instead of performing HTTP
    monkeypatch.setattr(MilanunciosSource, "_fetch_html", lambda self: html)

    src = MilanunciosSource(url="https://www.milanuncios.com/casas-en-murcia/")

    # validate should succeed with the fixture
    v = src.validate()
    assert isinstance(v, dict)
    assert v.get("valid") is True
    assert v.get("entry_count", 0) > 0

    # parse items should return a non-empty list without network
    items = src.parse_items(limit=5)
    assert items is not None
    assert len(items) > 0

    # Basic content expectations
    for it in items:
        assert it.title

    # At least one parsed item should include a link
    assert any(it.link for it in items)

    # Metrics updated
    metrics = src.get_metrics()
    assert metrics.get("parse_runs", 0) >= 1
    assert metrics.get("items_extracted", 0) >= len(items)
