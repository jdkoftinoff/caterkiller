# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Reverse engineering of Caterkiller / Cater Killer / SNOOKUMS (1984) by Jeff Koftinoff, published through A.P.P.L.E. (Apple Pugetsound Program Library Exchange). An Apple II game with 3 levels and two distinct game engines, recovered from the author's DOS 3.3 disk. The disk image, the publisher's greeting program and the instruction text are deliberately not in the repository (Apple's DOS 3.3 and A.P.P.L.E.'s copyright); the game's own binaries are. The string "SYDNEY DEVELOPMENT CORPORATION PRESENTS" in the original title data is a leftover from a 1984 pitch to that company and was never displayed; do not describe the game as theirs. The annotated source in `games/caterkiller/source/` rebuilds those binaries byte for byte. `games/caterkiller/caterkiller2026/` is a new version of the game under active development. Only MIT or BSD licensed third-party material may be added or referenced, and nothing copyleft, not even as downloaded test data.

## Running the Tools

Python 3.6+ required. No external dependencies (standard library only). Tools are in `tools/`.

```bash
# List files on a DOS 3.3 disk image
python3 tools/extract_dos33.py disk.dsk

# Disassemble a binary (writes to stdout; load address defaults to 0x0800)
python3 tools/disasm6502.py input.bin 0x6000 > output.asm

# Assemble source to binary
python3 tools/asm6502.py input.s output.bin

# Format assembly source
python3 tools/fmt6502.py -e 24 -i source.s
```

## Building

```bash
make verify         # Assemble level1/2/3 and compare against the originals (all must MATCH)
make test           # verify + unit tests in tests/test_tools.py
make test-web       # node tests for the web frontend modules (needs node 20+)
make caterkiller2026
make tui            # Rust terminal frontend (needs cargo)
make run            # Build caterkiller2026 + tui and launch
make run-web        # Build caterkiller2026, serve the repo on localhost, open play.html (./run-web.sh [port])
make disasm         # Regenerate raw disassemblies into build/caterkiller/disassembly/
make deploy-web     # Tarball of play.html + bin + JS for a static web server
make all            # verify + caterkiller2026 (no cargo needed)
make clean
```

Output goes to `build/caterkiller/`. Run `make test` after any change to `tools/` or the level sources. Pipeline scripts in `games/caterkiller/pipeline/` refuse to write into `source/`, `sprites/`, `analysis/` or `original/` (see `_guard.py`); they write under `build/caterkiller/pipeline/`.

## Architecture

### Tools (`tools/`)
- **`disasm6502.py`** -- 6502 disassembler. All 56 opcodes, 13 addressing modes, Apple II hardware annotations.
- **`extract_dos33.py`** -- DOS 3.3 disk image parser. Reads VTOC, catalog chains, Track/Sector lists.
- **`asm6502.py`** -- 6502 assembler. Two-pass, supports `.ORG`, `.BYTE`, `.WORD`, `.INCLUDE`, `.ALIGN`, `.ALIGNPAGE`, labels, `<`/`>` byte operators, forward references. A forward `.ORG` or `.ALIGN` zero-fills the gap, so never pad with literal `.BYTE` blocks. An immediate operand outside 0-255 is an error (`LDA #TBL` must be `LDA #<TBL`); `.ORG`/`.ALIGN` values must be defined before use.
- **`fmt6502.py`** -- Assembly formatter with configurable column alignment.

### Caterkiller Game (`games/caterkiller/`)
- **`original/`** -- The 1984 binaries extracted from the disk: level1.bin at $4000, level2.bin at $4000, level3.bin at $6000, supervisor.bin at $0800, plus the files the supervisor loads (picture.bin $2000, explosion.bin $6000, drawexplo.bin $9300, intermission.bin $7800, chrset5.bin $9100, hiscores.bin $1800). No disk image.
- **`source/`** -- Hand-refined annotated assembly. level1.s and level2.s share the same engine; level3.s is completely different.
- **`sprites/`** -- 147 extracted BMP files across 3 levels
- **`analysis/`** -- Notes and font reference tables
- **`pipeline/`** -- Historical one-time scripts used during RE. `build_source.py` exports shared constants imported by the level2/level3 builders. `fix_level_symbols.py` imports `Assembler` from `tools/asm6502.py`.
- **`caterkiller2026/`** -- Active development. Main source `caterkiller2026.s` (load $6000, start PC $7200) `.INCLUDE`s `level1.s`..`level4.s`. Sprite pages $6000-$6FFF: each sprite version sits at offset $00 of its page; sprites drawn with COLORCYCLE set (SHAPE_04, the enemy) also carry an `_ODD` copy at offset $80 that CALCSPRADDR selects for odd byte columns. Score digits live in `DIGIT_FONT` (10 x 32 bytes, indexed by DRAWDIGIT). Code from $7200 is fully relocatable. Level maps (`level1.s`..`level4.s`) hold player start, three elevators, up to five enemy start positions, the enemy count for the level (loaded into DIFFICULTY as count-1) and the obstacle list; field offsets are the `*_OFFSET` equates at the top of the main source.

### Frontends (`frontends/`)
- **`web/`** -- HTML/JS with Three.js 3D view. Shared ES modules `apple2.js` (machine, input, 60 Hz clock), `hgr.js` (HGR decode, colour rules) and `view3d.js` (Three.js spheres); `index.html` is the developer page (file picker, breakpoint, trace), `play.html` the player page used by `make deploy-web`. Node tests in `web/test/` (`make test-web`, no npm install). Serve over HTTP (`python3 -m http.server`); ES module imports do not work from file://.
- **`tui/`** -- Rust terminal frontend (crossterm), Braille rendering of HGR. Library crate (`cpu`, `apple2`, `renderer`) plus a thin `main.rs`; tests in `tests/emulator.rs` (`make test-rust`, clippy must be clean). `serve_ssh.sh` is a login-shell wrapper for serving it over SSH.
- **`shared/cpu6502/`** -- `6502.bundle.js`, an esbuild bundle of the vendored mat-sz/6502 TypeScript emulator (`frontends/web/vendor/mat-sz/6502/src/`). Rebuild instructions in its README.

Third-party code and licenses are listed in `THIRD_PARTY_NOTICES.md`.

## Key Technical Details

- Apple II HGR: 280x192, page 1 at $2000-$3FFF, page 2 at $4000-$5FFF
- DRAW2 sprite engine: page-aligned `[WIDTH][HEIGHT][data...]`, 4 sub-pixel versions per sprite
- Score stored in BCD format (SED before arithmetic, CLD after)
- Font (CHRGEN) at $9100: index*8 bytes, 8 rows each. 0=space, 1-26=A-Z.
- Hardware soft switches: KEYBOARD ($C000), KBDSTRB ($C010), SPKR ($C030), graphics ($C050-$C057), paddles ($C061-$C062)
- Frontends use $C07E (VBLREG) as a ~60Hz frame counter, advanced once per game tick, and `STA $C054` as the present strobe. The web frontend ends a frame when the same instruction polls $C07E repeatedly (the game's SPEEDWAIT), so it never burns its CPU budget spinning
- Level 3 differs: loads at $6000, code in HGR page 2 ($7200-$77AD), no page flipping, timed obstacle course, self-modifying sprite engine
- `JMP $0803` = DOS loader exit (always unresolved, expected)
