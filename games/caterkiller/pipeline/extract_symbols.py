#!/usr/bin/env python3
"""Extract the embedded assembler symbol table from the level1 binary."""

import os
import sys
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/


def extract_symbols(binfile):
    """Parse the symbol table the original assembler left inside level1.bin.

    The table position is specific to level1.bin (loaded at $4000): it runs from
    $605A to $66E8. Format: [length_byte] [name_bytes...] [addr_lo] [addr_hi],
    where the low nibble of length_byte is the name length and the high nibble
    holds type flags.
    """
    with open(binfile, 'rb') as f:
        data = f.read()
    load_addr = 0x4000

    sym_start = 0x605A - load_addr  # file offset
    sym_end = 0x66E9 - load_addr
    if len(data) < sym_end:
        raise SystemExit(f"{binfile} is {len(data)} bytes; this script only understands "
                         f"level1.bin, which holds the symbol table at $605A-$66E8")

    symbols = []
    pos = sym_start

    while pos < sym_end:
        tag = data[pos]
        name_len = tag & 0x0F

        if name_len == 0:
            # Could be a separator or end marker
            pos += 1
            continue

        if pos + 1 + name_len + 2 > len(data):
            break

        name_bytes = data[pos+1 : pos+1+name_len]
        # Check if all name bytes are printable ASCII
        if not all(0x20 <= b < 0x7F for b in name_bytes):
            # Try name_len - 1
            if name_len > 1:
                name_bytes_alt = data[pos+1 : pos+name_len]
                if all(0x20 <= b < 0x7F for b in name_bytes_alt):
                    # The actual name is 1 shorter; last "name" byte is addr_lo
                    actual_len = name_len - 1
                    name = bytes(name_bytes_alt).decode('ascii')
                    addr_lo = data[pos + 1 + actual_len]
                    addr_hi = data[pos + 1 + actual_len + 1]
                    addr = addr_lo | (addr_hi << 8)
                    symbols.append((name, addr, tag, pos + load_addr))
                    pos += 1 + actual_len + 2
                    continue
            pos += 1
            continue

        name = bytes(name_bytes).decode('ascii')
        addr_lo = data[pos + 1 + name_len]
        addr_hi = data[pos + 1 + name_len + 1]
        addr = addr_lo | (addr_hi << 8)

        symbols.append((name, addr, tag, pos + load_addr))
        pos += 1 + name_len + 2

    return symbols

def main():
    default_bin = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'original', 'level1.bin')
    binfile = sys.argv[1] if len(sys.argv) > 1 else default_bin
    symbols = extract_symbols(binfile)

    # Sort by address
    symbols.sort(key=lambda s: s[1])

    # Print
    zp_vars = []
    labels = []
    for name, addr, tag, table_pos in symbols:
        if addr < 0x100:
            zp_vars.append((name, addr, tag))
            print(f"  ZP  ${addr:02X}     {name:<16s}  (tag=${tag:02X} at ${table_pos:04X})")
        else:
            labels.append((name, addr, tag))
            print(f"  LBL ${addr:04X}   {name:<16s}  (tag=${tag:02X} at ${table_pos:04X})")

    print(f"\nTotal: {len(symbols)} symbols ({len(zp_vars)} zero-page, {len(labels)} labels)")

if __name__ == '__main__':
    main()
