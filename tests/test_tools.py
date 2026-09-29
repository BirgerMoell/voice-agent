import pytest

from offline_voice_agent.tools import Tool, ToolRegistry, calculator_tool, safe_calculate


def test_calculator_handles_arithmetic():
    assert safe_calculate("(27 * 14) + 2")["result"] == 380


@pytest.mark.parametrize("expression", ["__import__('os')", "2 ** 99", "[1, 2]"])
def test_calculator_rejects_unsafe_or_excessive_expressions(expression):
    with pytest.raises(ValueError):
        safe_calculate(expression)


def test_registry_dispatches_json_arguments():
    registry = ToolRegistry().register(calculator_tool())

    result = registry.call("calculate", '{"expression":"8/2"}')

    assert result["result"] == 4


def test_registry_turns_failures_into_observations():
    registry = ToolRegistry().register(calculator_tool())

    assert "error" in registry.call("missing", {})
    assert "error" in registry.call("calculate", "not json")


def test_registry_rejects_duplicate_names():
    noop = Tool("same", "test", {"type": "object", "properties": {}}, lambda: None)
    registry = ToolRegistry().register(noop)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(noop)
