"""Tools with explicit state, useful for reliable follow-up commands.

Try: "Lägg till kaffe på listan", followed by "Vad finns på den?"
"""

from dataclasses import dataclass, field

from offline_voice_agent import VoiceAgent, VoiceAgentConfig
from offline_voice_agent.console import Trace
from offline_voice_agent.models import load_recognizer, load_synthesizer
from offline_voice_agent.ollama import OllamaToolAgent
from offline_voice_agent.tools import Tool, ToolRegistry


@dataclass
class ShoppingList:
    items: list[str] = field(default_factory=list)

    def add(self, item: str) -> dict:
        clean = item.strip()
        if not clean:
            raise ValueError("Item cannot be empty")
        self.items.append(clean)
        return {"added": clean, "items": self.items.copy()}

    def read(self) -> dict:
        return {"items": self.items.copy(), "count": len(self.items)}


state = ShoppingList()
tools = ToolRegistry()
tools.register(Tool(
    name="add_shopping_item",
    description="Add one item to the local shopping list.",
    parameters={
        "type": "object",
        "properties": {"item": {"type": "string"}},
        "required": ["item"],
    },
    handler=state.add,
))
tools.register(Tool(
    name="read_shopping_list",
    description="Read every item currently on the local shopping list.",
    parameters={"type": "object", "properties": {}, "required": []},
    handler=state.read,
))

config = VoiceAgentConfig.from_env()
trace = Trace()
agent = VoiceAgent(
    config,
    load_recognizer(config.stt_model),
    load_synthesizer(config.tts_model, config.language),
    OllamaToolAgent(
        base_url=config.ollama_url,
        model=config.llm_model,
        tools=tools,
        trace=trace,
    ),
    trace,
)
agent.run_forever()
