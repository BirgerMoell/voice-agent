# Tools, permissions, and safety

Local inference does not make tool execution safe. The model may misunderstand speech, choose the
wrong tool, or construct an incorrect argument.

## Tool design rules

- Make each tool narrow and name it after the outcome.
- Use JSON schemas with required fields and useful descriptions.
- Validate paths, identifiers, ranges, and output sizes in code.
- Return structured observations, including source and timestamps for live data.
- Convert exceptions into explicit errors the model can explain.
- Never treat model narration as evidence that an action occurred.

## Read versus write

Classify tools:

1. Pure computation, such as a calculator.
2. Read-only local state.
3. Read-only network state.
4. Reversible writes.
5. External communication or destructive actions.

Applications should make higher-impact capabilities visibly opt-in and may require confirmation
immediately before execution. Do not bury authorization in a broad system prompt.

## Bash mode

`--enable-bash` intentionally registers an unrestricted shell. The model runs as the current OS
user and can access the same files and credentials. Timeouts and output limits prevent runaway
logs; they do not create a security sandbox.

Safer production options include:

- a dedicated low-privilege OS account;
- a disposable container or VM;
- an allowlisted command tool instead of a shell;
- a workspace-only filesystem capability;
- human confirmation for destructive commands;
- an auditable event log.

## Prompt injection

Tool output, files, web pages, and transcripts can contain instructions. Treat them as data. Put
authorization and validation in host code, where a returned string cannot override them.
