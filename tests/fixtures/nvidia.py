from __future__ import annotations

import pytest


@pytest.fixture
def nvidia_positive_response() -> str:
    return "true"


@pytest.fixture
def nvidia_negative_response() -> str:
    return "false"
