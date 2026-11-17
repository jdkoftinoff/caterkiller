#!/usr/bin/env python3
"""
Rewrite .BYTE hex values in bitmap sections as binary literals so the pixel
pattern can be read straight from the source: $3F becomes %00111111. The
assembler accepts % binary literals, so the result still assembles.

Only sections introduced by a sprite/font label (SPRITEDATA, FONTREF, SHAPE_*,
NUMGEN, CHRGEN, DIGIT, CHAR) or by a sprite/font section-header comment are
converted. A section ends at the first instruction or at a section header that
mentions code.

Usage: python3 convert_to_binary.py [file.s ...]
       Defaults to source/level1.s, level2.s and level3.s. Output goes to
       build/caterkiller/pipeline/<name>.s; the inputs are never modified.
"""

import os
import re
import sys
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/

SECTION_LABELS = ('SPRITEDATA', 'FONT', 'SHAPE', 'BITMAP', 'NUMGEN', 'CHRGEN', 'DIGIT', 'CHAR')
EXCLUDED_LABELS = ('FONTREF',)  # a reference table, not font bitmaps, despite the name
BITMAP_TERMS = ('sprite', 'font', 'character', 'shape', 'bitmap', 'graphics data')
CODE_TERMS = ('code', 'routine', 'subroutine', 'handler')
MNEMONICS = {
    'ADC', 'AND', 'ASL', 'BCC', 'BCS', 'BEQ', 'BIT', 'BMI', 'BNE', 'BPL', 'BRK', 'BVC',
    'BVS', 'CLC', 'CLD', 'CLI', 'CLV', 'CMP', 'CPX', 'CPY', 'DEC', 'DEX', 'DEY', 'EOR',
    'INC', 'INX', 'INY', 'JMP', 'JSR', 'LDA', 'LDX', 'LDY', 'LSR', 'NOP', 'ORA', 'PHA',
    'PHP', 'PLA', 'PLP', 'ROL', 'ROR', 'RTI', 'RTS', 'SBC', 'SEC', 'SED', 'SEI', 'STA',
    'STX', 'STY', 'TAX', 'TAY', 'TSX', 'TXA', 'TXS', 'TYA',
}
HEX_BYTE = re.compile(r'^\$([0-9A-Fa-f]{1,2})$')
BYTE_LINE = re.compile(r'^(\s*)\.BYTE\s+(.+?)(\s*;.*)?$', re.IGNORECASE)
LABEL = re.compile(r'^([A-Za-z_]\w*):')


def convert_byte_line(line):
    """Rewrite the hex values of a .BYTE line as %binary; leave other lines untouched."""
    m = BYTE_LINE.match(line)
    if not m:
        return line
    indent, values_str, comment = m.group(1), m.group(2), m.group(3) or ''

    out = []
    for value in values_str.split(','):
        h = HEX_BYTE.match(value.strip())
        if not h:
            return line  # a label reference or expression: not bitmap data
        out.append('%' + format(int(h.group(1), 16), '08b'))
    return f"{indent}.BYTE {', '.join(out)}{comment}"


def next_section_state(line, in_section):
    """Whether the lines after this one are inside a bitmap section."""
    stripped = line.strip()
    if not stripped:
        return in_section

    if stripped.startswith(';'):
        lower = stripped.lower()
        if lower.startswith('; ---') or lower.startswith('; ==='):
            if any(term in lower for term in BITMAP_TERMS):
                return True
            if any(term in lower for term in CODE_TERMS):
                return False
        return in_section

    m = LABEL.match(line)
    if m:
        label = m.group(1).upper()
        if label in EXCLUDED_LABELS:
            return False
        if any(marker in label for marker in SECTION_LABELS):
            return True

    rest = line[m.end():] if m else line
    words = rest.split(None, 1)
    if words and words[0].upper() in MNEMONICS:
        return False
    return in_section


def process_file(input_path):
    """Convert one source file; returns the number of lines rewritten."""
    with open(input_path, 'r') as f:
        lines = f.read().split('\n')

    output = []
    in_section = False
    converted = 0
    for line in lines:
        if in_section and '.BYTE' in line.upper():
            new_line = convert_byte_line(line)
            if new_line != line:
                converted += 1
            output.append(new_line)
        else:
            output.append(line)
        in_section = next_section_state(line, in_section)

    out_file = output_path(os.path.basename(input_path))
    with open(out_file, 'w') as f:
        f.write('\n'.join(output))

    print(f"Converted {converted} .BYTE lines in {input_path} -> {out_file}")
    return converted


def main():
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        source_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'source')
        files = [os.path.join(source_dir, f'level{n}.s') for n in (1, 2, 3)]

    total = sum(process_file(f) for f in files)
    print(f"\nTotal: {total} lines converted")


if __name__ == '__main__':
    main()
