#!/usr/bin/env python3
"""
Build annotated level1.s source file from level1.bin using recovered symbols.
Produces a readable 6502 assembly listing with proper labels, comments,
and data/code region marking.
"""

import os
import struct
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CATERKILLER_DIR = os.path.join(_SCRIPT_DIR, '..')

# ============================================================
# 6502 opcode table: (mnemonic, addressing_mode, bytes)
# Addressing modes:
#   IMP=implied, ACC=accumulator, IMM=immediate,
#   ZP=zero page, ZPX=zp,X, ZPY=zp,Y,
#   ABS=absolute, ABX=abs,X, ABY=abs,Y,
#   IND=indirect, IXD=(ind,X), IDY=(ind),Y,
#   REL=relative
# ============================================================
OPCODES = {
    0x00: ("BRK", "IMP", 1), 0x01: ("ORA", "IXD", 2), 0x05: ("ORA", "ZP", 2),
    0x06: ("ASL", "ZP", 2), 0x08: ("PHP", "IMP", 1), 0x09: ("ORA", "IMM", 2),
    0x0A: ("ASL", "ACC", 1), 0x0D: ("ORA", "ABS", 3), 0x0E: ("ASL", "ABS", 3),
    0x10: ("BPL", "REL", 2), 0x11: ("ORA", "IDY", 2), 0x15: ("ORA", "ZPX", 2),
    0x16: ("ASL", "ZPX", 2), 0x18: ("CLC", "IMP", 1), 0x19: ("ORA", "ABY", 3),
    0x1D: ("ORA", "ABX", 3), 0x1E: ("ASL", "ABX", 3),
    0x20: ("JSR", "ABS", 3), 0x21: ("AND", "IXD", 2), 0x24: ("BIT", "ZP", 2),
    0x25: ("AND", "ZP", 2), 0x26: ("ROL", "ZP", 2), 0x28: ("PLP", "IMP", 1),
    0x29: ("AND", "IMM", 2), 0x2A: ("ROL", "ACC", 1), 0x2C: ("BIT", "ABS", 3),
    0x2D: ("AND", "ABS", 3), 0x2E: ("ROL", "ABS", 3),
    0x30: ("BMI", "REL", 2), 0x31: ("AND", "IDY", 2), 0x35: ("AND", "ZPX", 2),
    0x36: ("ROL", "ZPX", 2), 0x38: ("SEC", "IMP", 1), 0x39: ("AND", "ABY", 3),
    0x3D: ("AND", "ABX", 3), 0x3E: ("ROL", "ABX", 3),
    0x40: ("RTI", "IMP", 1), 0x41: ("EOR", "IXD", 2), 0x45: ("EOR", "ZP", 2),
    0x46: ("LSR", "ZP", 2), 0x48: ("PHA", "IMP", 1), 0x49: ("EOR", "IMM", 2),
    0x4A: ("LSR", "ACC", 1), 0x4C: ("JMP", "ABS", 3), 0x4D: ("EOR", "ABS", 3),
    0x4E: ("LSR", "ABS", 3),
    0x50: ("BVC", "REL", 2), 0x51: ("EOR", "IDY", 2), 0x55: ("EOR", "ZPX", 2),
    0x56: ("LSR", "ZPX", 2), 0x58: ("CLI", "IMP", 1), 0x59: ("EOR", "ABY", 3),
    0x5D: ("EOR", "ABX", 3), 0x5E: ("LSR", "ABX", 3),
    0x60: ("RTS", "IMP", 1), 0x61: ("ADC", "IXD", 2), 0x65: ("ADC", "ZP", 2),
    0x66: ("ROR", "ZP", 2), 0x68: ("PLA", "IMP", 1), 0x69: ("ADC", "IMM", 2),
    0x6A: ("ROR", "ACC", 1), 0x6C: ("JMP", "IND", 3), 0x6D: ("ADC", "ABS", 3),
    0x6E: ("ROR", "ABS", 3),
    0x70: ("BVS", "REL", 2), 0x71: ("ADC", "IDY", 2), 0x75: ("ADC", "ZPX", 2),
    0x76: ("ROR", "ZPX", 2), 0x78: ("SEI", "IMP", 1), 0x79: ("ADC", "ABY", 3),
    0x7D: ("ADC", "ABX", 3), 0x7E: ("ROR", "ABX", 3),
    0x81: ("STA", "IXD", 2), 0x84: ("STY", "ZP", 2), 0x85: ("STA", "ZP", 2),
    0x86: ("STX", "ZP", 2), 0x88: ("DEY", "IMP", 1), 0x8A: ("TXA", "IMP", 1),
    0x8C: ("STY", "ABS", 3), 0x8D: ("STA", "ABS", 3), 0x8E: ("STX", "ABS", 3),
    0x90: ("BCC", "REL", 2), 0x91: ("STA", "IDY", 2), 0x94: ("STY", "ZPX", 2),
    0x95: ("STA", "ZPX", 2), 0x96: ("STX", "ZPY", 2), 0x98: ("TYA", "IMP", 1),
    0x99: ("STA", "ABY", 3), 0x9A: ("TXS", "IMP", 1), 0x9D: ("STA", "ABX", 3),
    0xA0: ("LDY", "IMM", 2), 0xA1: ("LDA", "IXD", 2), 0xA2: ("LDX", "IMM", 2),
    0xA4: ("LDY", "ZP", 2), 0xA5: ("LDA", "ZP", 2), 0xA6: ("LDX", "ZP", 2),
    0xA8: ("TAY", "IMP", 1), 0xA9: ("LDA", "IMM", 2), 0xAA: ("TAX", "IMP", 1),
    0xAC: ("LDY", "ABS", 3), 0xAD: ("LDA", "ABS", 3), 0xAE: ("LDX", "ABS", 3),
    0xB0: ("BCS", "REL", 2), 0xB1: ("LDA", "IDY", 2), 0xB4: ("LDY", "ZPX", 2),
    0xB5: ("LDA", "ZPX", 2), 0xB6: ("LDX", "ZPY", 2), 0xB8: ("CLV", "IMP", 1),
    0xB9: ("LDA", "ABY", 3), 0xBA: ("TSX", "IMP", 1), 0xBC: ("LDY", "ABX", 3),
    0xBD: ("LDA", "ABX", 3), 0xBE: ("LDX", "ABY", 3),
    0xC0: ("CPY", "IMM", 2), 0xC1: ("CMP", "IXD", 2), 0xC4: ("CPY", "ZP", 2),
    0xC5: ("CMP", "ZP", 2), 0xC6: ("DEC", "ZP", 2), 0xC8: ("INY", "IMP", 1),
    0xC9: ("CMP", "IMM", 2), 0xCA: ("DEX", "IMP", 1), 0xCC: ("CPY", "ABS", 3),
    0xCD: ("CMP", "ABS", 3), 0xCE: ("DEC", "ABS", 3),
    0xD0: ("BNE", "REL", 2), 0xD1: ("CMP", "IDY", 2), 0xD5: ("CMP", "ZPX", 2),
    0xD6: ("DEC", "ZPX", 2), 0xD8: ("CLD", "IMP", 1), 0xD9: ("CMP", "ABY", 3),
    0xDD: ("CMP", "ABX", 3), 0xDE: ("DEC", "ABX", 3),
    0xE0: ("CPX", "IMM", 2), 0xE1: ("SBC", "IXD", 2), 0xE4: ("CPX", "ZP", 2),
    0xE5: ("SBC", "ZP", 2), 0xE6: ("INC", "ZP", 2), 0xE8: ("INX", "IMP", 1),
    0xE9: ("SBC", "IMM", 2), 0xEA: ("NOP", "IMP", 1), 0xEC: ("CPX", "ABS", 3),
    0xED: ("SBC", "ABS", 3), 0xEE: ("INC", "ABS", 3),
    0xF0: ("BEQ", "REL", 2), 0xF1: ("SBC", "IDY", 2), 0xF5: ("SBC", "ZPX", 2),
    0xF6: ("INC", "ZPX", 2), 0xF8: ("SED", "IMP", 1), 0xF9: ("SBC", "ABY", 3),
    0xFD: ("SBC", "ABX", 3), 0xFE: ("INC", "ABX", 3),
}

# ============================================================
# Zero-page symbol names
# ============================================================
ZP_SYMBOLS = {
    0x03: "COLORMASK",
    0x09: "TEMP9",
    0x0A: "TEMPA",
    0x0F: "TEMP0F",
    0x10: "SHAPE",
    0x11: "COLOR",
    0x14: "SHPLO",
    0x15: "SHPHI",
    0x16: "TOLO",
    0x17: "TOHI",
    0x18: "X",
    0x19: "Y",
    0x1A: "XX",
    0x1B: "YY",
    0x1C: "WIDTH",
    0x1D: "HEIGHT",
    0x1E: "TEMPWID",
    0x1F: "REPORT",
    0x4E: "COUNT",
    0x50: "PAUSEFLAG",
    0x56: "SCANLINE",
    0x59: "SCRLO",
    0x5A: "SCRHI",
    0x62: "PAGEFLIP",
    0x70: "ASAVE1",
    0x76: "PADCOUNT",
    0x77: "JOYFLG",
    0x78: "LEVEL",
    0x79: "FOODC",
    0x7D: "YSAVE",
    0x7E: "FLAGSAVE",
    0x7F: "YOUHITS",
    0x80: "YOULIVES",
    0x81: "YOUX",
    0x82: "YOUY",
    0x83: "MUSIC",
    0x84: "SOUND",
    0x85: "TEMPX",
    0x86: "TEMPY",
    0x87: "TEMPSHP",
    0x88: "DEMO",
    0x8A: "SCORELO",
    0x8B: "SCOREHI",
    0x8C: "SCOREHI1",
    0x8D: "TIME",
    0x8E: "YOUSHP",
    0x8F: "YOUC",
    0x90: "NUMCATS",
    0x91: "XSAVE",
    0x92: "CATCOUNT",
    0x93: "CATX",       # array $93-$9A
    0x9B: "CATY",       # array $9B-$A2
    0xA3: "CATDIR",     # array $A3-$AA
    0xAB: "CATWALK",    # array $AB-$B2
    0xB3: "CATUSE",     # array $B3-$BA
    0xBB: "FOODX",
    0xC3: "FOODY",
    0xF0: "STRLO",
    0xF1: "STRHI",
    0xFD: "ASAVE",
    0xFE: "FLAG",
}

# ============================================================
# Code labels from symbol table
# ============================================================
LABELS = {
    0x6F52: "PAGESWITCH",
    0x6F5F: "SELECTPAGE",
    0x6F67: "SELPAGE2",
    0x6F6B: "DELAY1",
    0x6F76: "DELAY2",
    0x6F96: "SPRITEDRAW",
    0x7003: "HITBL",
    0x7013: "CATBTBL",
    0x7016: "PLACESX",
    0x701E: "PLACESY",
    0x7026: "CLICK",
    0x702D: "ORPLOTS",
    0x703B: "PLOTS",
    0x7049: "BORDER",
    0x7064: "BORDER1",
    0x7072: "BORDER2",
    0x7081: "BORDER3",
    0x7093: "BORDER4",
    0x70E2: "BORDER5",
    0x70F7: "CHKJOY",
    0x7110: "NOJOY",
    0x7111: "CHKL",
    0x711C: "CHKUPDO",
    0x712B: "CHKLERI",
    0x713A: "MOVUP",
    0x7141: "MOVLE",     # MOVLEA
    0x7148: "MOVDO",
    0x714F: "MOVRI",
    0x7156: "DECTIME",
    0x7158: "DEC1",
    0x715E: "DEC2",
    0x7187: "DEC3",
    0x718C: "PUTSCORE",
    0x71DB: "PUTLIVES",
    0x7217: "PUTHITS",
    0x7259: "UPDATEYOUZ",
    0x725C: "UPDATEYOU",
    0x7279: "UP1",
    0x728C: "UPDLFT1",
    0x728E: "CHKUD",
    0x729A: "UPDUP1",
    0x729C: "UPDON",
    0x72A4: "NOFIXX",
    0x72AA: "NOFIXX1",
    0x72B2: "NOFIXY",
    0x72B8: "NOFIXY1",
    0x72C4: "NOPEFXS",
    0x72C5: "YESFXS",
    0x72F4: "UPDATEYOU1",
    0x7312: "YOUDIED",
    0x7315: "ZNOFIXY1",
    0x7318: "UP",
    0x7327: "DO",
    0x7336: "LE",
    0x7345: "RI",
    0x7351: "NOFIXER1",
    0x7354: "DRAWYOU",
    0x7358: "DRAWYOU1",
    0x7362: "DRAWYOU2",
    0x7365: "DRAWYOU3",
    0x736B: "DRAWYOU6",
    0x736E: "DRAWYOU3Z",
    0x737A: "DRAWYOU4",
    0x73C6: "DRAWYOU4A",
    0x73CB: "DRAWYOU4B",
    0x7405: "DRAWYOU5",
    0x740A: "ERAYOU",
    0x7421: "SNOOKHIT",
    0x7431: "SNOOKHIT1",
    0x7456: "SNOOKDED",
    0x7473: "STILMOR",
    0x7492: "SNOOKOK",
    0x7499: "SNOKKL",
    0x74B5: "TWOTONE",
    0x74BD: "SNOKSND",
    0x74BF: "SNOKSND1",
    0x74C1: "SNOKSND2",
    0x74D0: "SNOKSND3",
    0x74D2: "SNOKSND4",
    0x74E8: "SNOKOK1",
    0x74F5: "INITCAT",
    0x74F7: "INITCAT1",
    0x750B: "PUTCAT",
    0x7517: "DRAWCAT",
    0x7522: "CATRI",
    0x7526: "CATNX",
    0x7532: "STACAT",
    0x753D: "STACATRI",
    0x7541: "STACATNX",
    0x754D: "NOWALK",
    0x755B: "ZEROX",
    0x755F: "NOWALKLES",
    0x7563: "NOWALKCU",
    0x7573: "NWLKU",
    0x7579: "NWLKS",
    0x757C: "SKIPCAT1",
    0x757F: "UPCAT",
    0x7585: "UPCAT1",
    0x759D: "MOVCAT",
    0x75A6: "UPCATLE",
    0x75A8: "UPCATL1",
    0x75AD: "UPMAYDO",
    0x75B2: "UPNODO",
    0x75D2: "PLO",
    0x75F3: "HITSI",
    0x75F9: "HITTB",
    0x75FF: "UG",
    0x7618: "SKIPCAT",
    0x7620: "FINISH",
    0x7623: "UPCAT1A",
    0x7626: "UPNOGOOD",
    0x7651: "SNDHIT",
    0x765A: "SNDHIT1",
    0x7664: "CLICK1",
    0x766E: "FINISHED",
    0x7682: "FINBONUS",
    0x7683: "ADDSCORE",
    0x769A: "ADDSCORE1",
    0x769E: "BEGIN",
    0x76A4: "CONTINU",
    0x76BE: "ASEDF",
    0x76F1: "BEGIN1",
    0x76F3: "BEGIN2",
    0x7703: "PAUSE1",
    0x770D: "FIXSOUND",
    0x7713: "NOKEY",
    0x771F: "BEGIN3",
    0x7732: "UPEYOU",
    0x773E: "UPEYOU1",
    0x7747: "GETTIME",
    0x7A00: "DRAW",
    0x7A03: "CLRSCRN",
    0x7A06: "ORPLOT",
    0x7A09: "PLOT",
    0x7A0C: "STABW",
    0x7B3D: "ERABW",
    0x8A00: "NUMGEN",
    0x9000: "CHRGEN",
    # Additional labels discovered in code analysis
    0x5F80: "KBDCHECK",
    0x5F8D: "KBDGOT",
    0x5F98: "KBDNOPAUSE",
    0x5F9E: "KBDCONT",
    0x6F6D: "DELAY1LP",
    0x6F78: "DELAY2LP",
    # Internal code targets (JSR/JMP destinations without symbol table names)
    0x7140: "READPADDLE",
    0x717A: "SOUNDTICK",
    0x71B0: "SHOWSCORE",
    0x71FF: "SHOWLEVEL",
    0x723B: "SHOWHITS",
    0x7256: "SHOWNUM",
    0x727C: "REDRAWSCENE",
    0x7280: "REDRAW",
    0x72DC: "MOVEEND",
    0x731B: "KBDDISPATCH",
    0x7331: "DOMOVUP",
    0x7340: "DOMOVDO",
    0x734F: "DOMOVLE",
    0x735E: "DOMOVRI",
    0x736D: "DRAWSPRITE",
    0x73E4: "PLACEFOOD",
    0x73F4: "PLACEFOOD2",
    0x741E: "HITPROCESS",
    0x7423: "ERASESPRITE",
    0x743A: "HITFINISH",
    0x744A: "HITCONTINUE",
    0x746F: "GAMEOVER",
    0x74A1: "DEATHSOUND",
    0x74CE: "SOUNDLOOP1",
    0x74D6: "TWOTONEMAIN",
    0x7501: "SOUNDLOOP2",
    0x750E: "GETPLAYERX",
    0x7518: "GETPLAYERY",
    0x7544: "CATMOVECHECK",
    0x7567: "CATSNDHIT",
    0x756F: "CATHITCHECK",
    0x75BE: "UPDATECATS",
    0x75C4: "UPCATLOOP",
    0x75DC: "CATDONELOOP",
    0x7657: "CATHITSND",
    0x7665: "DRAWCATSPRITE",
    0x76AD: "SCOREBONUS",
    0x76C2: "BCDADD",
    0x76CF: "BCDADDHI",
    0x76DD: "INITLIVES",
    0x76E3: "LEVELSTART",
    0x76FD: "INITCATLOOP",
    0x777F: "MAINLOOPTIMING",
    0x7795: "UPDATEENEMIES",
    0x77A1: "UPDATEPLAYER",
    0x77AA: "GETTIMECALC",
    0x780E: "PAGESETUP1",
    0x7828: "PAGESETUP2",
    0x785C: "PAGESETUP3",
    0x786F: "PAGEINIT1",
    0x7880: "PAGEINIT2",
    0x789A: "PAGEINITLOOP",
    # Drawing engine internals
    0x7900: "DRAWVEC",
    0x7906: "DRAWVEC_OR",
    0x7909: "DRAWVEC_DIR",
    0x790F: "PLOTDIRECT",
    0x792F: "PLOTOR",
    0x7950: "PLOTRTS",
    0x7951: "HGRLO",
    0x7A0F: "PLOTIMPL",
    0x7A11: "HGRHI",
    0x7A25: "ORPLOTIMPL",
    0x7A3D: "DRAWIMPL",
    0x7ACB: "CLRSCR2",
    0x7AFF: "ERABW2",
    0x7B7B: "DRAWCMP",
    0x7BDC: "HGRLO2",
    0x7C9C: "HGRHI2",
    # Title/credits
    0x8020: "TITLESETUP",
    0x813A: "RENDERSTR",
    0x8156: "STR_DEVELOPMENT",
    0x8162: "STR_CORPORATION",
    0x816E: "STR_PRESENTS",
    0x8177: "STR_SNOOKUMS",
    0x8180: "STR_BYJEFF",
    0x8192: "STR_COPYRIGHT",
    0x81A0: "XORSCREEN",
    0x81E0: "SPRITEDATA",
    # NUMGEN internals
    0x8A3B: "NUMGENPLOT",
    0x8A4F: "NUMGENTBL",
    # Font/screen data
    0x8776: "SPRITADATA2",
    0x8805: "FONTREF",
    0x8F16: "HGRDATA1",
    0x8F98: "HGRDATA2",
    # CHRGEN internals
    0x9019: "CHRGENROW",
    0x901E: "CHRGENPIXEL",
    0x9047: "CHRGENNEXT",
    0x906B: "CHRGENCOLOR",
    0x9087: "CHRGENPLOT",
    0x91A6: "CATTBL",
    # Page 2 sprite engine
    0x9300: "DRAW2",
    0x9303: "CLRSCRN2",
    0x9306: "ORPLOT2",
    0x9309: "PLOT2",
    0x930C: "STABW2",
    0x930F: "PLOTIMPL2",
    0x9325: "ORPLOTIMPL2",
    0x933D: "DRAWIMPL2",
    0x93AC: "CLRSCR2B",
    0x93E0: "ERABW2B",
    0x943D: "HGR2LO",
    0x94FD: "HGR2HI",
}

# Apple II hardware soft switches
HW_NAMES = {
    0xC000: "KEYBOARD",
    0xC010: "KBDSTRB",
    0xC030: "SPKR",
    0xC050: "TXTCLR",
    0xC051: "TXTSET",
    0xC052: "MIXCLR",
    0xC053: "MIXSET",
    0xC054: "LOWSCR",
    0xC055: "HISCR",
    0xC056: "LORES",
    0xC057: "HIRES",
    0xC061: "PB0",
    0xC062: "PB1",
    0xC063: "PB2",
}

# Apple II ROM routines
ROM_NAMES = {
    0xFCA8: "WAIT",
    0xFC58: "HOME",
    0xFB1E: "PREAD",
    0xFDED: "COUT",
}

# ============================================================
# Data regions (these should NOT be disassembled as code)
# ============================================================
DATA_REGIONS = [
    # (start, end, description)
    (0x4000, 0x5F80, "Hi-Res Graphics Page 1 - Game playfield bitmap"),
    (0x5FA4, 0x6000, "Hi-Res Graphics data (continued)"),
    (0x6000, 0x6059, "Embedded assembler source text (high-bit ASCII)"),
    (0x6059, 0x66E9, "Assembler symbol table"),
    (0x66E9, 0x6F19, "Sprite/graphics data"),
    (0x6FFE, 0x7003, "Data bytes"),
    (0x7003, 0x7013, "HITBL - Hit detection table"),
    (0x7013, 0x7026, "CATBTBL/PLACESX/PLACESY - Enemy placement tables"),
    (0x78A6, 0x7900, "Table of $FF/$00 bytes between PAGEINITLOOP and DRAWVEC (not code)"),
    (0x7951, 0x7A00, "HGRLO - Hi-Res screen address table (low bytes, also used as HGRHI at $7A11)"),
    # Note: $7A00-$7ACB is CODE (DRAW dispatch + STABW sprite engine)
    # The PLOTDIRECT at $790F references $7A11 as HGRHI table, which overlaps
    # with the sprite engine code bytes - a dual-purpose memory technique.
    (0x7BDC, 0x7C9C, "HGRLO2 - Screen address table 2 (low bytes)"),
    (0x7C9C, 0x7D5C, "HGRHI2 - Screen address table 2 (high bytes)"),
    (0x7D5C, 0x8000, "Hi-Res screen fill data"),
    (0x8000, 0x8020, "Graphics pattern data"),
    (0x814F, 0x819F, "Encoded text strings (title/credits)"),
    (0x81BA, 0x81E0, "Character font bitmap data"),
    (0x81E0, 0x89FF, "Sprite shape tables"),
    (0x8A49, 0x8D00, "Font bitmap data and screen data"),
    (0x8D00, 0x9000, "Hi-Res address tables and screen data"),
    (0x90BE, 0x90C6, "Pixel mask table"),
    (0x90C6, 0x9300, "Hi-Res screen data"),
    (0x943D, 0x95BD, "Hi-Res Page 2 address tables"),
    (0x95BD, 0x9600, "Trailing screen data"),
]

# Section headers for major code regions
SECTION_HEADERS = {
    0x4000: """; ================================================================
; SNOOKUMS - Level 1
; By Jeff Koftinoff
; 1984, published through A.P.P.L.E. (Apple Pugetsound Program Library Exchange)
;
; Binary: level1.bin
; Load address: $4000
; Size: 22016 bytes ($5600)
; Memory range: $4000-$95FF
;
; Memory Map:
;   $4000-$5F7F  Hi-Res Page 1 graphics (game playfield)
;   $5F80-$5F9E  Keyboard check / pause handler
;   $6000-$66E8  Assembler artifacts (source text + symbol table)
;   $66E9-$6F18  Sprite and graphics data
;   $6F19-$6F95  Page flip and delay routines
;   $6F96-$6FFD  Low-level sprite draw
;   $6FFE-$7027  Data tables (hit, placement, speed)
;   $7028-$7048  Sound click routines
;   $7049-$7110  Screen/border initialization
;   $7111-$71FE  Joystick, paddle, score display
;   $71FF-$727A  Level/lives/hits display
;   $7280-$736A  Player movement + keyboard input
;   $736D-$7422  Player sprite draw + collision
;   $7423-$750A  Erase, food, snook hit/death
;   $750B-$757E  Enemy init, draw, walk logic
;   $757F-$7620  Enemy AI update loop
;   $7621-$76BD  Finish level, scoring
;   $76BE-$7749  Main game init + game loop (ENTRY)
;   $774A-$78A5  Game loop continued + GETTIME
;   $7900-$7A10  Plot vector table + plot routines
;   $7A00-$7ACA  DRAW/STABW sprite engine (collision)
;   $7ACB-$7BDB  CLRSCRN + ERABW (no collision)
;   $7BDC-$7FFF  Address lookup tables + screen data
;   $8020-$819F  Title screen setup + credits text
;   $81A0-$81BF  Screen dissolve effect
;   $81E0-$89FF  Sprite shape data
;   $8A00-$8CFF  NUMGEN character/number rendering + fonts
;   $8D00-$8FFF  Address tables
;   $9000-$90BD  CHRGEN large character rendering
;   $9300-$943C  Page 2 sprite engine (double buffering)
;   $943D-$95FF  Page 2 address tables
;
; Controls:
;   W = Up,  S = Down,  J = Left,  K = Right
;   Ctrl-S = Toggle sound    Ctrl-T = Pause
;   ESC = Pause until keypress
;
; ================================================================
""",

    0x5F80: """
; ----------------------------------------------------------------
; Keyboard check & pause toggle handler
; Checks for Ctrl-T to toggle pause flag at $50
; Falls through to main keyboard dispatch at UP ($7318)
; ----------------------------------------------------------------
""",
    0x5FA4: "",
    0x6000: """
; ----------------------------------------------------------------
; ASSEMBLER ARTIFACTS
; The assembler left source text and the complete symbol table
; in the binary. This region is NOT executable code.
; ----------------------------------------------------------------
""",
    0x6F19: """
; ----------------------------------------------------------------
; Utility routines: page switching and delays
; ----------------------------------------------------------------
""",
    0x6F52: """
; PAGESWITCH - Toggle display page variable ($62)
""",
    0x6F5F: """
; SELECTPAGE - Select HGR display page based on PAGEFLIP ($62)
""",
    0x6F6B: """
; DELAY1 - Short delay using Monitor WAIT
""",
    0x6F76: """
; DELAY2 - Longer delay using Monitor WAIT
""",
    0x6F96: """
; ----------------------------------------------------------------
; Low-level sprite drawing with shift/mask (XOR blit)
; Uses SCANLINE ($56) and PAGEFLIP ($62) for double buffering
; ----------------------------------------------------------------
""",
    0x7003: """
; ----------------------------------------------------------------
; Data tables for enemies
; ----------------------------------------------------------------
""",
    0x7026: """
; ----------------------------------------------------------------
; Sound routines
; ----------------------------------------------------------------
; CLICK - Short speaker click
""",
    0x7049: """
; ----------------------------------------------------------------
; BORDER - Game screen initialization
; Sets up the playing field borders, switches to hi-res mode,
; and draws the game title text using CHRGEN
; ----------------------------------------------------------------
""",
    0x70F7: """
; ----------------------------------------------------------------
; CHKJOY - Joystick/paddle input handler
; Reads paddle buttons (PB0/PB1/PB2) and paddle position (PREAD)
; ----------------------------------------------------------------
""",
    0x718C: """
; ----------------------------------------------------------------
; Score and status display routines
; Uses BCD format and NUMGEN for digit rendering
; ----------------------------------------------------------------
; PUTSCORE - Display current score
""",
    0x71DB: """
; PUTLIVES - Display lives remaining
""",
    0x7217: """
; PUTHITS - Display hit count
""",
    0x725C: """
; ----------------------------------------------------------------
; UPDATEYOU - Main player update
; Saves current position, handles demo mode AI,
; checks keyboard/joystick input, and clamps to boundaries
; ----------------------------------------------------------------
""",
    0x7318: """
; ----------------------------------------------------------------
; UP - Keyboard dispatch for player movement
; W=$D7=Up, S=$D3=Down, J=$CA=Left, K=$CB=Right
; ----------------------------------------------------------------
""",
    0x7354: """
; ----------------------------------------------------------------
; DRAWYOU - Player sprite drawing with animation
; Selects animation frame and calls DRAW engine
; ERAYOU - Erase player by drawing in erase color
; ----------------------------------------------------------------
""",
    0x7421: """
; ----------------------------------------------------------------
; SNOOKHIT - Player collision handling
; SNOOKDED - Player death sequence
; SNOOKOK - Player safe after hit
; SNOKKL - Process snook kill
; ----------------------------------------------------------------
""",
    0x74B5: """
; ----------------------------------------------------------------
; TWOTONE - Two-frequency sweep sound effect
; Alternates between two frequencies, sweeping them
; Respects SOUND mute flag ($84 bit 7)
; ----------------------------------------------------------------
""",
    0x74F5: """
; ----------------------------------------------------------------
; INITCAT - Initialize a new enemy (cat)
; Sets position from PLACESX/PLACESY tables,
; direction to 1 (right), walk counter to 5
; ----------------------------------------------------------------
""",
    0x750B: """
; ----------------------------------------------------------------
; PUTCAT/DRAWCAT - Enemy sprite rendering
; CATRI/CATNX - Cat movement right/next
; STACAT - Start cat movement
; NOWALK - Handle enemy at rest
; ----------------------------------------------------------------
""",
    0x757F: """
; ----------------------------------------------------------------
; UPCAT - Update all active enemies
; Enemies chase the player by comparing positions
; Handles collision with player and food
; ----------------------------------------------------------------
""",
    0x7620: """
; ----------------------------------------------------------------
; FINISH - Level completion handler
; FINISHED - End of level sequence
; FINBONUS - Bonus scoring at level end
; ----------------------------------------------------------------
""",
    0x7683: """
; ----------------------------------------------------------------
; ADDSCORE - Add to score using BCD arithmetic
; Uses 6502 decimal mode (SED/CLD)
; 3-byte BCD score: SCORELO, SCOREHI, SCOREHI1
; ----------------------------------------------------------------
""",
    0x76DD: """
; ----------------------------------------------------------------
; Game initialization
; INITLIVES - Set starting lives (3)
; LEVELSTART - Set up screen, enemies, player start position
; Main game loop begins at L_772C (32-frame loop)
;
; Loop structure:
;   Outer: L_772C loads frame counter = $20 (32)
;   Inner: L_772E processes one frame:
;     - Check Ctrl-S (sound toggle) / ESC (pause)
;     - Update enemies (UPDATEENEMIES)
;     - Update player (UPDATEPLAYER)
;     - Difficulty-based speed: easy=2x player, hard=3x enemies
;   After 32 frames: SOUNDTICK, then loop
; ----------------------------------------------------------------
""",
    0x7747: """
; ----------------------------------------------------------------
; GETTIME - Calculate game speed from level number
; Higher level = lower delay = faster enemies
; Returns timing value in A for WAIT routine
; ----------------------------------------------------------------
""",
    0x7900: """
; ----------------------------------------------------------------
; Plot vector dispatch table
; Entries: DRAW, CLRSCRN, ORPLOT, PLOT, STABW
; ----------------------------------------------------------------
""",
    0x7A00: """
; ----------------------------------------------------------------
; DRAW - Main drawing dispatch
; CLRSCRN - Clear hi-res screen
; ORPLOT - OR a pixel onto screen
; PLOT - Direct pixel write
; STABW - Sprite blit with collision detection (AND test)
;
; The sprite engine uses XOR drawing: same call draws and erases.
; Collision is detected by ANDing sprite with existing screen
; content during the blit loop (stored in REPORT).
; ----------------------------------------------------------------
""",
    0x7B3D: """
; ----------------------------------------------------------------
; ERABW - Sprite draw without collision checking
; Used for background elements (borders, decorations)
; ----------------------------------------------------------------
""",
    0x8020: """
; ----------------------------------------------------------------
; Title screen setup
; Draws "SYDNEY DEVELOPMENT CORPORATION PRESENTS" (left over from a 1984 pitch to that company; never shown to players)
;       "SNOOKUMS"
;       "BY JEFF KOFTINOFF"
;       "COPYRIGHT (C)"
; ----------------------------------------------------------------
""",
    0x81A0: """
; ----------------------------------------------------------------
; XORSCREEN - Visual dissolve/scramble effect
; XORs each screen byte with its low address byte
; Creates a visual transition effect
; ----------------------------------------------------------------
""",
    0x8A00: """
; ----------------------------------------------------------------
; NUMGEN - Character/number rendering on hi-res screen
; Draws characters using bitmap font data
; ----------------------------------------------------------------
""",
    0x9000: """
; ----------------------------------------------------------------
; CHRGEN - Large character rendering system
; Draws multi-pixel text characters with color patterns
; Used for title text, score display, level labels
; ----------------------------------------------------------------
""",
    0x9300: """
; ----------------------------------------------------------------
; Page 2 sprite engine (duplicate of STABW/ERABW/DRAW)
; Used for double-buffered rendering
; Draw to back buffer while displaying front buffer
; ----------------------------------------------------------------
""",
}


def is_data_region(addr):
    """Return True and description if addr is in a data region."""
    for start, end, desc in DATA_REGIONS:
        if start <= addr < end:
            return True, desc
    return False, None


def format_zp_comment(zp_addr):
    """Return symbolic name for a zero-page address."""
    if zp_addr in ZP_SYMBOLS:
        return ZP_SYMBOLS[zp_addr]
    # Check if it's an offset into an array
    for base, name in [(0x93, "CATX"), (0x9B, "CATY"), (0xA3, "CATDIR"),
                       (0xAB, "CATWALK"), (0xB3, "CATUSE")]:
        if base <= zp_addr < base + 8:
            idx = zp_addr - base
            return f"{name}+{idx}"
    return None


def format_abs_name(addr):
    """Return symbolic name for an absolute address."""
    if addr in LABELS:
        return LABELS[addr]
    if addr in HW_NAMES:
        return HW_NAMES[addr]
    if addr in ROM_NAMES:
        return ROM_NAMES[addr]
    return None


def get_label(addr):
    """Get label for an address, or generate one."""
    if addr in LABELS:
        return LABELS[addr]
    return None


def disassemble(data, load_addr):
    """Disassemble binary data into annotated source lines."""
    lines = []
    end_addr = load_addr + len(data)

    # First pass: find all branch/jump targets so we can add labels
    targets = set()
    pos = 0
    while pos < len(data):
        addr = load_addr + pos
        is_data, _ = is_data_region(addr)
        if is_data:
            pos += 1
            continue
        opcode = data[pos]
        if opcode not in OPCODES:
            pos += 1
            continue
        mnem, mode, nbytes = OPCODES[opcode]
        if pos + nbytes > len(data):
            pos += 1
            continue
        if mode == "REL" and nbytes == 2:
            offset = data[pos + 1]
            if offset >= 0x80:
                offset -= 256
            target = addr + 2 + offset
            targets.add(target)
        elif mode == "ABS" and nbytes == 3 and mnem in ("JSR", "JMP"):
            target = data[pos + 1] | (data[pos + 2] << 8)
            if load_addr <= target < end_addr:
                targets.add(target)
        pos += nbytes

    # Add known labels as targets
    for a in LABELS:
        if load_addr <= a < end_addr:
            targets.add(a)

    # Second pass: generate output
    pos = 0
    current_data_region = None

    while pos < len(data):
        addr = load_addr + pos

        # Check for section headers
        if addr in SECTION_HEADERS:
            lines.append(SECTION_HEADERS[addr])

        # Check for data region
        is_data, desc = is_data_region(addr)

        if is_data:
            # Find extent of this data region
            region_end = addr
            for start, end, d in DATA_REGIONS:
                if start <= addr < end:
                    region_end = end
                    break

            if current_data_region != desc:
                current_data_region = desc
                # Add label if one exists
                label = get_label(addr)
                if label:
                    lines.append(f"{label}:")

            # Emit data bytes in groups of 16
            chunk_end = min(region_end, end_addr)
            remaining = chunk_end - addr
            chunk_size = min(remaining, len(data) - pos)

            row = 0
            i = 0
            while i < chunk_size:
                row_addr = addr + i
                # Check for labels within data
                lbl = get_label(row_addr)
                if lbl and i > 0:
                    lines.append(f"{lbl}:")

                n = min(16, chunk_size - i)
                # Check if next label is within this row
                for j in range(1, n):
                    if get_label(row_addr + j):
                        n = j
                        break

                hex_bytes = data[pos + i : pos + i + n]
                byte_strs = ", ".join(f"${b:02X}" for b in hex_bytes)
                # Check if it looks like ASCII text (high-bit)
                text = ""
                if all((b & 0x7F) >= 0x20 and (b & 0x7F) < 0x7F for b in hex_bytes):
                    decoded = "".join(chr(b & 0x7F) for b in hex_bytes)
                    text = f'  ; "{decoded}"'
                lines.append(f"        .BYTE {byte_strs}{text}")
                i += n

            pos += chunk_size
            if pos >= len(data):
                break
            current_data_region = None
            continue

        current_data_region = None

        # Add label
        label = get_label(addr)
        if label:
            lines.append(f"{label}:")
        elif addr in targets:
            lines.append(f"L_{addr:04X}:")

        opcode = data[pos]
        if opcode not in OPCODES:
            # Unknown opcode - emit as data byte
            lines.append(f"        .BYTE ${opcode:02X}            ; ${addr:04X} - illegal opcode")
            pos += 1
            continue

        mnem, mode, nbytes = OPCODES[opcode]
        if pos + nbytes > len(data):
            lines.append(f"        .BYTE ${opcode:02X}            ; ${addr:04X} - truncated")
            pos += 1
            continue

        raw_bytes = data[pos:pos + nbytes]
        hex_str = " ".join(f"{b:02X}" for b in raw_bytes)

        comment = ""
        operand = ""

        if mode == "IMP":
            operand = ""
        elif mode == "ACC":
            operand = "A"
        elif mode == "IMM":
            val = data[pos + 1]
            operand = f"#${val:02X}"
            # Add character interpretation for CMP with keyboard values
            if mnem == "CMP" and val >= 0x80 and val < 0xFF:
                ch = val & 0x7F
                if 0x20 <= ch < 0x7F:
                    comment = f"; '{chr(ch)}' key"
                elif ch < 0x20:
                    comment = f"; Ctrl-{chr(ch + 0x40)}"
        elif mode == "ZP":
            zp = data[pos + 1]
            zp_name = format_zp_comment(zp)
            if zp_name:
                operand = f"{zp_name}"
                comment = f"; ${zp:02X}"
            else:
                operand = f"${zp:02X}"
        elif mode == "ZPX":
            zp = data[pos + 1]
            zp_name = format_zp_comment(zp)
            if zp_name:
                operand = f"{zp_name},X"
                comment = f"; ${zp:02X}"
            else:
                operand = f"${zp:02X},X"
        elif mode == "ZPY":
            zp = data[pos + 1]
            zp_name = format_zp_comment(zp)
            if zp_name:
                operand = f"{zp_name},Y"
                comment = f"; ${zp:02X}"
            else:
                operand = f"${zp:02X},Y"
        elif mode == "ABS":
            abs_addr = data[pos + 1] | (data[pos + 2] << 8)
            name = format_abs_name(abs_addr)
            if name:
                operand = f"{name}"
                comment = f"; ${abs_addr:04X}"
            else:
                operand = f"${abs_addr:04X}"
        elif mode == "ABX":
            abs_addr = data[pos + 1] | (data[pos + 2] << 8)
            name = format_abs_name(abs_addr)
            if name:
                operand = f"{name},X"
                comment = f"; ${abs_addr:04X}"
            else:
                operand = f"${abs_addr:04X},X"
        elif mode == "ABY":
            abs_addr = data[pos + 1] | (data[pos + 2] << 8)
            name = format_abs_name(abs_addr)
            if name:
                operand = f"{name},Y"
                comment = f"; ${abs_addr:04X}"
            else:
                operand = f"${abs_addr:04X},Y"
        elif mode == "IND":
            abs_addr = data[pos + 1] | (data[pos + 2] << 8)
            name = format_abs_name(abs_addr)
            if name:
                operand = f"({name})"
                comment = f"; ${abs_addr:04X}"
            else:
                operand = f"(${abs_addr:04X})"
        elif mode == "IXD":
            zp = data[pos + 1]
            zp_name = format_zp_comment(zp)
            if zp_name:
                operand = f"({zp_name},X)"
                comment = f"; ${zp:02X}"
            else:
                operand = f"(${zp:02X},X)"
        elif mode == "IDY":
            zp = data[pos + 1]
            zp_name = format_zp_comment(zp)
            if zp_name:
                operand = f"({zp_name}),Y"
                comment = f"; ${zp:02X}"
            else:
                operand = f"(${zp:02X}),Y"
        elif mode == "REL":
            offset = data[pos + 1]
            if offset >= 0x80:
                offset -= 256
            target = addr + 2 + offset
            target_name = get_label(target)
            if target_name:
                operand = target_name
            elif target in targets:
                operand = f"L_{target:04X}"
            else:
                operand = f"${target:04X}"

        # Format the instruction line
        inst = f"{mnem} {operand}".strip()
        # Pad for alignment
        addr_prefix = f"        {inst:<28s}"
        if comment:
            line = f"{addr_prefix}{comment}"
        else:
            line = addr_prefix.rstrip()
        lines.append(line)

        # Add blank line after RTS/JMP for readability
        if mnem in ("RTS", "RTI") or (mnem == "JMP" and mode == "ABS"):
            lines.append("")

        pos += nbytes

    return lines


def main():
    data = open(os.path.join(_CATERKILLER_DIR, 'original', 'level1.bin'), 'rb').read()
    load_addr = 0x4000

    # Build the ZP equates header
    header_lines = []
    header_lines.append("; ================================================================")
    header_lines.append("; Zero-page variable definitions")
    header_lines.append("; (recovered from embedded assembler symbol table)")
    header_lines.append("; ================================================================")
    header_lines.append("")

    sorted_zp = sorted(ZP_SYMBOLS.items())
    for addr, name in sorted_zp:
        header_lines.append(f"{name:<16s} = ${addr:02X}")
    header_lines.append("")

    header_lines.append("; ================================================================")
    header_lines.append("; Apple II hardware addresses")
    header_lines.append("; ================================================================")
    header_lines.append("")
    for addr, name in sorted(HW_NAMES.items()):
        header_lines.append(f"{name:<16s} = ${addr:04X}")
    header_lines.append("")

    header_lines.append("; ================================================================")
    header_lines.append("; Apple II ROM routines")
    header_lines.append("; ================================================================")
    header_lines.append("")
    for addr, name in sorted(ROM_NAMES.items()):
        header_lines.append(f"{name:<16s} = ${addr:04X}")
    header_lines.append("")

    header_lines.append(f"        .ORG ${load_addr:04X}")
    header_lines.append("")

    # Disassemble
    code_lines = disassemble(data, load_addr)

    # Write output
    with open(output_path('level1.s'), 'w') as f:
        for line in header_lines:
            f.write(line + '\n')
        for line in code_lines:
            f.write(line + '\n')

    print(f"Written level1.s ({len(header_lines) + len(code_lines)} lines)")


if __name__ == '__main__':
    main()
