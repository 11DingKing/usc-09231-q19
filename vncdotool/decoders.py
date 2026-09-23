"""Framebuffer encodings the client offers to decode, best first."""
from __future__ import annotations

from .const import Encoding

#: Encodings offered when the caller does not ask for a specific set.
#: Ordered by preference: Tight carries lossy JPEG and compressed pixels,
#: Hextile compresses solid regions, and Raw is the universal fallback.
DEFAULT_ENCODINGS = [
    Encoding.TIGHT,
    Encoding.HEXTILE,
    Encoding.RAW,
]
