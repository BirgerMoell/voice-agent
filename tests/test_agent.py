from types import SimpleNamespace

from offline_voice_agent.agent import VoiceAgent
from offline_voice_agent.config import VoiceAgentConfig
from offline_voice_agent.ollama import TurnResult


class FakeBrain:
    def __init__(self):
        self.seen = []

    def run(self, messages, on_token):
        self.seen.append(messages.copy())
        on_token("A short answer")
        return TurnResult("A short answer", 0.01, 0)


def test_text_turn_preserves_bounded_history():
    config = VoiceAgentConfig(history_messages=2)
    brain = FakeBrain()
    agent = VoiceAgent(
        config,
        recognizer=SimpleNamespace(),
        synthesizer=SimpleNamespace(),
        brain=brain,
    )

    assert agent.text_turn("First") == "A short answer"
    agent.text_turn("Second")

    assert len(agent.history) == 2
    assert agent.history[0] == {"role": "user", "content": "Second"}
    assert brain.seen[1][1] == {"role": "user", "content": "First"}
