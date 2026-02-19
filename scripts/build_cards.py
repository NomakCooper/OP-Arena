#!/usr/bin/env python3
"""Merge Vegapull JSON card sources into a single English cards.json file."""

from __future__ import annotations

import argparse
import json
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


def normalize_card(card: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(card)

    card_id = str(_first_non_empty(card, ("id", "code", "card_id", "number", "cardNumber"), "")).strip()
    number = str(_first_non_empty(card, ("number", "cardNumber", "id", "code"), "")).strip()
    category = str(_first_non_empty(card, ("category", "card_type", "type_en", "kind"), "")).strip()
    colors = _as_list(_first_non_empty(card, ("colors", "color"), []))
    attributes = _as_list(_first_non_empty(card, ("attributes", "attribute"), []))
    types = _as_list(_first_non_empty(card, ("types", "type", "trait"), []))

    normalized.update(
        {
            "id": card_id,
            "number": number,
            "name": str(_first_non_empty(card, ("name", "card_name", "name_en"), "")).strip(),
            "category": category,
            "colors": colors,
            "cost": _as_int_or_none(_first_non_empty(card, ("cost",), None)),
            "power": _as_int_or_none(_first_non_empty(card, ("power",), None)),
            "counter": _as_int_or_none(_first_non_empty(card, ("counter",), None)),
            "life": _as_int_or_none(_first_non_empty(card, ("life",), None)),
            "attributes": attributes,
            "types": types,
            "type": str(_first_non_empty(card, ("type", "types", "trait"), "")).strip(),
            "rarity": str(_first_non_empty(card, ("rarity",), "")).strip(),
            "block_number": str(_first_non_empty(card, ("block_number", "blockNumber", "block"), "")).strip(),
            "set": str(_first_non_empty(card, ("set", "set_name", "setName"), "")).strip(),
            "image": str(_first_non_empty(card, ("image", "image_url", "img", "thumbnail"), "")).strip(),
            "text": str(_first_non_empty(card, ("text", "effect", "description"), "")).strip(),
        }
    )

    return normalized


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

    cards = [normalize_card(card) for card in (list(merged.values()) + fallback_cards)]
    cards.sort(key=lambda c: (str(c.get("id") or c.get("code") or ""), str(c.get("name") or "")))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "game": "one-piece-card-game",
                "language": "en",
                "generatedBy": "scripts/build_cards.py",
                "count": len(cards),
                "cards": cards,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Merged {len(cards)} cards into {output}")


if __name__ == "__main__":
    main()
