"""Map the negotiated RFB :class:`~vncdotool.rfb.PixelFormat` onto the raw
decoder mode Pillow needs to unpack the wire bytes.

RFB describes a pixel by the bit position of each colour channel while
Pillow's ``raw`` decoder names the *byte* order it sees, so the two only line
up once little-endian packing has been accounted for.
"""
from __future__ import annotations

from .rfb import PixelFormat


class UnsupportedPixelFormat(Exception):
    """The server's :class:`PixelFormat` cannot be fed directly to Pillow."""


#: Ready-made formats offered to servers that cannot keep the one they
#: announced.  Names describe byte order in memory (e.g. ``rgbx8888`` is
#: red, green, blue and one unused byte).
PIXEL_FORMATS: dict[str, PixelFormat] = {
    "rgbx8888": PixelFormat(32, 24, False, True, 255, 255, 255, 0, 8, 16),
    "bgrx8888": PixelFormat(32, 24, False, True, 255, 255, 255, 24, 16, 8),
    "rgb888": PixelFormat(24, 24, False, True, 255, 255, 255, 0, 8, 16),
    "bgr888": PixelFormat(24, 24, False, True, 255, 255, 255, 16, 8, 0),
    "rgb565": PixelFormat(16, 16, False, True, 31, 63, 31, 11, 5, 0),
}


# (redshift, greenshift, blueshift) -> Pillow raw mode, for the formats
# vncdotool knows how to decode straight off the wire.
_RAW_MODES: dict[tuple[int, int, int, int], str] = {
    (32, 0, 8, 16): "RGBX",
    (32, 24, 16, 8): "XBGR",
    (32, 16, 8, 0): "BGRX",
    (32, 8, 16, 24): "XRGB",
    (24, 0, 8, 16): "RGB",
    (24, 16, 8, 0): "BGR",
    (16, 11, 5, 0): "BGR;16",
    (16, 10, 5, 11): "BGR;15",
}


def raw_mode(pixel_format: PixelFormat) -> str:
    """Return the Pillow ``raw`` decoder mode for ``pixel_format``.

    Raises :class:`UnsupportedPixelFormat` for paletted, big-endian or
    otherwise undecodable layouts so the caller can ask the server for a
    simpler format instead.
    """
    if not pixel_format.truecolor:
        raise UnsupportedPixelFormat("palettised pixel formats are not supported")
    if pixel_format.bigendian:
        raise UnsupportedPixelFormat("big-endian pixel formats are not supported")

    try:
        return _RAW_MODES[
            (
                pixel_format.bpp,
                pixel_format.redshift,
                pixel_format.greenshift,
                pixel_format.blueshift,
            )
        ]
    except KeyError:
        raise UnsupportedPixelFormat(
            f"no Pillow raw mode for {pixel_format}"
        ) from None
