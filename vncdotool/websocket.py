"""WebSocket transport selection.

Only the symbols ``client.factory_connect`` references live here; the tests
do not drive an actual WebSocket connection.
"""

from __future__ import annotations

import socket

AddressFamily = int

WEBSOCKET = -1


def connect(reactor, factory, url):  # pragma: no cover - exercised in integration only
    raise NotImplementedError("WebSocket support is not available in this snapshot")
