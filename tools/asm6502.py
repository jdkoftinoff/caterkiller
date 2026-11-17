#!/usr/bin/env python3
"""
Simple two-pass 6502 assembler for the Caterkiller reverse engineering project.
Supports the exact syntax used in our .s files:
  - .ORG $xxxx
  - .BYTE $xx, $xx, ...
  - .WORD $xxxx, ...  (little-endian 16-bit values)
  - .INCLUDE "file.s"
  - .ALIGN $80 / .ALIGNPAGE [LABEL]  (zero-fill to the next multiple of N / next page)
  - LABEL = $xx (equates)
  - LABEL: (code labels)
  - Standard 6502 mnemonics
  - Operands: $hex, %binary, decimal, symbols, + and -, <expr / >expr (low / high byte)

Instruction sizes are fixed in pass 1 and checked in pass 2, so a zero-page
symbol defined after its first use assembles as absolute rather than shifting
every later address. Duplicate labels and moved labels are reported as errors.

No external dependencies required.
"""

import re
import sys
import os

# 6502 instruction set - (opcode, addressing_mode, bytes)
# Addressing modes: IMP, IMM, ZP, ZPX, ZPY, ABS, ABX, ABY, IND, IZX, IZY, REL
OPCODES = {
    'ADC': {'IMM': 0x69, 'ZP': 0x65, 'ZPX': 0x75, 'ABS': 0x6D, 'ABX': 0x7D, 'ABY': 0x79, 'IZX': 0x61, 'IZY': 0x71},
    'AND': {'IMM': 0x29, 'ZP': 0x25, 'ZPX': 0x35, 'ABS': 0x2D, 'ABX': 0x3D, 'ABY': 0x39, 'IZX': 0x21, 'IZY': 0x31},
    'ASL': {'IMP': 0x0A, 'ZP': 0x06, 'ZPX': 0x16, 'ABS': 0x0E, 'ABX': 0x1E},
    'BCC': {'REL': 0x90},
    'BCS': {'REL': 0xB0},
    'BEQ': {'REL': 0xF0},
    'BIT': {'ZP': 0x24, 'ABS': 0x2C},
    'BMI': {'REL': 0x30},
    'BNE': {'REL': 0xD0},
    'BPL': {'REL': 0x10},
    'BRK': {'IMP': 0x00},
    'BVC': {'REL': 0x50},
    'BVS': {'REL': 0x70},
    'CLC': {'IMP': 0x18},
    'CLD': {'IMP': 0xD8},
    'CLI': {'IMP': 0x58},
    'CLV': {'IMP': 0xB8},
    'CMP': {'IMM': 0xC9, 'ZP': 0xC5, 'ZPX': 0xD5, 'ABS': 0xCD, 'ABX': 0xDD, 'ABY': 0xD9, 'IZX': 0xC1, 'IZY': 0xD1},
    'CPX': {'IMM': 0xE0, 'ZP': 0xE4, 'ABS': 0xEC},
    'CPY': {'IMM': 0xC0, 'ZP': 0xC4, 'ABS': 0xCC},
    'DEC': {'ZP': 0xC6, 'ZPX': 0xD6, 'ABS': 0xCE, 'ABX': 0xDE},
    'DEX': {'IMP': 0xCA},
    'DEY': {'IMP': 0x88},
    'EOR': {'IMM': 0x49, 'ZP': 0x45, 'ZPX': 0x55, 'ABS': 0x4D, 'ABX': 0x5D, 'ABY': 0x59, 'IZX': 0x41, 'IZY': 0x51},
    'INC': {'ZP': 0xE6, 'ZPX': 0xF6, 'ABS': 0xEE, 'ABX': 0xFE},
    'INX': {'IMP': 0xE8},
    'INY': {'IMP': 0xC8},
    'JMP': {'ABS': 0x4C, 'IND': 0x6C},
    'JSR': {'ABS': 0x20},
    'LDA': {'IMM': 0xA9, 'ZP': 0xA5, 'ZPX': 0xB5, 'ABS': 0xAD, 'ABX': 0xBD, 'ABY': 0xB9, 'IZX': 0xA1, 'IZY': 0xB1},
    'LDX': {'IMM': 0xA2, 'ZP': 0xA6, 'ZPY': 0xB6, 'ABS': 0xAE, 'ABY': 0xBE},
    'LDY': {'IMM': 0xA0, 'ZP': 0xA4, 'ZPX': 0xB4, 'ABS': 0xAC, 'ABX': 0xBC},
    'LSR': {'IMP': 0x4A, 'ZP': 0x46, 'ZPX': 0x56, 'ABS': 0x4E, 'ABX': 0x5E},
    'NOP': {'IMP': 0xEA},
    'ORA': {'IMM': 0x09, 'ZP': 0x05, 'ZPX': 0x15, 'ABS': 0x0D, 'ABX': 0x1D, 'ABY': 0x19, 'IZX': 0x01, 'IZY': 0x11},
    'PHA': {'IMP': 0x48},
    'PHP': {'IMP': 0x08},
    'PLA': {'IMP': 0x68},
    'PLP': {'IMP': 0x28},
    'ROL': {'IMP': 0x2A, 'ZP': 0x26, 'ZPX': 0x36, 'ABS': 0x2E, 'ABX': 0x3E},
    'ROR': {'IMP': 0x6A, 'ZP': 0x66, 'ZPX': 0x76, 'ABS': 0x6E, 'ABX': 0x7E},
    'RTI': {'IMP': 0x40},
    'RTS': {'IMP': 0x60},
    'SBC': {'IMM': 0xE9, 'ZP': 0xE5, 'ZPX': 0xF5, 'ABS': 0xED, 'ABX': 0xFD, 'ABY': 0xF9, 'IZX': 0xE1, 'IZY': 0xF1},
    'SEC': {'IMP': 0x38},
    'SED': {'IMP': 0xF8},
    'SEI': {'IMP': 0x78},
    'STA': {'ZP': 0x85, 'ZPX': 0x95, 'ABS': 0x8D, 'ABX': 0x9D, 'ABY': 0x99, 'IZX': 0x81, 'IZY': 0x91},
    'STX': {'ZP': 0x86, 'ZPY': 0x96, 'ABS': 0x8E},
    'STY': {'ZP': 0x84, 'ZPX': 0x94, 'ABS': 0x8C},
    'TAX': {'IMP': 0xAA},
    'TAY': {'IMP': 0xA8},
    'TSX': {'IMP': 0xBA},
    'TXA': {'IMP': 0x8A},
    'TXS': {'IMP': 0x9A},
    'TYA': {'IMP': 0x98},
}

class Assembler:
    def __init__(self):
        self.symbols = {}
        self.output = bytearray()
        self.output_dict = {}   # addr -> byte, supports backward .ORG
        self.org = 0
        self.pc = 0
        self.lines = []          # expanded source text, one entry per line
        self.locations = []      # (file, line) for each entry of self.lines
        self.modes = {}          # line index -> addressing mode chosen in pass 1
        self.errors = []
        self.warnings = []
        self.pass_num = 0
        self._line = 0           # line currently being assembled, for errors raised while parsing values

    def _loc(self, line_num):
        """Human-readable location for error messages."""
        if 0 < line_num <= len(self.locations):
            fname, ln = self.locations[line_num - 1]
            return f"{fname}:{ln}"
        return f"Line {line_num}"

    def _error(self, line_num, msg):
        text = f"{self._loc(line_num)}: {msg}"
        if text not in self.errors:
            self.errors.append(text)

    def _emit(self, data):
        """Write bytes at current PC into the output dict."""
        for i, b in enumerate(data):
            addr = self.pc + i
            if addr in self.output_dict and self.output_dict[addr] != (b & 0xFF):
                self.warnings.append(
                    f"ORG overlap at ${addr:04X}: overwriting ${self.output_dict[addr]:02X} with ${b & 0xFF:02X}"
                )
            self.output_dict[addr] = b & 0xFF

    def _int(self, digits, base, text):
        """int() that reports a malformed literal as an assembly error instead of a traceback."""
        try:
            return int(digits, base)
        except ValueError:
            self._error(self._line, f"Malformed number: {text}")
            return None

    def parse_value(self, s):
        """Parse a numeric value or symbol reference."""
        s = s.strip()

        # Only + and - are supported; name anything else so the error is not "undefined symbol"
        m = re.search(r'[*/&|^~]', s)
        if m:
            self._error(self._line, f"Unsupported operator '{m.group(0)}' in expression: {s}")
            return None

        # Handle expressions with + or -
        if '+' in s or '-' in s[1:]:  # s[1:] to allow negative numbers
            # Simple expression parsing
            parts = re.split(r'([+-])', s)
            result = 0
            op = '+'
            for part in parts:
                part = part.strip()
                if part == '+':
                    op = '+'
                elif part == '-':
                    op = '-'
                elif part:
                    val = self.parse_value(part)
                    if val is None:
                        return None
                    if op == '+':
                        result += val
                    else:
                        result -= val
            return result

        # Hex
        if s.startswith('$'):
            return self._int(s[1:], 16, s)

        # Binary
        if s.startswith('%'):
            return self._int(s[1:], 2, s)

        # Decimal
        if s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
            return int(s)

        # Low byte of symbol
        if s.startswith('<'):
            val = self.parse_value(s[1:])
            return val & 0xFF if val is not None else None

        # High byte of symbol
        if s.startswith('>'):
            val = self.parse_value(s[1:])
            return (val >> 8) & 0xFF if val is not None else None

        # Symbol lookup
        if s in self.symbols:
            return self.symbols[s]

        # Unknown symbol (will be resolved in pass 2)
        return None

    def parse_operand(self, operand, mnemonic):
        """Parse operand and return (addressing_mode, value, size)."""

        if not operand:
            return ('IMP', 0, 1)

        operand = operand.strip()

        # Accumulator (same as implicit for ASL, LSR, ROL, ROR)
        if operand.upper() == 'A':
            return ('IMP', 0, 1)

        # Immediate: #$xx or #value
        m = re.match(r'^#(.+)$', operand)
        if m:
            val = self.parse_value(m.group(1))
            return ('IMM', val, 2)

        # Indirect indexed: ($xx),Y
        m = re.match(r'^\((.+)\),Y$', operand, re.IGNORECASE)
        if m:
            val = self.parse_value(m.group(1))
            return ('IZY', val, 2)

        # Indexed indirect: ($xx,X)
        m = re.match(r'^\((.+),X\)$', operand, re.IGNORECASE)
        if m:
            val = self.parse_value(m.group(1))
            return ('IZX', val, 2)

        # Indirect: ($xxxx)
        m = re.match(r'^\((.+)\)$', operand)
        if m:
            val = self.parse_value(m.group(1))
            return ('IND', val, 3)

        # Indexed by X: $xxxx,X or symbol,X
        m = re.match(r'^(.+),X$', operand, re.IGNORECASE)
        if m:
            val = self.parse_value(m.group(1))
            # Decide ZPX vs ABX based on value
            if val is not None and val < 256 and mnemonic in OPCODES and 'ZPX' in OPCODES[mnemonic]:
                return ('ZPX', val, 2)
            return ('ABX', val, 3)

        # Indexed by Y: $xxxx,Y or symbol,Y
        m = re.match(r'^(.+),Y$', operand, re.IGNORECASE)
        if m:
            val = self.parse_value(m.group(1))
            # Decide ZPY vs ABY based on value
            if val is not None and val < 256 and mnemonic in OPCODES and 'ZPY' in OPCODES[mnemonic]:
                return ('ZPY', val, 2)
            return ('ABY', val, 3)

        # Branch instructions use relative addressing
        if mnemonic in ['BCC', 'BCS', 'BEQ', 'BMI', 'BNE', 'BPL', 'BVC', 'BVS']:
            val = self.parse_value(operand)
            return ('REL', val, 2)

        # Plain value - zero page or absolute
        val = self.parse_value(operand)
        if val is not None and val < 256 and mnemonic in OPCODES and 'ZP' in OPCODES[mnemonic]:
            return ('ZP', val, 2)

        return ('ABS', val, 3)

    def assemble_instruction(self, mnemonic, operand, line_num):
        """Assemble a single instruction, return bytes."""

        mnemonic = mnemonic.upper()

        if mnemonic not in OPCODES:
            self._error(line_num, f"Unknown mnemonic: {mnemonic}")
            return None

        mode, value, size = self.parse_operand(operand, mnemonic)

        # Handle unresolved symbols in pass 1
        if value is None and self.pass_num == 1:
            # Use placeholder, will be resolved in pass 2
            value = 0

        if value is None and self.pass_num == 2:
            self._error(line_num, f"Undefined symbol in: {operand}")
            return None

        # Check if addressing mode is valid for this instruction
        if mode not in OPCODES[mnemonic]:
            # Try alternate modes
            if mode == 'ZP' and 'ABS' in OPCODES[mnemonic]:
                mode = 'ABS'
                size = 3
            elif mode == 'ZPX' and 'ABX' in OPCODES[mnemonic]:
                mode = 'ABX'
                size = 3
            elif mode == 'ZPY' and 'ABY' in OPCODES[mnemonic]:
                mode = 'ABY'
                size = 3
            else:
                self._error(line_num, f"Invalid addressing mode {mode} for {mnemonic}")
                return None

        # Freeze the addressing mode chosen in pass 1 so instruction sizes cannot
        # change between passes (a forward-referenced zero-page symbol is unknown in
        # pass 1 and would otherwise shrink from absolute to zero page in pass 2).
        if self.pass_num == 1:
            self.modes[line_num] = mode
        else:
            frozen = self.modes.get(line_num, mode)
            if frozen != mode:
                widen = {('ZP', 'ABS'), ('ZPX', 'ABX'), ('ZPY', 'ABY')}
                if (mode, frozen) in widen:
                    mode, size = frozen, 3
                else:
                    self._error(line_num, f"Phase error: {mnemonic} sized as {frozen} in pass 1 but {mode} in pass 2")
                    return None

        opcode = OPCODES[mnemonic][mode]

        # An immediate operand must fit in one byte; silently truncating a 16-bit
        # address (LDA #TBL instead of LDA #<TBL) is a classic hard-to-find bug.
        if mode == 'IMM' and self.pass_num == 2 and not -128 <= value <= 255:
            self._error(line_num, f"Immediate value out of range (0-255): {operand} = {value}")
            return None

        # Calculate relative offset for branch instructions
        if mode == 'REL':
            if value is not None:
                offset = value - (self.pc + 2)
                # Only check range in pass 2 (pass 1 may have placeholder values)
                if self.pass_num == 2:
                    if offset < -128 or offset > 127:
                        self._error(line_num, f"Branch out of range: {offset}")
                        return None
                value = offset & 0xFF

        # Build instruction bytes
        result = bytearray([opcode])
        if size == 2:
            result.append(value & 0xFF)
        elif size == 3:
            result.append(value & 0xFF)
            result.append((value >> 8) & 0xFF)

        return result

    def parse_bytes(self, args, line_num=0):
        """Parse .BYTE directive arguments."""
        result = bytearray()
        for arg in args.split(','):
            arg = arg.strip()
            if not arg:
                continue
            val = self.parse_value(arg)
            if val is None and self.pass_num == 2:
                self._error(line_num, f"Undefined value: {arg}")
                return None
            elif val is None:
                val = 0
            result.append(val & 0xFF)
        return result

    def parse_words(self, args, line_num=0):
        """Parse .WORD directive arguments into little-endian 16-bit values."""
        result = bytearray()
        for arg in args.split(','):
            arg = arg.strip()
            if not arg:
                continue
            val = self.parse_value(arg)
            if val is None and self.pass_num == 2:
                self._error(line_num, f"Undefined value: {arg}")
                return None
            elif val is None:
                val = 0
            if self.pass_num == 2 and not -32768 <= val <= 65535:
                self._error(line_num, f".WORD value out of range: {arg} = {val}")
                return None
            result.append(val & 0xFF)
            result.append((val >> 8) & 0xFF)
        return result

    def _define_label(self, label, addr, line_num):
        """Define a code label: duplicates are errors in pass 1, moves are errors in pass 2."""
        if self.pass_num == 1:
            if label in self.symbols:
                self._error(line_num, f"Duplicate label: {label}")
                return
        elif label in self.symbols and self.symbols[label] != addr:
            self._error(line_num, f"Phase error: {label} was ${self.symbols[label]:04X} in pass 1, ${addr:04X} in pass 2")
            return
        self.symbols[label] = addr

    def assemble_line(self, line, line_num):
        """Assemble a single line of source code."""
        self._line = line_num

        # Remove comments
        if ';' in line:
            line = line[:line.index(';')]

        line = line.strip()
        if not line:
            return

        # Handle equates: LABEL = value
        m = re.match(r'^(\w+)\s*=\s*(.+)$', line)
        if m:
            label, value = m.groups()
            if self.pass_num == 1 and label in self.symbols:
                self._error(line_num, f"Symbol redefined: {label}")
                return
            val = self.parse_value(value)
            if val is not None:
                self.symbols[label] = val
            elif self.pass_num == 2:
                self._error(line_num, f"Cannot resolve: {value}")
            return

        # Handle labels: LABEL:
        if ':' in line:
            parts = line.split(':', 1)
            label = parts[0].strip()
            if label and not label.startswith('.'):
                self._define_label(label, self.pc, line_num)
            line = parts[1].strip() if len(parts) > 1 else ''
            if not line:
                return

        # Parse the rest of the line
        parts = line.split(None, 1)
        if not parts:
            return

        directive_or_mnemonic = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ''

        # Handle .ALIGN directive: pad with zeros to the next multiple of N.
        # Syntax: .ALIGN $80
        if directive_or_mnemonic == '.ALIGN':
            n = self.parse_value(args.strip())
            if n is None:
                self._error(line_num, f".ALIGN value must be defined before this line: {args.strip()}")
                return
            if n <= 0:
                self._error(line_num, ".ALIGN needs a positive value")
                return
            aligned = ((self.pc + n - 1) // n) * n
            if self.pass_num == 2:
                padding = aligned - self.pc
                if padding > 0:
                    self._emit(bytearray(padding))
            self.pc = aligned
            return

        # Handle .ALIGNPAGE directive: pad to the next 256-byte boundary.
        # Syntax: .ALIGNPAGE [SYMBOL_NAME]   (the optional symbol is defined at the aligned address)
        if directive_or_mnemonic == '.ALIGNPAGE':
            label = args.strip()
            aligned = ((self.pc + 255) // 256) * 256  # round up to next 256-byte page
            if label:
                self._define_label(label, aligned, line_num)
            if self.pass_num == 2:
                padding = aligned - self.pc
                if padding > 0:
                    self._emit(bytearray(padding))
            self.pc = aligned
            return

        # Handle .ORG directive
        if directive_or_mnemonic == '.ORG':
            val = self.parse_value(args.strip())
            if val is None:
                # Both passes need the location counter, so a forward reference cannot work here
                self._error(line_num, f".ORG value must be defined before this line: {args.strip()}")
                return
            if self.pass_num == 2 and val < self.org:
                self._error(line_num, f"ORG ${val:04X} before start ${self.org:04X}")
                return
            # Backward or forward: dict-based output handles both
            self.pc = val
            if self.org == 0:
                self.org = val
            return

        # Handle .BYTE / .WORD directives
        if directive_or_mnemonic in ('.BYTE', '.WORD'):
            if directive_or_mnemonic == '.BYTE':
                data = self.parse_bytes(args, line_num)
            else:
                data = self.parse_words(args, line_num)
            if data:
                if self.pass_num == 2:
                    self._emit(data)
                self.pc += len(data)
            return

        # Handle instruction
        if directive_or_mnemonic in OPCODES:
            code = self.assemble_instruction(directive_or_mnemonic, args, line_num)
            if code:
                if self.pass_num == 2:
                    self._emit(code)
                self.pc += len(code)
            elif self.pass_num == 1:
                # Estimate size for pass 1
                _, _, size = self.parse_operand(args, directive_or_mnemonic)
                self.pc += size
            return

        self._error(line_num, f"Unknown directive or mnemonic: {directive_or_mnemonic}")

    def _expand_includes(self, lines, source_dir, source_name, depth=0):
        """Recursively expand .INCLUDE directives, returning (file, line_num, text) tuples."""
        if depth > 10:
            self.errors.append(f"{source_name}: Too many nested .INCLUDE levels (max 10)")
            return []
        result = []
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if ';' in stripped:
                stripped = stripped[:stripped.index(';')].strip()
            m = re.match(r'^\.INCLUDE\s+["\']?(.+?)["\']?\s*$', stripped, re.IGNORECASE)
            if m:
                inc_path = m.group(1)
                if not os.path.isabs(inc_path):
                    inc_path = os.path.join(source_dir, inc_path)
                inc_path = os.path.normpath(inc_path)
                try:
                    with open(inc_path, 'r', encoding='utf-8') as f:
                        inc_lines = f.read().split('\n')
                    inc_dir = os.path.dirname(inc_path)
                    result.extend(self._expand_includes(inc_lines, inc_dir, os.path.basename(inc_path), depth + 1))
                except FileNotFoundError:
                    self.errors.append(f"{source_name}:{line_num}: Include file not found: {inc_path}")
            else:
                result.append((source_name, line_num, line))
        return result

    def assemble(self, source, source_dir='.', source_name='<source>'):
        """Assemble source code (two-pass). Returns bytes, or None with self.errors filled in."""

        raw_lines = source.split('\n')
        self.errors = []
        self.warnings = []
        self.symbols = {}
        self.modes = {}
        expanded = self._expand_includes(raw_lines, source_dir, source_name)
        self.lines = [text for _, _, text in expanded]
        self.locations = [(fname, ln) for fname, ln, _ in expanded]

        if self.errors:
            return None

        # Pass 1: Collect symbols
        self.pass_num = 1
        self.org = 0
        self.pc = 0

        for line_num, line in enumerate(self.lines, 1):
            self.assemble_line(line, line_num)

        if self.errors:
            return None

        # Pass 2: Generate code into dict (supports backward .ORG)
        self.pass_num = 2
        self.pc = self.org
        self.output_dict = {}

        for line_num, line in enumerate(self.lines, 1):
            self.assemble_line(line, line_num)

        if self.errors:
            return None

        # Build contiguous output from dict, filling gaps with 0
        if self.output_dict:
            max_addr = max(self.output_dict.keys())
            size = max_addr - self.org + 1
            self.output = bytearray(size)
            for addr, byte in self.output_dict.items():
                self.output[addr - self.org] = byte
        else:
            self.output = bytearray()

        return bytes(self.output)


def main():
    if len(sys.argv) < 2:
        print("Usage: asm6502.py <source.s> [output.bin]")
        print("       asm6502.py --test")
        sys.exit(1)

    if sys.argv[1] == '--test':
        print("The test suite lives in tests/; run: make test")
        return

    source_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(source_file)[0] + '.bin'

    print(f"Assembling {source_file}...")

    with open(source_file, 'r', encoding='utf-8') as f:
        source = f.read()

    source_dir = os.path.dirname(os.path.abspath(source_file))
    asm = Assembler()
    result = asm.assemble(source, source_dir, os.path.basename(source_file))

    if result is None:
        print(f"\nAssembly failed with {len(asm.errors)} error(s):")
        for err in asm.errors[:20]:  # Show first 20 errors
            print(f"  {err}")
        if len(asm.errors) > 20:
            print(f"  ... and {len(asm.errors) - 20} more errors")
        sys.exit(1)

    with open(output_file, 'wb') as f:
        f.write(result)

    if asm.warnings:
        print(f"\n{len(asm.warnings)} warning(s):")
        for w in asm.warnings[:10]:
            print(f"  {w}")
        if len(asm.warnings) > 10:
            print(f"  ... and {len(asm.warnings) - 10} more")

    print(f"Output: {output_file}")
    print(f"Size: {len(result)} bytes")
    print(f"Start: ${asm.org:04X}")
    print(f"End: ${asm.org + len(result) - 1:04X}")


if __name__ == '__main__':
    main()
