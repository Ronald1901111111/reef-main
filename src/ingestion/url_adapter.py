import re
from typing import Optional

def extract_video_id(url: str) -> Optional[str]:
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

class SubtitleAcquisitionError(Exception):
    """Raised when subtitle acquisition fails due to network, auth or missing tracks."""
    pass

class URLAcquisitionAdapter:
    def __init__(self, fetcher_callable=None):
        self.fetcher = fetcher_callable

    def fetch_subtitles(self, url: str) -> Optional[str]:
        video_id = extract_video_id(url)
        if not video_id:
            raise SubtitleAcquisitionError(f"Invalid YouTube URL: {url}")
        
        if self.fetcher:
            try:
                return self.fetcher(url)
            except Exception as e:
                raise SubtitleAcquisitionError(f"Subtitle acquisition failed for {url}: {e}") from e

        # In offline/no-network sandbox, standard fallback
        raise SubtitleAcquisitionError(f"Network acquisition offline or subtitle unavailable for {url}")
