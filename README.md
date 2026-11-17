# Caterkiller (SNOOKUMS) -- 1984 Apple II game, reverse engineered by its author

In 1984 I wrote Caterkiller (sold as Cater Killer, and called SNOOKUMS inside the code), a
three-level Apple II game, in 6502 assembly language. I first showed it to Sydney Development
Corporation, who were not interested; the string "SYDNEY DEVELOPMENT CORPORATION PRESENTS"
still sitting in the title-screen data is a relic of that pitch and was never shown to a
player. (Sydney Development later became Distinctive Software and then part of Electronic
Arts.) The game was published by A.P.P.L.E., the Apple Pugetsound Program Library Exchange,
who put their front end on the disk and typeset the manual; the 1984 disk and documentation
were their copyright. The game code was, and is, mine.

Forty years later the only thing left was my own copy of that disk. This repository is the
result of taking it apart: the game's original binaries, fully annotated and re-assemblable
source that rebuilds them byte for byte, the sprites, the tools I wrote to do it, two
frontends that run the game today, and a new version of the game built on what I learned.

More about the game:

- [Cater Killer on my historic projects page](https://mobile.jdkoftinoff.com/main/Historic_Projects/Cater_Killer/)
- [Cater Killer paperback on Lulu](https://www.lulu.com/shop/jeff-koftinoff/cater-killer/paperback/product-12qprpy4.html)
- CALL-A.P.P.L.E., the original publisher: [callapple.org](https://www.callapple.org/)

## What is here

| | |
|---|---|
| [`games/caterkiller/original/`](games/caterkiller/original/) | The 1984 disk image and the binaries extracted from it |
| [`games/caterkiller/source/`](games/caterkiller/source/) | Annotated 6502 source for all three levels. `make verify` proves it rebuilds the originals exactly |
| [`games/caterkiller/sprites/`](games/caterkiller/sprites/) | 147 sprite and font bitmaps extracted from the binaries |
| [`games/caterkiller/caterkiller2026/`](games/caterkiller/caterkiller2026/) | Caterkiller 2026, a new version of the game in the same engine |
| [`tools/`](tools/) | DOS 3.3 extractor, 6502 disassembler, assembler and formatter. Python, no dependencies |
| [`frontends/web/`](frontends/web/) | Browser frontend: JavaScript 6502 emulator with a Three.js 3D view of the Apple II screen |
| [`frontends/tui/`](frontends/tui/) | Rust terminal frontend that renders the HGR screen as Braille characters. Playable over SSH |

## Quick start

```bash
# Rebuild the three original levels and check them against the 1984 binaries
make verify

# Build Caterkiller 2026, then play it in the terminal (needs Rust)
make run

# Or play it in a browser: builds the game, starts a local web server, opens the page
make run-web                       # or ./run-web.sh [port]
```

The browser pages need a web server because they use ES module imports, which browsers
will not load from `file://`. `run-web.sh` does the whole loop: edit the assembly, run it
again (or just `make caterkiller2026` while it is still serving) and reload the page.

Requirements: Python 3.6+ and GNU Make, on macOS or Linux. The terminal frontend needs a
Rust toolchain (1.70 or newer) and the web frontend's tests need Node.js 20 or newer. Nothing
is installed from PyPI or npm.

## The game

Caterkiller has two different engines on one disk:

- **Levels 1 and 2** are cat-and-mouse play. Page-flipped hi-res graphics, a sprite engine
  (DRAW2) with four pre-shifted copies of every shape, BCD scoring. Both levels share the
  engine and differ only in data. Level 1 still carries the original assembler's symbol
  table, which is how most of the names in the source were recovered.
- **Level 3** is a timed obstacle course with elevators and bouncing obstacles. Different
  engine, no page flipping, and a self-modifying sprite routine.

The disk also carried Apple's DOS 3.3 and A.P.P.L.E.'s own greeting program and instruction
text, so the disk image and those files are not part of this repository. The game's own
files are: the three levels, the supervisor that chains them, and the title picture,
explosion, intermission, character set and high-score files the supervisor loads. The
three levels are what the source rebuilds.

See [`games/caterkiller/README.md`](games/caterkiller/README.md) for memory maps, binary
layout and the sprite format.

## Tools

All four tools are single-file Python scripts with no dependencies.

```bash
python3 tools/extract_dos33.py disk.dsk                 # list files on a DOS 3.3 disk
python3 tools/extract_dos33.py disk.dsk LEVEL1          # extract one file
python3 tools/disasm6502.py game.bin 0x4000 > game.asm  # disassemble at a load address
python3 tools/asm6502.py game.s game.bin                # assemble
python3 tools/fmt6502.py -e 24 -i game.s                # reformat source in place
```

See [`tools/README.md`](tools/README.md) for details and a workflow for taking apart other
Apple II binaries.

## Building, testing and deploying

```bash
make all             # verify + Caterkiller 2026 (Python only)
make caterkiller2026 # assemble the 2026 game to build/caterkiller/caterkiller2026.bin
make tui             # build the Rust terminal frontend (frontends/tui/target/release/caterkiller-tui)
make run             # build the game and the terminal frontend, then play
make run-web         # build the game, serve it on localhost and open it in the browser
make deploy-web      # package the browser version as build/caterkiller/caterkiller2026-web.tar.gz
make disasm          # raw disassemblies of the original binaries into build/caterkiller/disassembly/
make clean

make test            # rebuild the three originals byte for byte, then the Python unit tests
make test-web        # node tests for the web frontend modules and the JavaScript 6502 bundle
make test-rust       # cargo tests for the terminal frontend
```

`make deploy-web` produces a directory and tarball containing the player page, the game
binary, the emulator, three.js and the license texts; extract it on any static web server.
`run-caterkiller2026.sh` builds and launches the terminal version in one step,
`run-web.sh` does the same for the browser version, and `frontends/tui/serve_ssh.sh`
serves the terminal version to anyone who connects over SSH. The frontend
READMEs ([web](frontends/web/README.md), [terminal](frontends/tui/README.md)) have the
details.

CI runs all three test suites on every push, lints the Rust with clippy, and builds the web
deploy package.

## Repository layout

```
tools/                         Python RE tools
tests/                         Unit tests for the tools (python3 -m unittest)
games/caterkiller/
  original/                    The 1984 binaries extracted from the disk
  source/                      Annotated 6502 source (level1.s, level2.s, level3.s)
  sprites/                     Extracted BMPs
  analysis/                    Notes and font reference tables
  pipeline/                    One-time scripts used during the reverse engineering
  caterkiller2026/             The 2026 game
frontends/
  shared/cpu6502/              JavaScript 6502 emulator bundle used by the web frontend
  web/                         Browser frontend: ES modules, two pages, node tests
  tui/                         Rust terminal frontend
build/                         Generated output (not tracked)
```

## License

MIT, see [LICENSE](LICENSE). Third-party code under `frontends/` is listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
