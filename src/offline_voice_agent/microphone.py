from __future__ import annotations

import os
import queue
import tempfile
from collections import deque
from collections.abc import Callable
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad

from .config import VoiceAgentConfig
from .models import SpeechRecognizer


class Microphone:
    """WebRTC-VAD microphone with pre-roll, silence turn detection, and a shared frame queue."""

    def __init__(self, config: VoiceAgentConfig) -> None:
        self.config = config
        self.block = config.sample_rate * config.frame_ms // 1000
        self.frames: queue.Queue[tuple[bytes, bool]] = queue.Queue()
        self.vad = webrtcvad.Vad(config.vad_aggressiveness)
        self.consecutive_speech = 0
        self.stream = sd.RawInputStream(
            samplerate=config.sample_rate, blocksize=self.block, channels=1,
            dtype="int16", callback=self._callback,
        )

    def _callback(self, data, frames, timing, status) -> None:  # sounddevice callback signature
        raw = bytes(data)
        speech = self.vad.is_speech(raw, self.config.sample_rate)
        self.consecutive_speech = self.consecutive_speech + 1 if speech else 0
        self.frames.put((raw, speech))

    def start(self) -> None:
        self.stream.start()

    def close(self) -> None:
        self.stream.stop()
        self.stream.close()

    def drain(self) -> None:
        while True:
            try:
                self.frames.get_nowait()
            except queue.Empty:
                return

    def capture(self, on_partial: Callable[[bytes], None] | None = None) -> bytes:
        pre_frames = max(1, self.config.pre_roll_ms // self.config.frame_ms)
        silence_frames = max(1, self.config.silence_ms // self.config.frame_ms)
        preview_frames = max(1, self.config.partial_interval_ms // self.config.frame_ms)
        pre: deque[bytes] = deque(maxlen=pre_frames)
        captured: list[bytes] = []
        speaking = False
        silence = 0
        last_preview = 0
        while True:
            raw, speech = self.frames.get()
            if not speaking:
                pre.append(raw)
                if speech:
                    speaking = True
                    captured.extend(pre)
            else:
                captured.append(raw)
                silence = 0 if speech else silence + 1
                if on_partial and len(captured) - last_preview >= preview_frames and silence < 10:
                    last_preview = len(captured)
                    on_partial(b"".join(captured))
                if silence >= silence_frames:
                    return b"".join(captured)


def transcribe_pcm(recognizer: SpeechRecognizer, raw: bytes, sample_rate: int = 16_000) -> str:
    """Adapters receive a WAV path, while the microphone produces in-memory PCM."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        sf.write(temp.name, np.frombuffer(raw, dtype=np.int16), sample_rate, subtype="PCM_16")
        path = Path(temp.name)
    try:
        return recognizer.transcribe(path)
    finally:
        os.unlink(path)
