from __future__ import annotations

import pytest

from app import database
from app.services.orchestrator import Orchestrator
from app.sources.milanuncios_source import MilanunciosSource


@pytest.mark.asyncio
async def test_milanuncios_constructed_url_dedup(monkeypatch, fake_supabase):
    # prepare fake supabase and a feed
    monkeypatch.setattr(database, "supabase", fake_supabase)

    feed = {"id": 1, "user_id": 201, "url": "https://milanuncios.local/search/", "is_active": True}
    fake_supabase.seed("feeds", [feed])

    # create a sample HTML where the article has no href but trackingData provides product id
    sample_html = '''
    <html>
      <body>
        <article class="ma-AdCardV2">
          <h2>Casa en Murcia preciosa</h2>
          <p class="ma-AdCardV2-description">Descripción</p>
        </article>
        <script>var trackingData = {"products": [{"id": 9999, "title": "Casa en Murcia preciosa"}]};</script>
      </body>
    </html>
    '''

    # instantiate source and patch its HTTP fetch
    src = MilanunciosSource(feed["url"])
    monkeypatch.setattr(src, "_request_text", lambda url=None: sample_html)

    items = src.parse_items(limit=5)
    assert items and len(items) == 1
    it = items[0]
    # ensure constructed URL includes the id
    assert str(it.url).endswith("-9999.htm")

    # seed an existing alert with that exact URL to simulate a prior save
    fake_supabase.seed(
        "alerts",
        [{"id": 1, "user_id": 201, "feed_id": 1, "post_url": it.url, "post_title": it.title, "post_content": it.summary}],
    )

    # monkeypatch orchestrator helpers to use our database and parsed item
    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", database.get_active_feeds)
    monkeypatch.setattr("app.services.orchestrator.get_alert_by_url", database.get_alert_by_url)
    monkeypatch.setattr("app.services.orchestrator.save_alert", database.save_alert)
    monkeypatch.setattr("app.services.orchestrator.update_feed_last_check", lambda _id: None)

    # have the orchestrator use our parsed item as the discovered opportunity
    monkeypatch.setattr(
        "app.services.orchestrator.check_user_source_entries",
        lambda _feed: [{"title": it.title, "summary": it.summary, "url": it.url, "author": "u", "question": "q"}],
    )

    # send_alert must not be called for duplicates
    async def _fail_send(**_kwargs):
        raise AssertionError("telegram should not run for duplicates")

    monkeypatch.setattr("app.services.orchestrator.send_alert", _fail_send)

    orchestrator = Orchestrator()
    count = await orchestrator.run_feed_checks()

    assert count == 1
    # alerts unchanged
    assert len(fake_supabase.alerts) == 1
