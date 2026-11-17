# Web frontend

Runs an Apple II binary in a JavaScript 6502 emulator and shows the HGR screen on a
Three.js 3D surface, one small sphere per pixel.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Developer page: pick any `.bin`, set load address, start PC and a breakpoint, run, see a trace on halt |
| `play.html` | Player page: auto-loads `caterkiller2026.bin`, touch controls, what `make deploy-web` packages |
| `apple2.js` | Machine model: RAM, soft switches, ROM stubs, keyboard and paddle input, 60 Hz game clock |
| `hgr.js` | HGR decoding to 140x192 colour indices or 280x192 mono pixels |
| `view3d.js` | Three.js scene with instanced colour and mono meshes, auto-orbit, fit-to-viewport |
| `test/` | Node tests for `apple2.js` and `hgr.js`, run against the CPU bundle (`make test-web`) |
| `vendor/` | three.js r160 and the mat-sz/6502 TypeScript source |

The CPU itself is `../shared/cpu6502/6502.bundle.js`, loaded as a classic script that
defines the global `CPU6502`.

## Running locally

The pages use ES module imports, so they need to be served over HTTP rather than opened
from the file system. The quick way, from the repository root:

```bash
make run-web            # or ./run-web.sh [port]
```

builds the game, serves the repository on localhost, opens the player page in the
default browser and keeps serving until Ctrl-C. Edit the assembly, rebuild with
`make caterkiller2026`, reload the page. Set `CATERKILLER_NO_OPEN=1` to skip the
browser launch.

By hand, from the repository root (the pages load the CPU bundle from `frontends/shared/`
and the binary from `build/`, so the server must be started there):

```bash
make caterkiller2026
python3 -m http.server 8000
# developer page: http://localhost:8000/frontends/web/
# player page:    http://localhost:8000/frontends/web/play.html
```

`play.html` looks for the game binary next to itself first and then in
`build/caterkiller/`, so it works both in the repository and in a deployment.

## Testing

```bash
make test-web
```

runs the node test suite (no npm install needed; `package.json` only marks the directory
as ES modules). It covers the soft switches, ROM stubs, present strobe, keyboard mapping,
the 60 Hz clock and the HGR colour rules, and runs small programs through the CPU bundle.
The CI workflow runs it on every push.

## Deploying the game

```bash
make deploy-web
```

produces `build/caterkiller/caterkiller2026-web.tar.gz` containing `index.html` (from
`play.html`, with paths flattened), the three modules, the game binary, the emulator
bundle, three.js, and a `licenses/` directory with the license texts for everything in
the archive. Extract it on any static web server.

## Controls

- J or left arrow: move left. K or right arrow: move right. Esc: pause.
- On touch devices the bottom half of the screen is split into left and right buttons.
- Drag: orbit the 3D view. Shift+drag: pan. Scroll: zoom. Auto-orbit: gentle automatic camera motion.
- Color / B&W: toggle NTSC artifact colour (140 pixels wide) and monochrome (280 pixels wide).
- Keys with Cmd, Ctrl or Alt held are left to the browser.

## Emulation notes

- Frame sync: `$C07E` (VBLREG) advances once per 60 Hz game tick. The pages convert display
  frames into game ticks, so the game runs at the same speed on 30, 60 and 120 Hz displays.
- Present strobe: `STA $C054` marks a drawn frame; the screen is decoded and uploaded once per tick.
- A frame ends when the game parks in its wait loop (the same instruction polling `$C07E`),
  so the CPU budget is not burnt spinning; the next tick releases it. Frames the game spends
  waiting without drawing, such as level-start delays, cost almost nothing.
- ROM stubs: WAIT, HOME and COUT return immediately; PREAD returns the paddle value the
  keyboard or touch buttons set; the IRQ, NMI and RESET vectors point at an RTI.
- Executing from memory the loader did not write halts the machine, which catches runaway code.
- Colour: lone pixels are violet or green (bit 7 clear) and blue or orange (bit 7 set) by
  column parity; adjacent pixels are white.

## Vendored code

- `vendor/three/` -- three.js r160 and OrbitControls (MIT)
- `vendor/mat-sz/6502/` -- 6502 emulator TypeScript source (BSD 3-Clause Clear)

See `THIRD_PARTY_NOTICES.md` at the repository root.
