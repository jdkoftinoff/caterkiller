# Caterkiller (SNOOKUMS)

A 1984 Apple II game by Jeff Koftinoff, published through A.P.P.L.E. (Apple Pugetsound Program Library Exchange).

## Overview

Caterkiller (sold as Cater Killer through CALL-A.P.P.L.E.) is a 3-level Apple II game. Its files were extracted from the author's DOS 3.3 disk with `tools/extract_dos33.py`; the disk image itself is not in the repository because it also carried Apple's DOS. The game features two distinct engines:

- **Levels 1 & 2** -- Cat-and-mouse gameplay with the DRAW2 sprite engine, page flipping, and BCD scoring. Same engine, different level data.
- **Level 3** -- Completely different obstacle-course engine with timed gameplay, horizontal-only movement, bouncing obstacles, elevators, and joystick support.

## Binary Layout

| File | Load Address | Size | Notes |
|------|-------------|------|-------|
| level1.bin | $4000 | 22,016 bytes | Has embedded symbol table at $6059-$66E9 |
| level2.bin | $4000 | 22,016 bytes | Same engine as level1, no symbol table |
| level3.bin | $6000 | 13,824 bytes | Completely different engine |
| supervisor.bin | $0800 | 2,048 bytes | Loader that chains the levels (BLOADs the files below plus LEVEL1-3) |
| picture.bin | $2000 | 8,191 bytes | Title picture, an HGR page 1 image |
| explosion.bin | $6000 | 5,120 bytes | Explosion graphics data (named by the disk; not yet analysed) |
| drawexplo.bin | $9300 | 564 bytes | Explosion drawing routine (not yet analysed) |
| intermission.bin | $7800 | 524 bytes | Intermission between levels (not yet analysed) |
| chrset5.bin | $9100 | 255 bytes | CHRGEN character set; the disk holds nine (CHRSET1-9), the supervisor patches the digit it loads |
| hiscores.bin | $1800 | 255 bytes | High-score table, all zeros on this disk |

## Building

From the project root:

```bash
# Assemble all levels and verify against originals
make verify

# Build just the level binaries
make caterkiller

# Build Caterkiller 2026
make caterkiller2026
```

## Directory Structure

- `original/` -- The 1984 binaries as extracted from the disk: the three levels, the supervisor that chains them, and the title picture, explosion, intermission, character set and high-score files it loads. The publisher's greeting program and instruction text are not included
- `source/` -- Hand-refined annotated 6502 assembly (the main deliverable)
- `analysis/` -- Human-written analysis and reference documents
- `sprites/` -- Extracted sprite BMPs (147 files across 3 levels)
- `pipeline/` -- One-time scripts used during the reverse engineering process
- `caterkiller2026/` -- Caterkiller 2026, a new version of the game

Raw disassembler output is not tracked; `make disasm` regenerates it into `build/caterkiller/disassembly/`.

## Sprite System (DRAW2 Engine)

Sprites are page-aligned with format: `[WIDTH][HEIGHT][WIDTH*HEIGHT data bytes]`.
Each sprite has 4 sub-pixel versions at consecutive pages (SHAPE+0..+3).

- Levels 1/2: base_page=$40, shapes: $00,$04,$08 (player), $0C,$10 (cats), $14,$18 (food)
- Level 3: base_page=$60, shapes: $00,$04,$08,$0C

Font data (CHRGEN) at $9100: index*8 bytes, 8 rows per character. Mapping: 0=space, 1-26=A-Z, 27+=punctuation.

## Extracting from Disk

This is how the files in `original/` were produced from the disk image (DOS 3.3 file
names `LEVEL1`, `LEVEL2`, `LEVEL3`, `SUPERVISOR`, `PICTURE`, `EXPLOSION`, `DRAWEXPLO`,
`INTERMISSION`, `CHRSET5` and `HISCORES`):

```bash
# List files on a disk image
python3 tools/extract_dos33.py CATERKLR.DSK

# Extract a specific level
python3 tools/extract_dos33.py CATERKLR.DSK LEVEL1 games/caterkiller/original/level1.bin
```
