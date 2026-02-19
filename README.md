# OP-Arena

Automation repository for building **One Piece Card Game** data files for **TCG Arena custom game**.

## What this repository generates

The GitHub Action builds and publishes:

- `cards.json`: one merged English card list sourced from [Vegapull](https://github.com/Coko7/vegapull)
- `game.json`: One Piece game definition (rules summary, mechanics, and playmat layout metadata) that references `cards.json`
- `build-info.json`: generation metadata

Published files are pushed to the `gh-pages` branch and available through GitHub Pages.

## Workflow

Workflow file: `.github/workflows/build-data.yml`

It runs on:

- manual trigger (`workflow_dispatch`)
- daily schedule
- pushes to `main`

Pipeline steps:

1. Clone Vegapull in the action workspace.
2. Merge all discovered Vegapull card JSON sources into one English `dist/cards.json`.
3. Generate `dist/game.json` linked to the expected GitHub Pages `cards.json` URL.
4. Publish `dist/` to `gh-pages`.

## Local scripts

- `scripts/fetch_vegapull.sh`: clones Vegapull, builds `vega` with Cargo, and runs `vega pull all` to fetch the complete card dataset
- `scripts/build_cards.py`: merges card files into one `cards.json`
- `scripts/build_game.py`: builds `game.json` from the merged card set

## Local run (optional)

```bash
# Requires Rust/Cargo to build vegapull's vega CLI
./scripts/fetch_vegapull.sh .cache/vegapull
python scripts/build_cards.py --vegapull-dir .cache/vegapull --output dist/cards.json
python scripts/build_game.py --cards dist/cards.json --cards-url "https://<owner>.github.io/<repo>/cards.json" --output dist/game.json
```

## Important note about TCG Arena schema

TCG Arena custom game schema can evolve. This repo outputs a practical baseline structure and may need field-level adjustments to fully match the latest TCG Arena JSON expectations.
