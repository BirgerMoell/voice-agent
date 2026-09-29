# Latency and natural turn-taking

Voice quality is dominated by the pauses between components.

## Latency budget

Track at least:

```text
end-of-speech detection
+ final transcription
+ LLM first token
+ complete response or first speakable chunk
+ TTS generation
+ playback startup
```

The included pipeline synthesizes the full response before playback. This is simple and reliable.
For longer answers, split at sentence boundaries and synthesize/play bounded chunks on separate
queues. Never send arbitrary token fragments to TTS; punctuation and phrase boundaries affect
prosody.

## Turn completion

Short silence improves responsiveness but can cut off reflective speakers. Long silence feels
sluggish. The default 600 ms is a starting point. Tune it with real users and preserve pre-roll
so initial consonants are not lost.

## Partial transcripts

The reference implementation periodically retranscribes the accumulated utterance. This is easy
to understand but duplicates work. A production recognizer with true incremental decoding should
replace it behind the same callback.

## Interruption modes

### Space-to-interrupt

Best default for laptop speakers. Space stops `afplay`, drains queued speaker echo, and returns to
capture. It is predictable and avoids acoustic echo cancellation.

### Voice barge-in

The microphone remains active while the agent talks. Use headphones or proper echo cancellation;
otherwise the agent's own speaker output may trigger VAD.

## Keep spoken responses short

Voice is sequential. A user cannot scan ahead as they can in text. Put detail in a screen or file
and speak the conclusion. Prompt for concise natural sentences, not Markdown lists.
