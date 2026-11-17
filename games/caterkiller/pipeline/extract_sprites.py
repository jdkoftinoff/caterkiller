#!/usr/bin/env python3
"""
Extract sprite bitmaps from Caterkiller (SNOOKUMS) binary files.

Extracts game sprites and font characters from all 3 levels,
rendering them as ASCII art (stdout) and BMP images (sprites/ directory).

Apple II HGR pixel format:
  - 7 visible bits per byte (bits 0-6), LSB = leftmost pixel
  - Bit 7 = color palette flag:
    0 = group 1 (violet/green)
    1 = group 2 (blue/orange)

Sprite format (DRAW2 engine):
  - Page-aligned at address (SHAPE | base_page) * 256
  - Byte 0 = WIDTH (bytes), Byte 1 = HEIGHT (rows)
  - Then WIDTH * HEIGHT data bytes, row-major
  - 4 sub-pixel versions at consecutive pages (SHAPE+0..SHAPE+3)
"""

import os
import struct
import sys
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/


# Apple II HGR colors (approximate RGB values)
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
VIOLET  = (148, 33, 246)   # group 1, odd pixel
GREEN   = (20, 245, 60)    # group 1, even pixel
BLUE    = (20, 107, 246)   # group 2, odd pixel
ORANGE  = (255, 108, 20)   # group 2, even pixel

# Level definitions
LEVELS = {
    'level1': {
        'file': os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'original', 'level1.bin'),
        'load_addr': 0x4000,
        'base_page': 0x40,
        'shapes': {
            0x00: 'Player Right',
            0x04: 'Player/Enemy',
            0x08: 'Player Left',
            0x0C: 'Cat Left',
            0x10: 'Cat Right',
            0x14: 'Food A',
            0x18: 'Food B',
        },
        'font_addr': 0x9100,   # CHRGEN font data: index*8 bytes, 8 rows each
    },
    'level2': {
        'file': os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'original', 'level2.bin'),
        'load_addr': 0x4000,
        'base_page': 0x40,
        'shapes': {
            0x00: 'Player Right',
            0x04: 'Player/Enemy',
            0x08: 'Player Left',
            0x0C: 'Cat Left',
            0x10: 'Cat Right',
            0x14: 'Food A',
            0x18: 'Food B',
        },
        'font_addr': 0x9100,
    },
    'level3': {
        'file': os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'original', 'level3.bin'),
        'load_addr': 0x6000,
        'base_page': 0x60,
        'shapes': {
            0x00: 'Player',
            0x04: 'Enemy/Obstacle',
            0x08: 'Food/Ball',
            0x0C: 'Obstacle',
        },
        'font_addr': 0x9100,
    },
}

# CHRGEN/PIXRENDER font character mapping
# Font data at $9100: each character is 8 bytes (8 rows, 7 visible bits per row)
# CHRGEN code: ASL A * 3 (index*8), SHPHI=$91 → address = $9100 + index*8
# Mapping: 0=space, 1=A, 2=B, ..., 26=Z, 27+=[, \, ], ^, _, special chars
FONT_CHARS = {
    0: ' ',
    **{i: chr(ord('A') + i - 1) for i in range(1, 27)},  # 1-26: A-Z
    27: '[', 28: '\\', 29: ']', 30: '^', 31: '_',
}


def read_binary(filename):
    """Read a binary file and return its contents."""
    with open(filename, 'rb') as f:
        return f.read()


def get_byte(data, load_addr, addr):
    """Read a byte from the binary at a given address."""
    offset = addr - load_addr
    if 0 <= offset < len(data):
        return data[offset]
    return None


def extract_sprite(data, load_addr, base_page, shape):
    """Extract a sprite from binary data.

    Returns (width, height, pixel_data) or None if invalid.
    pixel_data is a list of rows, each row is a list of bytes.
    """
    addr = (shape | base_page) * 256
    offset = addr - load_addr

    if offset < 0 or offset + 2 > len(data):
        return None

    width = data[offset]
    height = data[offset + 1]

    # Validate dimensions
    if width == 0 or height == 0 or width > 40 or height > 192:
        return None

    data_start = offset + 2
    data_end = data_start + width * height

    if data_end > len(data):
        return None

    rows = []
    for row in range(height):
        row_start = data_start + row * width
        row_data = list(data[row_start:row_start + width])
        rows.append(row_data)

    return (width, height, rows)


def sprite_to_ascii(width, height, rows):
    """Convert sprite data to ASCII art string.

    Each byte produces 7 characters (visible bits) plus a color indicator.
    '#' = pixel set (group 1, bit7=0)
    '@' = pixel set (group 2, bit7=1)
    '.' = pixel clear
    """
    lines = []
    for row in rows:
        line = ''
        for byte_val in row:
            color_bit = (byte_val >> 7) & 1
            char_set = '@' if color_bit else '#'
            for bit in range(7):
                if byte_val & (1 << bit):
                    line += char_set
                else:
                    line += '.'
        lines.append(line)
    return '\n'.join(lines)


def sprite_to_color_pixels(width, height, rows):
    """Convert sprite data to colored pixel array for BMP output.

    Returns list of rows, each row is list of (R,G,B) tuples.
    Implements Apple II HGR color rules:
    - Isolated pixel: color depends on column parity and bit 7
    - Adjacent set bits: white
    """
    pixel_rows = []

    for row in rows:
        # Build flat array of (bit_set, color_group) for entire row
        pixels = []
        for byte_idx, byte_val in enumerate(row):
            color_group = (byte_val >> 7) & 1
            for bit in range(7):
                is_set = bool(byte_val & (1 << bit))
                col = byte_idx * 7 + bit
                pixels.append((is_set, color_group, col))

        # Now colorize
        pixel_colors = []
        for i, (is_set, group, col) in enumerate(pixels):
            if not is_set:
                pixel_colors.append(BLACK)
            else:
                # Check neighbors for white detection
                left_set = (i > 0) and pixels[i-1][0]
                right_set = (i < len(pixels)-1) and pixels[i+1][0]

                if left_set or right_set:
                    pixel_colors.append(WHITE)
                else:
                    # Isolated pixel - color by column parity and group
                    if group == 0:
                        pixel_colors.append(VIOLET if (col % 2 == 1) else GREEN)
                    else:
                        pixel_colors.append(BLUE if (col % 2 == 1) else ORANGE)

        pixel_rows.append(pixel_colors)

    return pixel_rows


def write_bmp(filename, pixel_rows, scale=4):
    """Write pixel data as a BMP file with scaling.

    pixel_rows: list of rows, each row is list of (R,G,B) tuples.
    scale: integer scale factor for each pixel.
    """
    if not pixel_rows or not pixel_rows[0]:
        return

    img_width = len(pixel_rows[0]) * scale
    img_height = len(pixel_rows) * scale

    # BMP row padding (rows must be multiple of 4 bytes)
    row_bytes = img_width * 3
    row_padding = (4 - (row_bytes % 4)) % 4
    padded_row_bytes = row_bytes + row_padding

    pixel_data_size = padded_row_bytes * img_height
    file_size = 54 + pixel_data_size  # 14 (file header) + 40 (info header) + pixels

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'wb') as f:
        # BMP File Header (14 bytes)
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(struct.pack('<HH', 0, 0))  # reserved
        f.write(struct.pack('<I', 54))       # pixel data offset

        # BMP Info Header (40 bytes)
        f.write(struct.pack('<I', 40))        # header size
        f.write(struct.pack('<i', img_width))
        f.write(struct.pack('<i', img_height))
        f.write(struct.pack('<HH', 1, 24))    # planes, bpp
        f.write(struct.pack('<I', 0))         # compression (none)
        f.write(struct.pack('<I', pixel_data_size))
        f.write(struct.pack('<ii', 2835, 2835))  # pixels/meter
        f.write(struct.pack('<II', 0, 0))     # colors

        # Pixel data (BMP is bottom-up, BGR order)
        padding = b'\x00' * row_padding
        for src_row in reversed(pixel_rows):
            scaled_row = bytearray()
            for r, g, b in src_row:
                scaled_row.extend([b, g, r] * scale)  # BGR
            row_data = bytes(scaled_row)
            for _ in range(scale):
                f.write(row_data)
                f.write(padding)


def extract_font_chars(data, load_addr, font_addr):
    """Extract 8-byte font characters from CHRGEN font area at $9100.

    Font layout: index*8 bytes from font_addr.
    Index 0 = space (blank), 1 = A, 2 = B, ..., 26 = Z, 27+ = special.

    Returns list of (index, char_label, char_rows).
    """
    offset = font_addr - load_addr
    if offset < 0 or offset >= len(data):
        return []

    chars = []
    # Scan up to 32 characters (space + A-Z + a few specials)
    max_chars = min(32, (len(data) - offset) // 8)

    for i in range(max_chars):
        char_offset = offset + i * 8
        if char_offset + 8 > len(data):
            break

        char_rows = []
        for row in range(8):
            char_rows.append(data[char_offset + row])

        label = FONT_CHARS.get(i, f'#{i}')
        chars.append((i, label, char_rows))

    return chars


def font_char_to_ascii(char_rows):
    """Convert an 8-byte font character to ASCII art."""
    lines = []
    for byte_val in char_rows:
        line = ''
        for bit in range(7):
            if byte_val & (1 << bit):
                line += '#'
            else:
                line += '.'
        lines.append(line)
    return '\n'.join(lines)


def font_char_to_pixels(char_rows):
    """Convert font character to pixel rows for BMP."""
    pixel_rows = []
    for byte_val in char_rows:
        row = []
        for bit in range(7):
            if byte_val & (1 << bit):
                row.append(WHITE)
            else:
                row.append(BLACK)
        pixel_rows.append(row)
    return pixel_rows


def write_font_sheet(filename, chars, scale=4):
    """Write all font characters as a single sprite sheet BMP."""
    if not chars:
        return

    chars_per_row = 16
    char_width = 7
    char_height = 8
    spacing = 1  # pixel gap between chars

    num_rows = (len(chars) + chars_per_row - 1) // chars_per_row

    sheet_width = chars_per_row * (char_width + spacing) + spacing
    sheet_height = num_rows * (char_height + spacing) + spacing

    # Initialize sheet with dark gray background
    GRAY = (40, 40, 40)
    sheet = [[GRAY] * sheet_width for _ in range(sheet_height)]

    for idx, (char_idx, char_rows) in enumerate(chars):
        col = idx % chars_per_row
        row = idx // chars_per_row

        x_start = col * (char_width + spacing) + spacing
        y_start = row * (char_height + spacing) + spacing

        pixels = font_char_to_pixels(char_rows)
        for y, pixel_row in enumerate(pixels):
            for x, color in enumerate(pixel_row):
                sheet[y_start + y][x_start + x] = color

    write_bmp(filename, sheet, scale)


def process_level(level_name, config):
    """Process a single level: extract and render all sprites."""
    print(f"\n{'='*60}")
    print(f"  {level_name.upper()}: {config['file']}")
    print(f"  Load: ${config['load_addr']:04X}  Base page: ${config['base_page']:02X}")
    print(f"{'='*60}")

    filepath = config['file']
    if not os.path.exists(filepath):
        print(f"  WARNING: {filepath} not found, skipping")
        return

    data = read_binary(filepath)
    load_addr = config['load_addr']
    base_page = config['base_page']

    out_dir = os.path.dirname(output_path('sprites', level_name, 'x'))
    os.makedirs(out_dir, exist_ok=True)

    # --- Known sprites ---
    print(f"\n  Known Sprites:")
    print(f"  {'-'*50}")

    for shape, name in sorted(config['shapes'].items()):
        print(f"\n  SHAPE ${shape:02X} - {name}")

        # Extract all 4 sub-pixel versions
        for version in range(4):
            actual_shape = shape + version
            result = extract_sprite(data, load_addr, base_page, actual_shape)

            if result is None:
                print(f"    v{version}: (invalid or out of range)")
                continue

            width, height, rows = result
            addr = (actual_shape | base_page) * 256
            print(f"    v{version}: ${addr:04X}  {width}x{height} bytes  ({width*7}x{height} pixels)")

            # ASCII art (only show v0 to avoid clutter)
            if version == 0:
                ascii_art = sprite_to_ascii(width, height, rows)
                for line in ascii_art.split('\n'):
                    print(f"      {line}")

            # BMP output
            pixel_rows = sprite_to_color_pixels(width, height, rows)
            bmp_path = os.path.join(out_dir, f"shape_{shape:02X}_v{version}.bmp")
            write_bmp(bmp_path, pixel_rows)

            # Also write monochrome version
            mono_rows = []
            for row in rows:
                mono_row = []
                for byte_val in row:
                    for bit in range(7):
                        if byte_val & (1 << bit):
                            mono_row.append(WHITE)
                        else:
                            mono_row.append(BLACK)
                mono_rows.append(mono_row)
            mono_path = os.path.join(out_dir, f"shape_{shape:02X}_v{version}_mono.bmp")
            write_bmp(mono_path, mono_rows)

    # Note: there is deliberately no "scan every page for a plausible width/height
    # header" pass. The sprite pages sit inside the HGR page 2 playfield bitmap,
    # so such a scan produced false positives (shape_1C..1F_scan.bmp) that were
    # just rows of screen data. The shape list in LEVELS is authoritative.

    # --- Font characters (CHRGEN system) ---
    font_addr = config.get('font_addr')
    if font_addr:
        font_offset = font_addr - load_addr
        if 0 <= font_offset < len(data):
            print(f"\n  CHRGEN Font (${font_addr:04X}):")
            print(f"  {'-'*50}")

            chars = extract_font_chars(data, load_addr, font_addr)

            for idx, label, char_rows in chars:
                if any(b != 0 for b in char_rows):
                    print(f"\n    Char {idx} '{label}':")
                    ascii_art = font_char_to_ascii(char_rows)
                    for line in ascii_art.split('\n'):
                        print(f"      {line}")

            # Write font sheet
            sheet_path = os.path.join(out_dir, "font_sheet.bmp")
            # Adapt chars for write_font_sheet (expects (index, rows) tuples)
            sheet_chars = [(idx, char_rows) for idx, label, char_rows in chars]
            write_font_sheet(sheet_path, sheet_chars)
            print(f"\n    Font sheet saved: {sheet_path}")
        else:
            print(f"\n  Font at ${font_addr:04X} is outside binary range")


def main():
    print("Caterkiller - Sprite Bitmap Extractor")
    print("========================================")
    print("7 visible bits per byte, bit 7 = color palette shift")
    print("'#' = pixel set (group 1: violet/green)")
    print("'@' = pixel set (group 2: blue/orange)")
    print("'.' = pixel clear")

    for level_name, config in LEVELS.items():
        process_level(level_name, config)

    print(f"\n{'='*60}")
    print(f"  BMP files saved under {output_path('sprites')}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
