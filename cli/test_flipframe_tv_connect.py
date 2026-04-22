#!/usr/bin/env python3
"""Tests for Samsung art channel websocket connection retries.

Run:
  cd flipframe/cli && /opt/homebrew/bin/python3 -m pytest test_flipframe_tv_connect.py -q
"""

import json
from pathlib import Path
from unittest.mock import patch

import flipframe
import websocket


class FakeWS:
    def __init__(self, responses):
        self.responses = list(responses)
        self.closed = False
        self.timeouts = []

    def settimeout(self, value):
        self.timeouts.append(value)

    def recv(self):
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return json.dumps(item)

    def close(self):
        self.closed = True


def test_connect_retries_when_tv_only_sends_connect_event(tmp_path):
    first = FakeWS([
        {"event": "ms.channel.connect", "data": {"clients": [{"attributes": {"token": "abc123"}}]}},
        websocket.WebSocketTimeoutException(),
    ])
    second = FakeWS([
        {"event": "ms.channel.connect", "data": {"clients": [{"attributes": {"token": "abc123"}}]}},
        {"event": "ms.channel.ready"},
    ])

    tv = flipframe.FrameTVArt("192.168.1.81", token_file=str(tmp_path / "token"), timeout=30)

    with patch.object(flipframe.websocket, "create_connection", side_effect=[first, second]), \
         patch.object(flipframe.time, "sleep") as mock_sleep:
        tv.connect()

    assert tv.ws is second
    assert first.closed is True
    assert second.closed is False
    assert mock_sleep.call_count == 1
    assert Path(tv.token_file).read_text() == "abc123"


def test_connect_raises_after_exhausting_retries(tmp_path):
    sockets = [
        FakeWS([
            {"event": "ms.channel.connect"},
            websocket.WebSocketTimeoutException(),
        ])
        for _ in range(3)
    ]

    tv = flipframe.FrameTVArt("192.168.1.81", token_file=str(tmp_path / "token"), timeout=30)

    with patch.object(flipframe.websocket, "create_connection", side_effect=sockets), \
         patch.object(flipframe.time, "sleep") as mock_sleep:
        try:
            tv.connect()
        except ConnectionError as exc:
            assert "ms.channel.connect" in str(exc)
        else:
            raise AssertionError("Expected ConnectionError")

    assert mock_sleep.call_count == 2
    assert all(ws.closed for ws in sockets)
