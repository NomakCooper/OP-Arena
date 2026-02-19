#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-.cache/vegapull}"

rm -rf "$OUT_DIR"
git clone --depth 1 https://github.com/Coko7/vegapull.git "$OUT_DIR"

echo "Vegapull cloned into $OUT_DIR"
