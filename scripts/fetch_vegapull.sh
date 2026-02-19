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
./target/release/vega pull all
popd >/dev/null

echo "Vegapull cloned and data pulled into $OUT_DIR"
