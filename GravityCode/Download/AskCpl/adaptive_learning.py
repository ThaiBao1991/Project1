"""State and validation helpers for adaptive, Gemini-rendered learning paths.

The roadmap remains the curriculum map.  This module stores what is specific to
one learner, selects the small amount of history relevant to a Day, and keeps
the model output machine-readable before it is rendered as HTML.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from typing import Any

from domain_profiles import instruction_for


PROFILE_FILE = "course_profile.json"
STATE_FILE = "learner_state.json"

LESSON_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "lesson_markdown": {"type": "string", "description": "Bài học đầy đủ bằng tiếng Việt."},
        "learning_objectives": {"type": "array", "items": {"type": "string"}},
        "deliverable": {"type": "string", "description": "Sản phẩm/bằng chứng người học phải nộp."},
        "completion_check": {"type": "array", "items": {"type": "string"}},
        "review_summary": {"type": "string", "description": "Ôn đúng kiến thức liên quan trước đó."},
        "clarifying_questions": {
            "type": "array",
            "description": "Tối đa hai câu hỏi chỉ khi câu trả lời làm thay đổi bài tiếp theo.",
            "items": {"type": "string"},
        },
        "visual_plan": {
            "type": "object",
            "properties": {
                "needed": {"type": "boolean"},
                "purpose": {"type": "string"},
                "prompts": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["needed", "purpose", "prompts"],
        },
        "source_usage": {"type": "array", "items": {"type": "string"}},
        "factual_claims": {
            "type": "array",
            "description": "Chỉ dùng khi có Knowledge Pack; mỗi fact phải trỏ entity/source đã được phép.",
            "items": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                    "claim": {"type": "string"},
                },
                "required": ["entity_id", "source_ids", "claim"],
            },
        },
    },
    "required": [
        "lesson_markdown", "learning_objectives", "deliverable", "completion_check",
        "review_summary", "clarifying_questions", "visual_plan", "source_usage",
    ],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_write(path: str, payload: dict[str, Any]) -> None:
    folder = os.path.dirname(path) or "."
    os.makedirs(folder, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".adaptive_", suffix=".json", dir=folder, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _load(path: str, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else fallback
    except (OSError, json.JSONDecodeError):
        return fallback


def default_profile() -> dict[str, Any]:
    return {
        "version": 1,
        "title": "",
        "domain": "",
        "goal": "",
        "current_level": "",
        "minutes_per_day": 30,
        "language": "Tiếng Việt",
        "available_resources": "",
        "constraints": "",
        "learning_preference": "Thực hành tạo sản phẩm",
        "created_at": _now(),
        "updated_at": _now(),
    }


def default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "generated_days": {},
        "learner_feedback": {},
        "mastery": {},
        "open_questions": [],
        "updated_at": _now(),
    }


def profile_path(out_dir: str) -> str:
    return os.path.join(out_dir, PROFILE_FILE)


def state_path(out_dir: str) -> str:
    return os.path.join(out_dir, STATE_FILE)


def load_profile(out_dir: str) -> dict[str, Any]:
    profile = default_profile()
    profile.update(_load(profile_path(out_dir), {}))
    return profile


def save_profile(out_dir: str, values: dict[str, Any]) -> dict[str, Any]:
    profile = default_profile()
    profile.update(values)
    profile["updated_at"] = _now()
    _atomic_write(profile_path(out_dir), profile)
    return profile


def load_state(out_dir: str) -> dict[str, Any]:
    state = default_state()
    state.update(_load(state_path(out_dir), {}))
    for key in ("generated_days", "learner_feedback", "mastery"):
        if not isinstance(state.get(key), dict):
            state[key] = {}
    if not isinstance(state.get("open_questions"), list):
        state["open_questions"] = []
    return state


def save_state(out_dir: str, state: dict[str, Any]) -> None:
    state["updated_at"] = _now()
    _atomic_write(state_path(out_dir), state)


def profile_questions(profile: dict[str, Any]) -> list[dict[str, str]]:
    """Small, deterministic intake question set; it prevents daily re-asking."""
    questions: list[dict[str, str]] = []
    required = [
        ("domain", "Bạn muốn học/chế tạo chủ đề cụ thể nào?"),
        ("goal", "Bạn muốn làm được sản phẩm/kết quả cụ thể gì sau khóa học?"),
        ("current_level", "Bạn đã biết gì về chủ đề này? Hãy nêu ví dụ cụ thể."),
        ("minutes_per_day", "Bạn có thể học/thực hành bao nhiêu phút mỗi ngày?"),
        ("available_resources", "Bạn đang có thiết bị, phần mềm, tài liệu hoặc vật liệu nào?"),
    ]
    for field, question in required:
        if not str(profile.get(field, "")).strip():
            questions.append({"field": field, "question": question})
    domain = str(profile.get("domain", "")).casefold()
    if any(word in domain for word in ("đồ chơi", "diy", "thủ công", "craft")) and not str(profile.get("constraints", "")).strip():
        questions.append({
            "field": "constraints",
            "question": "Trẻ ở độ tuổi nào, có người lớn giám sát không, và có vật liệu/dụng cụ nào phải tránh?",
        })
    return questions[:5]


def _day_number(day_title: str) -> str:
    match = re.search(r"Day\s+(\d+[a-z]?)", day_title, re.IGNORECASE)
    return match.group(1) if match else day_title


def build_day_context(profile: dict[str, Any], state: dict[str, Any], day_title: str,
                      prompt: str, source_names: list[str] | None = None) -> str:
    """Build bounded, relevant state.  Do not send an entire multi-year roadmap."""
    feedback = state.get("learner_feedback", {})
    recent_items = list(feedback.items())[-5:]
    recent = [f"- Day {key}: {str(value)[:900]}" for key, value in recent_items if str(value).strip()]
    mastery = state.get("mastery", {})
    mastery_text = "; ".join(f"{key}={value}" for key, value in list(mastery.items())[-12:]) or "Chưa có dữ liệu"
    sources = ", ".join(source_names or []) or "Không có nguồn cục bộ"
    return f"""Bạn là gia sư thích nghi. Luôn trả lời bằng tiếng Việt.

HỒ SƠ KHÓA HỌC:
- Chủ đề: {profile.get('domain') or 'Chưa xác định'}
- Mục tiêu: {profile.get('goal') or 'Chưa xác định'}
- Trình độ: {profile.get('current_level') or 'Chưa xác định'}
- Thời lượng: {profile.get('minutes_per_day') or 30} phút/ngày
- Tài nguyên có sẵn: {profile.get('available_resources') or 'Chưa xác định'}
- Ràng buộc/an toàn: {profile.get('constraints') or 'Không có'}
- Cách học: {profile.get('learning_preference') or 'Thực hành'}

TRẠNG THÁI GẦN ĐÂY:
- Mức nắm vững: {mastery_text}
{chr(10).join(recent) if recent else '- Chưa có phản hồi Day trước.'}

DAY HIỆN TẠI: {day_title} (mã { _day_number(day_title) })
NGUỒN CÓ THỂ DÙNG: {sources}
YÊU CẦU ROADMAP:
{prompt}

NHIỆM VỤ:
1. Dạy đúng Day hiện tại, không lặp lại lý thuyết đã nắm vững.
2. Chỉ ôn lại phần liên quan trực tiếp từ trạng thái gần đây.
3. Nêu đầu ra thực hành có thể kiểm chứng.
4. Nếu cần thông tin làm thay đổi Day tiếp theo, đặt tối đa 2 câu hỏi ngắn trong clarifying_questions; nếu không để mảng rỗng.
5. Với DIY/trẻ em, không tuyên bố sản phẩm đạt chứng nhận an toàn và phải nêu giám sát/rủi ro thực tế.
6. Chỉ đề xuất visual_plan khi hình thật sự giúp người học làm đúng; ảnh không phải bằng chứng an toàn.
7. {instruction_for(str(profile.get('domain', '')))}
"""


def parse_lesson_response(raw: str) -> dict[str, Any] | None:
    try:
        value = json.loads(raw.strip())
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def validate_lesson(lesson: dict[str, Any]) -> list[str]:
    missing = []
    for key in LESSON_RESPONSE_SCHEMA["required"]:
        value = lesson.get(key)
        optional_empty_list = key in {"clarifying_questions", "source_usage", "factual_claims"}
        if (value is None or (isinstance(value, str) and not value.strip())
                or (isinstance(value, list) and not value and not optional_empty_list)):
            missing.append(key)
    if not isinstance(lesson.get("clarifying_questions", []), list) or len(lesson.get("clarifying_questions", [])) > 2:
        missing.append("clarifying_questions (tối đa 2)")
    visual = lesson.get("visual_plan")
    if not isinstance(visual, dict) or not isinstance(visual.get("needed"), bool):
        missing.append("visual_plan")
    return missing


def lesson_to_markdown(lesson: dict[str, Any]) -> str:
    base = str(lesson.get("lesson_markdown", "")).strip()
    extras = [
        "\n\n## Đầu ra cần nộp\n" + str(lesson.get("deliverable", "")),
        "\n\n## Checklist hoàn thành\n" + "\n".join(f"- [ ] {item}" for item in lesson.get("completion_check", [])),
    ]
    questions = lesson.get("clarifying_questions", [])
    if questions:
        extras.append("\n\n## Cần bạn xác nhận trước Day tiếp theo\n" + "\n".join(f"- {item}" for item in questions))
    visual = lesson.get("visual_plan", {})
    if isinstance(visual, dict) and visual.get("needed"):
        extras.append("\n\n> Hình minh họa nên có: " + str(visual.get("purpose", "")))
    assets = lesson.get("visual_assets", [])
    if isinstance(assets, list) and assets:
        extras.append("\n\n## Ảnh minh họa\n" + "\n".join(
            f"![Minh họa bước làm]({path})" for path in assets
        ))
    return base + "".join(extras)


def record_generated_lesson(state: dict[str, Any], day_title: str, lesson: dict[str, Any]) -> None:
    key = _day_number(day_title)
    state.setdefault("generated_days", {})[key] = {
        "title": day_title,
        "deliverable": lesson.get("deliverable", ""),
        "completion_check": lesson.get("completion_check", []),
        "generated_at": _now(),
    }
    state["open_questions"] = lesson.get("clarifying_questions", [])


def record_learner_feedback(out_dir: str, day: str, feedback: str, mastery: str = "") -> dict[str, Any]:
    state = load_state(out_dir)
    key = _day_number(day)
    state["learner_feedback"][key] = feedback.strip()
    if mastery.strip():
        state["mastery"][key] = mastery.strip()
    save_state(out_dir, state)
    return state
