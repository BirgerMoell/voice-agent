# Designing replaceable modules

Modularity here means the orchestration code depends on behavior, not a particular checkpoint.

## Replace speech recognition

Implement one method:

```python
class MyRecognizer:
    model_id = "my-local-model"

    def transcribe(self, audio_path):
        return my_engine.transcribe(str(audio_path)).strip()
```

Pass the instance to `VoiceAgent`. Nothing in VAD, tools, history, or TTS changes.

## Replace speech synthesis

Expose a sample rate and return a one-dimensional numeric waveform:

```python
class MySynthesizer:
    model_id = "my-voice"
    sample_rate = 24_000

    def synthesize(self, text):
        return my_engine.generate(text)
```

If a backend streams chunks, add a playback adapter that accepts chunks rather than changing
the tool loop. Keep model generation and device playback separate.

## Replace Ollama

`VoiceAgent` only requires a brain with `run(messages, on_token) -> TurnResult`. A llama.cpp,
MLX-LM, or custom inference server adapter can preserve the same contract.

Important behaviors to preserve:

- stream visible text;
- represent tool calls structurally;
- append tool observations before final generation;
- cap the number of agent steps;
- return a non-empty fallback.

## Add application state

Do not hide state inside prompts when code can represent it explicitly. For example, a music
agent should keep `current_track_id` in an application state object. A follow-up like “pause it”
can then route deterministically instead of asking the model to recover an identifier from prose.

## Add a UI

Replace `Trace` with an event sink that emits structured objects to a desktop app, WebSocket,
or terminal UI. Avoid parsing console strings. Useful event types are:

- listening started;
- partial transcript;
- final transcript;
- first model token;
- tool requested;
- tool completed;
- synthesis completed;
- playback interrupted;
- turn failed.

## Dependency injection pays off

Tests can use fake recognizers, synthesizers, brains, and tools. They do not need microphone
permission or multi-gigabyte model weights. Hardware tests then focus on the boundaries that
unit tests cannot validate.
