#!/usr/bin/env python3
"""Reformat 6502 assembly source files.

Usage: python3 fmt6502.py [options] input.s [output.s]

If output is omitted, prints to stdout. Use -i for in-place editing.

Options:
  -c COL    Column for opcodes/directives (default: 8)
  -m COL    Column for end-of-line comments (default: 40)
  -e COL    Column for '=' in symbol assignments (default: 17)
  -i        Edit file in place
"""

import sys

OPCODES = {
    'ADC','AND','ASL','BCC','BCS','BEQ','BIT','BMI','BNE','BPL','BRK','BVC',
    'BVS','CLC','CLD','CLI','CLV','CMP','CPX','CPY','DEC','DEX','DEY','EOR',
    'INC','INX','INY','JMP','JSR','LDA','LDX','LDY','LSR','NOP','ORA','PHA',
    'PHP','PLA','PLP','ROL','ROR','RTI','RTS','SBC','SEC','SED','SEI','STA',
    'STX','STY','TAX','TAY','TSX','TXA','TXS','TYA',
}

DIRECTIVES = {
    '.BYTE', '.WORD', '.ORG', '.ALIGNPAGE', '.ALIGN', '.INCLUDE',
}


def is_instruction(word):
    return word.upper() in OPCODES or word.upper() in DIRECTIVES


def split_comment(line):
    """Split a line into code and comment parts, respecting quoted strings."""
    in_quote = False
    quote_char = None
    for i, ch in enumerate(line):
        if in_quote:
            if ch == quote_char:
                in_quote = False
        elif ch in ('"', "'"):
            in_quote = True
            quote_char = ch
        elif ch == ';':
            return line[:i], line[i + 1:]  # return comment text without leading ;
    return line, None


def pad_to(s, col):
    """Pad string s with spaces to reach at least column col."""
    if len(s) >= col:
        return s + ' '
    return s + ' ' * (col - len(s))


def format_line(line, opcode_col, comment_col, eq_col):
    # Preserve blank lines
    if not line.strip():
        return ''

    stripped = line.lstrip()

    # Full-line comments (start with ;)
    if stripped.startswith(';'):
        return stripped

    has_leading_space = len(line) > 0 and line[0] in (' ', '\t')

    # Split code from comment
    code_part, comment_text = split_comment(line)
    code_part = code_part.rstrip()
    code_stripped = code_part.strip()

    if not code_stripped:
        # Comment-only line (shouldn't reach here but just in case)
        if comment_text is not None:
            return '; ' + comment_text.strip()
        return ''

    # --- Symbol assignment: NAME = VALUE ---
    if '=' in code_stripped and not is_instruction(code_stripped.split()[0]):
        parts = code_stripped.split('=', 1)
        name = parts[0].rstrip()
        value = parts[1].strip()
        result = pad_to(name, eq_col) + '= ' + value
        if comment_text is not None:
            result = pad_to(result, comment_col) + '; ' + comment_text.strip()
        return result.rstrip()

    # Split off the first word; the operand keeps its own spacing so quoted
    # strings such as .INCLUDE "two  spaces.s" are not altered.
    parts = code_stripped.split(None, 1)
    first = parts[0]
    rest_text = parts[1].strip() if len(parts) > 1 else ''

    # --- Label at column 0 (no leading whitespace, not an instruction) ---
    if not has_leading_space and not is_instruction(first):
        label = first

        if not rest_text and comment_text is None:
            return label

        if not rest_text:
            result = label
            result = pad_to(result, comment_col) + '; ' + comment_text.strip()
            return result.rstrip()

        # Label + instruction [+ operand]
        rest = rest_text.split(None, 1)
        instr = rest[0]
        operand = rest[1].strip() if len(rest) > 1 else ''

        result = label
        result = pad_to(result, opcode_col) + instr
        if operand:
            result += ' ' + operand
        if comment_text is not None:
            result = pad_to(result, comment_col) + '; ' + comment_text.strip()
        return result.rstrip()

    # --- Indented instruction line ---
    instr = first
    operand = rest_text

    result = ' ' * opcode_col + instr
    if operand:
        result += ' ' + operand
    if comment_text is not None:
        result = pad_to(result, comment_col) + '; ' + comment_text.strip()
    return result.rstrip()


def format_file(text, opcode_col=8, comment_col=40, eq_col=17):
    lines = text.split('\n')
    result = []
    for line in lines:
        result.append(format_line(line, opcode_col, comment_col, eq_col))
    return '\n'.join(result)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Reformat 6502 assembly source')
    parser.add_argument('input', help='Input .s file')
    parser.add_argument('output', nargs='?', help='Output file (default: stdout)')
    parser.add_argument('-c', type=int, default=8, help='Opcode column (default: 8)')
    parser.add_argument('-m', type=int, default=40, help='Comment column (default: 40)')
    parser.add_argument('-e', type=int, default=17, help='Equals column for assignments (default: 17)')
    parser.add_argument('-i', action='store_true', help='Edit in place')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    formatted = format_file(text, opcode_col=args.c, comment_col=args.m, eq_col=args.e)

    if args.i:
        with open(args.input, 'w', encoding='utf-8') as f:
            f.write(formatted)
    elif args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(formatted)
    else:
        sys.stdout.write(formatted)


if __name__ == '__main__':
    main()
