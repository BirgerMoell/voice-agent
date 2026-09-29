"""A narrow file-writing tool is safer and more reliable than arbitrary Bash."""

from pathlib import Path

from offline_voice_agent import VoiceAgent, VoiceAgentConfig
from offline_voice_agent.console import Trace
from offline_voice_agent.models import load_recognizer, load_synthesizer
from offline_voice_agent.ollama import OllamaToolAgent
from offline_voice_agent.tools import Tool, ToolRegistry

WORKSPACE = (Path.cwd() / "voice-agent-output").resolve()
WORKSPACE.mkdir(exist_ok=True)


def write_note(filename: str, content: str) -> dict[str, str | int]:
    safe_name = Path(filename).name
    if safe_name != filename or not safe_name.endswith(".txt"):
        raise ValueError("filename must be a plain .txt filename")
    target = (WORKSPACE / safe_name).resolve()
    if target.parent != WORKSPACE:
        raise ValueError("path escapes the output directory")
    target.write_text(content, encoding="utf-8")
    return {"path": str(target), "characters": len(content)}


writer = Tool(
    name="write_text_note",
    description="Write UTF-8 text to a .txt file in the dedicated output directory.",
    parameters={
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "A plain filename ending in .txt"},
            "content": {"type": "string"},
        },
        "required": ["filename", "content"],
    },
    handler=write_note,
)

config = VoiceAgentConfig.from_env()
trace = Trace()
agent = VoiceAgent(
    config,
    load_recognizer(config.stt_model),
    load_synthesizer(config.tts_model, config.language),
    OllamaToolAgent(
        base_url=config.ollama_url,
        model=config.llm_model,
        tools=ToolRegistry().register(writer),
        trace=trace,
    ),
    trace,
)
agent.run_forever()
