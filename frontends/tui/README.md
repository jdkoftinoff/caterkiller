# Terminal frontend

A Rust 6502 runner that renders the Apple II HGR screen as Unicode Braille.
Each Braille cell is a 2x4 pixel block, so the 280x192 display fits in 140
columns by 48 rows, plus one status line. The only dependency is crossterm.

The crate is a library (`cpu`, `apple2`, `renderer`) with a thin binary on top,
so the emulator can be tested and reused.

## Build and run

```bash
make tui                         # cargo build --release
make run                         # build Caterkiller 2026 and launch it

# or directly
frontends/tui/target/release/caterkiller-tui build/caterkiller/caterkiller2026.bin --load=0x6000 --start=0x7200
frontends/tui/target/release/caterkiller-tui games/caterkiller/original/level3.bin --load=0x6000 --start=0x7200
frontends/tui/target/release/caterkiller-tui --help
```

The terminal needs at least 140 columns by 49 rows; a smaller window shows a
message instead of the screen and keeps emulating. The screen is redrawn at
60 frames per second, sending only the lines that changed, so it stays light
over SSH.

## Controls

- Ctrl-C quits.
- Esc Esc (double tap) pauses and resumes. A single Esc is forwarded to the game.
- Arrow keys and letters are forwarded to the Apple II keyboard.
- J / K (or left / right arrows) move the emulated paddle.

## Emulation notes

- The CPU runs every official opcode with NMOS decimal-mode flag behaviour and
  the indirect-JMP page-wrap bug, and runs the original 1984 binaries. Illegal
  opcodes stop the frontend with a message rather than being skipped. Stores
  never read their target.
- The frame counter at `$C07E` advances once per frame; the game spins on it
  to pace itself. A write to `$C054` marks the frame as presented.
- Monitor ROM calls the game makes (`PREAD`, `WAIT`, `HOME`, `COUT`) are
  stubbed; the paddle value is written into the `PREAD` stub.

## Tests

```bash
cargo test --release --manifest-path frontends/tui/Cargo.toml    # or: make test-rust
```

The suite covers CPU flags and decimal arithmetic, the stack, the indirect
JMP bug, illegal-opcode handling, the absence of phantom reads on stores, the
soft switches, the Braille mapping, and a run of the original level 3. CI runs
it on every push.

## Serving over SSH

`serve_ssh.sh` is a login-shell wrapper. Set it as a dedicated user's shell or
as an SSH `ForceCommand` and anyone who connects gets the game and nothing
else. Setup instructions are in the script header. It looks for the built
`caterkiller-tui` binary and `caterkiller2026.bin` relative to the repository,
and can be pointed elsewhere with the `CATERKILLER_TUI` and `CATERKILLER_BIN`
environment variables.
