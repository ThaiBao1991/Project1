# -*- coding: utf-8 -*-
"""tools/statefile.py — Kho trạng thái bền vững cho pipeline media.

VÌ SAO: các file `*_done.json` trong `data/logs` đã nhiều lần biến mất (dọn
worktree, công cụ ngoài, đồng bộ thư mục…). Khi mất:
  • `finalize_lite` tưởng chưa upload ⇒ pack/upload lại (tốn GB + thời gian);
  • `cleanup_done_media` không dám xoá media local ⇒ đầy đĩa, pipeline dừng;
  • `fill_remaining_after_chinese` chờ mãi mốc "Trung đã xong".

CÁCH LÀM: lưu mỗi trạng thái ở HAI nơi, đọc bản mới hơn:
  1. `D:\\VocabularyAppData\\state\\<name>`  ← bản chính, ngoài repo
  2. `data/logs/<name>`                      ← bản sao cho log/tool cũ
Mỗi lần ghi còn tạo snapshot trong `...\\state\\history\\` (giữ 30 bản gần nhất)
để truy được trạng thái đã từng có, kể cả khi một bên bị xoá.

API:
  statefile.path(name)      -> đường dẫn bản chính (tự đồng bộ 2 bên)
  statefile.load(name)      -> dict (rỗng nếu chưa có/hỏng)
  statefile.save(name, obj) -> ghi cả 2 bản + snapshot
"""
from __future__ import annotations

import json
import os
import shutil
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY = os.path.join(BASE, "data", "logs")
CANON = os.environ.get("VOCAB_STATE_DIR") or r"D:\VocabularyAppData\state"
HIST = os.path.join(CANON, "history")
KEEP_HIST = 30


def _read_json(p: str):
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _write_json(p: str, data: dict) -> bool:
    tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(tmp, p)
        return True
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False


def _at(v) -> str:
    return str((v or {}).get("at") or "") if isinstance(v, dict) else ""


def _merged(canon: dict, legacy: dict) -> dict:
    """Hợp nhất 2 bản: khóa nào có `at` mới hơn thì thắng.

    Không dùng mtime vì tiến trình cũ có thể ghi đè bản sao với nội dung cũ.
    """
    out = dict(legacy)
    for k, v in canon.items():
        if k not in out:
            out[k] = v
        elif _at(v) >= _at(out[k]):
            out[k] = v
    return out


def sync(name: str) -> str:
    """Đồng bộ 2 bản (hợp nhất, không mất khóa) và trả về bản chính."""
    try:
        os.makedirs(CANON, exist_ok=True)
    except OSError:
        return os.path.join(LEGACY, name)
    canon = os.path.join(CANON, name)
    legacy = os.path.join(LEGACY, name)
    c, l = _read_json(canon), _read_json(legacy)
    if c is None and l is not None:
        c = l
    elif c is not None and l is None:
        l = c
    if c is None:
        return canon
    merged = _merged(c, l)
    if merged != c or not os.path.isfile(canon):
        _write_json(canon, merged)
    if merged != l or not os.path.isfile(legacy):
        _write_json(legacy, merged)
    return canon


def path(name: str) -> str:
    return sync(name)


def load(name: str) -> dict:
    p = path(name)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _snapshot(name: str, src: str) -> None:
    try:
        os.makedirs(HIST, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        dst = os.path.join(HIST, f"{name}.{stamp}")
        shutil.copy2(src, dst)
        olds = sorted(f for f in os.listdir(HIST) if f.startswith(name + "."))
        for f in olds[:-KEEP_HIST]:
            try:
                os.remove(os.path.join(HIST, f))
            except OSError:
                pass
    except OSError:
        pass


def save(name: str, data: dict) -> str:
    """Ghi atomically cả bản chính lẫn bản sao; trả về đường dẫn bản chính."""
    targets: list[str] = []
    try:
        os.makedirs(CANON, exist_ok=True)
        targets.append(os.path.join(CANON, name))
    except OSError:
        pass
    try:
        os.makedirs(LEGACY, exist_ok=True)
        targets.append(os.path.join(LEGACY, name))
    except OSError:
        pass
    if not targets:
        return ""
    for p in targets:
        _write_json(p, data)
    _snapshot(name, targets[0])
    return targets[0]
