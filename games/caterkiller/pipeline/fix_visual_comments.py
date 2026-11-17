#!/usr/bin/env python3
"""
Clean up visual bitmap comments in the level sources and emit font reference tables.

1. Remove "; |#######|" visual comments from STR_* sections. Those bytes are
   CHRGEN character indices, not bitmaps, so the patterns were meaningless.
2. Write <level>_font_reference.txt with the CHRGEN font at $9100 rendered
   character by character (the checked-in copies live in analysis/).

Reads source/levelN.s and original/levelN.bin; writes to build/caterkiller/pipeline/.

Usage: python3 fix_visual_comments.py
"""

import re
import os
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/


BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# CHRGEN character mapping: 0=space, 1-26=A-Z, 27-31=[ \ ] ^ _
CHAR_NAMES = {0: 'SPACE', 27: '[', 28: '\\', 29: ']', 30: '^', 31: '_'}
CHAR_NAMES.update({i: chr(ord('A') + i - 1) for i in range(1, 27)})


def hex_to_visual(val):
    """Convert byte value to 7-bit visual pattern (LSB = leftmost pixel)."""
    return ''.join('#' if (val >> i) & 1 else '.' for i in range(7))


def remove_str_visual_comments(content):
    """Remove visual binary comments from STR_* sections."""
    lines = content.split('\n')
    new_lines = []
    in_str_section = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Entering a STR_ section: keep the label, drop the visual-pattern header comments
        if re.match(r'^STR_\w+:', line):
            in_str_section = True
            new_lines.append(line)
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if 'Visual binary pattern' in next_line or '7 bits shown' in next_line or next_line.strip() == '':
                    i += 1
                    continue
                break
            continue

        # Any other label ends the section
        if in_str_section and re.match(r'^[A-Z_]\w*:', line) and not line.startswith('STR_'):
            in_str_section = False

        if in_str_section and '.BYTE' in line:
            line = re.sub(r'\s*;\s*\|[#.]+\|$', '', line)

        new_lines.append(line)
        i += 1

    return '\n'.join(new_lines)


def format_font_reference(binary_data, base_addr, font_addr):
    """Render the 32 CHRGEN characters at font_addr as an annotated .BYTE listing."""
    font_offset = font_addr - base_addr

    out = []
    out.append("; =================================================================")
    out.append(f"; CHRGEN Font Data at ${font_addr:04X}")
    out.append("; 8 bytes per character, 7 visible bits per row (LSB = leftmost)")
    out.append("; =================================================================")
    out.append("CHRGEN_FONTDATA:")

    for char_idx in range(32):
        char_offset = font_offset + char_idx * 8
        char_data = binary_data[char_offset:char_offset + 8]
        name = CHAR_NAMES.get(char_idx, f'#{char_idx}')
        out.append(f"        ; --- '{name}' (char {char_idx}) ---")
        for b in char_data:
            out.append(f"        .BYTE ${b:02X}        ; |{hex_to_visual(b)}|")

    return '\n'.join(out)


def process_level(level_file, binary_file, base_addr, font_addr):
    """Process a single level file."""
    print(f"\nProcessing {level_file}...")

    with open(os.path.join(BASE_DIR, level_file), 'r') as f:
        content = f.read()
    with open(os.path.join(BASE_DIR, binary_file), 'rb') as f:
        binary_data = f.read()

    content = remove_str_visual_comments(content)
    out_file = output_path(os.path.basename(level_file))
    with open(out_file, 'w') as f:
        f.write(content)
    print(f"  - Removed visual comments from STR_* sections -> {out_file}")

    font_ref_file = output_path(os.path.basename(level_file).replace('.s', '_font_reference.txt'))
    with open(font_ref_file, 'w') as f:
        f.write(format_font_reference(binary_data, base_addr, font_addr))
    print(f"  - Wrote {font_ref_file}")


def main():
    levels = [
        ('source/level1.s', 'original/level1.bin', 0x4000, 0x9100),
        ('source/level2.s', 'original/level2.bin', 0x4000, 0x9100),
        ('source/level3.s', 'original/level3.bin', 0x6000, 0x9100),
    ]
    for level_file, binary_file, base_addr, font_addr in levels:
        process_level(level_file, binary_file, base_addr, font_addr)

    print("\nDone.")


if __name__ == '__main__':
    main()
