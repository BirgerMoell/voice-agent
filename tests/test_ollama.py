from offline_voice_agent.ollama import OllamaToolAgent
from offline_voice_agent.tools import ToolRegistry, calculator_tool


def test_agent_executes_tool_then_returns_final_answer(monkeypatch):
    agent = OllamaToolAgent(
        base_url="http://unused",
        model="test",
        tools=ToolRegistry().register(calculator_tool()),
    )
    replies = iter([
        ("", [{"function": {"name": "calculate", "arguments": {"expression": "6*7"}}}]),
        ("The answer is 42.", []),
    ])
    monkeypatch.setattr(agent, "_stream", lambda messages, on_token: next(replies))
    messages = [{"role": "user", "content": "What is six times seven?"}]

    result = agent.run(messages)

    assert result.text == "The answer is 42."
    assert result.tool_calls == 1
    assert messages[-1]["role"] == "tool"
    assert '"result": 42' in messages[-1]["content"]


def test_agent_uses_fallback_for_empty_model_response(monkeypatch):
    agent = OllamaToolAgent(base_url="http://unused", model="test", fallback_text="Try again")
    monkeypatch.setattr(agent, "_stream", lambda messages, on_token: ("", []))

    result = agent.run([])

    assert result.text == "Try again"
