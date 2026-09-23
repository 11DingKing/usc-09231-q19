"""Fuzzy image comparison for ``expectScreen``/``expectRegion``."""

from __future__ import annotations

from PIL import Image, ImageChops, ImageFilter

from .pixelformat import PixelFormat


def matches(
    actual: Image.Image,
    expected: Image.Image,
    fuzz: int = 0,
    blur: int = 0,
) -> bool:
    """Return True when every pixel of *actual* sits within *fuzz* of
    *expected*.

    ``fuzz`` is the largest per-channel distance (0..255) that still counts
    as equal.  ``blur`` applies a Gaussian blur of that radius to both images
    first, which carries a match through a lossy encoding.
    """
    if actual.size != expected.size:
        return False

    if blur:
        actual = actual.filter(ImageFilter.GaussianBlur(blur))
        expected = expected.filter(ImageFilter.GaussianBlur(blur))

    difference = ImageChops.difference(actual, expected)
    if fuzz:
        allowance = Image.new("RGB", actual.size, (fuzz, fuzz, fuzz))
        # Pixels within the allowance subtract to zero; only excess remains.
        difference = ImageChops.subtract(difference, allowance)

    return difference.getbbox() is None


def fuzz_for_format(pixel_format: PixelFormat) -> int:
    """The distance a value may sit from its nearest encodable neighbour.

    A server sending 5-bit red rounds each 8-bit channel by up to
    ``2**(8 - bits) - 1``; an exact comparison could never come true.
    """
    fuzz = 0
    for maximum in (pixel_format.redmax, pixel_format.greenmax, pixel_format.bluemax):
        bits = maximum.bit_length()
        fuzz = max(fuzz, 2 ** (8 - bits) - 1)
    return fuzz
