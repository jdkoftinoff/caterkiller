#!/usr/bin/env python3
"""
Regenerate the sprite data section of a level source from the binary, with a
visual bitmap comment on every sprite row.

Sprites are page-aligned with format [WIDTH][HEIGHT][data...], four sub-pixel
versions per shape on consecutive 256-byte pages. The lines between the .ORG
header and the end of the sprite area are replaced; the rest of the file is
kept as is.

Reads source/levelN.s and original/levelN.bin; writes build/caterkiller/pipeline/levelN.s.
"""

import re
import os
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/


BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
HEX_BYTE = re.compile(r'\$[0-9A-Fa-f]{1,2}\b')


def hex_to_visual(val):
    """Convert byte value to 7-bit visual pattern (LSB = leftmost pixel)."""
    return ''.join('#' if (val >> i) & 1 else '.' for i in range(7))


def count_bytes(line):
    """Number of byte values on a .BYTE line. Addresses in the comment are not counted."""
    code = line.split(';', 1)[0]
    if '.BYTE' not in code.upper():
        return 0
    return len(HEX_BYTE.findall(code))


def generate_sprite_lines(binary, base_addr, shapes, sprite_end_offset):
    """Format the first sprite_end_offset bytes of the binary page by page."""
    lines = []
    offset = 0
    while offset < sprite_end_offset and offset + 1 < len(binary):
        page_addr = base_addr + offset
        page_index = offset // 256
        width = binary[offset]
        height = binary[offset + 1]

        shape = version = None
        for s in shapes:
            if s <= page_index < s + 4:
                shape, version = s, page_index - s
                break

        if shape is not None and 1 <= width <= 8 and 1 <= height <= 32:
            lines.append("; ----------------------------------------------------------------")
            lines.append(f"; SHAPE_{shape:02X}_V{version} at ${page_addr:04X}")
            lines.append(f"; Width: {width} bytes ({width * 7} pixels), Height: {height} rows")
            lines.append("; ----------------------------------------------------------------")
            lines.append(f"        .BYTE ${width:02X}, ${height:02X}                     ; width={width}, height={height}")

            data_offset = offset + 2
            for row in range(height):
                row_bytes = []
                row_visuals = []
                for col in range(width):
                    idx = data_offset + row * width + col
                    if idx < len(binary):
                        b = binary[idx]
                        row_bytes.append(f'${b:02X}')
                        row_visuals.append(hex_to_visual(b))
                lines.append(f"        .BYTE {', '.join(row_bytes):<24} ; |{''.join(row_visuals)}|")

            sprite_size = 2 + width * height
            padding_size = 256 - sprite_size
            if padding_size > 0:
                lines.append(f"        ; --- padding ({padding_size} bytes) ---")
                padding_offset = offset + sprite_size
                for p in range(0, padding_size, 16):
                    chunk = binary[padding_offset + p:padding_offset + p + min(16, padding_size - p)]
                    lines.append(f"        .BYTE {', '.join(f'${b:02X}' for b in chunk)}")
        else:
            lines.append(f"; --- Page ${page_addr:04X} ---")
            for p in range(0, 256, 16):
                chunk_start = offset + p
                if chunk_start >= sprite_end_offset:
                    break
                chunk = binary[chunk_start:chunk_start + min(16, sprite_end_offset - chunk_start)]
                lines.append(f"        .BYTE {', '.join(f'${b:02X}' for b in chunk)}")

        lines.append("")
        offset += 256

    return lines


def process_level(level_file, binary_file, base_addr, shapes, sprite_end_offset):
    """Replace the sprite data section of one level source."""
    with open(os.path.join(BASE_DIR, binary_file), 'rb') as f:
        binary = f.read()
    with open(os.path.join(BASE_DIR, level_file), 'r') as f:
        lines = f.read().split('\n')

    # The sprite data starts after the .ORG line and the comments that follow it
    header_end = 0
    for i, line in enumerate(lines):
        if '.ORG' in line.upper():
            header_end = i + 1
            while header_end < len(lines) and (
                lines[header_end].strip() == '' or lines[header_end].strip().startswith(';')
            ):
                header_end += 1
            break

    # It ends once sprite_end_offset bytes have been counted, or at the first label
    byte_count = 0
    data_end = header_end
    for i in range(header_end, len(lines)):
        line = lines[i]
        n = count_bytes(line)
        if n:
            byte_count += n
            data_end = i + 1
            if byte_count >= sprite_end_offset:
                break
        elif line.strip() and not line.strip().startswith(';') and not line.startswith(' ') and ':' in line:
            break

    print(f"  Header ends at line {header_end}")
    print(f"  Sprite data: lines {header_end}-{data_end} ({byte_count} bytes)")

    new_lines = lines[:header_end] + generate_sprite_lines(binary, base_addr, shapes, sprite_end_offset) + lines[data_end:]

    out_file = output_path(os.path.basename(level_file))
    with open(out_file, 'w') as f:
        f.write('\n'.join(new_lines))
    print(f"  Wrote {out_file}")


def main():
    # Level 1/2: shapes $00-$18, each with 4 versions = pages $40-$5B = 0x1C00 bytes
    # Level 3:   shapes $00-$0C, 4 versions each = pages $60-$6F = 0x1000 bytes
    levels = [
        ('source/level1.s', 'original/level1.bin', 0x4000, [0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18], 0x1C00),
        ('source/level2.s', 'original/level2.bin', 0x4000, [0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18], 0x1C00),
        ('source/level3.s', 'original/level3.bin', 0x6000, [0x00, 0x04, 0x08, 0x0C], 0x1000),
    ]

    for level_file, binary_file, base_addr, shapes, sprite_end in levels:
        print(f"\nProcessing {level_file}...")
        process_level(level_file, binary_file, base_addr, shapes, sprite_end)

    print("\nDone!")


if __name__ == '__main__':
    main()
