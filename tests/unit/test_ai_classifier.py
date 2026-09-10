from __future__ import annotations

import httpx
import pytest

import app.services.ai_classifier as ai_mod
from tests.mocks.fake_nvidia_http import FakeSSEResponse, make_client_factory


async def _async_value(value):
    return value


class FakeTrace:
    async def start(self, **_k):
        return "evt"

    async def success(self, *a, **k):
        return None

    async def error(self, *a, **k):
        return None


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Evita esperas reales durante los reintentos con backoff."""
    monkeypatch.setattr(ai_mod.asyncio, "sleep", lambda *_a, **_k: _async_value(None))


def _new_classifier() -> ai_mod.AIClassifier:
    cls = ai_mod.AIClassifier()
    cls._api_key = "test-api-key"
    cls._base_url = "https://nvidia.local/v1"
    cls._model = "moonshotai/kimi-k3"
    cls._endpoint = "https://nvidia.local/v1/chat/completions"
    cls._ai_enabled = True
    return cls


def _sse_lines(*texts: str, done: bool = True) -> list[str]:
    lines: list[str] = []
    for text in texts:
        lines.append("")  # línea vacía intercalada, debe ignorarse
        lines.append('data: {"choices":[{"delta":{"content":"%s"}}]}' % text)
    if done:
        lines.append("data: [DONE]")
    return lines


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------


def test_model_centralizado_en_settings():
    cls = _new_classifier()
    assert cls._model == "moonshotai/kimi-k3"
    assert cls._endpoint == "https://nvidia.local/v1/chat/completions"


@pytest.mark.asyncio
async def test_sin_api_key_devuelve_false(monkeypatch):
    cls = _new_classifier()
    cls._api_key = None
    monkeypatch.setattr(ai_mod, "get_trace_service", lambda: FakeTrace())

    assert await cls.is_business_opportunity("t", "s") is False


@pytest.mark.asyncio
async def test_call_nvidia_sin_api_key_devuelve_none():
    cls = _new_classifier()
    cls._api_key = None
    assert await cls._call_nvidia("t", "s") is None


# ---------------------------------------------------------------------------
# Construcción del request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_incluye_endpoint_headers_y_payload_correctos(monkeypatch):
    cls = _new_classifier()
    response = FakeSSEResponse(status_code=200, lines=_sse_lines("SI"))
    factory = make_client_factory([response])
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    result = await cls._call_nvidia("Busco piso", "Alquiler en el centro")

    assert result == "SI"
    call = factory.client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "https://nvidia.local/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer test-api-key"
    assert call["headers"]["Accept"] == "text/event-stream"
    payload = call["json"]
    assert payload["model"] == "moonshotai/kimi-k3"
    assert payload["stream"] is True
    assert payload["max_tokens"] == 1024
    assert payload["temperature"] == 0.2
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["content"] == "Título: Busco piso\n\nContenido: Alquiler en el centro"


# ---------------------------------------------------------------------------
# Parsing de streaming (SSE)
# ---------------------------------------------------------------------------


def test_parse_sse_concatena_multiples_chunks():
    cls = _new_classifier()
    lines = _sse_lines("Hola", " mundo")
    assert cls._parse_sse_lines(lines) == "Hola mundo"


def test_parse_sse_ignora_lineas_vacias_y_no_data():
    cls = _new_classifier()
    lines = ["", "   ", ": comentario", 'data: {"choices":[{"delta":{"content":"ok"}}]}', "data: [DONE]"]
    assert cls._parse_sse_lines(lines) == "ok"


def test_parse_sse_detecta_done_y_detiene_parsing():
    cls = _new_classifier()
    lines = [
        'data: {"choices":[{"delta":{"content":"antes"}}]}',
        "data: [DONE]",
        'data: {"choices":[{"delta":{"content":"despues"}}]}',
    ]
    assert cls._parse_sse_lines(lines) == "antes"


def test_parse_sse_ignora_json_invalido(monkeypatch):
    cls = _new_classifier()
    lines = [
        "data: {esto no es json}",
        'data: {"choices":[{"delta":{"content":"valido"}}]}',
        "data: [DONE]",
    ]
    assert cls._parse_sse_lines(lines) == "valido"


def test_parse_sse_sin_done_devuelve_contenido_acumulado():
    """Streaming interrumpido sin [DONE]: debe devolver lo acumulado hasta el corte."""
    cls = _new_classifier()
    lines = ['data: {"choices":[{"delta":{"content":"parcial"}}]}']
    assert cls._parse_sse_lines(lines) == "parcial"


def test_parse_sse_respuesta_vacia():
    cls = _new_classifier()
    assert cls._parse_sse_lines([]) == ""
    assert cls._parse_sse_lines(["data: [DONE]"]) == ""


def test_parse_sse_bytes_decodificados():
    cls = _new_classifier()
    lines = [b'data: {"choices":[{"delta":{"content":"bytes"}}]}', b"data: [DONE]"]
    assert cls._parse_sse_lines(lines) == "bytes"


@pytest.mark.asyncio
async def test_call_nvidia_respuesta_vacia_devuelve_none(monkeypatch):
    cls = _new_classifier()
    response = FakeSSEResponse(status_code=200, lines=[])
    monkeypatch.setattr(ai_mod.httpx, "Client", make_client_factory([response]))

    assert await cls._call_nvidia("t", "s") is None


# ---------------------------------------------------------------------------
# Errores HTTP / conexión / timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_nvidia_401_no_reintenta(monkeypatch):
    cls = _new_classifier()
    response = FakeSSEResponse(status_code=401, lines=[])
    factory = make_client_factory([response])
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    assert await cls._call_nvidia("t", "s") is None
    assert len(factory.client.calls) == 1


@pytest.mark.asyncio
async def test_call_nvidia_403_no_reintenta(monkeypatch):
    cls = _new_classifier()
    response = FakeSSEResponse(status_code=403, lines=[])
    factory = make_client_factory([response])
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    assert await cls._call_nvidia("t", "s") is None
    assert len(factory.client.calls) == 1


@pytest.mark.asyncio
async def test_call_nvidia_400_reintenta_y_falla(monkeypatch):
    cls = _new_classifier()
    responses = [FakeSSEResponse(status_code=400, lines=[]) for _ in range(cls._max_retries)]
    factory = make_client_factory(responses)
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    assert await cls._call_nvidia("t", "s") is None
    assert len(factory.client.calls) == cls._max_retries


@pytest.mark.asyncio
async def test_call_nvidia_429_reintenta_y_falla(monkeypatch):
    cls = _new_classifier()
    responses = [FakeSSEResponse(status_code=429, lines=[]) for _ in range(cls._max_retries)]
    factory = make_client_factory(responses)
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    assert await cls._call_nvidia("t", "s") is None
    assert len(factory.client.calls) == cls._max_retries


@pytest.mark.asyncio
async def test_call_nvidia_500_reintenta_hasta_exito(monkeypatch):
    cls = _new_classifier()
    responses = [
        FakeSSEResponse(status_code=500, lines=[]),
        FakeSSEResponse(status_code=200, lines=_sse_lines("SI")),
    ]
    factory = make_client_factory(responses)
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    assert await cls._call_nvidia("t", "s") == "SI"
    assert len(factory.client.calls) == 2


@pytest.mark.asyncio
async def test_call_nvidia_timeout_reintenta_y_falla(monkeypatch):
    cls = _new_classifier()
    queue = [httpx.TimeoutException("timeout") for _ in range(cls._max_retries)]
    factory = make_client_factory(queue)
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    assert await cls._call_nvidia("t", "s") is None
    assert len(factory.client.calls) == cls._max_retries


@pytest.mark.asyncio
async def test_call_nvidia_error_conexion_reintenta_y_falla(monkeypatch):
    cls = _new_classifier()
    request = httpx.Request("POST", "https://nvidia.local/v1/chat/completions")
    queue = [httpx.ConnectError("connection refused", request=request) for _ in range(cls._max_retries)]
    factory = make_client_factory(queue)
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    assert await cls._call_nvidia("t", "s") is None
    assert len(factory.client.calls) == cls._max_retries


# ---------------------------------------------------------------------------
# Parsing de la respuesta de negocio y caché (comportamiento previo, sin cambios)
# ---------------------------------------------------------------------------


def test_parse_response_and_cache_behavior():
    cls = ai_mod.classifier
    assert cls._parse_response(None) is False
    assert cls._parse_response("true") is True
    assert cls._parse_response("False") is False

    before = cls.clear_cache()
    cls._set_cached_result("k1", True)
    assert cls._get_cached_result("k1") is True
    assert cls.clear_cache() >= 1
    assert before >= 0


@pytest.mark.asyncio
async def test_is_business_opportunity_usa_cache_y_respeta_ai_disabled(monkeypatch):
    cls = _new_classifier()
    monkeypatch.setattr(ai_mod, "get_trace_service", lambda: FakeTrace())

    key = cls._build_cache_key("t", "s")
    cls._set_cached_result(key, True)

    async def _should_not_call(*_a, **_k):
        raise AssertionError("no debería llamarse a NVIDIA si hay caché")

    monkeypatch.setattr(cls, "_call_nvidia", _should_not_call)
    assert await cls.is_business_opportunity("t", "s") is True

    monkeypatch.setattr(cls, "_ai_enabled", False)
    assert await cls.is_business_opportunity("t2", "s2") is True
