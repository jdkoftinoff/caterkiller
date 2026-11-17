#! /bin/sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/../../../tools/fmt6502.py" -e 24 -i "$SCRIPT_DIR/caterkiller2026.s"
