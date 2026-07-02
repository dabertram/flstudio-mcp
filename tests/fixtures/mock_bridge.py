"""A stateful mock of the FL bridge for offline integration tests.

Implements the subset of ``FLBridge.call(command, params)`` that the server-side
tools and the safety layer exercise, holding mixer-track / channel / plugin
state in memory so snapshot -> write -> readback -> rollback can be tested with
no live FL. Every call is recorded in ``call_log`` for assertions.
"""
from __future__ import annotations

from typing import Any

from fl_studio_mcp import protocol


def _norm_to_db(n: float) -> float:
    # FL mixer fader: 0.8 == unity (0 dB). Rough monotonic mapping, good enough
    # for tests that only need round-trip consistency.
    if n <= 0:
        return -60.0
    return round(40.0 * (n - 0.8) / 0.8, 2)


class MockBridge:
    def __init__(self, tracks: list[dict] | None = None,
                 channels: list[dict] | None = None):
        # Master at index 0, then a small default mix.
        self.tracks = tracks or [
            {"index": 0, "name": "Master", "vol_norm": 0.8, "vol_db": 0.0,
             "pan": 0.0, "mute": False, "solo": False, "color": {"int": 0}},
            {"index": 1, "name": "Kick", "vol_norm": 0.8, "vol_db": 0.0,
             "pan": 0.0, "mute": False, "solo": False, "color": {"int": 0}},
            {"index": 2, "name": "Snare", "vol_norm": 0.7, "vol_db": -3.0,
             "pan": 0.0, "mute": False, "solo": False, "color": {"int": 0}},
            {"index": 3, "name": "Lead Vocal", "vol_norm": 0.75, "vol_db": -2.0,
             "pan": 0.0, "mute": False, "solo": False, "color": {"int": 0}},
        ]
        self.channels = channels or [
            {"index": 0, "name": "Kick", "target": 1},
            {"index": 1, "name": "Serum 2", "target": 3},
        ]
        # routes[src] = set(dst)
        self.routes: dict[int, set[int]] = {1: {0}, 2: {0}, 3: {0}}
        # plugins[track] = [{"slot", "name"}]
        self.plugins: dict[int, list[dict]] = {
            3: [{"slot": 0, "name": "Fruity Limiter"}],
        }
        # params[(track, slot)] = [{"i", "name", "v", "s"}]
        self.params: dict[tuple, list[dict]] = {}
        self.peaks: dict[int, float] = {}
        self.call_log: list[dict] = []
        self._alive = True

    # -- FLBridge interface --------------------------------------------------
    def call(self, command: str, params: dict | None = None, *, timeout: Any = None):
        params = params or {}
        self.call_log.append({"cmd": command, "params": dict(params)})
        return self._dispatch(command, params)

    def is_alive(self) -> bool:
        return self._alive

    def heartbeat_age(self) -> float:
        return 0.1

    def open(self) -> None:  # parity
        return None

    def close(self) -> None:  # parity
        return None

    # -- helpers -------------------------------------------------------------
    def _track(self, i: int) -> dict:
        for t in self.tracks:
            if t["index"] == i:
                return t
        raise KeyError(i)

    def _channel(self, i: int) -> dict:
        for c in self.channels:
            if c["index"] == i:
                return c
        raise KeyError(i)

    # -- command dispatch ----------------------------------------------------
    def _dispatch(self, command: str, p: dict):
        P = protocol
        if command == P.CMD_PING:
            return {"fl_version": "mock", "protocol_version": P.PROTOCOL_VERSION}

        # mixer reads
        if command == P.CMD_MIXER_GET_TRACK:
            return dict(self._track(int(p["index"])))
        if command == P.CMD_MIXER_LIST_TRACKS:
            return self._page(self.tracks, p, "tracks")

        # mixer writes
        if command == P.CMD_MIXER_SET_VOLUME:
            t = self._track(int(p["track"]))
            if p.get("unit") == "db":
                t["vol_db"] = float(p["value"])
            else:
                t["vol_norm"] = float(p["value"])
                t["vol_db"] = _norm_to_db(float(p["value"]))
            return dict(t)
        if command == P.CMD_MIXER_SET_PAN:
            t = self._track(int(p["track"]))
            t["pan"] = float(p["value"])
            return dict(t)
        if command == P.CMD_MIXER_SET_MUTE:
            t = self._track(int(p["track"]))
            t["mute"] = bool(p["state"])
            return dict(t)
        if command == P.CMD_MIXER_SET_SOLO:
            t = self._track(int(p["track"]))
            t["solo"] = bool(p["state"])
            return dict(t)
        if command == P.CMD_MIXER_SET_NAME:
            t = self._track(int(p["track"]))
            t["name"] = str(p["name"])
            return dict(t)
        if command == P.CMD_MIXER_SET_COLOR:
            t = self._track(int(p["track"]))
            col = int(p.get("color", 0))
            t["color"] = {"int": col}
            return dict(t)
        if command == P.CMD_MIXER_GET_COLOR:
            t = self._track(int(p["track"]))
            return {"track": t["index"], "color": t.get("color", {"int": 0})}

        # channels
        if command == P.CMD_CHANNEL_GET:
            return dict(self._channel(int(p["index"])))
        if command == P.CMD_CHANNEL_LIST:
            return self._page(self.channels, p, "channels")

        # peaks
        if command == P.CMD_MIXER_GET_PEAKS:
            return {"track": int(p["track"]), "peak_max": self.peaks.get(int(p["track"]), 0.0)}

        # routing
        if command == P.CMD_MIXER_GET_ROUTING:
            src = int(p["track"])
            dests = sorted(self.routes.get(src, set()))
            return {"track": src, "routes_to": [{"dst": d} for d in dests]}
        if command == P.CMD_MIXER_SET_ROUTE:
            src, dst, enabled = int(p["src"]), int(p["dst"]), bool(p["enabled"])
            self.routes.setdefault(src, set())
            if enabled:
                self.routes[src].add(dst)
            else:
                self.routes[src].discard(dst)
            return {"src": src, "dst": dst, "enabled": enabled}

        # plugins
        if command == P.CMD_PLUGIN_LIST:
            return {"track": int(p["track"]), "slots": self.plugins.get(int(p["track"]), [])}
        if command == P.CMD_PLUGIN_GET_PARAM:
            plist = self.params.get((int(p["track"]), int(p["slot"])), [])
            idx = int(p["param"])
            for pr in plist:
                if pr["i"] == idx:
                    return dict(pr)
            return {"i": idx, "name": "", "v": 0.0, "s": ""}
        if command == P.CMD_PLUGIN_SET_PARAM:
            plist = self.params.setdefault((int(p["track"]), int(p["slot"])), [])
            idx = int(p["param"])
            for pr in plist:
                if pr["i"] == idx:
                    pr["v"] = float(p["value"])
                    return dict(pr)
            pr = {"i": idx, "name": "", "v": float(p["value"]), "s": ""}
            plist.append(pr)
            return dict(pr)
        if command == P.CMD_PLUGIN_GET_PARAMS:
            plist = self.params.get((int(p["track"]), int(p["slot"])), [])
            return self._page(plist, p, "params")

        raise ValueError(f"MockBridge: unhandled command {command!r}")

    @staticmethod
    def _page(items: list, p: dict, key: str, page_size: int = 150):
        start = int(p.get("start", 0))
        chunk = items[start:start + page_size]
        nxt = start + page_size
        next_start = nxt if nxt < len(items) else None
        return {"total": len(items), "start": start, "next_start": next_start, key: list(chunk)}
