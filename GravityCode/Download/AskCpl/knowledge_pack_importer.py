"""Import a human-reviewed CSV folder into a Knowledge Pack JSON file."""

from __future__ import annotations

import csv
import json
import os
from typing import Any

from verified_knowledge import ENTITY_TYPES, empty_pack, validate_pack


def _list(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def import_csv_folder(folder: str, output_path: str, title: str = "") -> dict[str, Any]:
    """Import sources.csv and optional heroes/units/items/secrets/builds.csv.

    Each entity CSV needs id,name,source_ids,verification_status. Additional
    columns are preserved, so game-specific fields (stats, skill, location)
    do not require a new app release.
    """
    pack = empty_pack(title)
    for file_name, destination in (("sources.csv", "sources"),):
        path = os.path.join(folder, file_name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                row = {key: value.strip() if isinstance(value, str) else value for key, value in row.items()}
                pack[destination].append(row)
    for kind in ENTITY_TYPES:
        path = os.path.join(folder, f"{kind}.csv")
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                item = {key: value.strip() if isinstance(value, str) else value for key, value in row.items()}
                item["source_ids"] = _list(str(item.get("source_ids", "")))
                pack["entities"][kind].append(item)
    errors = validate_pack(pack)
    if errors:
        raise ValueError("Knowledge Pack không hợp lệ: " + "; ".join(errors))
    with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(pack, handle, ensure_ascii=False, indent=2)
    return pack
