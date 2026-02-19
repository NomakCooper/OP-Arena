#!/usr/bin/env python3
"""Build a TCG Arena-compatible game.json for One Piece Card Game."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", required=True, type=Path)
    parser.add_argument("--cards-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def load_cards(cards_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(cards_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        cards = payload.get("cards", [])
        if isinstance(cards, list):
            return [card for card in cards if isinstance(card, dict)]
    return []


def _normalize_to_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str):
        return [value] if value else []
    return []


def collect_game_metadata(cards: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str], int, int]:
    colors = sorted(
        {
            color
            for card in cards
            for color in _normalize_to_list(card.get("colors") or card.get("color"))
            if color
        }
    )

    categories = sorted(
        {
            str(card.get("category") or card.get("type") or "")
            for card in cards
            if card.get("category") or card.get("type")
        }
    )

    rarities = sorted({str(card.get("rarity")) for card in cards if card.get("rarity")})

    leaders = sum(1 for card in cards if str(card.get("category", "")).lower() == "leader")
    non_leaders = max(0, len(cards) - leaders)

    return colors, categories, rarities, leaders, non_leaders


def _layout_column(content: list[Any]) -> dict[str, Any]:
    return {"direction": "column", "content": content, "noQuickActions": False}


def _layout_row(content: list[Any], *, symmetrical_for_opponents: bool | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"direction": "row", "content": content, "noQuickActions": False}
    if symmetrical_for_opponents is not None:
        payload["isSymetricalForOpponents"] = symmetrical_for_opponents
    return payload


def main() -> None:
    args = parse_args()
    cards = load_cards(args.cards)

    colors, categories, rarities, leaders, non_leaders = collect_game_metadata(cards)

    game = {
        "name": "One Piece Card Game",
        "menuBackgroundImage": "https://files.catbox.moe/kqvbme.png",
        "defaultRessources": {
            "backgrounds": ["https://files.catbox.moe/kqvbme.png"],
            "decksUrl": "",
        },
        "customHelp": (
            "Victory: defeat opponent by dealing damage to their Leader when they have 0 Life, "
            "or when their deck reaches 0 cards. Setup: 1 Leader, 50-card deck "
            "(Characters/Events/Stages), 10-card DON!! deck. Opening hand 5; mulligan once. "
            "Turn: Refresh (set rested to active; return given DON!! to cost rested), Draw "
            "(skip for first player on first turn), DON!! phase (+1 for first player T1, "
            "otherwise +2), Main, End."
        ),
        "cardRotation": 90,
        "cards": {
            "dataUrl": args.cards_url,
            "cardBack": "https://cf.geekdo-images.com/cpyej29PfijgBDtiOuSFsQ__imagepage/img/aDMUMr-kD-RtLyOR2sKmzXtaXtk=/fit-in/900x600/filters:no_upscale():strip_icc()/pic6974116.jpg",
        },
        "deckBuilding": {
            "mainFilters": [
                "color",
                "category",
                "cost",
                "power",
                "attribute",
                "type",
                "rarity",
                "block",
            ],
            "formats": ["Classic"],
            "filtersDict": {
                "color": {"label": "Color", "field": "colors", "type": "multi", "isDictionary": False},
                "category": {"label": "Category", "field": "category", "type": "multi", "isDictionary": False},
                "cost": {"label": "Cost", "field": "cost", "type": "range", "isDictionary": False},
                "power": {"label": "Power", "field": "power", "type": "range", "isDictionary": False},
                "attribute": {"label": "Attribute", "field": "attributes", "type": "multi", "isDictionary": False},
                "type": {"label": "Type", "field": "types", "type": "multi", "isDictionary": False},
                "rarity": {"label": "Rarity", "field": "rarity", "type": "multi", "isDictionary": False},
                "block": {"label": "Block", "field": "block_number", "type": "multi", "isDictionary": False},
            },
            "formatsDict": {
                "Classic": {
                    "name": "Classic",
                    "rules": {
                        "leader": {"min": 1, "max": 1, "category": "Leader"},
                        "mainDeck": {
                            "size": 50,
                            "allowedCategories": ["Character", "Event", "Stage"],
                            "maxSameCardNumber": 4,
                            "colorsMustBeSubsetOfLeader": True,
                        },
                        "donDeck": {"size": 10, "name": "DON!! Deck"},
                    },
                }
            },
        },
        "gameplay": {
            "Classic": {
                "mulligan": {
                    "info": "Each player draws 5. Starting with the first player, each may return all cards, shuffle, and redraw 5 once.",
                    "startingHandSize": 5,
                    "drawNewHand": True,
                    "putSelectionAtBottom": False,
                    "drawNewSelectedCards": False,
                },
                "newTurn": {
                    "drawOnStart": True,
                    "sharedTurn": False,
                    "firstPlayerTokenName": "First Player",
                    "drawPerTurn": 1,
                    "firstPlayerSkipsDrawFirstTurn": True,
                },
                "defaultNotes": "Characters cannot attack the turn they are played. You can have max 5 Characters and max 1 Stage on the field. You can attack Leader or a rested Character.",
                "tokens": [{"name": "First Player", "count": 1}, {"name": "DON!!", "count": 10}],
                "countersStartingValues": [0],
                "hideFacedDownCards": False,
                "sections": {
                    "customSections": ["Life", "Deck", "Trash", "Leader", "Stage", "Characters", "Cost", "DonDeck"],
                    "layout": _layout_row(
                        [
                            _layout_column(["Life", "DonDeck"]),
                            _layout_column(["Characters", _layout_row(["Leader", "Stage", "Deck"]), "Cost"]),
                            _layout_column(["Trash"]),
                        ],
                        symmetrical_for_opponents=True,
                    ),
                    "categoriesAlreadyOnBoard": [],
                    "autoPlayFromHand": {"Character": "Characters", "Stage": "Stage"},
                    "autoPlayFromStack": {},
                    "sectionsDict": {
                        "Life": {"title": "Life", "isHidden": "yes", "height": "MEDIUM", "alignment": "START", "opponentAlignment": False, "isHorizontalAllowed": False, "displayedTitle": "Life", "enterTapped": False, "enterSpun": False, "isGroupForbidden": False, "keepTappedNewTurn": True, "showHiddenCardInHistory": False, "noQuickActions": False},
                        "Deck": {"title": "Deck", "isHidden": "yes", "height": "SMALL", "alignment": "START", "opponentAlignment": False, "isHorizontalAllowed": False, "displayedTitle": "Deck", "enterTapped": False, "enterSpun": False, "isGroupForbidden": True, "keepTappedNewTurn": True, "showHiddenCardInHistory": False, "noQuickActions": False},
                        "Trash": {"title": "Trash", "isHidden": "no", "height": "SMALL", "alignment": "START", "opponentAlignment": False, "isHorizontalAllowed": True, "displayedTitle": "Trash", "enterTapped": False, "enterSpun": False, "isGroupForbidden": False, "keepTappedNewTurn": True, "showHiddenCardInHistory": True, "noQuickActions": False},
                        "Leader": {"title": "Leader", "isHidden": "no", "height": "SMALL", "alignment": "CENTER", "opponentAlignment": False, "isHorizontalAllowed": True, "displayedTitle": "Leader", "enterTapped": False, "enterSpun": False, "isGroupForbidden": True, "keepTappedNewTurn": False, "showHiddenCardInHistory": True, "noQuickActions": False},
                        "Stage": {"title": "Stage", "isHidden": "no", "height": "SMALL", "alignment": "CENTER", "opponentAlignment": False, "isHorizontalAllowed": True, "displayedTitle": "Stage", "enterTapped": False, "enterSpun": False, "isGroupForbidden": True, "keepTappedNewTurn": False, "showHiddenCardInHistory": True, "noQuickActions": False},
                        "Characters": {"title": "Character Area", "isHidden": "no", "height": "LARGE", "alignment": "START", "opponentAlignment": False, "isHorizontalAllowed": True, "displayedTitle": "Character Area (max 5)", "enterTapped": False, "enterSpun": False, "isGroupForbidden": False, "keepTappedNewTurn": False, "showHiddenCardInHistory": True, "noQuickActions": False, "maxCards": 5},
                        "Cost": {"title": "Cost Area", "isHidden": "no", "height": "MEDIUM", "alignment": "START", "opponentAlignment": False, "noAutoPayTo": "true", "isHorizontalAllowed": True, "displayedTitle": "Cost (DON!!)", "enterTapped": False, "enterSpun": False, "isGroupForbidden": False, "keepTappedNewTurn": False, "showHiddenCardInHistory": True, "noQuickActions": False},
                        "DonDeck": {"title": "DON!! Deck", "isHidden": "no", "height": "SMALL", "alignment": "START", "opponentAlignment": False, "isHorizontalAllowed": False, "displayedTitle": "DON!! Deck (open)", "enterTapped": False, "enterSpun": False, "isGroupForbidden": True, "keepTappedNewTurn": True, "showHiddenCardInHistory": True, "noQuickActions": False},
                    },
                },
            }
        },
        "metadata": {
            "generatedBy": "scripts/build_game.py",
            "cardsCount": len(cards),
            "leadersCount": leaders,
            "mainDeckPoolCount": non_leaders,
            "detectedColors": colors,
            "detectedCategories": categories,
            "detectedRarities": rarities,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(game, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated {args.output} using {len(cards)} cards")


if __name__ == "__main__":
    main()
