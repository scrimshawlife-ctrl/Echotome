from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def try_git_head() -> Optional[str]:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return None


def env_fingerprint() -> Dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git_head": try_git_head(),
        "cwd": os.getcwd(),
    }


@dataclass(frozen=True)
class Provenance:
    run_id: str
    ts_utc: str
    payload_hash: str
    env: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "ts_utc": self.ts_utc,
            "payload_hash": self.payload_hash,
            "env": self.env,
        }


def make_provenance(
    overlay: str,
    capability: str,
    payload: Dict[str, Any],
    seed: Optional[str] = None,
) -> Provenance:
    ts = utc_iso()
    payload_hash = sha256_hex(_canon(payload))
    salt = seed if seed is not None else ts
    run_id = sha256_hex(
        _canon(
            {
                "overlay": overlay,
                "capability": capability,
                "payload_hash": payload_hash,
                "salt": salt,
            }
        )
    )
    return Provenance(run_id=run_id, ts_utc=ts, payload_hash=payload_hash, env=env_fingerprint())
