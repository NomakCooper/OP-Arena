# OP-Arena

![Static Badge](https://img.shields.io/badge/TCG-red?logo=bandai&label=ONE%20PIECE) ![Static Badge](https://img.shields.io/badge/Arena-red?label=TCG)

Automation repository for building [**One Piece Card Game**](https://en.onepiece-cardgame.com/) data files for [**TCG Arena**](https://tcg-arena.fr/).

![OP-Banner](https://files.catbox.moe/kqvbme.png)

## What this repository generates

The GitHub Action builds and publishes the following files:

- `cards.json`: one merged English card list sourced from [Vegapull](https://github.com/Coko7/vegapull)
- `game.json`: One Piece game definition (rules summary, mechanics, and playmat layout metadata) that references `cards.json`
- `build-info.json`: generation metadata

Published files are pushed to the `gh-pages` branch and available through GitHub Pages.
