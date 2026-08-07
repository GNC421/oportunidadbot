from __future__ import annotations


class FakeNvidia:
    def __init__(self) -> None:
        self.mode = "YES"
        self.calls: list[tuple[str, str]] = []

    def configure(self, mode: str) -> None:
        self.mode = mode

    async def is_business_opportunity(self, title: str, summary: str) -> bool:
        self.calls.append((title, summary))

        if self.mode == "YES":
            return True
        if self.mode == "NO":
            return False
        if self.mode == "TIMEOUT":
            raise TimeoutError("nvidia timeout")
        if self.mode == "HTTP500":
            raise RuntimeError("http 500")
        if self.mode == "INVALID":
            raise ValueError("invalid response")
        return False
