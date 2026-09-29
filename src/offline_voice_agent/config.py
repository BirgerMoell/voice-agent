from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class VoiceAgentConfig:
    """Runtime choices live here so the pipeline is not hard-coded."""

    ollama_url: str = "http://127.0.0.1:11434"
    llm_model: str = "qwen3.5:4b"
    stt_model: str = "pianissimo"
    tts_model: str = "supertonic"
    language: str = "sv"
    sample_rate: int = 16_000
    frame_ms: int = 30
    vad_aggressiveness: int = 2
    silence_ms: int = 600
    pre_roll_ms: int = 300
    partial_interval_ms: int = 1_200
    history_messages: int = 8
    max_agent_steps: int = 6
    space_to_talk: bool = True
    voice_barge_in: bool = False
    system_prompt: str = (
        "You are a concise local voice assistant. Answer in the user's language as natural "
        "speech without Markdown. Use tools for facts or actions they own. Never invent tool output."
    )

    @classmethod
    def from_env(cls) -> VoiceAgentConfig:
        defaults = cls()
        return cls(
            ollama_url=os.getenv("OLLAMA_URL", defaults.ollama_url),
            llm_model=os.getenv("VOICE_LLM_MODEL", defaults.llm_model),
            stt_model=os.getenv("VOICE_STT_MODEL", defaults.stt_model),
            tts_model=os.getenv("VOICE_TTS_MODEL", defaults.tts_model),
            language=os.getenv("VOICE_LANGUAGE", defaults.language),
        )
