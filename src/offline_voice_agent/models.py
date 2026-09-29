from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any

PIANISSIMO = "KlangAI/pianissimo-sv-mlx-8bit"
PARAKEET = "mlx-community/parakeet-tdt-0.6b-v3"
SUPERTONIC = "Supertone/supertonic-3"
KOKORO = "mlx-community/Kokoro-82M-bf16"


class SpeechRecognizer:
    def transcribe(self, audio_path: str | Path) -> str:
        raise NotImplementedError


class PianissimoRecognizer(SpeechRecognizer):
    """Swedish-first MLX Whisper model loaded from its Hugging Face snapshot."""

    def __init__(self, model_id: str = PIANISSIMO) -> None:
        from huggingface_hub import snapshot_download

        model_path = snapshot_download(model_id)
        if model_path not in sys.path:
            sys.path.insert(0, model_path)
        self.loader = importlib.import_module("pianissimo_mlx")
        self.model = self.loader.load(model_path)
        self.model_id = model_id

    def transcribe(self, audio_path: str | Path) -> str:
        return self.loader.transcribe(self.model, str(audio_path)).text.strip()


class ParakeetRecognizer(SpeechRecognizer):
    """Multilingual fallback using the MLX Audio adapter."""

    def __init__(self, model_id: str = PARAKEET) -> None:
        from mlx_audio.stt.utils import load

        self.model = load(model_id)
        self.model_id = model_id

    def transcribe(self, audio_path: str | Path) -> str:
        return self.model.generate(str(audio_path)).text.strip()


class SpeechSynthesizer:
    sample_rate: int

    def synthesize(self, text: str) -> Any:
        raise NotImplementedError


class SupertonicSynthesizer(SpeechSynthesizer):
    """Fast local Swedish or English TTS; runs on CPU and leaves the GPU to the LLM."""

    def __init__(self, language: str = "sv", voice: str = "F1") -> None:
        from supertonic import TTS

        self.model = TTS(auto_download=True)
        self.style = self.model.get_voice_style(voice_name=voice)
        self.language = language
        self.model_id = SUPERTONIC
        self.sample_rate = int(self.model.sample_rate)

    def synthesize(self, text: str) -> Any:
        import numpy as np

        if not text.strip():
            raise ValueError("Cannot synthesize empty text")
        audio, _ = self.model.synthesize(text, voice_style=self.style, lang=self.language)
        return np.asarray(audio).squeeze()


class KokoroSynthesizer(SpeechSynthesizer):
    """Small English MLX voice model."""

    def __init__(self, model_id: str = KOKORO, voice: str = "af_heart") -> None:
        from mlx_audio.tts.utils import load_model

        self.model = load_model(model_id)
        self.model_id = model_id
        self.voice = voice
        self.sample_rate = 24_000

    def synthesize(self, text: str) -> Any:
        import numpy as np

        parts = list(self.model.generate(text=text, voice=self.voice, speed=1.0, lang_code="a"))
        if not parts:
            raise RuntimeError("Kokoro returned no audio")
        self.sample_rate = int(getattr(parts[0], "sample_rate", self.sample_rate))
        return np.concatenate([np.asarray(part.audio) for part in parts])


def load_recognizer(name: str | None = None) -> SpeechRecognizer:
    selected = (name or os.getenv("VOICE_STT_MODEL") or "pianissimo").casefold()
    if selected in {"pianissimo", "swedish", "sv", PIANISSIMO.casefold()}:
        return PianissimoRecognizer()
    if selected in {"parakeet", "multilingual", PARAKEET.casefold()}:
        return ParakeetRecognizer()
    raise ValueError("Unknown STT backend. Use pianissimo or parakeet.")


def load_synthesizer(name: str | None = None, language: str = "sv") -> SpeechSynthesizer:
    selected = (name or os.getenv("VOICE_TTS_MODEL") or
                ("supertonic" if language == "sv" else "kokoro")).casefold()
    if selected == "supertonic":
        return SupertonicSynthesizer(language)
    if selected == "kokoro":
        return KokoroSynthesizer()
    raise ValueError("Unknown TTS backend. Use supertonic or kokoro.")
