"""Verified Knowledge Pack helpers.

Facts shown as game data must come from this pack, never from a model's memory.
The module is deliberately domain-neutral so it also protects DIY, Python, and
other courses that need cited facts.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from typing import Any


PACK_FILE = "knowledge_pack.json"
ENTITY_TYPES = ("heroes", "units", "items", "secrets", "builds")
VERIFIED = "verified"


def empty_pack(title: str = "") -> dict[str, Any]:
    return {
        "version": 1,
        "title": title,
        "subject": "",
        "game_version": "",
        "sources": [],
        "entities": {kind: [] for kind in ENTITY_TYPES},
        # Target counts are intentionally user/source supplied.  Guessing the
        # total number of heroes in a mod would defeat the purpose of a pack.
        "coverage_targets": {},
    }


def load_pack(path: str | None) -> dict[str, Any]:
    if not path or not os.path.isfile(path):
        return empty_pack()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return empty_pack()
    result = empty_pack()
    if isinstance(value, dict):
        result.update(value)
    if not isinstance(result.get("sources"), list):
        result["sources"] = []
    if not isinstance(result.get("entities"), dict):
        result["entities"] = {}
    for kind in ENTITY_TYPES:
        if not isinstance(result["entities"].get(kind), list):
            result["entities"][kind] = []
    if not isinstance(result.get("coverage_targets"), dict):
        result["coverage_targets"] = {}
    return result


def pack_path_for_course(out_dir: str, profile: dict[str, Any]) -> str:
    configured = str(profile.get("knowledge_pack_path", "")).strip()
    if configured:
        return configured
    return os.path.join(out_dir, PACK_FILE)


def _entity_rows(pack: dict[str, Any]):
    for kind in ENTITY_TYPES:
        for entity in pack.get("entities", {}).get(kind, []):
            if isinstance(entity, dict):
                yield kind, entity


def validate_pack(pack: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source_ids = set()
    for source in pack.get("sources", []):
        source_id = str(source.get("id", "")).strip() if isinstance(source, dict) else ""
        if not source_id:
            errors.append("Nguồn thiếu id")
        elif source_id in source_ids:
            errors.append(f"Trùng source id: {source_id}")
        else:
            source_ids.add(source_id)
    entity_ids = set()
    for kind, entity in _entity_rows(pack):
        entity_id = str(entity.get("id", "")).strip()
        if not entity_id:
            errors.append(f"{kind} có dòng thiếu id")
            continue
        if entity_id in entity_ids:
            errors.append(f"Trùng entity id: {entity_id}")
        entity_ids.add(entity_id)
        refs = entity.get("source_ids", [])
        if entity.get("verification_status") == VERIFIED and not refs:
            errors.append(f"{entity_id} được đánh dấu verified nhưng không có source_ids")
        if not isinstance(refs, list) or any(ref not in source_ids for ref in refs):
            errors.append(f"{entity_id} tham chiếu source không tồn tại")
    return errors


def verified_entities(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(entity["id"]): dict(entity, entity_type=kind)
        for kind, entity in _entity_rows(pack)
        if entity.get("verification_status") == VERIFIED and str(entity.get("id", "")).strip()
    }


def coverage_report(pack: dict[str, Any], prompt: str = "") -> dict[str, Any]:
    verified = Counter(entity["entity_type"] for entity in verified_entities(pack).values())
    targets = pack.get("coverage_targets", {})
    requested_all = bool(re.search(r"\b(toàn bộ|tất cả|all)\b", prompt or "", re.I))
    rows = []
    complete = True
    for kind in ENTITY_TYPES:
        target = targets.get(kind)
        count = verified.get(kind, 0)
        if target is None:
            if requested_all and kind in _requested_types(prompt):
                complete = False
            rows.append({"type": kind, "verified": count, "target": None, "complete": False})
        else:
            ok = count >= int(target)
            complete = complete and ok
            rows.append({"type": kind, "verified": count, "target": int(target), "complete": ok})
    return {"requested_all": requested_all, "complete": complete if requested_all else True, "rows": rows}


def _requested_types(text: str) -> set[str]:
    value = (text or "").casefold()
    requested = set()
    terms = {
        "heroes": ("tướng", "hero", "general"),
        "units": ("lính", "binh chủng", "unit"),
        "items": ("trang bị", "vật phẩm", "item"),
        "secrets": ("bí mật", "ẩn", "secret"),
        "builds": ("train", "build", "ghép tướng", "kết hợp"),
    }
    for kind, words in terms.items():
        if any(word in value for word in words):
            requested.add(kind)
    return requested or set(ENTITY_TYPES)


def build_fact_context(pack: dict[str, Any], prompt: str, limit: int = 80) -> tuple[str, dict[str, Any]]:
    report = coverage_report(pack, prompt)
    entities = verified_entities(pack)
    wanted = _requested_types(prompt)
    selected = [row for row in entities.values() if row.get("entity_type") in wanted][:limit]
    sources = {str(row.get("id")): row for row in pack.get("sources", []) if isinstance(row, dict)}
    compact = []
    for entity in selected:
        compact.append({key: value for key, value in entity.items() if key not in {"verification_status", "entity_type"}})
    source_summary = [{"id": sid, "title": src.get("title", ""), "url": src.get("url", ""),
                       "language": src.get("language", ""), "game_version": src.get("game_version", "")}
                      for sid, src in sources.items()]
    payload = {"game_version": pack.get("game_version", ""), "entities": compact, "sources": source_summary,
               "coverage": report}
    policy = (
        "KNOWLEDGE-PACK POLICY: Only the JSON records below are verified facts. Do not invent names, stats, "
        "locations, versions, mods, files, skills, or sources. Put factual references only in factual_claims using "
        "an entity_id and its existing source_ids. If coverage.complete is false, state that a complete catalogue is "
        "not available and teach the verification workflow instead.\n"
    )
    return policy + json.dumps(payload, ensure_ascii=False), report


def validate_fact_claims(lesson: dict[str, Any], pack: dict[str, Any]) -> list[str]:
    claims = lesson.get("factual_claims", [])
    if not isinstance(claims, list):
        return ["factual_claims không phải mảng"]
    entities = verified_entities(pack)
    source_ids = {str(src.get("id")) for src in pack.get("sources", []) if isinstance(src, dict)}
    errors = []
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("factual_claims có phần tử không hợp lệ")
            continue
        entity = entities.get(str(claim.get("entity_id", "")))
        refs = claim.get("source_ids", [])
        if not entity:
            errors.append(f"claim dùng entity không verified: {claim.get('entity_id', '')}")
        elif not isinstance(refs, list) or not refs or any(ref not in source_ids for ref in refs):
            errors.append(f"claim {claim.get('entity_id', '')} thiếu source hợp lệ")
        elif any(ref not in entity.get("source_ids", []) for ref in refs):
            errors.append(f"claim {claim.get('entity_id', '')} không dùng đúng source của entity")
    return errors


def evidence_for_claims(lesson: dict[str, Any], pack: dict[str, Any]) -> list[dict[str, Any]]:
    entities = verified_entities(pack)
    sources = {str(row.get("id")): row for row in pack.get("sources", []) if isinstance(row, dict)}
    result = []
    for claim in lesson.get("factual_claims", []):
        if not isinstance(claim, dict) or str(claim.get("entity_id", "")) not in entities:
            continue
        result.append({"entity": entities[str(claim["entity_id"])], "claim": str(claim.get("claim", "")),
                       "sources": [sources[sid] for sid in claim.get("source_ids", []) if sid in sources]})
    return result
