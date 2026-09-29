# Troubleshooting

## Microphone permission

If capture blocks or returns no audio, enable Terminal or your editor under macOS microphone
privacy settings, then restart the process.

## No input device

List devices:

```bash
uv run python -c "import sounddevice as sd; print(sd.query_devices())"
```

Install PortAudio if needed:

```bash
brew install portaudio
```

## Ollama connection refused

```bash
ollama serve
ollama list
ollama pull qwen3.5:4b
```

Override the server with `OLLAMA_URL`.

## First run is slow

The first run downloads checkpoints and builds caches. Run once before a workshop. Subsequent
runs should report cached files and start much faster.

## TTS says text is empty

This usually means the LLM returned no content after a tool-routing failure. The included Ollama
adapter substitutes a non-empty fallback. Custom brains should preserve that invariant.

## Agent interrupts itself

Do not use `--barge-in` through laptop speakers. The speaker output is speech and can trigger VAD.
Use default Space-to-interrupt or wear headphones.

## Space does not interrupt

Space capture requires an interactive TTY. It will not activate when stdin is redirected or the
agent runs as a background service. A GUI should call its playback-cancel method directly.

## Model does not call tools

- Confirm the model supports native tool calling.
- Make the tool name and description outcome-oriented.
- Keep schemas small.
- State in the system prompt that tool-owned facts must not be guessed.
- For critical routing, implement a host-side policy rather than relying only on prompting.
