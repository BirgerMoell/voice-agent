# Model selection

Model choice is a latency and memory budget, not a leaderboard decision.

## Speech recognition

### Pianissimo MLX 8-bit

Use for Swedish-first applications on Apple Silicon. It is the default because it handles the
language better than a generic multilingual model while remaining practical on a laptop.

### Parakeet TDT 0.6B

Use when users switch languages or Swedish specialization is unnecessary. It is smaller and a
useful fallback, but test your actual acoustic environment and vocabulary.

## Language model

The default `qwen3.5:4b` prioritizes conversational latency. Larger models improve planning and
tool reliability but increase time to first token and memory pressure. A voice agent that starts
speaking in 700 ms often feels more capable than one that gives a marginally better answer after
ten seconds.

Change it without code:

```bash
VOICE_LLM_MODEL=your-installed-model uv run --extra apple voice-agent
```

Your model needs native tool calling if tools are registered.

## Speech synthesis

### Supertonic 3

The default for Swedish. Its small CPU runtime lets Ollama and MLX speech recognition use unified
memory without fighting a second large GPU model.

### Kokoro 82M

The default English option. It is small, clear, and useful for prototyping.

## Memory planning

On unified-memory Macs, every model, KV cache, audio buffer, and application shares one pool.
Avoid loading several large models “just in case.” Choose one STT, one LLM, and one TTS backend,
load them once, and keep them warm.

## Evaluate with your workload

Measure:

- word error rate on your languages, names, and room acoustics;
- time from end-of-speech to final transcript;
- LLM time to first token and tool-call accuracy;
- TTS real-time factor and pronunciation;
- peak memory during a full turn, not each model in isolation.
