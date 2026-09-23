"""Compare a captured framebuffer against an expected image.

A match is judged per channel: after optionally blurring both frames (which
is what carries a comparison through a lossy encoding), no pixel may sit
further than ``fuzz`` from its counterpart.  ``fuzz`` runs 0 (exact) to 255
(the furthest apart two channels can be).
"""
from __future__ import annotations

from PIL import Image, ImageChops, ImageFilter

from .pixelformat import UnsupportedPixelFormat
from .rfb import PixelFormat


def matches(
    actual: Image.Image, expected: Image.Image, fuzz: int, blur: int
) -> bool:
    """Return True when every pixel of ``actual`` is within ``fuzz`` of
    ``expected``.

    Images of different sizes never match: a tight crop against a larger
    target would otherwise compare only the overlap.
    """
    if actual.size != expected.size:
        return False

    actual_rgb = actual.convert("RGB")
    expected_rgb = expected.convert("RGB")
    if blur:
        actual_rgb = actual_rgb.filter(ImageFilter.GaussianBlur(blur))
        expected_rgb = expected_rgb.filter(ImageFilter.GaussianBlur(blur))

    difference = ImageChops.difference(actual_rgb, expected_rgb)
    return all(high <= fuzz for _low, high in difference.getextrema())


def fuzz_for_format(pixel_format: PixelFormat) -> int:
    """The distance two pixels may show while encoding identically.

    A channel with ``max`` of 2**n - 1 quantises each 8-bit value onto a
    grid with spacing ``256 // (max + 1)``, so two 8-bit values the server
    cannot distinguish can be that far apart minus one.  A server given
    8-bit channels reproduces values exactly, hence fuzz 0.
    """
    if not pixel_format.truecolor:
        raise UnsupportedPixelFormat("no fuzz for palettised pixel formats")
    return max(
        255 // (channel_max + 1)
        for channel_max in (
            pixel_format.redmax,
            pixel_format.greenmax,
            pixel_format.bluemax,
        )
    )
