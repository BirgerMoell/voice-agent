# Offline Voice Agent

<p align="center">
  <img src="assets/voice-agent-hero.png" alt="A local voice-agent pipeline flowing from a microphone through speech recognition, reasoning, tools, and speech synthesis on a laptop" width="100%">
</p>

<p align="center">
  <strong>Speak. Think. Act. Entirely on your Mac.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-22c55e.svg"></a>
  <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-3776ab.svg">
  <img alt="Apple Silicon" src="https://img.shields.io/badge/Apple%20Silicon-optimized-8b5cf6.svg">
  <img alt="Local first" src="https://img.shields.io/badge/inference-local-06b6d4.svg">
  <img alt="Swedish and English" src="https://img.shields.io/badge/voice-Swedish%20%7C%20English-f97316.svg">
</p>

A fast, inspectable speech-to-speech agent for Apple Silicon. Talk naturally, watch the live
transcript, let a local LLM use real tools, hear the answer, and interrupt it whenever you want.
Every major component is replaceable, so the same foundation can power a workshop demo, a focused
desktop assistant, or a production-grade offline application.

> **No API key. No audio sent to a cloud model. No black box.** After one-time provisioning, the
> default pipeline runs locally from microphone to spoken response.

After the one-time model downloads, the default pipeline does not send audio, transcripts,
prompts, tool results, or generated speech to a cloud service.

```text
microphone → WebRTC VAD → local STT → Ollama + tools → local TTS → afplay
     ↑                                                            │
     └──────────── Space-to-interrupt / optional voice barge-in ───┘
```

This repository is both a working agent and a reference implementation. Each boundary is a
small interface so you can replace one model or subsystem without rewriting the rest.

## See one turn come alive

Ask: **“Vad är 27 gånger 14?”**

```text
listening   speak now
live        "Vad är 27 gånger..."
transcript  "Vad är 27 gånger 14?"
thinking    model step 1...
action      calculate({"expression":"27*14"})
result      {"expression":"27*14","result":378}
thinking    model step 2...
response    Det är 378.
voice       synthesized in 0.61s
speaking    press SPACE to interrupt
```

The transcript, reasoning steps, tool arguments, verified result, and speech latency remain visible.
That observability makes the agent fun to demo—and practical to debug.

## Why build on this?

- **It feels immediate.** Voice activity detection, model streaming, fast local TTS, and interruption
  keep the interaction moving.
- **It can actually do things.** Typed tools turn speech into grounded calculations, files, device
  controls, or your own application actions.
- **It is yours.** The default runtime keeps recordings, transcripts, prompts, and responses on the
  machine.
- **It teaches the real architecture.** Every module is small enough to understand, replace, and
  test independently.
- **It fails visibly.** Tool errors become observations instead of silently turning into invented
  success stories.

## What works

- Swedish-first transcription with `KlangAI/pianissimo-sv-mlx-8bit`
- Multilingual transcription with Parakeet MLX
- Local reasoning and native function calling through Ollama
- Fast Swedish speech with Supertonic 3
- Small English speech with Kokoro
- Partial transcripts while the user is talking
- WebRTC voice activity detection and silence-based turn completion
- Streaming LLM text with visible tool calls and observations
- Space-to-interrupt that works safely through laptop speakers
- Optional hands-free voice barge-in for headphone use
- A typed, extensible tool registry
- Explicit opt-in unrestricted Bash tool
- Empty-response and tool-error handling that keep the voice loop alive

## Recommended hardware

The defaults target a 32 GB Apple Silicon Mac. They also work on many smaller machines, but
model choice matters more as memory shrinks.

| Component | Default | Why |
| --- | --- | --- |
| STT | Pianissimo MLX 8-bit | Strong Swedish recognition, Apple GPU acceleration |
| LLM | `qwen3.5:4b` in Ollama | Low first-token latency and reliable enough tool calling |
| TTS | Supertonic 3 | Fast Swedish synthesis on CPU, leaving GPU memory for STT/LLM |
| VAD | WebRTC VAD | Tiny, deterministic, and offline |
| Playback | macOS `afplay` | No extra playback daemon or service |

For English, use Parakeet plus Kokoro:

```bash
voice-agent --language en --stt parakeet --tts kokoro
```

## Your first conversation

Prerequisites:

- macOS on Apple Silicon
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/)
- PortAudio (`brew install portaudio` if `sounddevice` cannot find an input device)

```bash
git clone https://github.com/BirgerMoell/voice-agent.git
cd voice-agent
./scripts/bootstrap_macos.sh
uv run --extra apple voice-agent
```

The bootstrap script installs the Python environment, starts Ollama when necessary, and pulls
the default LLM. Speech models download on first use. Later runs use the local model caches.

Then say something. Try these:

```text
Vad är 144 delat med 12?
Explain local-first AI in one sentence.
Berätta något roligt om rymden.
```

On first microphone use, allow Terminal or your editor under:

`System Settings → Privacy & Security → Microphone`

Press **Space** while speech is playing to stop it and immediately return to listening. This
mode clears speaker audio queued in the microphone and therefore works with laptop speakers.

For hands-free interruption, use headphones and enable microphone barge-in:

```bash
uv run --extra apple voice-agent --barge-in
```

## Text-mode smoke tests

Test the LLM/tool path without microphone or audio playback:

```bash
uv run --extra apple voice-agent --text "What is 27 * 14?" --no-play
```

Test synthesis too:

```bash
uv run --extra apple voice-agent --text "Säg hej till workshopen"
```

## Modularity

The package separates policy from mechanism:

```text
src/offline_voice_agent/
├── agent.py       conversation lifecycle and history
├── cli.py         one concrete assembly of the components
├── config.py      runtime policy and model selection
├── console.py     replaceable observability surface
├── microphone.py  capture, VAD, pre-roll, turn completion
├── models.py      STT and TTS adapters
├── ollama.py      streaming LLM and tool loop
├── playback.py    playback and interruption
└── tools.py       typed tool registry and example tools
```

`VoiceAgent` depends on interfaces, not specific model implementations. A production app can
replace `PianissimoRecognizer`, `SupertonicSynthesizer`, `OllamaToolAgent`, or `Trace`
independently.

Read [Architecture](docs/architecture.md) for the data flow and ownership rules, and
[Modularity](docs/modularity.md) for extension patterns.

## Add a tool

A tool is a JSON schema plus an ordinary Python function:

```python
from datetime import datetime
from offline_voice_agent.tools import Tool, ToolRegistry

def local_time() -> dict:
    return {"time": datetime.now().astimezone().isoformat(timespec="seconds")}

clock = Tool(
    name="get_local_time",
    description="Read the actual local computer time.",
    parameters={"type": "object", "properties": {}, "required": []},
    handler=local_time,
)

tools = ToolRegistry().register(clock)
```

Pass the registry to `OllamaToolAgent`. The loop prints the model's arguments, executes the
function, serializes its result, and returns the observation to the model before it speaks.

See [examples/02_custom_tool.py](examples/02_custom_tool.py) for a complete runnable assembly.

## Unrestricted Bash mode

Bash is intentionally not registered by default. Enable it only for a controlled demo or an
agent whose OS account and filesystem are appropriately sandboxed:

```bash
uv run --extra apple voice-agent --enable-bash
```

That flag grants the local model the same shell authority as the current macOS user. It is not
an allowlisted toy shell. Commands have a timeout and bounded returned output, but they may
read, change, or delete anything your account can. Read [Tools and safety](docs/tools-and-safety.md).

## Build your own agent

The smallest programmatic assembly is:

```python
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
```

From there, customize the system prompt, tool registry, model adapters, persistence, or UI.

The examples are ordered by complexity:

- [`01_minimal.py`](examples/01_minimal.py): the complete default pipeline;
- [`02_custom_tool.py`](examples/02_custom_tool.py): a real-time clock tool;
- [`03_stateful_tools.py`](examples/03_stateful_tools.py): explicit state for reliable follow-ups;
- [`04_safe_workspace_tool.py`](examples/04_safe_workspace_tool.py): constrained file output instead
  of unrestricted shell access.

## Offline does not mean preinstalled

There are two distinct phases:

1. **Provisioning:** packages and model weights are downloaded from PyPI, Hugging Face, and
   Ollama's registry.
2. **Inference:** microphone audio, transcripts, prompts, tool observations, and speech remain
   local with the default tools.

If you add web, email, calendar, or remote database tools, those tools are not offline merely
because the LLM is local. Make data boundaries explicit in the UI and documentation.

## Documentation

- [Architecture and event flow](docs/architecture.md)
- [Designing replaceable modules](docs/modularity.md)
- [Model selection and memory](docs/models.md)
- [Latency and natural turn-taking](docs/latency.md)
- [Tools, permissions, and safety](docs/tools-and-safety.md)
- [Testing voice systems](docs/testing.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Taking the agent from demo to production](docs/building-a-real-agent.md)

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

The unit tests avoid loading speech checkpoints or requiring a microphone. Hardware and model
validation is described separately in [Testing](docs/testing.md).

## License

MIT. Model checkpoints have their own licenses; review them before redistribution or commercial
deployment.
