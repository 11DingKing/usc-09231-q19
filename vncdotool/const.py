"""Encoding-related constants."""

from __future__ import annotations

from .rfb import Encoding

# Tight JPEG quality level pseudo-encodings: level 0 is -32 (lowest
# quality), level 9 is -23 (highest).
JPEG_QUALITY_ENCODINGS = tuple(-32 + level for level in range(10))
