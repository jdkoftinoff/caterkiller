# Reverse Engineering Pipeline Scripts

These are **one-time scripts** used during the reverse engineering process. They are preserved here for reference but are not part of the normal build flow. The outputs they generated (the `.s` source files and sprite BMPs) are the actual deliverables, checked into `source/` and `sprites/`, and were refined by hand afterwards. Regenerating them does not reproduce the checked-in files.

## Script Dependency Chain

```
extract_symbols.py          (extracts the symbol table embedded in level1.bin)
        |
        v
build_source.py             (builds level1.s; exports shared constants)
    |           |
    v           v
build_source_level2.py    build_source_level3.py
    (imports OPCODES,         (imports OPCODES,
     ZP_SYMBOLS, etc.)        HW_NAMES, etc.)
```

Post-processing (applied after initial source generation):
```
fix_level_symbols.py        (adds missing symbol definitions; imports asm6502.py from tools/)
fix_visual_comments.py      (strips bitmap comments from STR_* text tables; writes font reference tables)
convert_to_binary.py        (rewrites bitmap .BYTE values as %binary literals)
convert_sprites_to_binary.py (adds |#..#| bitmap comments to sprite/font sections)
add_sprite_visuals.py       (regenerates the sprite data section from the binary with bitmap comments)
extract_sprites.py          (extracts sprites and the CHRGEN font to BMP files)
```

## Usage

Every script imports `_guard.py`, which makes any write into `source/`, `sprites/`, `analysis/` or `original/` fail with a message, and all of them write their output under `build/caterkiller/pipeline/` instead. Set `CATERKILLER_PIPELINE_OVERWRITE=1` only if you really mean to overwrite the hand-edited sources.

The scripts resolve input paths from their own location, so they can be run from anywhere:

```bash
# Regenerate level1.s from the original binary (into build/caterkiller/pipeline/)
python3 games/caterkiller/pipeline/build_source.py

# Extract sprites to BMP
python3 games/caterkiller/pipeline/extract_sprites.py
```

## Known limitations

- The three builders each carry their own copy of the linear-sweep disassembler. They were written one after another as the understanding of each binary grew and were never merged, because there is no way to verify a merged version against the hand-refined sources.
- Mistakes the generators made were corrected in `source/` by hand and later in the scripts, but the generated output still differs from the checked-in sources in thousands of hand-written comments. Two errors worth knowing about if you compare them: early versions placed `STR_PRESENTS` one byte late ($816F instead of $816E), and left the hit table at $700B-$7012 and the $FF/$00 tables before `DRAWVEC` out of `DATA_REGIONS`, so their `$00` bytes were disassembled as `BRK` instructions.
- `extract_sprites.py` colours isolated pixels by their column parity within the sprite, not the screen column where the sprite is drawn, so HGR colours in the BMPs are approximate.
