from __future__ import annotations

import argparse
import json
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple

from .provenance import make_provenance

JSON_CT = "application/json; charset=utf-8"


# ============================================================
# INTERNAL ECHOTOME BINDING
# ============================================================
def _try_import_echotome_core():
    """
    Bind Echotome REAL encode/decode entrypoints here.
    This overlay refuses to hallucinate internal APIs.

    Example (replace with real path):
        from echotome.core import encode_audio_to_artifact, decode_artifact_to_audio
        return {"encode": encode_audio_to_artifact, "decode": decode_artifact_to_audio}

    Until wired, encode/decode return structured errors.
    """
    try:
        # TODO: replace with real Echotome entrypoints
        return {"encode": None, "decode": None}
    except Exception:
        return {"encode": None, "decode": None}


_CORE = _try_import_echotome_core()


# ============================================================
# HTTP HELPERS
# ============================================================
def _read_json(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("root must be object")
    return obj


def _write_json(handler: BaseHTTPRequestHandler, status: int, body: Dict[str, Any]) -> None:
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", JSON_CT)
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


# ============================================================
# CAPABILITY ROUTER
# ============================================================
def _capability_router(cap: str, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    if cap == "echotome.ping":
        return True, {"pong": True, "encode_bound": _CORE.get("encode") is not None, "decode_bound": _CORE.get("decode") is not None}

    if cap == "echotome.echo":
        return True, {"echo": payload}

    if cap == "echotome.encode":
        fn = _CORE.get("encode")
        if fn is None:
            return False, {
                "message": "Echotome encode not wired",
                "expected_input": {
                    "audio_path": "string OR base64_audio: string",
                    "mode": "e.g. 'stego'|'encrypt'|'both'",
                    "key": "optional string",
                    "params": "optional dict"
                },
                "action": "Bind encode function in _try_import_echotome_core()"
            }
        # Example once wired:
        # out = fn(**payload)
        # return True, out
        return False, {"message": "encode wired but not implemented"}

    if cap == "echotome.decode":
        fn = _CORE.get("decode")
        if fn is None:
            return False, {
                "message": "Echotome decode not wired",
                "expected_input": {
                    "artifact_path": "string OR base64_artifact: string",
                    "key": "optional string",
                    "params": "optional dict"
                },
                "action": "Bind decode function in _try_import_echotome_core()"
            }
        # Example once wired:
        # out = fn(**payload)
        # return True, out
        return False, {"message": "decode wired but not implemented"}

    return False, {"message": f"unknown capability: {cap}", "known": ["echotome.ping","echotome.echo","echotome.encode","echotome.decode"]}


# ============================================================
# HTTP SERVER
# ============================================================
class EchotomeOverlayHandler(BaseHTTPRequestHandler):
    server_version = "echotome-overlay/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/health":
            _write_json(self, 200, {"ok": True, "service": "echotome_overlay"})
            return
        _write_json(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/run":
            _write_json(self, 404, {"ok": False, "error": "not found"})
            return

        try:
            req = _read_json(self)
        except Exception as e:
            _write_json(self, 400, {"ok": False, "error": f"invalid json: {e}"})
            return

        cap = req.get("capability", "echotome.echo")
        seed = req.get("seed")
        input_payload = req.get("input", {})
        if not isinstance(input_payload, dict):
            _write_json(self, 400, {"ok": False, "error": "input must be an object"})
            return

        prov = make_provenance("echotome", cap, input_payload, seed=seed).to_dict()
        ok, out = _capability_router(cap, input_payload)

        if ok:
            _write_json(self, 200, {"ok": True, "result": out, "error": None, "provenance": prov})
        else:
            _write_json(self, 200, {"ok": False, "result": None, "error": out, "provenance": prov})


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8793)
    args = ap.parse_args()

    srv = ThreadedHTTPServer((args.host, args.port), EchotomeOverlayHandler)
    try:
        srv.serve_forever()
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
