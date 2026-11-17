# Apple II Reverse Engineering Tools

Reusable Python tools for extracting and analyzing binary files from Apple II DOS 3.3 disk images. No external dependencies -- Python 3.6+ standard library only.

## Tools

### `extract_dos33.py` - DOS 3.3 File Extractor

Extracts binary files from Apple II DOS 3.3 disk images (.dsk, 140KB).

```bash
# List all files on a disk
python3 tools/extract_dos33.py disk_image.dsk

# Extract a specific file (written to filename.bin in the current directory, or to a given path)
python3 tools/extract_dos33.py disk_image.dsk "FILENAME" [output.bin]
```

Parses the VTOC at Track 17 Sector 0, follows catalog chains, and reconstructs files via Track/Sector lists. Binary files have their 4-byte load address and length header stripped; Applesoft and Integer BASIC files have their 2-byte length stripped; other types are written raw.

### `disasm6502.py` - 6502 Disassembler

Disassembles 6502 machine code into annotated assembly.

```bash
python3 tools/disasm6502.py input.bin [load_address_hex] > output.asm
```

Output goes to stdout. The load address defaults to `$0800` if omitted.

Features: all 56 official 6502 opcodes, 13 addressing modes, automatic label generation for branch/jump targets, Apple II hardware soft switch annotation ($C000-$C0FF), high-bit ASCII string detection, illegal opcode flagging.

### `asm6502.py` - 6502 Assembler

Assembles 6502 source files to binary. Two-pass assembly with forward reference resolution, all standard addressing modes, `LABEL = value` equates, and `<LABEL` / `>LABEL` for the low and high byte of an address.

Directives:

| Directive | Effect |
|-----------|--------|
| `.ORG $addr` | Set the location counter. A forward `.ORG` leaves a zero-filled gap |
| `.BYTE $xx, ...` | Emit bytes |
| `.WORD $xxxx, ...` | Emit little-endian 16-bit words |
| `.INCLUDE "file.s"` | Insert another source file (relative to the including file) |
| `.ALIGN $80` | Zero-fill to the next multiple of the value |
| `.ALIGNPAGE [LABEL]` | Zero-fill to the next 256-byte page, optionally defining LABEL there |

Operands accept `$hex`, `%binary`, decimal, symbols, and `+` / `-`. `<expr` and `>expr` take the low and high byte and bind tighter than `+`, so `#>TBL+1` is the high byte of TBL plus one (ca65 convention). Zero-page addressing is chosen automatically when the operand is known to be below $100; a symbol defined later in the file assembles as absolute. Duplicate labels, redefined symbols, unsupported operators, malformed numbers, immediates outside 0-255 (write `#<TBL`, not `#TBL`) and `.ORG`/`.ALIGN` values that are not yet defined are errors, and errors name the file and line even inside `.INCLUDE`d files.

```bash
python3 tools/asm6502.py input.s output.bin
```

### `fmt6502.py` - Assembly Source Formatter

Reformats 6502 assembly source with consistent column alignment.

```bash
# Format to stdout
python3 tools/fmt6502.py input.s

# Format in-place
python3 tools/fmt6502.py -i input.s

# Custom comment column
python3 tools/fmt6502.py -e 24 -i input.s
```

## Workflow: Analyzing a New Game

1. **Extract**: `python3 tools/extract_dos33.py game.dsk` to list files, then extract the game binary. Note the load address.
2. **Disassemble**: `python3 tools/disasm6502.py game.bin 0xLOAD_ADDR > game.asm`
3. **Analyze**: Look for entry points, graphics mode setup (`$C050-$C057`), main loop (`JMP` back), keyboard reads (`$C000`), sound (`$C030`), and sprite data blocks.
4. **Document**: Map zero page variables, subroutines, data structures, and game flow.

## Apple II Hardware Addresses

| Address | Name | Description |
|---------|------|-------------|
| $C000 | KEYBOARD | Keyboard data (key + $80) |
| $C010 | KBDSTRB | Clear keyboard strobe |
| $C030 | SPKR | Speaker toggle |
| $C050 | TXTCLR | Graphics mode |
| $C051 | TXTSET | Text mode |
| $C052 | MIXCLR | Full screen |
| $C053 | MIXSET | Mixed mode (4 lines text) |
| $C054 | PAGE1 | Display page 1 |
| $C055 | PAGE2 | Display page 2 |
| $C056 | LORES | Lo-res graphics |
| $C057 | HIRES | Hi-res graphics |
| $C061 | PB0 | Paddle button 0 |
| $C062 | PB1 | Paddle button 1 |

## File Formats

### DOS 3.3 Disk Image (.dsk)
- 140KB (35 tracks x 16 sectors x 256 bytes)
- Track 17 contains VTOC and catalog

### Binary File Header
- Bytes 0-1: Load address (little-endian)
- Bytes 2-3: Length (little-endian)
- Bytes 4+: Program data

## Tests

```bash
make test        # make verify, then python3 -m unittest discover -s tests
```

`tests/test_tools.py` covers the assembler (encoding, phase stability, error reporting, alignment), the disassembler, the disk extractor against the real disk image, the formatter, and rebuilds the three original levels as golden tests.
