"""Subtitle text shaping, timing, and measured-canvas geometry."""

import os
import re
import unicodedata
from decimal import Decimal
from pathlib import Path

from lib import CONFIG
from assemble_constants import (
    SUBTITLE_STYLE_REF_H,
    SUBTITLE_STYLE_REF_W,
    _SUBTITLE_CLOSING_QUOTES,
    _SUBTITLE_TERMINAL_PUNCTUATION,
)
from media import _ratio_to_float

def _seconds_to_srt_time(seconds):
    """Floor times to SRT milliseconds without float remainder artifacts.

    Coercing first keeps Fraction/Decimal/str inputs working and clamps a negative
    time to zero instead of emitting a negative-component SRT stamp.
    """
    seconds = max(0.0, float(seconds))
    total_ms = int(Decimal(str(seconds)) * 1000)
    h, remainder = divmod(total_ms, 3_600_000)
    m, remainder = divmod(remainder, 60_000)
    s, ms = divmod(remainder, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _seconds_to_ass_time(seconds):
    """将秒数转为 ASS 时间格式 H:MM:SS.cc"""
    centiseconds = int(round(float(seconds) * 100))
    h = centiseconds // 360000
    centiseconds %= 360000
    m = centiseconds // 6000
    centiseconds %= 6000
    s = centiseconds // 100
    cs = centiseconds % 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _subtitle_style_config(canvas=None):
    """Return the internal default burn-in subtitle style.

    When ``canvas`` ({"width","height"}) is given AND the user has not pinned PlayRes via
    SUBTITLE_PLAY_RES_X/Y, the style is scaled to that canvas: PlayRes is set to the frame
    dimensions (so libass never stretches glyphs — the old hardcoded 1280x720 squished
    portrait text), horizontal metrics scale with width, vertical metrics with height, and
    the font is additionally capped so a full ``max_chars`` line fits the usable width. A
    16:9 source (or the 1280x720 default) reproduces the legacy values exactly.
    """
    style = {
        "font_name": CONFIG["subtitle_font_name"],
        "font_file": CONFIG["subtitle_font_file"],
        "font_size": CONFIG["subtitle_font_size"],
        "primary_color": CONFIG["subtitle_primary_color"],
        "outline_color": CONFIG["subtitle_outline_color"],
        "outline": CONFIG["subtitle_outline"],
        "shadow": CONFIG["subtitle_shadow"],
        "alignment": CONFIG["subtitle_alignment"],
        "margin_l": CONFIG["subtitle_margin_l"],
        "margin_r": CONFIG["subtitle_margin_r"],
        "margin_v": CONFIG["subtitle_margin_v"],
        "max_chars": CONFIG["subtitle_max_chars"],
        "play_res_x": CONFIG["subtitle_play_res_x"],
        "play_res_y": CONFIG["subtitle_play_res_y"],
    }
    pinned = "SUBTITLE_PLAY_RES_X" in os.environ or "SUBTITLE_PLAY_RES_Y" in os.environ
    if canvas is None or pinned:
        return style  # legacy / manually-pinned: unchanged

    cw, ch = canvas["width"], canvas["height"]
    base_font = float(style["font_size"])
    kx = cw / float(SUBTITLE_STYLE_REF_W)  # horizontal metrics ∝ width
    ky = ch / float(SUBTITLE_STYLE_REF_H)  # vertical metrics ∝ height
    margin_l = round(float(style["margin_l"]) * kx)
    margin_r = round(float(style["margin_r"]) * kx)
    margin_v = round(float(style["margin_v"]) * ky)
    # height-proportional size, then cap so a full line of CJK glyphs (≈1em wide) fits the
    # usable width — this is what keeps portrait text on-screen instead of overflowing.
    usable_w = max(1.0, cw - margin_l - margin_r)
    width_cap = usable_w / int(style["max_chars"])
    font_size = max(1, int(min(base_font * ky, width_cap)))  # floor so a full line never overflows
    font_scale = font_size / base_font
    style.update({
        "font_size": font_size,
        "outline": max(0, round(float(style["outline"]) * font_scale)),
        "shadow": max(0, round(float(style["shadow"]) * font_scale)),
        "margin_l": margin_l,
        "margin_r": margin_r,
        "margin_v": margin_v,
        "play_res_x": cw,
        "play_res_y": ch,
    })
    return style


def _measured_subtitle_band(canvas):
    """Explicit (y_top, y_bot) display-frame subtitle band validated against the canvas, or None."""
    y_top = CONFIG["subtitle_y_top"]
    y_bot = CONFIG["subtitle_y_bot"]
    if y_top < 0 and y_bot < 0:
        return None
    sar_text = canvas["sample_aspect_ratio"]
    if abs(_ratio_to_float(sar_text, 0.0) - 1.0) >= 1e-9:
        raise ValueError(
            f"字幕带坐标仅支持方形像素画布 (SAR 1:1)；当前 SAR={sar_text}"
        )
    canvas_h = canvas["height"]
    if not 0 <= y_top < y_bot <= canvas_h:
        raise ValueError(
            f"字幕带坐标无效: top={y_top}, bot={y_bot}, 画布高度={canvas_h}；"
            "必须满足 0 <= top < bot <= height"
        )
    return y_top, y_bot


def _style_for_measured_subtitle_band(style, canvas):
    """Fit ASS subtitle positioning and font into an explicit measured Y band."""
    style = dict(style)
    safe_area = _measured_subtitle_safe_area(style, canvas)
    if safe_area is None:
        return style
    alignment = style["alignment"]
    if alignment not in {1, 2, 3, 5}:
        raise ValueError(
            "measured subtitle coordinates require bottom alignment (1/2/3) "
            f"or center alignment (5); got {alignment}"
        )
    canvas_h = canvas["height"]
    scale_y = float(style["play_res_y"]) / canvas_h
    if alignment in {1, 2, 3}:
        style["margin_v"] = max(0, round((canvas_h - CONFIG["subtitle_y_bot"]) * scale_y))
    else:
        safe_top = max(0, CONFIG["subtitle_y_top"] - CONFIG["subtitle_mask_padding"])
        style["measured_center_y"] = round(
            ((safe_top + CONFIG["subtitle_y_bot"]) / 2) * scale_y
        )
    current_font = int(style["font_size"])
    current_outline = float(style["outline"])
    current_shadow = float(style["shadow"])
    available_height = safe_area["height"]
    for candidate in range(current_font, 7, -1):
        scale = candidate / current_font
        outline = max(1 if current_outline > 0 else 0, round(current_outline * scale))
        shadow = max(0, round(current_shadow * scale))
        vertical_factor = 2.5 if alignment == 5 else 1.25
        if candidate * vertical_factor + outline * 2 + shadow <= available_height + 1e-6:
            fitted_font = candidate
            break
    else:
        # Keep the renderer's minimum readable size; visual QC will block because it cannot fit.
        fitted_font = min(current_font, 8)
    if fitted_font < current_font:
        scale = fitted_font / current_font
        style["font_size"] = fitted_font
        style["outline"] = max(
            1 if current_outline > 0 else 0, round(current_outline * scale)
        )
        style["shadow"] = max(0, round(current_shadow * scale))
    return style


def _measured_subtitle_safe_area(style, canvas):
    """Return the padded measured band in ASS PlayRes coordinates, or None."""
    band = _measured_subtitle_band(canvas)
    if band is None:
        return None
    y_top, y_bot = band
    canvas_h = canvas["height"]
    safe_top = max(0, y_top - CONFIG["subtitle_mask_padding"])
    # The ASS style remains bottom-anchored at the measured y_bot. Bottom mask padding hides
    # source glyph edges but is not usable subtitle layout space; only top padding can extend
    # the line box without moving its baseline below the measured band.
    play_x = int(style["play_res_x"])
    scale_y = int(style["play_res_y"]) / canvas_h
    margin_l = int(style["margin_l"])
    margin_r = int(style["margin_r"])
    return {
        "x": margin_l,
        "y": round(safe_top * scale_y),
        "width": max(1, play_x - margin_l - margin_r),
        "height": max(1, round((y_bot - safe_top) * scale_y)),
        "bottom_margin": max(0, round((canvas_h - y_bot) * scale_y)),
    }


def _subtitle_display_text(text):
    """Return display-only subtitle text with trailing sentence punctuation removed.

    Narration/TTS source text stays untouched; this is applied only to SRT/ASS cue text.
    Closing quotes/brackets are preserved, so 「原声台词。」 renders as 「原声台词」.
    """
    text = text.strip()
    suffix = ""
    while text and text[-1] in _SUBTITLE_CLOSING_QUOTES:
        suffix = text[-1] + suffix
        text = text[:-1].rstrip()
    text = text.rstrip(_SUBTITLE_TERMINAL_PUNCTUATION).rstrip()
    return (text + suffix).strip()


def _subtitle_chunk_weight(text):
    """Weight spoken text without counting Burmese combining marks as extra syllables."""
    weight = 0.0
    for char in text:
        category = unicodedata.category(char)
        if char.isspace():
            continue
        if category.startswith("M") or category.startswith("C"):
            continue
        weight += 1.0
    return max(1.0, weight)


def _split_subtitle_sentences(text):
    """Split source text at sentence endings used by Burmese and common languages."""
    text = text.strip()
    if not text:
        return []
    endings = "။。！？!?"
    sentences, start = [], 0
    for index, char in enumerate(text):
        if char not in endings:
            continue
        end = index + 1
        while end < len(text) and text[end] in _SUBTITLE_CLOSING_QUOTES:
            end += 1
        sentence = text[start:end].strip()
        if sentence:
            sentences.append(sentence)
        start = end
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def _read_edge_word_boundaries(seg):
    """Read Edge TTS WordBoundary sidecar cues in source-audio seconds."""
    receipt = seg.get("provider_receipt") or {}
    path_value = receipt.get("subtitle_timing_path")
    if not path_value:
        return None
    path = Path(path_value)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return None
    time_pattern = re.compile(
        r"^(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})\s+-->\s+"
        r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{3})$"
    )
    cues = []
    for block in re.split(r"\r?\n\s*\r?\n", text.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next(
            (i for i, line in enumerate(lines) if time_pattern.match(line)), None
        )
        if timing_index is None:
            continue
        match = time_pattern.match(lines[timing_index])
        values = [int(value) for value in match.groups()]
        start = ((values[0] * 60 + values[1]) * 60 + values[2]) + values[3] / 1000
        end = ((values[4] * 60 + values[5]) * 60 + values[6]) + values[7] / 1000
        cue_text = "".join(lines[timing_index + 1:]).strip()
        if cue_text and 0 <= start < end:
            cues.append({"start": start, "end": end, "text": cue_text})
    return cues or None


def _normalize_timing_match_text(text):
    """Remove visual punctuation/spacing for matching Edge boundary text to approved text."""
    return "".join(
        char.casefold()
        for char in unicodedata.normalize("NFKC", text)
        if not unicodedata.category(char).startswith(("P", "Z", "C"))
    )


def _edge_aligned_entries(seg, max_chars):
    """Group Edge word-boundary cues into approved sentences and readable caption lines."""
    cues = _read_edge_word_boundaries(seg)
    if not cues:
        return None
    sentences = _split_subtitle_sentences(seg["spoken_text"])
    sentence_cues = []
    cue_index = 0
    for sentence in sentences:
        target = _normalize_timing_match_text(sentence)
        matched = []
        collected_text = ""
        while cue_index < len(cues):
            cue = cues[cue_index]
            piece = _normalize_timing_match_text(cue["text"])
            if not piece:
                matched.append(cue)
                cue_index += 1
                continue
            candidate = collected_text + piece
            if not target.startswith(candidate):
                return None
            matched.append(cue)
            cue_index += 1
            collected_text = candidate
            if collected_text == target:
                break
        if not matched or collected_text != target:
            return None
        sentence_cues.append({
            "start": min(cue["start"] for cue in matched),
            "end": max(cue["end"] for cue in matched),
            "cues": matched,
        })
    if cue_index != len(cues):
        return None

    source_duration = float(seg.get("source_audio_duration") or seg.get("audio_duration") or 0)
    placed_duration = float(seg.get("placed_audio_duration") or 0)
    if source_duration <= 0 or placed_duration <= 0:
        return None
    scale = placed_duration / source_duration
    placement_start = float(seg["actual_place_start"])
    placement_end = float(seg["actual_place_end"])
    entries = []
    for sentence, cue in zip(sentences, sentence_cues):
        start = min(placement_end, placement_start + cue["start"] * scale)
        end = min(placement_end, placement_start + cue["end"] * scale)
        if end <= start:
            return None
        chunks = _subtitle_entry_chunks(_split_subtitle_chunks(sentence, max_chars))
        chunk_cues = []
        word_index = 0
        for chunk in chunks:
            target = _normalize_timing_match_text(chunk["raw"])
            collected = ""
            matched = []
            while word_index < len(cue["cues"]):
                word = cue["cues"][word_index]
                piece = _normalize_timing_match_text(word["text"])
                if not piece:
                    matched.append(word)
                    word_index += 1
                    continue
                candidate = collected + piece
                if not target.startswith(candidate):
                    matched = []
                    break
                matched.append(word)
                word_index += 1
                collected = candidate
                if collected == target:
                    break
            if not matched or collected != target:
                chunk_cues = []
                break
            chunk_cues.append(matched)

        if chunk_cues and word_index == len(cue["cues"]):
            for chunk, matched in zip(chunks, chunk_cues):
                cue_start = min(item["start"] for item in matched)
                cue_end = max(item["end"] for item in matched)
                entry_start = min(placement_end, placement_start + cue_start * scale)
                entry_end = min(placement_end, placement_start + cue_end * scale)
                if entry_end <= entry_start:
                    return None
                entries.append({
                    "start": entry_start,
                    "end": entry_end,
                    "text": chunk["text"],
                    "timing_source": "edge_word_boundaries",
                })
        else:
            for entry in _distribute_chunks(
                [chunk["raw"] for chunk in chunks], start, end
            ):
                entry["timing_source"] = "edge_sentence_window"
                entries.append(entry)
    return entries or None


def _subtitle_entry_chunks(raw_chunks):
    """Pair raw chunks used for timing with their final display text.

    Timing remains based on the raw split topology. Terminal punctuation is stripped only
    on the emitted text, while quote-only suffix chunks are folded into the previous cue
    so a closing bracket never renders alone.
    """
    out = []
    for chunk in raw_chunks:
        display = _subtitle_display_text(chunk)
        if not display:
            continue
        if all(ch in _SUBTITLE_CLOSING_QUOTES for ch in display):
            if out:
                out[-1]["text"] += display
            continue
        out.append({"raw": chunk, "text": display})
    return out


def _normalize_subtitle_text(text):
    """Normalize Chinese em-dashes in burned subtitle text: a run of one-or-more "—" (incl. "——")
    collapses to a single "，". Then collapse any resulting double commas ("，，"→"，") so the dash
    swap never leaves a doubled comma."""
    return re.sub(r"，{2,}", "，", re.sub(r"—+", "，", text))


def _split_subtitle_chunks(text, max_chars):
    """Split one narration block (often several sentences) into short display chunks.

    A block is synthesized as one continuous TTS utterance for fluent prosody, but showing the
    whole paragraph as a single subtitle would force a tall multi-line band and lag the picture.
    So we cut the block at punctuation into clauses, then greedily pack adjacent clauses into
    chunks of at most `max_chars` — each chunk renders as ONE readable line synced to its slice of
    the block's audio. Punctuation stays attached here for lossless splitting; the display layer
    strips terminal sentence marks per subtitle-cue style."""
    text = text.strip()
    if not text:
        return []
    breakers = "，。！？、；：…—,.!?;:၊။"
    clauses, buf = [], ""
    for ch in text:
        buf += ch
        if ch in breakers:
            clauses.append(buf)
            buf = ""
    if buf.strip():
        clauses.append(buf)
    # Any single clause longer than max_chars is hard-wrapped so no chunk ever exceeds one line.
    # Balance those pieces instead of slicing exactly at max_chars: a 21-character clause must
    # not become a readable 20-character cue followed by a 1-character flash.
    sized = []
    for clause in clauses:
        if len(clause) <= max_chars:
            sized.append(clause)
        else:
            piece_count = (len(clause) + max_chars - 1) // max_chars
            base, extra = divmod(len(clause), piece_count)
            cursor = 0
            for piece_index in range(piece_count):
                width = base + (1 if piece_index < extra else 0)
                sized.append(clause[cursor:cursor + width])
                cursor += width
    chunks, cur = [], ""
    for clause in sized:
        sentence_closed = cur.rstrip().endswith(tuple(_SUBTITLE_TERMINAL_PUNCTUATION))
        if cur and (sentence_closed or len(cur) + len(clause) > max_chars):
            chunks.append(cur)
            cur = clause
        else:
            cur += clause
    if cur.strip():
        chunks.append(cur)
    return [c.strip() for c in chunks if c.strip()]


def _subtitle_entries(narration):
    """Use Edge word cues when available; mark proportional fallback timing for visual QC.

    Edge cues keep each displayed line aligned to its spoken words. Other providers and unmatched
    Edge text fall back to Burmese-aware sentence windows and character weighting. Unplaced
    segments have a zero-width window and produce no cue."""
    max_chars = CONFIG["subtitle_max_chars"]
    entries = []
    for seg in narration:
        aligned = _edge_aligned_entries(seg, max_chars)
        if aligned is not None:
            entries.extend(aligned)
            continue
        text = seg["spoken_text"]
        start, end = float(seg["actual_place_start"]), float(seg["actual_place_end"])
        estimated = _distribute_chunks(_split_subtitle_chunks(text, max_chars), start, end)
        for entry in estimated:
            entry["timing_source"] = "character_estimate"
        entries.extend(estimated)
    return entries


def _distribute_chunks(chunks, start, end):
    """Distribute [start,end] across raw chunks while emitting display-clean text.

    Terminal subtitle punctuation is visual-only: it is stripped from final cue text,
    but the raw split chunks remain the timing topology. A slice too short to show on its
    own is folded into the previous line of the same block, so no chunk is ever dropped.
    """
    chunks = _subtitle_entry_chunks(chunks)
    if not chunks or end - start < 0.1:
        return []
    if len(chunks) == 1:
        return [{"start": start, "end": end, "text": chunks[0]["text"]}]
    total_chars = sum(_subtitle_chunk_weight(c["raw"]) for c in chunks)
    span = end - start
    out, cursor = [], start
    for i, chunk in enumerate(chunks):
        weight = _subtitle_chunk_weight(chunk["raw"])
        chunk_end = end if i == len(chunks) - 1 else cursor + span * (weight / total_chars)
        if out and chunk_end - cursor < 0.05:
            out[-1]["text"] += chunk["text"]
            out[-1]["end"] = chunk_end
        else:
            out.append({"start": cursor, "end": chunk_end, "text": chunk["text"]})
        cursor = chunk_end
    return out


def _bracketed_original_chunks(text, start, end, max_chars):
    """Split original dialogue into timed chunks wrapped in 「」 for visual distinction."""
    raw = text.strip()
    if raw.startswith("「") and raw.endswith("」"):
        raw = raw[1:-1].strip()
    chunks = _split_subtitle_chunks(raw, max_chars)
    if chunks:
        chunks[0] = "「" + chunks[0]
        chunks[-1] = chunks[-1] + "」"
    return _distribute_chunks(chunks, start, end)
