"""Tests for the Python tools in tools/. Run with: make test  (or python3 -m unittest discover -s tests)."""

import os
import re
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, 'tools')
CK = os.path.join(REPO, 'games', 'caterkiller')
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(CK, 'pipeline'))

import asm6502      # noqa: E402
import disasm6502   # noqa: E402
import extract_dos33  # noqa: E402
import fmt6502      # noqa: E402
import _guard       # noqa: E402


def assemble(src, **kw):
    asm = asm6502.Assembler()
    out = asm.assemble(src, **kw)
    return out, asm


class AssemblerTests(unittest.TestCase):

    def test_basic_encoding(self):
        out, asm = assemble("        .ORG $6000\n        LDA #$01\n        STA $10\n        JMP LOOP\nLOOP:   INX\n        BNE LOOP\n        RTS\n")
        self.assertEqual(out, bytes([0xA9, 0x01, 0x85, 0x10, 0x4C, 0x07, 0x60, 0xE8, 0xD0, 0xFD, 0x60]))

    def test_forward_zero_page_reference_keeps_sizes_stable(self):
        # ZPVAR is unknown in pass 1, so the LDA must stay absolute and DONE must not move.
        out, asm = assemble("        .ORG $6000\n        LDA ZPVAR\n        JMP DONE\nDONE:   RTS\nZPVAR   = $10\n")
        self.assertEqual(asm.errors, [])
        self.assertEqual(out[:3], bytes([0xAD, 0x10, 0x00]))        # absolute LDA
        self.assertEqual(out[3:6], bytes([0x4C, 0x06, 0x60]))        # JMP $6006
        self.assertEqual(out[6], 0x60)                               # RTS really is at $6006

    def test_duplicate_label_is_an_error(self):
        out, asm = assemble("        .ORG $6000\nL1:     NOP\n        JMP L1\nL1:     RTS\n")
        self.assertIsNone(out)
        self.assertTrue(any('Duplicate label: L1' in e for e in asm.errors), asm.errors)

    def test_symbol_redefinition_is_an_error(self):
        out, asm = assemble("FOO = 1\nFOO = 2\n        .ORG $6000\n        LDA #FOO\n")
        self.assertIsNone(out)
        self.assertTrue(any('Symbol redefined: FOO' in e for e in asm.errors), asm.errors)

    def test_unsupported_operator_is_named(self):
        out, asm = assemble("        .ORG $6000\n        LDA #FOO*2\nFOO = 3\n")
        self.assertIsNone(out)
        self.assertTrue(any("Unsupported operator '*'" in e for e in asm.errors), asm.errors)

    def test_low_high_byte_and_expressions(self):
        out, asm = assemble("        .ORG $6000\nTBL:    .BYTE 1, 2\n        LDA #<TBL\n        LDA #>TBL\n        LDA TBL+2-1\n")
        self.assertEqual(out[2:4], bytes([0xA9, 0x00]))
        self.assertEqual(out[4:6], bytes([0xA9, 0x60]))
        self.assertEqual(out[6:9], bytes([0xAD, 0x01, 0x60]))

    def test_align_and_alignpage_zero_fill(self):
        out, asm = assemble("        .ORG $6000\n        NOP\n        .ALIGN $80\nA:      NOP\n        .ALIGNPAGE B\n        NOP\n")
        self.assertEqual(asm.symbols['A'], 0x6080)
        self.assertEqual(asm.symbols['B'], 0x6100)
        self.assertEqual(len(out), 0x101)
        self.assertEqual(out[1:0x80], bytes(0x7F))

    def test_forward_org_leaves_zero_gap(self):
        out, asm = assemble("        .ORG $6000\n        NOP\n        .ORG $6010\n        RTS\n")
        self.assertEqual(out, bytes([0xEA]) + bytes(15) + bytes([0x60]))

    def test_word_directive_is_little_endian(self):
        out, asm = assemble("        .ORG $6000\nTBL:    .WORD $1234, TBL, 5\n")
        self.assertEqual(asm.errors, [])
        self.assertEqual(out, bytes([0x34, 0x12, 0x00, 0x60, 0x05, 0x00]))

    def test_immediate_out_of_range_is_an_error(self):
        out, asm = assemble("        .ORG $6000\nTBL:    .BYTE 1\n        LDA #TBL\n")
        self.assertIsNone(out)
        self.assertTrue(any('Immediate value out of range' in e for e in asm.errors), asm.errors)
        out, asm = assemble("        .ORG $6000\n        LDA #-1\n        LDA #255\n")
        self.assertEqual(out, bytes([0xA9, 0xFF, 0xA9, 0xFF]))

    def test_org_with_undefined_symbol_is_an_error(self):
        out, asm = assemble("        .ORG $6000\n        NOP\n        .ORG NOWHERE\n        RTS\n")
        self.assertIsNone(out)
        self.assertTrue(any('.ORG value must be defined' in e for e in asm.errors), asm.errors)

    def test_malformed_number_is_reported_not_raised(self):
        out, asm = assemble("        .ORG $6000\n        LDA #$G1\n        .BYTE %012\n")
        self.assertIsNone(out)
        self.assertTrue(any(e.startswith('<source>:2:') and 'Malformed number: $G1' in e for e in asm.errors), asm.errors)
        self.assertTrue(any(e.startswith('<source>:3:') and 'Malformed number: %012' in e for e in asm.errors), asm.errors)

    def test_branch_out_of_range(self):
        out, asm = assemble("        .ORG $6000\n        BNE FAR\n" + "        NOP\n" * 200 + "FAR:    RTS\n")
        self.assertIsNone(out)
        self.assertTrue(any('Branch out of range' in e for e in asm.errors), asm.errors)

    def test_include_errors_report_file_and_line(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'inc.s'), 'w', encoding='utf-8') as f:
                f.write("        NOP\n        BOGUS\n")
            out, asm = assemble('        .ORG $6000\n        .INCLUDE "inc.s"\n', source_dir=d, source_name='main.s')
        self.assertIsNone(out)
        self.assertTrue(any(e.startswith('inc.s:2:') for e in asm.errors), asm.errors)

    def test_missing_include_is_reported(self):
        out, asm = assemble('        .ORG $6000\n        .INCLUDE "nope.s"\n', source_dir='/nonexistent', source_name='main.s')
        self.assertIsNone(out)
        self.assertTrue(any('Include file not found' in e for e in asm.errors), asm.errors)

    def test_cli_reads_utf8_regardless_of_locale(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, 't.s')
            with open(src, 'w', encoding='utf-8') as f:
                f.write("        .ORG $6000\n        NOP ; 16 × 8 = 128\n")
            env = dict(os.environ, LC_ALL='C', LANG='C', PYTHONUTF8='0')
            r = subprocess.run([sys.executable, '-X', 'utf8=0', os.path.join(TOOLS, 'asm6502.py'), src, os.path.join(d, 't.bin')],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class GoldenTests(unittest.TestCase):
    """The annotated sources must rebuild the 1984 binaries byte for byte."""

    def _check(self, name):
        src = os.path.join(CK, 'source', f'{name}.s')
        with open(src, encoding='utf-8') as f:
            out, asm = assemble(f.read(), source_dir=os.path.dirname(src), source_name=f'{name}.s')
        self.assertEqual(asm.errors, [])
        with open(os.path.join(CK, 'original', f'{name}.bin'), 'rb') as f:
            self.assertEqual(out, f.read(), f'{name} does not match the original binary')

    def test_level1(self): self._check('level1')
    def test_level2(self): self._check('level2')
    def test_level3(self): self._check('level3')

    def test_caterkiller2026_assembles(self):
        src = os.path.join(CK, 'caterkiller2026', 'caterkiller2026.s')
        with open(src, encoding='utf-8') as f:
            out, asm = assemble(f.read(), source_dir=os.path.dirname(src), source_name='caterkiller2026.s')
        self.assertEqual(asm.errors, [])
        self.assertEqual(asm.org, 0x6000)
        self.assertIn('LEVELINIT', asm.symbols)
        self.assertEqual(asm.symbols['LEVELINIT'], 0x7200)


class DisassemblerTests(unittest.TestCase):

    def test_labels_used_consistently(self):
        code = bytes([0x20, 0x06, 0x60,   # $6000 JSR $6006
                      0x4C, 0x06, 0x60,   # $6003 JMP $6006  (same target: must stay SUB_)
                      0xE8,               # $6006 INX
                      0xD0, 0xFD,         # $6007 BNE $6006
                      0x60])              # $6009 RTS
        text = '\n'.join(disasm6502.disassemble(code, 0x6000))
        self.assertIn('SUB_6006:', text)
        self.assertNotIn('L_6006', text)
        self.assertRegex(text, r'JSR +SUB_6006')
        self.assertRegex(text, r'JMP +SUB_6006')
        self.assertRegex(text, r'BNE +SUB_6006')

    def test_hardware_annotation_and_data_bytes(self):
        text = '\n'.join(disasm6502.disassemble(bytes([0xAD, 0x63, 0xC0, 0xFF]), 0x6000))
        self.assertIn('PB2', text)
        self.assertIn('.BYTE $FF', text)

    def test_rom_calls_keep_their_address_and_get_a_name(self):
        text = '\n'.join(disasm6502.disassemble(bytes([0x20, 0xED, 0xFD, 0x4C, 0x03, 0x08]), 0x6000))
        self.assertRegex(text, r'JSR +\$FDED  ; COUT')
        self.assertRegex(text, r'JMP +\$0803')
        self.assertNotIn('SUB_FDED', text)
        self.assertNotIn('L_0803', text)

    def test_every_label_used_is_defined(self):
        for name, start in (('level1', 0x4000), ('level3', 0x6000)):
            with open(os.path.join(CK, 'original', f'{name}.bin'), 'rb') as f:
                code = f.read()
            text = '\n'.join(disasm6502.disassemble(code, start))
            used = set(re.findall(r'\b((?:SUB|L)_[0-9A-F]{4})\b', text))
            defined = set(re.findall(r'^((?:SUB|L)_[0-9A-F]{4})(?::| =)', text, re.M))
            self.assertGreater(len(defined), 100)
            self.assertEqual(used - defined, set(), f'{name}: labels used but never defined')
            # a target inside another instruction becomes an equate, not a label line
            self.assertTrue(re.search(r'^L_[0-9A-F]{4} = \$[0-9A-F]{4}$', text, re.M), f'{name}: no mid-instruction equates')


def make_disk(entries):
    """A minimal DOS 3.3 image: VTOC, one catalog sector, and a T/S list plus data sectors per file.

    entries: (name, type_byte, locked, payload) where payload is the on-disk file content
    including any header. Each file gets its own track; data sectors run from 14 downwards.
    """
    img = bytearray(35 * 16 * 256)
    sector = lambda t, s: (t * 16 + s) * 256
    vtoc = sector(17, 0)
    img[vtoc + 1], img[vtoc + 2] = 17, 15
    catalog = sector(17, 15)
    track = 18
    for i, (name, type_byte, locked, payload) in enumerate(entries):
        entry = catalog + 11 + i * 35
        img[entry], img[entry + 1] = track, 15
        img[entry + 2] = type_byte | (0x80 if locked else 0)
        img[entry + 3:entry + 33] = bytes(c | 0x80 for c in name.ljust(30).encode('ascii'))
        n = (len(payload) + 255) // 256
        img[entry + 33] = n + 1
        ts_list = sector(track, 15)
        for k in range(n):
            img[ts_list + 12 + 2 * k], img[ts_list + 13 + 2 * k] = track, 14 - k
            data = sector(track, 14 - k)
            chunk = payload[k * 256:(k + 1) * 256]
            img[data:data + len(chunk)] = chunk
        track += 1
    return bytes(img)


class ExtractorTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.code = bytes((i * 7) & 0xFF for i in range(700))                 # a 700-byte "binary"
        binary = bytes([0x00, 0x60, 700 & 0xFF, 700 >> 8]) + cls.code       # B file: load $6000, length 700
        cls.tokens = b'\x10\x08\x0a\x00\xba"HI"\x00\x00\x00'
        basic = bytes([len(cls.tokens) & 0xFF, len(cls.tokens) >> 8]) + cls.tokens  # A file: 2-byte length
        cls.disk = make_disk([('LEVEL1', 0x04, True, binary), ('HELLO', 0x02, False, basic)])
        cls.files = {f['name']: f for f in extract_dos33.list_catalog(cls.disk)}

    def test_catalog(self):
        self.assertEqual(sorted(self.files), ['HELLO', 'LEVEL1'])
        self.assertEqual(self.files['LEVEL1']['type'], 'B')
        self.assertTrue(self.files['LEVEL1']['locked'])
        self.assertEqual(self.files['LEVEL1']['sectors'], 4)
        self.assertEqual(self.files['HELLO']['type'], 'A')
        self.assertFalse(self.files['HELLO']['locked'])

    def test_binary_extraction_strips_header_and_trims_to_length(self):
        load, length, data = extract_dos33.extract_file(self.disk, self.files['LEVEL1'])
        self.assertEqual((load, length), (0x6000, 700))
        self.assertEqual(data, self.code)

    def test_basic_file_strips_length_header(self):
        load, length, data = extract_dos33.extract_file(self.disk, self.files['HELLO'])
        self.assertIsNone(load)
        self.assertEqual(length, len(self.tokens))
        self.assertEqual(data, self.tokens)

    def test_corrupt_images_are_rejected_instead_of_hanging(self):
        img = bytearray(35 * 16 * 256)
        vtoc = 17 * 16 * 256
        img[vtoc + 1], img[vtoc + 2] = 17, 15
        cat = 17 * 16 * 256 + 15 * 256
        img[cat + 1], img[cat + 2] = 17, 15          # catalog sector points at itself
        with self.assertRaises(ValueError):
            extract_dos33.list_catalog(bytes(img))
        img[cat + 1], img[cat + 2] = 40, 0           # next catalog sector beyond the image
        with self.assertRaises(ValueError):
            extract_dos33.list_catalog(bytes(img))


class FormatterTests(unittest.TestCase):

    def test_idempotent_on_main_source(self):
        with open(os.path.join(CK, 'caterkiller2026', 'caterkiller2026.s'), encoding='utf-8') as f:
            text = f.read()
        once = fmt6502.format_file(text, eq_col=24)
        self.assertEqual(once, fmt6502.format_file(once, eq_col=24))

    def test_formatting_preserves_assembly_output(self):
        src = os.path.join(CK, 'source', 'level3.s')
        with open(src, encoding='utf-8') as f:
            text = f.read()
        out1, _ = assemble(text, source_dir=os.path.dirname(src))
        out2, asm = assemble(fmt6502.format_file(text), source_dir=os.path.dirname(src))
        self.assertEqual(asm.errors, [])
        self.assertEqual(out1, out2)

    def test_include_is_a_directive(self):
        self.assertEqual(fmt6502.format_file('.INCLUDE "x.s"'), '        .INCLUDE "x.s"')
        self.assertEqual(fmt6502.format_file('LABEL:  LDA #$01   ; c'), 'LABEL:  LDA #$01                        ; c')

    def test_operand_spacing_is_preserved(self):
        self.assertEqual(fmt6502.format_file('   .INCLUDE   "two  spaces.s"'), '        .INCLUDE "two  spaces.s"')
        self.assertEqual(fmt6502.format_file('L:   .BYTE  1,  2'), 'L:      .BYTE 1,  2')


class GuardTests(unittest.TestCase):
    """The pipeline write guard must block writes into the hand-refined directories."""

    def test_write_into_source_is_refused(self):
        env = os.environ.pop(_guard.OVERRIDE_VAR, None)
        try:
            with self.assertRaises(SystemExit):
                _guard.guarded_open(os.path.join(CK, 'source', 'level1.s'), 'w')
            with self.assertRaises(SystemExit):
                _guard.guarded_open(os.path.join(CK, 'sprites', 'x.bmp'), 'wb')
        finally:
            if env is not None:
                os.environ[_guard.OVERRIDE_VAR] = env

    def test_reads_and_writes_elsewhere_pass_through(self):
        with _guard.guarded_open(os.path.join(CK, 'source', 'level1.s')) as f:
            self.assertTrue(f.readline())
        with tempfile.TemporaryDirectory() as d:
            with _guard.guarded_open(os.path.join(d, 'out.txt'), 'w') as f:
                f.write('ok')
            with _guard.guarded_open(os.path.join(d, 'out.txt'), 'w', -1, 'latin-1') as f:
                f.write('positional encoding is honoured')
        self.assertTrue(_guard.OUTPUT_DIR.startswith(os.path.join(REPO, 'build')))


if __name__ == '__main__':
    unittest.main()
