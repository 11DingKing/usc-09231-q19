"""Pixel format descriptions used to unpack raw framebuffer rectangles.

Only the formats the tests reference are described; a layout Pillow has no
raw decoder for raises UnsupportedPixelFormat so the client can negotiate
another one.
"""

from __future__ import annotations

from dataclasses import dataclass


class UnsupportedPixelFormat(Exception):
    pass


@dataclass(frozen=True)
class PixelFormat:
    bpp: int = 32
    depth: int = 24
    bigendian: bool = False
    truecolor: bool = True
    redmax: int = 255
    greenmax: int = 255
    bluemax: int = 255
    redshift: int = 0
    greenshift: int = 8
    blueshift: int = 16

    @property
    def bypp(self) -> int:
        return self.bpp // 8

    def __iter__(self):
        # RFB wire order of the ten PixelFormat fields.
        return iter((
            self.bpp, self.depth, int(bool(self.bigendian)), int(bool(self.truecolor)),
            self.redmax, self.greenmax, self.bluemax,
            self.redshift, self.greenshift, self.blueshift,
        ))


# Pillow raw decoder modes keyed by channel shifts.  The mode names bytes
# in memory order: shift (16, 8, 0) puts blue in the first byte, so a 32-bit
# pixel decodes as BGRX while the same channels packed in 24 bits decode BGR.
# https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
_8BIT_24 = {
    (0, 8, 16): "RGB",
    (16, 8, 0): "BGR",
}
_8BIT_32 = {
    (0, 8, 16): "RGBX",
    (16, 8, 0): "BGRX",
    (24, 16, 8): "XBGR",
}
_565_CHANNELS = {
    (11, 5, 0): "BGR;16",
    (0, 5, 11): "RGB;16",
}
# ((redmax, greenmax, bluemax), bpp) -> shifts -> mode
_RAW_MODES = {
    ((255, 255, 255), 24): _8BIT_24,
    ((255, 255, 255), 32): _8BIT_32,
    ((31, 63, 31), 16): _565_CHANNELS,
}


def raw_mode(pixel_format: PixelFormat) -> str:
    maxima = (pixel_format.redmax, pixel_format.greenmax, pixel_format.bluemax)
    shifts = (
        pixel_format.redshift,
        pixel_format.greenshift,
        pixel_format.blueshift,
    )
    try:
        return _RAW_MODES[(maxima, pixel_format.bpp)][shifts]
    except KeyError:
        raise UnsupportedPixelFormat(
            f"no raw decoder for bpp={pixel_format.bpp} maxima {maxima} shifts {shifts}"
        )


PIXEL_FORMATS: dict[str, PixelFormat] = {
    "rgbx8888": PixelFormat(32, 24, False, True, 255, 255, 255, 0, 8, 16),
    "bgrx8888": PixelFormat(32, 24, False, True, 255, 255, 255, 16, 8, 0),
    "rgb565": PixelFormat(16, 16, False, True, 31, 63, 31, 11, 5, 0),
}
