from __future__ import annotations

from .config import VoiceAgentConfig
from .console import Trace
from .microphone import Microphone, transcribe_pcm
from .models import SpeechRecognizer, SpeechSynthesizer
from .ollama import Message, OllamaToolAgent
from .playback import play_audio


class VoiceAgent:
    """Coordinates turn-taking while keeping every subsystem replaceable."""

    def __init__(
        self,
        config: VoiceAgentConfig,
        recognizer: SpeechRecognizer,
        synthesizer: SpeechSynthesizer,
        brain: OllamaToolAgent,
        trace: Trace | None = None,
    ) -> None:
        self.config = config
        self.recognizer = recognizer
        self.synthesizer = synthesizer
        self.brain = brain
        self.trace = trace or Trace()
        self.history: list[Message] = []

    def text_turn(self, utterance: str) -> str:
        messages: list[Message] = [
            {"role": "system", "content": self.config.system_prompt},
            *self.history,
            {"role": "user", "content": utterance},
        ]
        began = False

        def token(token_text: str) -> None:
            nonlocal began
            if not began:
                self.trace.event("response", "", "32")
                began = True
            print(token_text, end="", flush=True)

        result = self.brain.run(messages, token)
        if began:
            print(flush=True)
        self.trace.event("answered", f"{result.elapsed_seconds:.2f}s, {result.tool_calls} tool call(s)", "32")
        self.history.extend([
            {"role": "user", "content": utterance},
            {"role": "assistant", "content": result.text},
        ])
        self.history = self.history[-self.config.history_messages:]
        return result.text

    def speak(self, text: str, microphone: Microphone | None = None) -> bool:
        started = self.trace.timer()
        audio = self.synthesizer.synthesize(text)
        self.trace.event("voice", f"synthesized in {self.trace.elapsed(started)}", "36")
        self.trace.event("speaking", "press SPACE to interrupt", "36")
        return play_audio(
            audio, self.synthesizer.sample_rate, microphone,
            space_to_talk=self.config.space_to_talk,
            voice_barge_in=self.config.voice_barge_in,
        )

    def run_forever(self) -> None:
        microphone = Microphone(self.config)
        microphone.start()
        self.trace.event("ready", "speak now; Ctrl+C stops", "32")
        try:
            while True:
                partial = ""

                def preview(raw: bytes) -> None:
                    nonlocal partial
                    candidate = transcribe_pcm(self.recognizer, raw, self.config.sample_rate)
                    if candidate and candidate != partial:
                        partial = candidate
                        self.trace.event("live", f'"{partial}"', "90")

                raw = microphone.capture(preview)
                utterance = transcribe_pcm(self.recognizer, raw, self.config.sample_rate)
                self.trace.event("transcript", f'"{utterance}"', "36")
                if not utterance:
                    continue
                response = self.text_turn(utterance)
                self.speak(response, microphone)
                self.trace.event("listening", "speak now", "32")
        except KeyboardInterrupt:
            self.trace.event("stopped", "goodbye", "90")
        finally:
            microphone.close()
