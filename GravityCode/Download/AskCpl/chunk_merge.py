import json
import os
import re

from gemini_safe import pace  # re-export từ bộ điều phối an toàn dùng chung


def _hard_cut(text, max_chars):
    text = text.strip()
    cut = text.rfind("\n", 0, max_chars)
    if cut <= 0:
        cut = max_chars
    return text[:cut].strip(), text[cut:].strip()


def split_text(text, max_chars=30000, min_chars=2000):
    """Chia văn bản thành các phần deterministic, ưu tiên cắt tại biên đoạn.

    - Cắt tại dòng trắng (\n\n) gần max_chars nếu có.
    - Đoạn đơn quá dài sẽ bị hard-cut tại rfind("\n") hoặc max_chars.
    - Cùng input -> cùng output (không dùng ngẫu nhiên).
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    segments = re.split(r"(\n\s*\n)", text)
    parts = []
    current = ""
    for seg in segments:
        if not seg:
            continue
        if current and len(current) + len(seg) > max_chars and len(current) >= min_chars:
            parts.append(current.strip())
            current = seg
            continue
        if len(current) + len(seg) > max_chars:
            remaining = current + seg
            while len(remaining) > max_chars:
                head, remaining = _hard_cut(remaining, max_chars)
                if not head:
                    head, remaining = remaining[:max_chars], remaining[max_chars:]
                parts.append(head)
            current = remaining
            continue
        current = current + seg
    if current.strip():
        parts.append(current.strip())
    return [p for p in parts if p]


def dedup_merge(parts, heading_pattern=None):
    """Nối các phần; nếu heading đầu của phần sau trùng phần trước thì bỏ để tránh lặp."""
    if not parts:
        return ""
    merged = []
    prev_heading = None
    for part in parts:
        text = part.strip()
        if not text:
            continue
        if heading_pattern:
            first_line = text.split("\n", 1)[0].strip()
            m = re.match(heading_pattern, first_line)
            if m:
                if m.group(0) == prev_heading:
                    text = text[len(first_line):].strip()
                else:
                    prev_heading = m.group(0)
        merged.append(text)
    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(merged))


class PartStore:
    """Checkpoint JSON per (unit_id, part_index) để chống trùng lặp khi retry/resume."""

    def __init__(self, path):
        self.path = path
        self._data = self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
        return {}

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False)
        os.replace(tmp, self.path)

    def parts(self, unit_id):
        return sorted(self._data.get(unit_id, {}).keys())

    def get(self, unit_id, part_index):
        return self._data.get(unit_id, {}).get(str(part_index))

    def save_part(self, unit_id, part_index, text):
        self._data.setdefault(unit_id, {})[str(part_index)] = text
        self._save()

    def clear(self, unit_id=None):
        if unit_id is None:
            self._data = {}
        else:
            self._data.pop(unit_id, None)
        self._save()