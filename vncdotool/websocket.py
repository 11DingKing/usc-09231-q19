"""WebSocket transport for VNC connections (``vnc://host`` over ``ws://``).

Only what :func:`vncdotool.client.factory_connect` needs: an address family
marker and a ``connect`` that wraps the RFB factory in a WebSocket tunnel.
"""
from __future__ import annotations

from typing import Union

from twisted.internet.protocol import ClientFactory

#: Address families accepted by ``factory_connect``: the ``socket.AF_*``
#: values, or :data:`WEBSOCKET` to tunnel RFB inside WebSocket frames.
AddressFamily = Union[int, "_WebSocketFamily"]


class _WebSocketFamily:
    def __repr__(self) -> str:
        return "WEBSOCKET"


#: Sentinel address family selecting a WebSocket tunnel.
WEBSOCKET = _WebSocketFamily()


def connect(reactor, factory: ClientFactory, url: str, family: AddressFamily = WEBSOCKET):
    """Open a WebSocket connection to ``url`` and speak RFB over it.

    The heavy lifting lives in the WebSocket protocol wrapper; here we only
    resolve the URL and start the connection.
    """
    from urllib.parse import urlparse

    from twisted.internet.endpoints import HostnameEndpoint

    parsed = urlparse(url if "//" in url else f"ws://{url}")
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "wss" else 80)
    endpoint = HostnameEndpoint(reactor, host, port)
    return endpoint.connect(factory)


__all__ = ["AddressFamily", "WEBSOCKET", "connect"]
