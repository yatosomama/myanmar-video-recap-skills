"""Free Microsoft Edge online TTS transport and word timing for Burmese narration."""

import asyncio
import os
from pathlib import Path

from lib import run_cmd


DEFAULT_VOICE = "my-MM-ThihaNeural"


def synthesize_edge_tts(text, output_wav, rate="+0%", pitch="+0Hz"):
    """Write one Burmese segment as a mono PCM WAV with Edge TTS word timings."""
    voice = os.environ.get("EDGE_TTS_VOICE", DEFAULT_VOICE).strip()
    if not voice.startswith("my-MM-"):
        raise ValueError(
            f"Edge TTS voice must be a Burmese my-MM voice, got {voice!r}; "
            "use my-MM-ThihaNeural or my-MM-NilarNeural"
        )

    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError(
            "This Python environment cannot import edge-tts; install it with "
            "`python -m pip install edge-tts` so audio and word-boundary timings use the same runtime"
        ) from exc

    output_wav = Path(output_wav)
    output_mp3 = output_wav.with_suffix(".edge.mp3")
    output_subtitles = output_wav.with_suffix(".edge.srt")
    output_subtitles.unlink(missing_ok=True)

    async def _write_edge_audio_and_word_boundaries():
        communicate = edge_tts.Communicate(
            text, voice, rate=rate, pitch=pitch, boundary="WordBoundary"
        )
        submaker = edge_tts.SubMaker()
        with output_mp3.open("wb") as media_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    media_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)
        boundaries_srt = submaker.get_srt()
        if boundaries_srt.strip():
            output_subtitles.write_text(boundaries_srt, encoding="utf-8")

    try:
        asyncio.run(asyncio.wait_for(_write_edge_audio_and_word_boundaries(), timeout=180))
    except TimeoutError as exc:
        output_mp3.unlink(missing_ok=True)
        output_subtitles.unlink(missing_ok=True)
        raise RuntimeError("Edge TTS timed out after 180 seconds") from exc
    except Exception:
        output_mp3.unlink(missing_ok=True)
        output_subtitles.unlink(missing_ok=True)
        raise
    if (
        not output_mp3.is_file() or output_mp3.stat().st_size == 0
        or not output_subtitles.is_file() or output_subtitles.stat().st_size == 0
    ):
        output_mp3.unlink(missing_ok=True)
        output_subtitles.unlink(missing_ok=True)
        raise RuntimeError("Edge TTS returned no audio or WordBoundary cues")

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

    timing_path = (
        str(output_subtitles.resolve())
        if output_subtitles.is_file() and output_subtitles.stat().st_size > 0
        else None
    )
    if timing_path is None:
        raise RuntimeError("Edge TTS returned audio without sentence-boundary subtitles")
    return {
        "provider": "edge-tts",
        "voice": voice,
        "subtitle_timing_path": timing_path,
        "subtitle_timing_kind": "word-boundaries",
    }
