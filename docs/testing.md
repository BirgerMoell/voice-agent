# Testing voice systems

A voice agent needs tests at three levels.

## Unit tests

Keep these deterministic and model-free:

- tool schema and dispatch;
- argument validation;
- arithmetic and state reducers;
- configuration;
- history truncation;
- empty-response fallbacks.

Run them with:

```bash
uv run --extra dev pytest
```

## Component tests

Validate one real boundary at a time:

- transcribe a fixed WAV and inspect the transcript;
- synthesize a fixed sentence and verify non-empty audio and sample rate;
- call Ollama in text mode;
- execute each tool with safe fixture data;
- play a WAV and press Space in a real terminal.

Exact generated wording is a poor assertion. Test observable invariants: a tool was called, a file
exists, an exit code is zero, audio has samples, or a transcript contains the critical entity.

## End-to-end tests

Use a short scripted scenario:

1. Ask a factual question with no tool.
2. Ask a calculation that must call a tool.
3. Interrupt playback with Space.
4. Ask a follow-up that relies on history.
5. Force a tool error and verify the loop survives.

Record latency for every boundary. A functionally correct agent that pauses unpredictably will
still feel broken.

## Acoustic testing

Test laptop speakers, headphones, quiet rooms, HVAC noise, distant speech, accents, names, numbers,
and users who pause mid-sentence. Automated audio fixtures cannot replace these sessions.
