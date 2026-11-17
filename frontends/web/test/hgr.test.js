import { test } from "node:test";
import assert from "node:assert/strict";
import * as HGR from "../hgr.js";

const { BLACK, GREEN, ORANGE, BLUE, VIOLET, WHITE, BRIGHT_WHITE } = HGR;

test("hiresOffset matches the Apple II interleaved layout", () => {
  assert.equal(HGR.hiresOffset(0, 0), 0x0000);
  assert.equal(HGR.hiresOffset(1, 0), 0x0400);
  assert.equal(HGR.hiresOffset(8, 0), 0x0080);
  assert.equal(HGR.hiresOffset(64, 0), 0x0028);
  assert.equal(HGR.hiresOffset(191, 39), 0x1FF7);
});

test("colour decode follows the Applesoft HCOLOR patterns", () => {
  const ram = new Uint8Array(0x10000);
  const out = new Uint8Array(HGR.COLOR_WIDTH * HGR.HEIGHT);
  // One byte at the start of rows 0..5, each a known HCOLOR fill pattern
  const cases = [
    [0, 0x55, VIOLET],       // HCOLOR=2: even pixels, bit 7 clear
    [1, 0x2A, GREEN],        // HCOLOR=1: odd pixels, bit 7 clear
    [2, 0xD5, BLUE],         // HCOLOR=6: even pixels, bit 7 set
    [3, 0xAA, ORANGE],       // HCOLOR=5: odd pixels, bit 7 set
    [4, 0x7F, WHITE],        // HCOLOR=3: all pixels
    [5, 0xFF, BRIGHT_WHITE], // HCOLOR=7: all pixels, bit 7 set
  ];
  for (const [y, byte] of cases) ram[HGR.PAGE1 + HGR.hiresOffset(y, 0)] = byte;
  HGR.decodeColor(ram, out);
  for (const [y, , color] of cases) {
    // the byte covers pixels 0..6, so colour pairs 0..2 are fully inside it
    for (let x = 0; x < 3; x++) assert.equal(out[y * HGR.COLOR_WIDTH + x], color, `row ${y} pair ${x}`);
    assert.equal(out[y * HGR.COLOR_WIDTH + 10], BLACK);
  }
});

test("a pair straddling two bytes takes the palette of the lit pixel's byte", () => {
  const ram = new Uint8Array(0x10000);
  const out = new Uint8Array(HGR.COLOR_WIDTH * HGR.HEIGHT);
  // pixel 6 is bit 6 of byte 0, pixel 7 is bit 0 of byte 1; pair 3 = pixels 6 and 7
  ram[HGR.PAGE1] = 0x40;          // pixel 6 lit (even), bit 7 clear -> violet
  ram[HGR.PAGE1 + 1] = 0x80;      // byte 1 has bit 7 set but no pixels lit
  HGR.decodeColor(ram, out);
  assert.equal(out[3], VIOLET);
  ram[HGR.PAGE1] = 0x00;
  ram[HGR.PAGE1 + 1] = 0x81;      // pixel 7 lit (odd), bit 7 set -> orange
  HGR.decodeColor(ram, out);
  assert.equal(out[3], ORANGE);
});

test("mono decode puts bit 0 leftmost", () => {
  const ram = new Uint8Array(0x10000);
  const out = new Uint8Array(HGR.WIDTH * HGR.HEIGHT);
  ram[HGR.PAGE1 + HGR.hiresOffset(10, 1)] = 0x01 | 0x40 | 0x80; // bits 0 and 6 lit, bit 7 ignored
  HGR.decodeMono(ram, out);
  const row = 10 * HGR.WIDTH;
  assert.deepEqual(Array.from(out.slice(row + 7, row + 14)), [1, 0, 0, 0, 0, 0, 1]);
});
