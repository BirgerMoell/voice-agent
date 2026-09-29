from __future__ import annotations

import json
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .console import Trace
from .tools import ToolRegistry

Message = dict[str, Any]


@dataclass(slots=True)
class TurnResult:
    text: str
    elapsed_seconds: float
    tool_calls: int


class OllamaToolAgent:
    """Native Ollama streaming client with a transparent tool-observation loop."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        tools: ToolRegistry | None = None,
        max_steps: int = 6,
        trace: Trace | None = None,
        fallback_text: str = "I did not produce a response. Please try again.",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.tools = tools or ToolRegistry()
        self.max_steps = max_steps
        self.trace = trace or Trace()
        self.fallback_text = fallback_text

    def _stream(self, messages: list[Message], on_token: Callable[[str], None]) -> tuple[str, list[Message]]:
        body = {
            "model": self.model,
            "messages": messages,
            "tools": self.tools.schemas(),
            "stream": True,
            "think": False,
            "keep_alive": "10m",
            "options": {"temperature": 0.2, "num_predict": 220},
        }
        request = urllib.request.Request(
            self.base_url + "/api/chat", data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        content: list[str] = []
        calls: list[Message] = []
        with urllib.request.urlopen(request, timeout=180) as response:
            for line in response:
                event = json.loads(line)
                if event.get("error"):
                    raise RuntimeError(event["error"])
                message = event.get("message", {})
                token = message.get("content", "")
                if token:
                    content.append(token)
                    on_token(token)
                calls.extend(message.get("tool_calls") or [])
        return "".join(content).strip(), calls

    def run(self, messages: list[Message], on_token: Callable[[str], None] | None = None) -> TurnResult:
        started = time.perf_counter()
        emitted = 0
        tool_count = 0

        def emit(token: str) -> None:
            nonlocal emitted
            emitted += 1
            if on_token:
                on_token(token)

        for step in range(1, self.max_steps + 1):
            self.trace.event("thinking", f"model step {step}...", "33")
            content, calls = self._stream(messages, emit)
            if not calls:
                text = content or self.fallback_text
                if not content:
                    self.trace.event("fallback", text, "31")
                return TurnResult(text, time.perf_counter() - started, tool_count)

            messages.append({"role": "assistant", "content": content, "tool_calls": calls})
            for call in calls:
                function = call.get("function", {})
                name = function.get("name", "")
                arguments = function.get("arguments") or {}
                self.trace.event("action", f"{name}({json.dumps(arguments, ensure_ascii=False)})", "35")
                result = self.tools.call(name, arguments)
                tool_count += 1
                serialized = json.dumps(result, ensure_ascii=False)
                self.trace.event("result", serialized[:1_200], "34")
                messages.append({"role": "tool", "tool_name": name, "content": serialized})
        raise RuntimeError(f"Agent exceeded {self.max_steps} model/tool steps")
