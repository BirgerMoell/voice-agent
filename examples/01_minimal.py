"""Smallest complete speech-to-speech assembly.

Run with:
    uv run --extra apple python examples/01_minimal.py
"""

from offline_voice_agent import VoiceAgent, VoiceAgentConfig
from offline_voice_agent.console import Trace
from offline_voice_agent.models import load_recognizer, load_synthesizer
from offline_voice_agent.ollama import OllamaToolAgent
from offline_voice_agent.tools import ToolRegistry, calculator_tool

config = VoiceAgentConfig.from_env()
trace = Trace()
tools = ToolRegistry().register(calculator_tool())

agent = VoiceAgent(
    config=config,
    recognizer=load_recognizer(config.stt_model),
    synthesizer=load_synthesizer(config.tts_model, config.language),
    brain=OllamaToolAgent(
        base_url=config.ollama_url,
        model=config.llm_model,
        tools=tools,
        trace=trace,
    ),
    trace=trace,
)
agent.run_forever()
