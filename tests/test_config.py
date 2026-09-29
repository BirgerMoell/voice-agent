from offline_voice_agent.config import VoiceAgentConfig


def test_defaults_are_strings(monkeypatch):
    for name in (
        "OLLAMA_URL", "VOICE_LLM_MODEL", "VOICE_STT_MODEL", "VOICE_TTS_MODEL", "VOICE_LANGUAGE",
    ):
        monkeypatch.delenv(name, raising=False)

    config = VoiceAgentConfig.from_env()

    assert config.ollama_url == "http://127.0.0.1:11434"
    assert config.llm_model == "qwen3.5:4b"
    assert config.language == "sv"


def test_environment_overrides(monkeypatch):
    monkeypatch.setenv("VOICE_LLM_MODEL", "local-test-model")
    monkeypatch.setenv("VOICE_LANGUAGE", "en")

    config = VoiceAgentConfig.from_env()

    assert config.llm_model == "local-test-model"
    assert config.language == "en"
