from __future__ import annotations

import argparse
from pathlib import Path

from .agent import VoiceAgent
from .config import VoiceAgentConfig
from .console import Trace
from .models import load_recognizer, load_synthesizer
from .ollama import OllamaToolAgent
from .tools import ToolRegistry, bash_tool, calculator_tool


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run a fully local modular voice agent")
    result.add_argument("--text", help="Run one text turn instead of opening the microphone")
    result.add_argument("--no-play", action="store_true", help="Do not synthesize or play --text output")
    result.add_argument("--language", choices=["sv", "en"])
    result.add_argument("--stt", choices=["pianissimo", "parakeet"])
    result.add_argument("--tts", choices=["supertonic", "kokoro"])
    result.add_argument("--model", help="Installed Ollama model name")
    result.add_argument("--enable-bash", action="store_true",
                        help="Opt in to unrestricted Bash execution as the current user")
    result.add_argument("--barge-in", action="store_true",
                        help="Hands-free speech interruption; use headphones")
    result.add_argument("--no-space-to-talk", action="store_true")
    return result


def main() -> None:
    args = parser().parse_args()
    config = VoiceAgentConfig.from_env()
    if args.language:
        config.language = args.language
    if args.stt:
        config.stt_model = args.stt
    if args.tts:
        config.tts_model = args.tts
    if args.model:
        config.llm_model = args.model
    config.voice_barge_in = args.barge_in
    config.space_to_talk = not args.no_space_to_talk

    trace = Trace()
    tools = ToolRegistry().register(calculator_tool())
    if args.enable_bash:
        tools.register(bash_tool(str(Path.cwd())))
        trace.event("warning", "unrestricted Bash is enabled", "31")

    brain = OllamaToolAgent(
        base_url=config.ollama_url, model=config.llm_model, tools=tools,
        max_steps=config.max_agent_steps, trace=trace,
        fallback_text=("Jag fick inget svar. Försök igen." if config.language == "sv"
                       else "I did not get a response. Please try again."),
    )

    # Text-only mode is intentionally lightweight: it proves the LLM/tool loop without loading
    # several gigabytes of speech models. This is useful in CI and during tool development.
    if args.text and args.no_play:
        trace.event("models", f"LLM={config.llm_model}; speech models skipped")
        printed = False

        def token(value: str) -> None:
            nonlocal printed
            if not printed:
                print("\nresponse   ", end="", flush=True)
                printed = True
            print(value, end="", flush=True)

        result = brain.run([
            {"role": "system", "content": config.system_prompt},
            {"role": "user", "content": args.text},
        ], token)
        if printed:
            print()
        trace.event("answered", f"{result.elapsed_seconds:.2f}s, {result.tool_calls} tool call(s)", "32")
        return

    trace.event("loading", "local speech models", "33")
    recognizer = load_recognizer(config.stt_model)
    synthesizer = load_synthesizer(config.tts_model, config.language)
    agent = VoiceAgent(config, recognizer, synthesizer, brain, trace)
    trace.event("models", f"STT={recognizer.model_id} LLM={config.llm_model} TTS={synthesizer.model_id}")

    if args.text:
        response = agent.text_turn(args.text)
        if not args.no_play:
            agent.speak(response)
    else:
        agent.run_forever()


if __name__ == "__main__":
    main()
