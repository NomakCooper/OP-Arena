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

# `vega pull all` currently expects a TTY-capable stdin even in CI contexts.
# GitHub Actions runs commands without an attached TTY, so we wrap it with
# `script` to provide a pseudo-terminal and avoid: "The input device is not a TTY".
if command -v script >/dev/null 2>&1; then
  script -q -e -c "./target/release/vega pull all" /dev/null
else
  ./target/release/vega pull all
fi
popd >/dev/null

echo "Vegapull cloned and data pulled into $OUT_DIR"
