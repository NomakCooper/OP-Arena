#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-.cache/vegapull}"

rm -rf "$OUT_DIR"
git clone --depth 1 https://github.com/Coko7/vegapull.git "$OUT_DIR"

if ! command -v cargo >/dev/null 2>&1; then
  echo "cargo is required to build vegapull. Please install Rust/Cargo and retry."
  exit 1
fi

pushd "$OUT_DIR" >/dev/null
cargo build --release

# `vega pull all` is interactive: it asks for language and confirmation.
# In CI we provide deterministic answers over stdin and, when possible, run
# under `script` so `vega` still sees a TTY-capable terminal.
VEGA_PULL_CMD="./target/release/vega pull all"
VEGA_PULL_INPUT=$'english-asia\ny\n'

if command -v script >/dev/null 2>&1; then
  printf '%s' "$VEGA_PULL_INPUT" | script -q -e -c "$VEGA_PULL_CMD" /dev/null
else
  printf '%s' "$VEGA_PULL_INPUT" | $VEGA_PULL_CMD
fi
popd >/dev/null

echo "Vegapull cloned and data pulled into $OUT_DIR"
