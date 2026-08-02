from __future__ import annotations

import os
import pytest
import unicodedata

pytest.importorskip("openai")
from openai import OpenAI
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

    client = OpenAI(base_url=base_url, api_key=api_key)

    title = "Busco piso de alquiler"
    summary = "Necesito un piso en el centro para mudarme cuanto antes"

    # Use the exact prompt composition the application uses
    messages = [
        {"role": "system", "content": REAL_ESTATE_CLASSIFIER_PROMPT},
        {"role": "user", "content": f"Título: {title}\n\nContenido: {summary}"},
    ]

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
            max_tokens=1024,
            stream=False,
        )
    except Exception as exc:
        pytest.skip(f"Live API call failed (connectivity): {exc}")

    # Extract content from response
    content = ""
    try:
        choices = resp.get("choices") if isinstance(resp, dict) else getattr(resp, "choices", None)
        if choices:
            first = choices[0]
            message = first.get("message") if isinstance(first, dict) else getattr(first, "message", None)
            content = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
    except Exception:
        content = str(resp)

    assert content, "La API no devolvió contenido"

    # normalize: remove diacritics, whitespace and lowercase
    normalized = unicodedata.normalize("NFKD", content).encode("ascii", "ignore").decode().strip().lower()
    normalized = normalized.replace("\n", " ").strip()

    assert normalized == "si", f"Respuesta inesperada (normalizada): {normalized} -- raw: {content}"
