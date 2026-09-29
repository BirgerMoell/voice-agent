"""Add a typed local-time tool without changing the voice pipeline.

Try saying: "Vad är klockan exakt just nu?"
"""

from datetime import datetime

from offline_voice_agent import VoiceAgent, VoiceAgentConfig
from offline_voice_agent.console import Trace
from offline_voice_agent.models import load_recognizer, load_synthesizer
from offline_voice_agent.ollama import OllamaToolAgent
from offline_voice_agent.tools import Tool, ToolRegistry


def get_local_time() -> dict[str, str]:
    now = datetime.now().astimezone()
    return {
        "iso_time": now.isoformat(timespec="seconds"),
        "timezone": str(now.tzinfo),
    }


clock = Tool(
    name="get_local_time",
    description="Read the current time and timezone from this computer.",
    parameters={"type": "object", "properties": {}, "required": []},
    handler=get_local_time,
)

config = VoiceAgentConfig.from_env()
trace = Trace()
brain = OllamaToolAgent(
    base_url=config.ollama_url,
    model=config.llm_model,
    tools=ToolRegistry().register(clock),
    trace=trace,
)
agent = VoiceAgent(
    config,
    load_recognizer(config.stt_model),
    load_synthesizer(config.tts_model, config.language),
    brain,
    trace,
)
agent.run_forever()
