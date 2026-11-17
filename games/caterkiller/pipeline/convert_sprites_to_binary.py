#!/usr/bin/env python3
"""
Convert sprite/font .BYTE data to visual binary format in assembly source.
Adds visual patterns as comments while keeping .BYTE directive for assembly.
Only bitmap sections are touched: SPRITEDATA, FONTREF and NUMGENTBL. STR_*
tables are CHRGEN character indices, not bitmaps, and are left alone.

Usage: python3 convert_sprites_to_binary.py [file.s ...]
       If no files specified, converts source/level1.s, level2.s, level3.s.
       Output goes to build/caterkiller/pipeline/<name>.s
"""

import re
import sys
import os
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/


def hex_to_binary_visual(hex_str):
    """
    Convert hex string like '$3F' to visual binary pattern.
    Apple II HGR uses 7 visible bits (bits 0-6), bit 7 is color palette.
    LSB (bit 0) is leftmost pixel on screen.
    Returns pattern like '######.' for $3F (bits 0-5 set)
    """
    hex_str = hex_str.strip().replace('$', '').replace('0x', '')
    try:
        val = int(hex_str, 16)
        # 7 visible bits, LSB = leftmost pixel
        bits = []
        for i in range(7):
            bits.append('#' if (val >> i) & 1 else '.')
        return ''.join(bits)
    except ValueError:
        return None

def parse_byte_values(values_str):
    """Parse comma-separated hex values from .BYTE line."""
    values = []
    for v in values_str.split(','):
        v = v.strip()
        if re.match(r'^\$[0-9A-Fa-f]{1,2}$', v):
            values.append(v)
        else:
            return None  # Non-hex value found
    return values

def format_visual_bytes(values, indent='        ', bytes_per_row=1):
    """
    Format hex values with visual binary patterns.
    One byte per line for maximum visual clarity.
    """
    lines = []
    for i, v in enumerate(values):
        pattern = hex_to_binary_visual(v)
        if pattern:
            lines.append(f"{indent}.BYTE {v:>4}        ; |{pattern}|\n")
        else:
            lines.append(f"{indent}.BYTE {v}\n")
    return lines

def process_font_section(all_bytes, indent='        '):
    """
    Process font data - 8 bytes per character.
    CHRGEN character mapping (see analysis/level1_font_reference.txt):
    0=space, 1-26=A-Z, 27-31=[ \\ ] ^ _
    """
    char_names = {
        0: 'SPACE', 1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G',
        8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L', 13: 'M', 14: 'N', 15: 'O',
        16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T', 21: 'U', 22: 'V', 23: 'W',
        24: 'X', 25: 'Y', 26: 'Z', 27: '[', 28: '\\', 29: ']', 30: '^', 31: '_',
    }

    lines = []
    char_idx = 0

    for i in range(0, len(all_bytes), 8):
        chunk = all_bytes[i:i+8]
        if len(chunk) < 8:
            # Incomplete character - just output as raw bytes
            for v in chunk:
                pattern = hex_to_binary_visual(v)
                if pattern:
                    lines.append(f"{indent}.BYTE {v:>4}        ; |{pattern}|\n")
                else:
                    lines.append(f"{indent}.BYTE {v}\n")
            break

        # Full 8-byte character
        char_name = char_names.get(char_idx, f'#{char_idx}')
        lines.append(f"{indent}; --- Character '{char_name}' ---\n")
        for v in chunk:
            pattern = hex_to_binary_visual(v)
            if pattern:
                lines.append(f"{indent}.BYTE {v:>4}        ; |{pattern}|\n")
            else:
                lines.append(f"{indent}.BYTE {v}\n")
        char_idx += 1

    return lines

def convert_file(filepath):
    """
    Convert a single assembly source file.
    Identifies font/sprite data sections and converts them to visual format.
    """
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')

    output_lines = []
    idx = 0
    converted_count = 0

    # Labels that mark bitmap data sections. STR_* tables are CHRGEN text indices and
    # FONTREF is a reference table, not font bitmaps, so neither is converted.
    font_labels = ['SPRITEDATA:', 'NUMGENTBL:']

    while idx < len(lines):
        line = lines[idx]

        # A label definition at column 0 that starts a data section (not a comment mentioning one)
        is_font_section = not line.lstrip().startswith(';') and any(line.startswith(label) for label in font_labels)

        if is_font_section:
            # Found a font/sprite data section
            output_lines.append(line)
            idx += 1

            # Add header comment
            output_lines.append('; Visual binary pattern: | = boundary, # = pixel on, . = pixel off')
            output_lines.append('; 7 bits shown (Apple II HGR format, LSB = leftmost pixel)')
            output_lines.append('')

            # Collect all consecutive .BYTE values
            all_bytes = []
            indent = '        '

            while idx < len(lines):
                current = lines[idx]

                # Blank lines and comments inside the section (including the header and
                # per-character comments from an earlier run) are regenerated below
                if not current.strip() or current.strip().startswith(';'):
                    idx += 1
                    continue

                # Parse .BYTE line
                match = re.match(r'^(\s*)\.BYTE\s+(.+?)(\s*;.*)?$', current, re.IGNORECASE)
                if match:
                    indent = match.group(1) or '        '
                    values_str = match.group(2)
                    values = parse_byte_values(values_str)

                    if values:
                        all_bytes.extend(values)
                        idx += 1
                        continue

                # Not a valid .BYTE line - end of section
                break

            # Convert collected bytes to visual format
            if all_bytes:
                if 'SPRITEDATA' in line.upper():
                    # Font character data - 8 bytes per character
                    converted_lines = process_font_section(all_bytes, indent)
                else:
                    # Generic sprite data - one byte per line
                    converted_lines = format_visual_bytes(all_bytes, indent)

                output_lines.extend([l.rstrip() for l in converted_lines])
                converted_count += 1

            continue

        output_lines.append(line)
        idx += 1

    # Write output under build/, never over the hand-refined source
    out_file = output_path(os.path.basename(filepath))
    with open(out_file, 'w') as f:
        f.write('\n'.join(output_lines))

    print(f"Converted {converted_count} sections in {filepath} -> {out_file}")
    return converted_count

def main():
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source')
        files = [
            os.path.join(base_dir, 'level1.s'),
            os.path.join(base_dir, 'level2.s'),
            os.path.join(base_dir, 'level3.s'),
        ]

    total = 0
    for f in files:
        if os.path.exists(f):
            count = convert_file(f)
            total += count
        else:
            print(f"File not found: {f}")

    print(f"\nTotal: {total} sections converted")

if __name__ == '__main__':
    main()
