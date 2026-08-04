"""Deterministic validation and rendering for the AskCpl roadmap generator.

The LLM may propose curriculum content, but it never decides whether that
content is safe to save.  This module is intentionally dependency-free so it
can be tested without an API key or a Tkinter window.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


class RoadmapValidationError(ValueError):
    """Raised when an LLM response cannot be used as a roadmap."""


def restore_locked_day_identity(existing: list[dict[str, Any]], candidate: Any) -> tuple[list[dict[str, Any]], list[tuple[int, str, str]]]:
    """Keep stable Day IDs/source metadata while accepting content revisions.

    Topic IDs are primary keys referenced by prerequisites and the registry.
    Models sometimes correct an opaque ID spelling, which must not invalidate a
    successful content review or silently break those links.
    """
    if not isinstance(candidate, list):
        raise RoadmapValidationError("phase tích hợp không trả về mảng JSON.")
    expected_days = [item.get("day") for item in existing]
    actual_days = [item.get("day") for item in candidate if isinstance(item, dict)]
    if actual_days != expected_days or len(candidate) != len(existing):
        raise RoadmapValidationError("phase tích hợp trả về thiếu, trùng hoặc sai Day.")
    restored, changes = [], []
    for original, generated in zip(existing, candidate):
        if not isinstance(generated, dict):
            raise RoadmapValidationError("phase tích hợp chứa Day không phải object JSON.")
        item = dict(generated)
        old_id, new_id = original.get("topic_id"), item.get("topic_id")
        if new_id != old_id:
            changes.append((original.get("day"), str(new_id), str(old_id)))
        item["topic_id"] = old_id
        # Source files are user-selected local provenance, not model content.
        item["source_files"] = list(original.get("source_files", []))
        restored.append(item)
    return restored, changes


def load_json_response(text: str) -> Any:
    """Accept only JSON, optionally surrounded by a Markdown code fence."""
    value = (text or "").strip()
    value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*```$", "", value).strip()
    # Gemini occasionally prefixes a JSON answer with one short sentence.
    # Decode the first complete JSON value rather than accepting prose as part
    # of the data contract.  This remains strict about the decoded value.
    first_object = min((index for index in (value.find("{"), value.find("[")) if index >= 0), default=-1)
    candidates = [value]
    if first_object > 0:
        candidates.append(value[first_object:])
    # Conservative repairs for two common JSON-mode defects: a trailing comma
    # and an unquoted ASCII key.  We intentionally do not attempt arbitrary
    # semantic repairs.
    repaired = re.sub(r",\s*([}\]])", r"\1", candidates[-1]) if candidates else value
    repaired = re.sub(r"([,{]\s*)([A-Za-z_][A-Za-z0-9_-]*)(\s*:)", r'\1"\2"\3', repaired)
    candidates.append(repaired)
    last_error = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            try:
                parsed, _end = json.JSONDecoder().raw_decode(candidate)
                return parsed
            except json.JSONDecodeError as raw_error:
                last_error = raw_error
    raise RoadmapValidationError(f"Phản hồi JSON không hợp lệ: {last_error.msg if last_error else 'rỗng'}") from last_error


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _similar(left: str, right: str) -> float:
    return SequenceMatcher(None, left.casefold(), right.casefold()).ratio()


def _cycles(edges: dict[str, list[str]]) -> bool:
    visiting, visited = set(), set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(child) for child in edges.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in edges)


def validate_plan(plan: Any, expected_days: int | None = None, require_micro: bool = False, sim_check_enabled: bool = True, sim_threshold: float = 0.96) -> dict[str, Any]:
    """Validate a reviewed skeleton and return it unchanged when it is safe."""
    if not isinstance(plan, dict):
        raise RoadmapValidationError("Roadmap phải là JSON object.")
    profile, skeleton = plan.get("domain_profile"), plan.get("skeleton")
    if not isinstance(profile, dict) or not isinstance(skeleton, list) or not skeleton:
        raise RoadmapValidationError("Thiếu domain_profile hoặc skeleton không rỗng.")

    days, ids, first_day = [], set(), {}
    titles: list[tuple[int, str]] = []
    for index, item in enumerate(skeleton, start=1):
        if not isinstance(item, dict):
            raise RoadmapValidationError(f"Day thứ {index} không phải object.")
        day, title = item.get("day"), _text(item.get("topic"))
        topic_id = _text(item.get("topic_id"))
        details, keywords, prerequisites = item.get("details"), item.get("keywords", []), item.get("prerequisites", [])
        if not isinstance(day, int) or day < 1:
            raise RoadmapValidationError(f"Day thứ {index} có số Day không hợp lệ.")
        if not title or not topic_id:
            raise RoadmapValidationError(f"Day {day} thiếu topic hoặc topic_id.")
        if not isinstance(details, list) or not all(_text(value) for value in details):
            raise RoadmapValidationError(f"Day {day} phải có details dạng mảng văn bản.")
        if not isinstance(keywords, list) or not isinstance(prerequisites, list):
            raise RoadmapValidationError(f"Day {day} có keywords/prerequisites không hợp lệ.")
        if day in days:
            raise RoadmapValidationError(f"Day {day} bị trùng.")
        days.append(day)
        if topic_id in ids:
            raise RoadmapValidationError(f"topic_id '{topic_id}' bị trùng; mỗi Day cần id riêng.")
        ids.add(topic_id)
        first_day[topic_id] = min(first_day.get(topic_id, day), day)
        titles.append((day, title))
        if require_micro:
            minutes = item.get("estimated_minutes")
            concrete = _text(item.get("concrete_project"))
            materials = item.get("materials")
            done = item.get("definition_of_done")
            if not isinstance(minutes, int) or not 5 <= minutes <= 30:
                raise RoadmapValidationError(f"Day {day} phải có estimated_minutes từ 5 đến 30.")
            if len(concrete) < 4:
                raise RoadmapValidationError(f"Day {day} thiếu concrete_project (món đồ/sản phẩm cụ thể).")
            vague = ("tìm hiểu", "nghiên cứu", "tổng quan", "học về", "khái niệm")
            if _text(item.get("kind")).casefold() == "lesson" and concrete.casefold().startswith(vague):
                raise RoadmapValidationError(f"Day {day} concrete_project còn chung chung, phải là món đồ/sản phẩm làm được.")
            if not isinstance(materials, list) or not all(_text(value) for value in materials):
                raise RoadmapValidationError(f"Day {day} thiếu danh sách materials cụ thể.")
            if not isinstance(done, list) or not all(_text(value) for value in done):
                raise RoadmapValidationError(f"Day {day} thiếu definition_of_done.")

    wanted = expected_days if expected_days is not None else max(days)
    if sorted(days) != list(range(1, wanted + 1)):
        raise RoadmapValidationError(f"Day phải liên tục từ 1 đến {wanted}, không thiếu hoặc trùng.")

    if sim_check_enabled:
        for position, (day, title) in enumerate(titles):
            for other_day, other_title in titles[:position]:
                ratio = _similar(title, other_title)
                if ratio >= sim_threshold:
                    raise RoadmapValidationError(
                        f"Day {day} trùng nội dung gần như hoàn toàn với Day {other_day} ({ratio:.0%})."
                    )

    is_wiki = any(_text(item.get("kind")).casefold() == "extraction" for item in skeleton)

    if not is_wiki:
        edges: dict[str, list[str]] = {}
        for item in skeleton:
            topic_id, day = item["topic_id"], item["day"]
            required = [_text(value) for value in item.get("prerequisites", [])]
            missing = [value for value in required if value not in ids]
            if missing:
                raise RoadmapValidationError(f"Day {day} tham chiếu prerequisite chưa tồn tại: {', '.join(missing)}.")
            later = [value for value in required if first_day[value] >= day and value != topic_id]
            if later:
                raise RoadmapValidationError(f"Day {day} học trước prerequisite: {', '.join(later)}.")
            edges.setdefault(topic_id, []).extend(value for value in required if value != topic_id)
        if _cycles(edges):
            raise RoadmapValidationError("Đồ thị prerequisites có vòng lặp.")

    phases = {_text(item.get("phase")) for item in skeleton if _text(item.get("phase"))}
    if len(phases) >= 2 and not any(_text(item.get("kind")).casefold() == "capstone" for item in skeleton):
        if not is_wiki:
            raise RoadmapValidationError("Roadmap nhiều phase phải có ít nhất một Day kind='capstone'.")
    return plan


def validate_revision(original_plan: dict, revised_plan: Any, expected_days: int | None = None, require_micro: bool = False, sim_check_enabled: bool = True, sim_threshold: float = 0.96) -> dict[str, Any]:
    """A critic may add material, but cannot silently delete existing topics."""
    validate_plan(original_plan, expected_days, require_micro, sim_check_enabled=sim_check_enabled, sim_threshold=sim_threshold)
    old_ids = {item["topic_id"] for item in original_plan["skeleton"]}
    new_items = revised_plan.get("skeleton", []) if isinstance(revised_plan, dict) else []
    new_ids = {item.get("topic_id") for item in new_items if isinstance(item, dict)}
    removed = old_ids - new_ids
    if removed:
        raise RoadmapValidationError("Bản phản biện làm mất topic cũ: " + ", ".join(sorted(removed)[:8]))
    validate_plan(revised_plan, expected_days=expected_days, require_micro=require_micro, sim_check_enabled=sim_check_enabled, sim_threshold=sim_threshold)
    return revised_plan


def render_toc(plan: dict[str, Any]) -> str:
    profile = plan["domain_profile"]
    lines = [f"# Roadmap: {_text(profile.get('title')) or 'Untitled'}", "", "## Mục lục"]
    for item in plan["skeleton"]:
        lines.append(f"- Day {item['day']}: {item['topic']} ({_text(item.get('phase')) or 'Core'})")
    return "\n".join(lines) + "\n"


def render_markdown(plan: dict[str, Any], lessons: Iterable[dict[str, Any]]) -> str:
    by_day = {item.get("day"): item for item in lessons if isinstance(item, dict)}
    lines = [f"# Roadmap: {_text(plan['domain_profile'].get('title')) or 'Untitled'}", ""]
    for item in plan["skeleton"]:
        lesson = by_day.get(item["day"], {})
        prompt = _text(lesson.get("prompt"))
        exercises = lesson.get("exercises")
        tags = lesson.get("tags")
        if not prompt or not isinstance(exercises, list) or not exercises or not isinstance(tags, list) or not tags:
            raise RoadmapValidationError(f"Nội dung Day {item['day']} thiếu prompt, exercises hoặc tags.")
        source_files = [str(source).strip() for source in item.get("source_files", []) if _text(source)]
        lines.extend([
            f"## Day {item['day']} — {item['topic']}",
            *( [f"<!-- sources: {', '.join(source_files)} -->"] if source_files else [] ),
            "**Prompt:**",
            prompt,
            "",
            "**Bài tập:**",
            *[f"- {_text(exercise)}" for exercise in exercises if _text(exercise)],
            "",
            "**Tags:**",
            " ".join(str(tag) for tag in tags if _text(tag)),
            "",
            "---",
            "",
        ])
    result = "\n".join(lines)
    verify_markdown(result, len(plan["skeleton"]))
    return result


def verify_markdown(markdown: str, expected_days: int) -> None:
    headings = [int(value) for value in re.findall(r"(?m)^## Day\s+(\d+)\s+—\s+.+$", markdown)]
    if headings != list(range(1, expected_days + 1)):
        raise RoadmapValidationError("Markdown thiếu/trùng/sai thứ tự heading Day.")
    for label in ("Prompt", "Bài tập", "Tags"):
        if len(re.findall(rf"(?m)^\*\*{re.escape(label)}:\*\*$", markdown)) != expected_days:
            raise RoadmapValidationError(f"Markdown phải có đúng {expected_days} khối {label}.")
    if any(bad in markdown for bad in ("Ãƒ", "Ã¢â‚¬", "Ã‚")):
        raise RoadmapValidationError("Markdown có dấu hiệu lỗi encoding.")


def atomic_write(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary, target)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
