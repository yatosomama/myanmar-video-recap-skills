"""Free Microsoft Edge online TTS transport for Burmese narration."""

import os
import shutil
import subprocess
from pathlib import Path

from lib import run_cmd


DEFAULT_VOICE = "my-MM-ThihaNeural"


def synthesize_edge_tts(text, output_wav, rate="+0%", pitch="+0Hz"):
    """Write one Burmese segment as a mono PCM WAV using the edge-tts CLI."""
    voice = os.environ.get("EDGE_TTS_VOICE", DEFAULT_VOICE).strip()
    if not voice.startswith("my-MM-"):
        raise ValueError(
            f"Edge TTS voice must be a Burmese my-MM voice, got {voice!r}; "
            "use my-MM-ThihaNeural or my-MM-NilarNeural"
        )

    executable = os.environ.get("EDGE_TTS_BIN", "edge-tts")
    resolved = shutil.which(executable)
    if not resolved:
        raise RuntimeError(
            "edge-tts executable was not found; install it with `python -m pip install edge-tts` "
            "or set EDGE_TTS_BIN"
        )

    output_wav = Path(output_wav)
    output_mp3 = output_wav.with_suffix(".edge.mp3")
    command = [
        resolved,
        "--voice", voice,
        "--rate", rate,
        "--pitch", pitch,
        "--text", text,
        "--write-media", str(output_mp3),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired as exc:
        output_mp3.unlink(missing_ok=True)
        raise RuntimeError("Edge TTS timed out after 180 seconds") from exc
    if result.returncode != 0 or not output_mp3.is_file() or output_mp3.stat().st_size == 0:
        output_mp3.unlink(missing_ok=True)
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Edge TTS failed: {detail or 'no audio was written'}")

    try:
        converted = run_cmd([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(output_mp3),
            "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(output_wav),
        ])
        if converted.returncode != 0 or not output_wav.is_file() or output_wav.stat().st_size <= 44:
            detail = converted.stderr.strip() if converted.stderr else "invalid WAV output"
            output_wav.unlink(missing_ok=True)
            raise RuntimeError(f"Edge TTS audio conversion failed: {detail}")
    finally:
        output_mp3.unlink(missing_ok=True)

    return {"provider": "edge-tts", "voice": voice}
