"""Minimal RFB (Remote Framebuffer) protocol machinery.

This is the slice of RFC 6143 the client needs: connection hand-keeping,
the handful of client-to-server messages, and parsing of server-to-server
``FramebufferUpdate`` messages down to rectangle callbacks on the
higher-level client.
"""

from __future__ import annotations

import logging
from enum import IntEnum
from struct import pack, unpack_from

from twisted.internet.protocol import Factory, Protocol

from .pixelformat import PixelFormat

log = logging.getLogger(__name__)


class Encoding(IntEnum):
    RAW = 0
    COPY_RECT = 1
    HEXTILE = 5
    TIGHT = 7

    PSEUDO_DESKTOP_SIZE = -223
    PSEUDO_LAST_RECT = -224
    PSEUDO_CURSOR = -239
    PSEUDO_QEMU_EXTENDED_KEY_EVENT = -258
    PSEUDO_FENCE = -312


class MsgC2S(IntEnum):
    SET_PIXEL_FORMAT = 0
    SET_ENCODINGS = 2
    FRAMEBUFFER_UPDATE_REQUEST = 3
    KEY_EVENT = 4
    POINTER_EVENT = 5
    CLIENT_CUT_TEXT = 6


class MsgS2C(IntEnum):
    FRAMEBUFFER_UPDATE = 0
    SET_COLOR_MAP = 1
    BELL = 2
    SERVER_CUT_TEXT = 3


_PHASE_HANDSHAKE = "handshake"
_PHASE_SERVER_INIT = "server-init"
_PHASE_READY = "ready"


class RFBClient(Protocol):
    def __init__(self) -> None:
        self._packet = bytearray()
        self._phase = _PHASE_HANDSHAKE
        self._version = ""
        self.width = 0
        self.height = 0
        self.pixel_format: PixelFormat = PixelFormat()
        self.bypp = self.pixel_format.bypp

    # -- handshake -------------------------------------------------------

    def _handleInitial(self) -> None:
        self._version = bytes(self._packet[4:11]).decode("ascii", "replace")
        # A fresh ServerInit (fed through _handleServerInit by the real flow
        # and by the tests) starts from an empty buffer.
        self._packet = bytearray()
        self._phase = _PHASE_SERVER_INIT
        # ClientInit: shared-flag = 1.
        self.transport.write(b"\x01")

    def _handleServerInit(self, data: bytes) -> None:
        (self.width, self.height) = unpack_from("!HH", data, 0)
        self.pixel_format = PixelFormat(*unpack_from("!BBBBHHHBBB", data, 4))
        self.bypp = self.pixel_format.bypp
        (name_length,) = unpack_from("!I", data, 20)
        self.name = data[24:24 + name_length].decode("utf-8", "replace")
        self._phase = _PHASE_READY
        self.vncConnectionMade()

    def vncConnectionMade(self) -> None:
        """Hook for higher-level clients."""

    # -- client-to-server messages --------------------------------------

    def setPixelFormat(self, pixel_format: PixelFormat) -> None:
        self.pixel_format = pixel_format
        self.bypp = pixel_format.bypp
        payload = pack(
            "!BBBBHHHBBB3x", *pixel_format
        )
        self.transport.write(pack("!BBBB", MsgC2S.SET_PIXEL_FORMAT, 0, 0, 0) + payload)

    def setEncodings(self, encodings: list[Encoding]) -> None:
        self._encodings = list(encodings)
        header = pack(
            "!BBxH", MsgC2S.SET_ENCODINGS, 0, len(self._encodings)
        )
        self.transport.write(header + b"".join(pack("!i", int(e)) for e in self._encodings))

    def framebufferUpdateRequest(
        self,
        incremental: int | bool = 0,
        x: int = 0,
        y: int = 0,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        if width is None:
            width = self.width
        if height is None:
            height = self.height
        self.transport.write(
            pack("!BBHHHH", MsgC2S.FRAMEBUFFER_UPDATE_REQUEST, 1 if incremental else 0,
                 x, y, width, height)
        )

    def keyEvent(self, key: int, down: int | bool = 1) -> None:
        self.transport.write(
            pack("!BBxHI", MsgC2S.KEY_EVENT, 1 if down else 0, 0, key)
        )

    def pointerEvent(self, x: int, y: int, buttonmask: int = 0) -> None:
        self.transport.write(
            pack("!BBHHH", MsgC2S.POINTER_EVENT, buttonmask, x, y)
        )

    def clientCutText(self, text: str) -> None:
        payload = text.encode("latin-1", "replace")
        self.transport.write(
            pack("!BBxHI", MsgC2S.CLIENT_CUT_TEXT, 0, 0, len(payload)) + payload
        )

    def sendPassword(self, password: str) -> None:  # pragma: no cover - auth path unused by tests
        raise NotImplementedError

    # -- server-to-server parsing ----------------------------------------

    def dataReceived(self, data: bytes) -> None:
        self._packet.extend(data)
        if self._phase != _PHASE_READY:
            return

        while self._packet:
            kind = self._packet[0]
            if kind == MsgS2C.FRAMEBUFFER_UPDATE:
                if not self._handleFramebufferUpdate():
                    return
            elif kind == MsgS2C.BELL:
                del self._packet[0]
                self.bell()
            elif kind == MsgS2C.SERVER_CUT_TEXT:
                if not self._handleServerCutText():
                    return
            else:
                self.vncProtocolError(f"unknown server message {kind}")
                return

    def _handleFramebufferUpdate(self) -> bool:
        """Parse one FramebufferUpdate.

        Returns False and leaves the buffer (and the screen) untouched when
        more bytes are needed; True once the whole message was consumed and
        dispatched.  Gathering before dispatching matters because a TCP stream
        may deliver an update in several chunks: a rectangle seen during a
        partial parse must not be painted twice when the rest arrives.
        """
        buf = bytes(self._packet)
        if len(buf) < 4:
            return False
        (number_of_rects,) = unpack_from("!H", buf, 2)

        position = 4
        gathered: list[tuple] = []
        last_rect = False
        count = 0

        # First pass: verify the whole message is present and collect each
        # rectangle without touching the screen.
        while count < number_of_rects:
            if len(buf) < position + 12:
                return False
            x, y, width, height, encoding = unpack_from("!HHHHi", buf, position)

            if encoding == Encoding.PSEUDO_LAST_RECT and x == y == width == height == 0:
                position += 12
                last_rect = True
                break

            header_end = position + 12
            if encoding == Encoding.RAW:
                payload_size = width * height * self.bypp
                if len(buf) < header_end + payload_size:
                    return False
                payload = buf[header_end:header_end + payload_size]
                gathered.append(
                    ("rect", (x, y, width, height), payload)
                )
            elif encoding == Encoding.COPY_RECT:
                if len(buf) < header_end + 4:
                    return False
                srcx, srcy = unpack_from("!HH", buf, header_end)
                payload_size = 4
                gathered.append(
                    ("copy", (srcx, srcy, x, y, width, height), b"")
                )
            elif encoding == Encoding.PSEUDO_DESKTOP_SIZE:
                payload_size = 0
                gathered.append(("desktop", (width, height), b""))
            elif encoding == Encoding.PSEUDO_CURSOR:
                mask_width = (width + 7) // 8
                payload_size = width * height * self.bypp + mask_width * height
                if len(buf) < header_end + payload_size:
                    return False
                image = buf[header_end:header_end + width * height * self.bypp]
                mask_start = header_end + width * height * self.bypp
                mask = buf[mask_start:mask_start + mask_width * height]
                gathered.append(
                    ("cursor", (x, y, width, height), (image, mask))
                )
            else:
                self.vncProtocolError(f"unknown encoding {encoding}")
                return False

            position = header_end + payload_size
            count += 1

        # Second pass: the message is complete; dispatch it.
        rectangles: list[tuple[int, int, int, int]] = []
        for kind, args, payload in gathered:
            if kind == "rect":
                x, y, width, height = args
                self.updateRectangle(x, y, width, height, payload, self.pixel_format)
                rectangles.append((x, y, width, height))
            elif kind == "copy":
                self.copyRectangle(*args)
                srcx, srcy, x, y, width, height = args
                rectangles.append((x, y, width, height))
            elif kind == "desktop":
                self.updateDesktopSize(*args)
            elif kind == "cursor":
                x, y, width, height = args
                image, mask = payload
                self.updateCursor(x, y, width, height, image, mask)

        del self._packet[:position]
        self.commitUpdate(rectangles)
        return True

    def _handleServerCutText(self) -> bool:
        buf = bytes(self._packet)
        if len(buf) < 8:
            return False
        (length,) = unpack_from("!I", buf, 4)
        if len(buf) < 8 + length:
            return False
        text = buf[8:8 + length].decode("latin-1", "replace")
        del self._packet[:8 + length]
        self.copy_text(text)
        return True

    # -- rectangle hooks, overridden by VNCDoToolClient ------------------

    def updateRectangle(self, x, y, width, height, data, pixel_format) -> None:
        pass

    def copyRectangle(self, srcx, srcy, x, y, width, height) -> None:
        pass

    def commitUpdate(self, rectangles=None) -> None:
        pass

    def updateCursor(self, x, y, width, height, image, mask) -> None:
        pass

    def updateDesktopSize(self, width, height) -> None:
        pass

    def bell(self) -> None:
        pass

    def copy_text(self, text: str) -> None:
        pass

    def vncProtocolError(self, reason: str) -> None:
        # The higher-level client decides whether (and how) to drop the
        # connection; callers like setImageMode tear it down themselves.
        log.error("protocol error: %s", reason)

    def vncAuthFailed(self, reason) -> None:
        log.error("authentication failed: %r", reason)


class RFBFactory(Factory):
    def buildProtocol(self, addr):
        protocol = Factory.buildProtocol(self, addr)
        return protocol
