"""Decoders advertised to the server."""

from __future__ import annotations

from .rfb import Encoding

# Encodings offered unless the caller overrides them.
DEFAULT_ENCODINGS: tuple[Encoding, ...] = (
    Encoding.TIGHT,
    Encoding.HEXTILE,
    Encoding.RAW,
)
