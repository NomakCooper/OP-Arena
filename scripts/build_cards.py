#!/usr/bin/env python3
"""Merge Vegapull JSON card sources into a single English cards.json file."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vegapull-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def iter_json_files(root: Path):
    for path in root.rglob("*.json"):
        relative_parts = path.relative_to(root).parts
        if any(part.startswith(".") for part in relative_parts):
            continue
        yield path


def extract_cards(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("cards", "data", "results", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    if all(k in payload for k in ("id", "name")):
        return [payload]

    return []


def is_probably_english(card: dict[str, Any], file_path: Path) -> bool:
    langs = [
        card.get("language"),
        card.get("lang"),
        card.get("locale"),
    ]
    lang_value = " ".join(str(v).lower() for v in langs if v)
    if lang_value:
        if "en" in lang_value or "english" in lang_value:
            return True
        if any(x in lang_value for x in ("jp", "ja", "fr", "it", "de", "es")):
            return False

    path_lower = str(file_path).lower()
    if "english" in path_lower:
        return True
    if "/en/" in path_lower or "_en" in path_lower or "-en" in path_lower:
        return True

    return True


def card_identifier(card: dict[str, Any]) -> str:
    for key in ("id", "code", "card_id", "number", "cardNumber"):
        value = card.get(key)
        if value:
            return str(value)
    return ""


def _first_non_empty(card: dict[str, Any], keys: tuple[str, ...], default: Any = "") -> Any:
    for key in keys:
        value = card.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        if "/" in value:
            chunks = value.split("/")
        elif "," in value:
            chunks = value.split(",")
        else:
            chunks = [value]
        return [chunk.strip() for chunk in chunks if chunk.strip()]
    return []


def _as_int_or_none(value: Any) -> int | None:
    if value in (None, "", "-"):
        return None
    try:
        return int(str(value).replace("+", "").strip())
    except (TypeError, ValueError):
        return None


def _extract_image_url(card: dict[str, Any]) -> str:
    direct = _first_non_empty(card, ("image", "image_url", "img", "thumbnail", "img_full_url", "img_url"), "")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    nested_candidates = (
        card.get("images"),
        card.get("imageUrls"),
        card.get("image_urls"),
        card.get("art"),
    )
    preferred_nested_keys = (
        "large",
        "full",
        "high",
        "highres",
        "default",
        "normal",
        "medium",
        "small",
        "thumb",
    )

    for candidate in nested_candidates:
        if not isinstance(candidate, dict):
            continue

        for key in preferred_nested_keys:
            value = candidate.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for value in candidate.values():
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def _normalize_category(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    normalized = text.lower().replace("_", " ").replace("-", " ")
    mapping = {
        "leader": "Leader",
        "character": "Character",
        "event": "Event",
        "stage": "Stage",
        "don": "DON!!",
        "don!!": "DON!!",
    }

    return mapping.get(normalized, text)


def _coerce_int(value: Any, fallback: int = 0) -> int:
    parsed = _as_int_or_none(value)
    if parsed is not None:
        return parsed
    return fallback


def _coerce_text_number(value: Any) -> str:
    if value in (None,):
        return ""
    text = str(value).strip()
    if text in ("-", "None"):
        return ""
    return text


def _normalize_type_for_tcg_arena(category: str, card_type: str) -> str | bool:
    if category.lower() == "leader":
        return False
    return card_type


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_card(card: dict[str, Any], card_back_image: str) -> dict[str, Any]:
    card_id = str(_first_non_empty(card, ("id", "code", "card_id", "number", "cardNumber"), "")).strip()
    name = _normalize_name(str(_first_non_empty(card, ("name", "card_name", "name_en"), "")).strip())
    category = _normalize_category(_first_non_empty(card, ("category", "card_type", "type_en", "kind"), ""))
    card_type = str(_first_non_empty(card, ("type",), category)).strip()
    colors = _as_list(_first_non_empty(card, ("colors", "color"), []))
    attributes = _as_list(_first_non_empty(card, ("attributes", "attribute"), []))
    types = _as_list(_first_non_empty(card, ("types", "trait"), []))
    effect = str(_first_non_empty(card, ("effect", "text", "description"), "")).strip()
    cost_text = _coerce_text_number(_first_non_empty(card, ("cost",), ""))
    cost_int = _coerce_int(_first_non_empty(card, ("cost",), 0), fallback=0)

    normalized_type = _normalize_type_for_tcg_arena(category, card_type)
    front_image = _extract_image_url(card)

    return {
        "id": card_id,
        "isToken": False,
        "face": {
            "front": {
                "name": name,
                "type": normalized_type,
                "cost": cost_int,
                "image": front_image,
                "isHorizontal": False,
            },
            "back": {
                "name": name,
                "type": "" if normalized_type is False else normalized_type,
                "cost": cost_int,
                "image": card_back_image,
                "isHorizontal": False,
            },
        },
        "name": name,
        "type": normalized_type,
        "cost": cost_text,
        "rarity": str(_first_non_empty(card, ("rarity",), "")).strip(),
        "category": category,
        "attributes": attributes,
        "power": _coerce_text_number(_first_non_empty(card, ("power",), "")),
        "colors": colors,
        "block_number": str(_first_non_empty(card, ("block_number", "blockNumber", "block"), "")).strip(),
        "types": types,
        "effect": effect,
    }


def main() -> None:
    args = parse_args()
    vegapull_dir: Path = args.vegapull_dir
    output: Path = args.output

    if not vegapull_dir.exists():
        raise SystemExit(f"Vegapull directory not found: {vegapull_dir}")

    merged: dict[str, dict[str, Any]] = {}
    fallback_cards: list[dict[str, Any]] = []

    for json_file in iter_json_files(vegapull_dir):
        try:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        for card in extract_cards(payload):
            if not is_probably_english(card, json_file):
                continue

            normalized = dict(card)
            normalized.setdefault("_source_file", str(json_file.relative_to(vegapull_dir)))

            identifier = card_identifier(normalized)
            if identifier:
                if identifier in merged:
                    merged[identifier].update({k: v for k, v in normalized.items() if v not in (None, "", [], {})})
                else:
                    merged[identifier] = normalized
            else:
                fallback_cards.append(normalized)

    card_back_image = "https://cf.geekdo-images.com/cpyej29PfijgBDtiOuSFsQ__imagepage/img/aDMUMr-kD-RtLyOR2sKmzXtaXtk=/fit-in/900x600/filters:no_upscale():strip_icc()/pic6974116.jpg"
    cards = [normalize_card(card, card_back_image) for card in (list(merged.values()) + fallback_cards)]
    cards.sort(key=lambda c: (str(c.get("id") or ""), str(c.get("name") or "")))

    cards_by_id: dict[str, dict[str, Any]] = {}
    for card in cards:
        card_id = str(card.get("id") or "").strip()
        if card_id:
            cards_by_id[card_id] = card

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(cards_by_id, indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    print(f"Merged {len(cards_by_id)} cards into {output}")


if __name__ == "__main__":
    main()
