// Apple II hi-res (HGR) decoding: 280x192 one-bit pixels, 40 bytes per row,
// 7 pixels per byte with bit 0 leftmost and bit 7 selecting the colour palette.
//
// Colour mode follows the NTSC artifact rules: pixels are taken in pairs, a
// lone pixel in an even column is violet (bit 7 clear) or blue (bit 7 set), a
// lone pixel in an odd column is green or orange, and two adjacent pixels are
// white. Mono mode shows all 280 pixels as black or white.

export const WIDTH = 280;
export const COLOR_WIDTH = 140;
export const HEIGHT = 192;
export const PAGE1 = 0x2000;
export const PAGE2 = 0x4000;

export const BLACK = 0, GREEN = 1, ORANGE = 2, BLUE = 3, VIOLET = 4, WHITE = 5, BRIGHT_WHITE = 6;

/** RGB in 0..1 for each colour index. */
export const PALETTE = [
  [0.0, 0.0, 0.0],  // black
  [0.0, 1.0, 0.0],  // green
  [1.0, 0.5, 0.0],  // orange
  [0.2, 0.4, 1.0],  // blue
  [0.7, 0.2, 1.0],  // violet
  [1.0, 1.0, 1.0],  // white
  [1.0, 1.0, 1.0],  // bright white (both pixels with bit 7 set)
];

/** Byte offset within an HGR page of row y, byte column xByte. */
export function hiresOffset(y, xByte) {
  // (y%8)*$400 + ((y/8)%8)*$80 + (y/64)*40 + xByte
  return ((y & 0x07) << 10) + ((y & 0x38) << 4) + ((y >> 6) * 40) + xByte;
}

/** Colour of a pixel pair: `even`/`odd` are the two bits, `high` the palette bit of their byte. */
export function pairColor(even, odd, high) {
  if (even && odd) return high ? BRIGHT_WHITE : WHITE;
  if (even) return high ? BLUE : VIOLET;
  if (odd) return high ? ORANGE : GREEN;
  return BLACK;
}

const rowBits = new Uint8Array(WIDTH);
const rowHigh = new Uint8Array(WIDTH);

function unpackRow(ram, base) {
  for (let xb = 0; xb < 40; xb++) {
    const v = ram[base + xb];
    const high = v >> 7;
    const px = xb * 7;
    for (let b = 0; b < 7; b++) {
      rowBits[px + b] = (v >> b) & 1;
      rowHigh[px + b] = high;
    }
  }
}

/** Decode a page into 140x192 colour indices. */
export function decodeColor(ram, out, page = PAGE1) {
  for (let y = 0; y < HEIGHT; y++) {
    unpackRow(ram, page + hiresOffset(y, 0));
    const row = y * COLOR_WIDTH;
    for (let x = 0; x < COLOR_WIDTH; x++) {
      const even = rowBits[2 * x], odd = rowBits[2 * x + 1];
      // a pair can straddle two bytes; the lit pixel's own byte decides the palette
      const high = even ? rowHigh[2 * x] : rowHigh[2 * x + 1];
      out[row + x] = pairColor(even, odd, high);
    }
  }
  return out;
}

/** Decode a page into 280x192 values of 0 (black) or 1 (white). */
export function decodeMono(ram, out, page = PAGE1) {
  for (let y = 0; y < HEIGHT; y++) {
    const base = page + hiresOffset(y, 0);
    const row = y * WIDTH;
    for (let xb = 0; xb < 40; xb++) {
      const v = ram[base + xb];
      const px = row + xb * 7;
      for (let b = 0; b < 7; b++) out[px + b] = (v >> b) & 1;
    }
  }
  return out;
}
