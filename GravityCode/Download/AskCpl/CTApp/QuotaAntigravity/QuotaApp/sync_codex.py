"""Read the latest non-sensitive Codex rate-limit snapshot from local sessions."""

from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import socket
from pathlib import Path


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def _read_data(path: Path) -> dict:
    try:
        return json.loads(base64.b64decode(path.read_text("utf-8").strip()).decode("utf-8"))
    except Exception:
        return {}


def _write_data(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    path.write_text(base64.b64encode(raw).decode("ascii"), "utf-8")


def _latest_rate_limits(sessions_dir: Path) -> tuple[dict | None, Path | None]:
    if not sessions_dir.exists():
        return None, None
    files = sorted(sessions_dir.rglob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True)
    for file_path in files:
        try:
            lines = file_path.read_text("utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            try:
                event = json.loads(line)
                limits = event.get("payload", {}).get("rate_limits")
                if limits:
                    return limits, file_path
            except json.JSONDecodeError:
                continue
    return None, None


def _window(data: dict | None) -> dict | None:
    if not data:
        return None
    return {
        "usedPercent": data.get("used_percent"),
        "remainingPercent": None if data.get("used_percent") is None else max(0, 100 - data["used_percent"]),
        "windowMinutes": data.get("window_minutes"),
        "resetsAt": data.get("resets_at"),
    }


def sync(target: Path, label_override: str = "") -> dict:
    limits, source = _latest_rate_limits(_codex_home() / "sessions")
    if not limits:
        return {
            "status": "no_data",
            "message": "Chua tim thay Codex rate-limit event. Hay dung Codex it nhat mot lan tren may nay.",
            "synced": 0,
        }

    plan = limits.get("plan_type") or "unknown"
    label = label_override.strip() or os.environ.get("CODEX_ACCOUNT_LABEL", "").strip() or f"Codex ({plan})"
    # Keep snapshots written by the multi-account extension.  This command only
    # refreshes the active local Codex profile; it must not erase other rows.
    snapshot = _read_data(target)
    snapshot.update({
        "schemaVersion": 1,
        "provider": "codex",
        "updatedAt": limits.get("updated_at"),
        "sourceMachine": socket.gethostname() or platform.node(),
        "sourceFile": source.name if source else "",
    })
    accounts = snapshot.setdefault("accounts", {})
    accounts[label] = {
        "label": label,
        "planType": plan,
        "primary": _window(limits.get("primary")),
        "secondary": _window(limits.get("secondary")),
        "rateLimitReached": limits.get("rate_limit_reached_type"),
        "updatedAt": limits.get("updated_at"),
    }
    _write_data(target, snapshot)
    return {"status": "ok", "message": "Codex quota da duoc dong bo", "synced": 1, "dataPath": str(target), "account": label}


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync non-sensitive local Codex quota metadata")
    parser.add_argument("data_path", nargs="?", default=str(Path.home() / ".quota-tracker" / "codex_quota_data.dat"))
    parser.add_argument("--label", default="", help="Optional user-defined account label; no token or credential is read")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = sync(Path(args.data_path), args.label)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result["message"])
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
