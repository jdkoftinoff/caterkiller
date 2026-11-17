# Shared 6502 emulator bundle

`6502.bundle.js` is a browser bundle of the [mat-sz/6502](https://github.com/mat-sz/6502)
TypeScript emulator (BSD 3-Clause Clear), exposed as the global `CPU6502`. The web frontend
loads it with a plain `<script>` tag.

The checked-in bundle was built from the package's compiled `lib/*.js` output (the
`// mat-sz/6502/lib/...` markers inside it). Building from the TypeScript source as below
gives the same code with different internal comments. `make test-web` exercises the bundle.

To rebuild it from the vendored source:

```bash
npx esbuild frontends/web/vendor/mat-sz/6502/src/index.ts \
    --bundle --format=iife --global-name=CPU6502 \
    --outfile=frontends/shared/cpu6502/6502.bundle.js
```
