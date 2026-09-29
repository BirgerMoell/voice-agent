from __future__ import annotations

import os
import time

COLOR = os.isatty(1) and "NO_COLOR" not in os.environ


def paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if COLOR else text


class Trace:
    """Small observable event surface; replace it with structured logging in an app."""

    def event(self, label: str, value: str = "", color: str = "36") -> None:
        print(paint(f"  {label:<11}", color) + value, flush=True)

    def timer(self) -> float:
        return time.perf_counter()

    def elapsed(self, started: float) -> str:
        return f"{time.perf_counter() - started:.2f}s"
