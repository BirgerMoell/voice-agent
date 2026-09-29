# From demo to a real offline agent

The reference CLI is deliberately small, but its boundaries are suitable for a serious local
application. Build outward from a narrow use case rather than giving the model every capability
on day one.

## 1. Define the job and the authority

Write down what the agent may observe and change. “Control a meeting room” is testable; “be a
general assistant” is not. For every action, decide whether it is:

- read-only and safe to execute immediately;
- reversible and safe to execute with visible feedback;
- consequential and requires explicit confirmation;
- outside the agent's authority.

Encode those rules in tool handlers and application state. A prompt is useful guidance, but it is
not a permission boundary.

## 2. Build narrow tools

Prefer `set_room_temperature(room, degrees)` over `run_bash(command)`. A narrow tool has a schema
the model can fill reliably, can validate its arguments, and can return structured evidence. Its
handler should follow this shape:

```python
def set_room_temperature(room: str, degrees: float) -> dict:
    if room not in ALLOWED_ROOMS:
        raise ValueError("Unknown room")
    if not 16 <= degrees <= 26:
        raise ValueError("Allowed range is 16–26°C")
    previous = controller.read(room)
    controller.write(room, degrees)
    return {"room": room, "previous": previous, "current": degrees}
```

The result tells the LLM what actually happened. The spoken answer should be based on that result,
never on an assumed success.

## 3. Represent state in code

Conversation history is useful for language, but it is a weak database. Keep device identifiers,
pending confirmations, timers, active documents, and user preferences in typed application state.
Tools should resolve phrases such as “turn it off” against that state and return an error when the
reference is ambiguous.

For durable state, persist only the fields you need in SQLite or another local store. Make retention
visible and provide a way to clear it. Raw audio usually does not need to be retained at all.

## 4. Add confirmation as a state machine

For a consequential action, do not ask the model to remember that confirmation is pending. Store a
short-lived proposal in code:

```text
requested → validated → awaiting_confirmation → executed | cancelled | expired
```

The confirmation turn should reference a stable proposal identifier and exact arguments. A generic
“yes” must not approve an old or unrelated action.

## 5. Make cancellation cooperative

Space-to-talk already stops playback. A production agent should propagate cancellation further:

1. stop audio playback;
2. cancel in-progress TTS generation;
3. cancel or ignore the current LLM stream;
4. cancel tools that declare themselves cancellable;
5. begin capture immediately.

Never terminate a write operation halfway unless its handler supports rollback. Some actions should
finish in the background and report their final state during the next turn.

## 6. Stream at each useful boundary

The LLM response is streamed to the terminal today, while TTS begins after the final answer. For
lower perceived latency, add a sentence segmenter between the LLM and TTS:

```text
LLM tokens → sentence boundary → TTS chunk → playback queue
```

Do not synthesize arbitrary token fragments. Wait for punctuation or a conservative character limit,
and never speak provisional text before the tool loop has completed. Otherwise the agent may announce
an action before knowing whether it succeeded.

## 7. Treat observability as a product feature

Capture monotonic timestamps for:

- speech start and end;
- final transcript;
- first model token;
- each tool request and completion;
- first synthesized sample;
- playback start and interruption.

Log structured events, not just formatted strings. Redact secrets at the tool boundary. Local-first
does not remove the need for privacy controls: transcripts and command output can still be sensitive.

## 8. Test scenarios, not exact prose

Build a table of representative utterances, including misrecognitions and incomplete requests. Assert
that the right tool and validated arguments were used. For acoustic testing, include the real room,
microphone, speaker, language switches, names, numbers, pauses, and interruptions.

A useful release gate is a recorded set of 20–50 tasks with:

- task completion rate;
- wrong-tool and wrong-argument rate;
- p50 and p95 end-of-speech to first-audio latency;
- interruption success rate;
- unrecovered conversation-loop crashes.

## 9. Package for offline deployment

Provision dependencies and model weights while connected, record model revisions and licenses, then
test with networking disabled. Cache locations differ across Ollama, Hugging Face, and MLX packages;
document or bundle them according to each model's license. Pin Python dependencies with `uv.lock`.

An offline acceptance test should verify:

1. the selected Ollama model is installed;
2. STT and TTS checkpoints are present;
3. the microphone and output device open;
4. one fixed WAV transcribes;
5. one sentence synthesizes and plays;
6. every offline tool completes without a network route.

## Suggested application structure

```text
my_agent/
├── app.py                 composition root
├── policy.py              permissions and confirmation rules
├── state.py               typed session and durable state
├── tools/
│   ├── calendar.py
│   ├── documents.py
│   └── devices.py
├── adapters/
│   ├── speech.py
│   └── inference.py
└── tests/
    ├── scenarios/
    ├── test_policy.py
    └── test_tools.py
```

Keep `app.py` boring: construct modules and connect them. Domain behavior belongs in state, policy,
and tool handlers, where it can be tested without audio or models.
