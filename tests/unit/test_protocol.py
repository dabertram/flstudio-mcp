"""Unit tests for protocol port helpers + SysEx wire codec (pure)."""
from __future__ import annotations

import pytest

from fl_studio_mcp import protocol

pytestmark = pytest.mark.unit


class TestPortNames:
    def test_defaults(self):
        assert protocol.port_to_fl_name() == "FLStudioMCP RX"
        assert protocol.port_from_fl_name() == "FLStudioMCP TX"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("FLSTUDIO_MCP_PORT_TO_FL", "Custom RX")
        monkeypatch.setenv("FLSTUDIO_MCP_PORT_FROM_FL", "Custom TX")
        assert protocol.port_to_fl_name() == "Custom RX"
        assert protocol.port_from_fl_name() == "Custom TX"


class TestRequestId:
    def test_length_and_charset(self):
        rid = protocol.new_request_id()
        assert len(rid) == protocol.REQUEST_ID_LEN
        assert all(c in protocol.REQUEST_ID_ALPHABET for c in rid)

    def test_unique_ish(self):
        ids = {protocol.new_request_id() for _ in range(1000)}
        assert len(ids) > 990  # effectively unique


class TestMakeRequest:
    def test_shape(self):
        req = protocol.make_request("ping", {"x": 1})
        assert req["v"] == protocol.PROTOCOL_VERSION
        assert req["cmd"] == "ping"
        assert req["params"] == {"x": 1}

    def test_default_params(self):
        assert protocol.make_request("ping")["params"] == {}


class TestSysExCodec:
    def test_roundtrip_request(self):
        rid = protocol.new_request_id()
        payload = {"cmd": "ping", "params": {"a": 1, "b": "two"}}
        data = protocol.encode_message(protocol.DIR_REQUEST, rid, payload)
        # All bytes must be 7-bit safe for MIDI SysEx.
        assert all(b <= 0x7F for b in data)
        direction, got_rid, got_payload = protocol.decode_message(data)
        assert direction == protocol.DIR_REQUEST
        assert got_rid == rid
        assert got_payload == payload

    def test_decode_rejects_foreign(self):
        assert protocol.decode_message(bytes([0x01, 0x02, 0x03])) is None

    def test_bad_direction_raises(self):
        with pytest.raises(ValueError):
            protocol.encode_message(0x7A, protocol.new_request_id(), {})

    def test_bad_request_id_raises(self):
        with pytest.raises(ValueError):
            protocol.encode_message(protocol.DIR_REQUEST, "short", {})
