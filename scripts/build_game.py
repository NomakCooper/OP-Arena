#!/usr/bin/env python3
"""Build a TCG Arena-oriented game.json for One Piece TCG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", required=True, type=Path)
    parser.add_argument("--cards-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cards_payload = json.loads(args.cards.read_text(encoding="utf-8"))
    cards = cards_payload.get("cards", []) if isinstance(cards_payload, dict) else []

    set_codes = sorted(
        {
            str(card.get("set") or card.get("set_code") or card.get("setCode"))
            for card in cards
            if card.get("set") or card.get("set_code") or card.get("setCode")
        }
    )

    game = {
        "id": "one-piece-card-game",
        "name": "One Piece Card Game",
        "version": "0.1.0",
        "format": "tcg-arena-custom-game",
        "cardsFile": args.cards_url,
        "metadata": {
            "language": "en",
            "cardsCount": len(cards),
            "setCodes": set_codes,
        },
        "rules": {
            "summary": "Leader-based battle game using DON!! to play characters/events/stages and reduce opponent Life to 0.",
            "winCondition": "Deal damage to opponent while they are at 0 Life.",
            "zones": [
                "deck",
                "hand",
                "life",
                "leader",
                "character_area",
                "stage_area",
                "trash",
                "don_deck",
                "don_area",
            ],
            "turnStructure": [
                "Refresh",
                "Draw",
                "DON!! phase",
                "Main phase",
                "Battle phase",
                "End phase",
            ],
            "mechanics": [
                "DON!! attachment",
                "Rush",
                "Blocker",
                "Banish",
                "Double Attack",
                "Counter",
                "Trigger",
            ],
        },
        "playmat": {
            "layout": "one_piece_default",
            "zones": {
                "leader": {"x": 0.50, "y": 0.78, "w": 0.11, "h": 0.18},
                "character_area": {"x": 0.50, "y": 0.60, "w": 0.70, "h": 0.20},
                "stage_area": {"x": 0.18, "y": 0.63, "w": 0.11, "h": 0.16},
                "life": {"x": 0.84, "y": 0.78, "w": 0.12, "h": 0.18},
                "deck": {"x": 0.09, "y": 0.80, "w": 0.10, "h": 0.16},
                "trash": {"x": 0.21, "y": 0.80, "w": 0.10, "h": 0.16},
                "don_deck": {"x": 0.09, "y": 0.60, "w": 0.10, "h": 0.16},
                "don_area": {"x": 0.30, "y": 0.80, "w": 0.28, "h": 0.16},
                "hand": {"x": 0.50, "y": 0.94, "w": 0.80, "h": 0.10},
            },
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(game, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated {args.output} using {len(cards)} cards")


if __name__ == "__main__":
    main()
