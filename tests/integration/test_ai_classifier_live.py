from __future__ import annotations

import os
import pytest
import httpx

from app.services.prompts import REAL_ESTATE_CLASSIFIER_PROMPT


@pytest.mark.integration
def test_live_nvidia_classifier_exact_si_with_app_prompt():
    """Llamada controlada a la API real usando exactamente el prompt de la app.

    Comprueba que la respuesta normalizada sea 'si'. Se salta si faltan credenciales
    o falla la conexión.
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    base_url = os.getenv("NVIDIA_BASE_URL")
    model = os.getenv("NVIDIA_MODEL")

    if not api_key or not base_url or not model:
        pytest.skip("NVIDIA credentials not provided in environment")

    title = "Busco piso de alquiler"
    summary = "Necesito un piso en el centro para mudarme cuanto antes"

    # Use the exact prompt composition the application uses
    messages = [
        {"role": "system", "content": REAL_ESTATE_CLASSIFIER_PROMPT},
        {"role": "user", "content": f"Título: {title}\n\nContenido: {summary}"},
    ]

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 1024,
        "stream": False,
    }

    try:
        resp = httpx.post(endpoint, json=payload, headers=headers, timeout=20.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        pytest.skip(f"Live API call failed (connectivity): {exc}")

    content = ""
    try:
        choices = data.get("choices") or []
        if choices:
            content = choices[0].get("message", {}).get("content", "")
    except Exception:
        content = str(data)

    assert content, "La API no devolvió contenido"


    # normalize: remove diacritics, whitespace and lowercase
    normalized = unicodedata.normalize("NFKD", content).encode("ascii", "ignore").decode().strip().lower()
    normalized = normalized.replace("\n", " ").strip()

    assert normalized == "si", f"Respuesta inesperada (normalizada): {normalized} -- raw: {content}"
