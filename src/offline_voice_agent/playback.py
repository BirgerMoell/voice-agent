from __future__ import annotations

import os
import select
import subprocess
import sys
import tempfile
import termios
import time
import tty

import numpy as np
import soundfile as sf

from .microphone import Microphone


def play_audio(
    audio,
    sample_rate: int,
    microphone: Microphone | None = None,
    *,
    space_to_talk: bool = True,
    voice_barge_in: bool = False,
) -> bool:
    """Play through macOS and return True when playback was interrupted.

    Space-to-talk is speaker-safe: it stops playback and clears queued speaker echo before the
    next capture. Voice barge-in is hands-free but should be used with headphones.
    """
    if microphone:
        # A speech run from the preceding capture must not immediately interrupt new playback.
        microphone.consecutive_speech = 0

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        sf.write(temp.name, np.asarray(audio, dtype=np.float32), sample_rate)
        audio_path = temp.name

    keyboard_fd = None
    terminal_state = None
    if space_to_talk and sys.stdin.isatty():
        try:
            keyboard_fd = sys.stdin.fileno()
            terminal_state = termios.tcgetattr(keyboard_fd)
            tty.setcbreak(keyboard_fd)
        except (OSError, termios.error):
            keyboard_fd = terminal_state = None

    process = subprocess.Popen(
        ["/usr/bin/afplay", audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    interrupted = False
    keyboard_interrupt = False
    try:
        while process.poll() is None:
            if (
                keyboard_fd is not None
                and select.select([keyboard_fd], [], [], 0)[0]
                and os.read(keyboard_fd, 1) == b" "
            ):
                interrupted = keyboard_interrupt = True
                process.terminate()
                if microphone:
                    microphone.drain()
                break
            if voice_barge_in and microphone and microphone.consecutive_speech >= 3:
                interrupted = True
                process.terminate()
                break
            time.sleep(0.03)
        _, error = process.communicate(timeout=3)
        if process.returncode not in {0, -15}:
            raise RuntimeError(f"afplay failed: {error.decode().strip()}")
    finally:
        if process.poll() is None:
            process.kill()
        os.unlink(audio_path)
        if terminal_state is not None:
            termios.tcsetattr(keyboard_fd, termios.TCSADRAIN, terminal_state)
    if microphone and (not interrupted or keyboard_interrupt):
        microphone.drain()
    return interrupted
