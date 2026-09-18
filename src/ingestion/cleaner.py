import re

def clean_subtitles_noise(text: str) -> str:
    # Remove audio markers like [Música], [Aplausos], [Risos], (música), etc.
    cleaned = re.sub(r"\[(Música|Aplausos|Risos|Ruído|Inaudível|Silêncio|Gargalhadas|Tosse)[^\]]*\]", " ", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\((Música|Aplausos|Risos|Ruído|Inaudível|Silêncio)[^\)]*\)", " ", cleaned, flags=re.IGNORECASE)
    # Remove HTML / formatting tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Normalize multiple spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()

def normalize_whitespace(text: str) -> str:
    lines = text.splitlines()
    normalized_paragraphs = []
    current_para = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_para:
                normalized_paragraphs.append(" ".join(current_para))
                current_para = []
        else:
            current_para.append(stripped)
    if current_para:
        normalized_paragraphs.append(" ".join(current_para))
        
    return "\n\n".join(normalized_paragraphs).strip()
