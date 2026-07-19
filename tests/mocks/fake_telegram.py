from __future__ import annotations

from typing import Any


class FakeTelegram:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.messages: list[dict[str, Any]] = []

    async def send_message(self, chat_id: int, text: str, parse_mode: str | None = None, reply_markup: Any = None) -> None:
        if self.should_fail:
            raise RuntimeError("telegram send failure")

        self.messages.append(
            {
                "chat_id": chat_id,
                "message": text,
                "parse_mode": parse_mode,
                "buttons": getattr(reply_markup, "inline_keyboard", None),
                "reply_markup": reply_markup,
            }
        )
