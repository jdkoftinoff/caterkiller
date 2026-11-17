# Third-party notices

The game, tools and frontends in this repository are MIT licensed (see LICENSE).
The following third-party code is included:

## three.js r160

- Location: `frontends/web/vendor/three/` (`three.module.js`, `OrbitControls.js`)
- Source: https://github.com/mrdoob/three.js
- License: MIT, see `frontends/web/vendor/three/LICENSE`

## mat-sz/6502

- Location: `frontends/web/vendor/mat-sz/6502/` (TypeScript source) and the bundle built
  from it at `frontends/shared/cpu6502/6502.bundle.js`
- Source: https://github.com/mat-sz/6502
- License: BSD 3-Clause Clear, see `frontends/web/vendor/mat-sz/6502/LICENSE`

## crossterm

- Used by the Rust terminal frontend as a Cargo dependency (not vendored)
- Source: https://github.com/crossterm-rs/crossterm
- License: MIT

## Not included

The 1984 disk the game was recovered from also carried Apple's DOS 3.3 and the greeting
program and instruction text of its publisher, A.P.P.L.E. (Apple Pugetsound Program Library
Exchange), who held the copyright on the disk and the documentation. None of that is in this
repository. `games/caterkiller/original/` holds only the game's own files, which are the
author's work.
