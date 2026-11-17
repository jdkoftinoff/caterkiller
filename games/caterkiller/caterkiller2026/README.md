# Caterkiller 2026

A new version of Caterkiller built on the level 3 engine recovered from the 1984 game.
Four levels, cycling, with level data split out into one file per level.

## Files

- `caterkiller2026.s` -- main source. Loads at `$6000`, entry point `$7200`.
- `level1.s` .. `level4.s` -- level maps, pulled in with `.INCLUDE`. Each holds the player start, three elevators, up to five enemy start positions, the number of enemies in play and the obstacle list; see the offset equates at the top of `caterkiller2026.s`
- `color.s` -- small colour test program (`make color`)
- `reformat.sh` -- runs `tools/fmt6502.py` on the source

## Memory layout

| Range | Contents |
|-------|----------|
| `$6000-$6FFF` | Sprite pages. Four pre-shifted versions per sprite, one page each. The enemy sprite (SHAPE_04) also has an `_ODD` copy at offset `$80` of each page for odd byte columns |
| `$7000-$71FF` | Unused |
| `$7200-` | Code, lookup tables, `DIGIT_FONT`, then `FONTDATA` (page aligned) and the level maps |

The assembler zero-fills gaps left by `.ORG`, `.ALIGN` and `.ALIGNPAGE`, so the source carries no literal padding.

## Building and running

From the repository root:

```bash
make caterkiller2026      # -> build/caterkiller/caterkiller2026.bin (+ a disassembly)
make run                  # play in the terminal frontend
make deploy-web           # package for the web frontend
```

For the web frontend's developer page, load the binary with load address `$6000` and
start PC `$7200`.
