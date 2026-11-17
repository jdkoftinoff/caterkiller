#!/bin/bash
# Build everything and launch Caterkiller 2026 in the terminal frontend.
set -e
cd "$(dirname "$0")"
make caterkiller2026 tui
exec ./frontends/tui/target/release/caterkiller-tui build/caterkiller/caterkiller2026.bin --load=0x6000 --start=0x7200
