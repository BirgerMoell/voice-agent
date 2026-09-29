# Security

The default calculator tool has no external side effects. `--enable-bash` is an explicit high-risk
option that lets the model execute arbitrary commands with the current user's permissions. Do not
enable it around untrusted speech, prompts, files, or tool output, and do not expose this CLI as a
remote service.

Prefer narrow tools with allowlisted resources, bounded inputs, timeouts, and confirmation for
consequential actions. Never rely on the system prompt as an authorization mechanism.

Please report vulnerabilities privately to the repository owner rather than opening a public issue.
