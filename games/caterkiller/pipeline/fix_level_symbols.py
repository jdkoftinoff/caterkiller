#!/usr/bin/env python3
"""
Fix undefined symbols in level1.s and level2.s (historical post-processing step).

The generated sources referenced a few symbols the disassembler never defined:
routines named in the level1 symbol table whose addresses fell inside data
regions, and branch targets that land inside data tables. This script:
1. Adds a label where the address is the start of a line of code or data
2. Adds equates at the top of the file for addresses that are not

Input is read from ../source/, output is written to build/caterkiller/pipeline/
(the checked-in sources already contain these fixes). The result is assembled
and compared against the original binary.
"""

import re
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', '..', '..', 'tools'))
SOURCE_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'source'))
ORIGINAL_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'original'))
sys.path.insert(0, TOOLS_DIR)

from asm6502 import Assembler
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/

# Symbols the assembler reported as undefined after generation, with their addresses
MISSING = {
    'level1': {
        'NUMGEN': 0x8A00,
        'SHOWNUM': 0x7256,
        'PLACEFOOD2': 0x73F4,
        'CATHITCHECK': 0x756F,
        'REDRAWSCENE': 0x727C,
        'L_6F0C': 0x6F0C,
        'L_7FCC': 0x7FCC,
        'L_80A9': 0x80A9,
        'L_80AB': 0x80AB,
        'L_80AD': 0x80AD,
    },
    'level2': {
        'NUMGEN': 0x8A00,
        'L_7FCC': 0x7FCC,
        'L_80A9': 0x80A9,
        'L_80AB': 0x80AB,
        'L_80AD': 0x80AD,
    },
}


def find_label_locations(lines):
    """Run assembler pass 1 over the lines. Returns (symbols, address -> line index)."""
    asm = Assembler()
    asm.lines = list(lines)
    asm.pass_num = 1
    asm.org = 0
    asm.pc = 0

    addr_to_line = {}
    for idx, line in enumerate(asm.lines):
        old_pc = asm.pc
        asm.assemble_line(line, idx + 1)
        if asm.pc != old_pc:
            addr_to_line[old_pc] = idx
    return asm.symbols, addr_to_line


def add_equates(lines, equates):
    """Insert an equate block just before the first .ORG line."""
    insert_at = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith(';') and '=' not in stripped and '.ORG' in stripped.upper():
            insert_at = i
            break

    block = ['', '; Missing symbol definitions (added by fix script)']
    block += [f'{name:16} = ${addr:04X}' for name, addr in sorted(equates.items(), key=lambda x: x[1])]
    block.append('')
    return lines[:insert_at] + block + lines[insert_at:]


def fix_level(name):
    """Add the missing symbols of one level and write the result under build/."""
    source_file = os.path.join(SOURCE_DIR, f'{name}.s')
    with open(source_file, 'r') as f:
        lines = f.read().split('\n')

    symbols, addr_to_line = find_label_locations(lines)

    as_label = {}
    as_equate = {}
    for sym, addr in MISSING[name].items():
        if sym in symbols:
            print(f"  {sym} already defined at ${symbols[sym]:04X}")
        elif addr in addr_to_line:
            as_label[sym] = addr_to_line[addr]
        else:
            as_equate[sym] = addr

    print(f"\n{name} fix plan:")
    print(f"  Add as labels:  {sorted(as_label)}")
    print(f"  Add as equates: {sorted(as_equate)}")

    # Insert labels bottom-up so earlier line indices stay valid
    for sym, idx in sorted(as_label.items(), key=lambda x: -x[1]):
        line = lines[idx]
        if re.match(r'^\w+:', line):
            print(f"  {sym}: line {idx + 1} already has a label, adding an equate instead")
            as_equate[sym] = MISSING[name][sym]
        elif line[:1] in (' ', '\t'):
            lines[idx:idx + 1] = [f'{sym}:', line]
        else:
            lines[idx] = f'{sym}: {line.lstrip()}'

    if as_equate:
        lines = add_equates(lines, as_equate)

    text = '\n'.join(lines)
    out_file = output_path(f'{name}.s')
    with open(out_file, 'w') as f:
        f.write(text)
    print(f"  Wrote {out_file}")

    verify(name, text)


def verify(name, source):
    """Assemble the fixed source and compare it with the original binary."""
    asm = Assembler()
    result = asm.assemble(source, source_dir=SOURCE_DIR, source_name=f'{name}.s')

    if result is None:
        print(f"  {name}: assembly failed with {len(asm.errors)} error(s):")
        for err in asm.errors[:10]:
            print(f"    {err}")
        if len(asm.errors) > 10:
            print(f"    ... and {len(asm.errors) - 10} more")
        return

    with open(os.path.join(ORIGINAL_DIR, f'{name}.bin'), 'rb') as f:
        original = f.read()

    if result == original:
        print(f"  {name}: MATCH - identical to the original")
        return

    print(f"  {name}: MISMATCH (original {len(original)} bytes, assembled {len(result)} bytes)")
    for i in range(min(len(result), len(original))):
        if result[i] != original[i]:
            print(f"    first difference at ${asm.org + i:04X}")
            break


def main():
    for name in ('level1', 'level2'):
        fix_level(name)
        print()


if __name__ == '__main__':
    main()
