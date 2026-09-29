# Architecture and event flow

The implementation uses a pipeline architecture because it gives an application explicit
control over privacy, prompts, tools, logs, latency, and failure handling.

## One turn

1. `Microphone` continuously receives 30 ms signed 16-bit PCM frames.
2. WebRTC VAD classifies each frame as speech or non-speech.
3. A 300 ms pre-roll keeps the first consonant from being clipped.
4. After speech begins, 600 ms of silence completes the turn.
5. `transcribe_pcm` writes a temporary WAV because model adapters consume file paths.
6. A local `SpeechRecognizer` returns text.
7. `OllamaToolAgent` streams the local LLM response.
8. If the model emits tool calls, `ToolRegistry` executes them and the observations are appended.
9. The LLM sees those observations and produces a grounded final response.
10. A local `SpeechSynthesizer` creates an audio waveform.
11. macOS `afplay` plays the WAV while Space and optional microphone barge-in are monitored.

## Ownership boundaries

Each module owns one kind of state:

| Module | Owns | Does not own |
| --- | --- | --- |
| `Microphone` | Frame queue, VAD, turn boundaries | Transcription or conversation |
| Recognizer | Audio-to-text model | Prompting or playback |
| `OllamaToolAgent` | One model/tool loop | Microphone or TTS |
| `ToolRegistry` | Schemas, dispatch, error observations | Model policy |
| Synthesizer | Text-to-waveform model | Playback or interruption |
| Playback | Temporary WAV, `afplay`, interruption | Conversation history |
| `VoiceAgent` | Orchestration and short history | Backend implementation details |

This prevents a common failure mode: one callback knowing about the microphone, the LLM,
network APIs, subprocesses, and speakers simultaneously.

## Conversation history

The default keeps the last eight user/assistant messages. Tool traces are retained inside their
turn while the model is deciding, but only the final user and assistant messages survive into
the next turn. Applications that need durable state should store explicit domain state rather
than relying on an ever-growing language-model context.

## Failure boundaries

- Tool exceptions become JSON observations so one broken integration does not kill audio.
- Empty model responses become a speakable fallback rather than crashing TTS.
- Playback restores terminal settings and deletes temporary audio in `finally` blocks.
- Bash timeouts terminate the whole subprocess group.
- Ctrl+C closes the microphone stream.

## Why not direct speech-to-speech?

Native speech-to-speech models can preserve emotion and reduce latency, but the pipeline is
easier to inspect and control. Every transcript, tool argument, observation, and answer is
visible. That makes this architecture excellent for offline applications, workshops, regulated
domains, and systems where deterministic tools matter more than vocal nuance.
