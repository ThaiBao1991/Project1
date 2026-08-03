"""Optional Gemini native-image asset generation for lessons that request it."""

from __future__ import annotations

import base64
import os
import re
from typing import Any

import requests


def _safe_part(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_") or "day"


def generate_visual_assets(api_key: str, model: str, prompts: list[str], output_dir: str,
                           day_id: str, timeout: int = 180) -> list[str]:
    """Generate up to three opted-in visuals and return paths relative to output_dir.

    A failure leaves the lesson intact: generated visuals are enhancement assets,
    never a condition for declaring a physical project safe or complete.
    """
    if not api_key or not prompts:
        return []
    asset_dir = os.path.join(output_dir, "assets", _safe_part(day_id))
    os.makedirs(asset_dir, exist_ok=True)
    output: list[str] = []
    for index, prompt in enumerate(prompts[:3], start=1):
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        parts = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data") or {}
            encoded = inline.get("data")
            if not encoded:
                continue
            mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
            extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(mime, "png")
            filename = f"visual_{index:02d}.{extension}"
            target = os.path.join(asset_dir, filename)
            with open(target, "wb") as handle:
                handle.write(base64.b64decode(encoded))
            output.append(os.path.relpath(target, output_dir).replace("\\", "/"))
            break
    return output
