import re
from pathlib import Path
from src.ingestion.cleaner import clean_subtitles_noise, normalize_whitespace

def parse_srt(srt_content: str) -> str:
    # Strip BOM if present
    content = srt_content.lstrip("\ufeff")
    
    # Blocks in SRT: index, timestamp line, text lines, blank line
    blocks = re.split(r"\n\s*\n", content.strip())
    text_segments = []
    
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        # Drop index line if purely digit
        if lines[0].strip().isdigit():
            lines = lines[1:]
        if not lines:
            continue
        # Drop timestamp line (00:00:00,000 --> 00:00:00,000)
        if "-->" in lines[0]:
            lines = lines[1:]
        block_text = " ".join(l.strip() for l in lines if l.strip())
        cleaned_block = clean_subtitles_noise(block_text)
        if cleaned_block:
            text_segments.append(cleaned_block)

    joined = " ".join(text_segments)
    return normalize_whitespace(joined)

def parse_plain_text(text: str) -> str:
    cleaned = clean_subtitles_noise(text)
    return normalize_whitespace(cleaned)

def parse_file(file_path: Path) -> str:
    content = file_path.read_text(encoding="utf-8", errors="replace")
    if file_path.suffix.lower() == ".srt":
        return parse_srt(content)
    return parse_plain_text(content)
