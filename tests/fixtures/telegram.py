from __future__ import annotations

import pytest


@pytest.fixture
def telegram_success_response() -> dict:
    return {"ok": True, "message_id": 55}


@pytest.fixture
def telegram_error_response() -> dict:
    return {"ok": False, "error": "blocked by user"}
