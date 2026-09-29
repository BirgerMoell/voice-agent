#!/usr/bin/env bash
set -euo pipefail

MODEL="${VOICE_LLM_MODEL:-qwen3.5:4b}"

for command in uv ollama; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Missing required command: $command" >&2
    echo "Install uv from https://docs.astral.sh/uv/ and Ollama from https://ollama.com/." >&2
    exit 1
  fi
done

if ! ollama list >/dev/null 2>&1; then
  echo "Starting Ollama in the background..."
  ollama serve >"${TMPDIR:-/tmp}/voice-agent-ollama.log" 2>&1 &
  for _ in {1..30}; do
    ollama list >/dev/null 2>&1 && break
    sleep 1
  done
fi

if ! ollama list >/dev/null 2>&1; then
  echo "Ollama did not become ready. See ${TMPDIR:-/tmp}/voice-agent-ollama.log" >&2
  exit 1
fi

echo "Pulling local language model: $MODEL"
ollama pull "$MODEL"

echo "Installing the Apple Silicon speech stack..."
uv sync --extra apple --extra dev

echo
echo "Ready. Start the agent with:"
echo "  uv run --extra apple voice-agent"
echo
echo "Speech checkpoints are downloaded and cached on first use."
