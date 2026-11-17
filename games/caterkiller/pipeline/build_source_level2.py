#!/usr/bin/env python3
"""
Build annotated level2.s source file from level2.bin.
Level2 has no embedded symbol table, so we apply the same ZP variable names
recovered from level1's symbol table (same game engine) and map the relocated
routine addresses.
"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CATERKILLER_DIR = os.path.join(_SCRIPT_DIR, '..')
sys.path.insert(0, _SCRIPT_DIR)  # find build_source and _guard next to this file, never in the cwd
from build_source import OPCODES, ZP_SYMBOLS, HW_NAMES, ROM_NAMES, format_zp_comment
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/

# ============================================================
# Code labels for level2 (relocated addresses)
# Same routine names as level1, at new addresses
# ============================================================
LABELS = {
    # Keyboard check / pause handler ($5F80 - same as level1)
    0x5F80: "KBDCHECK",
    0x5F8D: "KBDGOT",
    0x5F98: "KBDNOPAUSE",
    0x5F9E: "KBDCONT",
    # Page flip and delay routines (identical to level1)
    0x6F41: "SPRITEINIT",
    0x6F52: "PAGESWITCH",
    0x6F5F: "SELECTPAGE",
    0x6F67: "SELPAGE2",
    0x6F6B: "DELAY1",
    0x6F6D: "DELAY1LP",
    0x6F76: "DELAY2",
    0x6F78: "DELAY2LP",
    0x6F81: "DELAY3",
    0x6F96: "SPRITEDRAW",
    # Entry point
    0x6FFE: "ENTRY",
    # Data tables
    0x7007: "COLORTBL",
    0x701A: "PLACESX",
    0x7022: "PLACESY",
    # Sound routines
    0x702B: "CLICK",
    0x7031: "ORPLOTS",
    0x703F: "PLOTS",
    # Screen/border initialization
    0x704D: "BORDER",
    0x7068: "BORDER1",
    0x707C: "BORDER2",
    0x7083: "BORDER3",
    0x7092: "BORDER4",
    0x7097: "BORDER5",
    0x7108: "BORDERTXT",
    0x7113: "BORDERDONE",
    # Joystick/paddle input
    0x711D: "CHKJOY",
    0x713B: "NOJOY",
    0x714C: "READPDL1",
    0x715B: "READPDL0",
    0x716E: "JOYUP",
    0x7175: "JOYLEFT",
    0x717C: "JOYDOWN",
    0x7183: "JOYRIGHT",
    # Sound effect
    0x7186: "SOUNDTICK",
    # Score display
    0x71B1: "PUTSCORE",
    # Lives display
    0x7200: "PUTLIVES",
    # Hits display
    0x723C: "PUTHITS",
    0x7239: "PUTNUM",
    # Food placement
    0x727E: "PLACEFOOD",
    # Player update (demo mode AI)
    0x72A4: "UPDATEYOU",
    # Sprite redraw comparison
    0x7300: "REDRAWCHECK",
    # Keyboard dispatch back-jump
    0x733F: "KBDJMP",
    # Keyboard dispatch
    0x7342: "KBDDISPATCH",
    0x7358: "MOVUP",
    0x7367: "MOVDO",
    0x7376: "MOVLE",
    0x7385: "MOVRI",
    # Draw player sprite
    0x7394: "DRAWYOU",
    0x73B8: "ERASEYOU",
    0x73CF: "SNOOKHIT",
    0x73DC: "SNOOKHIT1",
    0x73DF: "RESPAWN",
    0x73F7: "RESPAWN1",
    0x73FE: "RESPAWN2",
    # Death handler
    0x7404: "YOUDIED",
    0x7412: "STILMOR",
    0x7420: "CONTDIE",
    0x7427: "CONTDIE1",
    0x743F: "FLASHYOU",
    0x7456: "FLASHDRAW",
    0x7462: "DEATHWAIT",
    0x746B: "DEATHSOUND",
    0x7473: "TWOTONE",
    0x749E: "TWOTONE2",
    # Init cats
    0x74AB: "INITCAT",
    0x74C4: "INITCATDRAW",
    # Draw cat sprite
    0x74DE: "DRAWCAT",
    0x7534: "DRAWCATWRITE",
    # Cat AI direction
    0x7557: "CATDIR_AI",
    # Cat update loop
    0x7589: "UPCAT",
    0x7593: "UPCATLOOP",
    0x75AB: "CATMOVE",
    0x75CF: "CATERASE",
    0x75DD: "CATREDRAW",
    0x7605: "CATHITYOU",
    0x7618: "CATNOWALL",
    0x7629: "CATREVERSE",
    0x7631: "CATFINISH",
    0x7634: "SKIPCAT",
    0x7642: "CATRESET",
    0x764B: "CATRESETDIR",
    0x766D: "CATHITSND",
    0x7690: "CATDEATHSND",
    0x76A6: "CATDRAW2",
    0x76B7: "CATDRAW3",
    0x76C0: "CATTOFOOD",
    0x76D6: "FOODDRAW1",
    0x76E5: "FOODDONE",
    # Food animation
    0x76E9: "FOODANIM",
    0x7734: "DRAWFOOD",
    0x775E: "DRAWFOODSPRITE",
    # Level complete
    0x7766: "FINISHED",
    # Add score (BCD)
    0x777B: "ADDSCORE",
    # Level start / game init
    0x7796: "LEVELSTART",
    0x77A4: "LEVELINIT",
    0x77D4: "DRAWPLAYER",
    0x77DB: "PLACEFOODINIT",
    0x77E5: "INITCATS2",
    # Main game loop
    0x77E8: "MAINLOOP",
    0x77EA: "MAINLOOPINNER",
    0x77F7: "PAUSELOOP",
    0x77FA: "PAUSEWAIT",
    0x7804: "FIXSOUND",
    0x780A: "NOKEY",
    0x782E: "MAINLOOPTIMING",
    0x7838: "PAGESETUP",
    0x7859: "PAGEINIT1",
    0x7893: "DRAWFOODAT",
    # Frame update
    0x78A6: "UPDATEENEMIES",
    0x78B7: "UPDATEPLAYER",
    # GETTIME
    0x78D1: "GETTIME",
    # Plot vector table (identical to level1)
    0x7900: "DRAWVEC",
    0x7906: "DRAWVEC_OR",
    0x7909: "DRAWVEC_DIR",
    0x790F: "PLOTDIRECT",
    0x792F: "PLOTOR",
    0x7950: "PLOTRTS",
    0x7951: "HGRLO",
    # Title screen (identical to level1)
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
    # NumGen (identical to level1)
    0x8A00: "NUMGEN",
    0x8A3B: "NUMGENPLOT",
    0x8A4F: "NUMGENTBL",
    # Screen data references
    0x8805: "FONTREF",
    0x8F16: "HGRDATA1",
    0x8F52: "SPRITEPLOT2A",
    0x8F5F: "SPRITEPLOT2B",
    0x8F98: "HGRDATA2",
    # ChrGen (identical to level1)
    0x9000: "CHRGEN",
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
    0x93C9: "CLRSCRIMPL2",
    0x93FD: "ERABW2",
    0x9477: "HGR2LO",
    0x9537: "HGR2HI",
    # Additional internal targets
    0x6071: "BORDERINIT2",
    0x7004: "ENTRYJMP",
}

# ============================================================
# Data regions for level2
# ============================================================
DATA_REGIONS = [
    (0x4000, 0x5F80, "Hi-Res Graphics Page 1 - Level 2 playfield bitmap"),
    (0x5FA4, 0x6F41, "Hi-Res Graphics data (Pages 1+2 continued - no symbol table in level2)"),
    (0x7007, 0x702B, "Data tables: COLORTBL, PLACESX, PLACESY"),
    (0x78DD, 0x7900, "Table of $FF/$00 bytes between GETTIME and DRAWVEC (not code)"),
    (0x7951, 0x7A00, "HGRLO - Hi-Res screen address table (low bytes)"),
    (0x7A00, 0x8000, "HGRHI + Hi-Res screen fill data"),
    (0x8000, 0x8020, "Graphics pattern data"),
    (0x814F, 0x819F, "Encoded text strings (title/credits)"),
    (0x81BA, 0x81E0, "Character font bitmap data"),
    (0x81E0, 0x89FF, "Sprite shape tables"),
    (0x8A49, 0x8D00, "Font bitmap data and screen data"),
    (0x8D00, 0x9000, "Hi-Res address tables and screen data"),
    (0x90BE, 0x90C6, "Pixel mask table"),
    (0x90C6, 0x9300, "Hi-Res screen data + font character bitmaps"),
    (0x9477, 0x9600, "Hi-Res Page 2 address tables + trailing data"),
]

# ============================================================
# Section headers
# ============================================================
SECTION_HEADERS = {
    0x4000: """; ================================================================
; SNOOKUMS - Level 2
; By Jeff Koftinoff
; 1984, published through A.P.P.L.E. (Apple Pugetsound Program Library Exchange)
;
; Binary: level2.bin
; Load address: $4000
; Size: 22016 bytes ($5600)
; Memory range: $4000-$95FF
;
; Memory Map:
;   $4000-$5F7F  Hi-Res Page 1 graphics (level 2 playfield)
;   $5F80-$5F9E  Keyboard check / pause handler
;   $5FA4-$6F40  Hi-Res graphics data (extended - no symbol table)
;   $6F41-$6F95  Sprite init, page flip, delay routines
;   $6F96-$6FFD  Low-level sprite draw
;   $6FFE-$7006  Entry point -> JMP LEVELSTART
;   $7007-$702A  Data tables (colors, placement)
;   $702B-$704C  Sound/click routines
;   $704D-$711C  Screen/border initialization
;   $711D-$71B0  Joystick, paddle, sound tick
;   $71B1-$727D  Score, lives, hits display
;   $727E-$72A3  Food placement
;   $72A4-$7341  Player update (demo AI) + redraw
;   $7342-$7393  Keyboard dispatch (W/S/J/K movement)
;   $7394-$7403  Player sprite draw + collision
;   $7404-$74AA  Death handler, respawn, sound effects
;   $74AB-$74DD  Init cats
;   $74DE-$7588  Draw cat, cat direction AI
;   $7589-$76E8  Cat update loop, cat-player collision
;   $76E9-$7765  Food animation
;   $7766-$7795  Level complete + BCD score addition
;   $7796-$78DC  Level start + MAIN GAME LOOP + GETTIME
;   $78DD-$78FF  HGR page padding
;   $7900-$79F8  Plot vector table + HGRLO address table
;   $7A00-$7FFF  HGRHI + screen fill data
;   $8020-$819F  Title screen credits (identical to level1)
;   $81A0-$81BF  Screen dissolve effect (identical to level1)
;   $81E0-$89FF  Sprite shape data (identical to level1)
;   $8A00-$8CFF  NUMGEN rendering + fonts
;   $8D00-$8FFF  Address tables and screen data
;   $9000-$90BD  CHRGEN text rendering (identical to level1)
;   $9300-$9476  Sprite engine (XOR draw, clear, OR, direct write)
;   $9477-$95FF  Page 2 address tables
;
; Controls (same as level1):
;   W = Up,  S = Down,  J = Left,  K = Right
;   Ctrl-S = Toggle sound    Ctrl-T = Pause
;   ESC = Pause until keypress
;
; Differences from level1:
;   - No embedded assembler symbol table (more graphics data)
;   - Different level playfield artwork
;   - Code relocated to different addresses (same engine)
;   - NUMCATS = ((LEVEL/4) & 3) + 1 (slightly different formula)
;   - Sprite engine at $9300 (was at $7A00/$9300 in level1)
;
; ================================================================
""",

    0x5F80: """
; ----------------------------------------------------------------
; Keyboard check & pause toggle handler
; Checks for Ctrl-T to toggle pause flag at $50
; Falls through to joystick check or keyboard dispatch
; ----------------------------------------------------------------
""",
    0x5FA4: "",
    0x6F41: """
; ----------------------------------------------------------------
; Sprite initialization, page flip, and delay routines
; ----------------------------------------------------------------
""",
    0x6F52: """
; PAGESWITCH - Toggle display page variable ($62)
""",
    0x6F5F: """
; SELECTPAGE - Select HGR display page based on PAGEFLIP ($62)
""",
    0x6F6B: """
; DELAY1/DELAY2 - Timing delays using Monitor WAIT
""",
    0x6F96: """
; ----------------------------------------------------------------
; Low-level sprite column plot with shift/mask
; ----------------------------------------------------------------
""",
    0x6FFE: """
; ----------------------------------------------------------------
; ENTRY - Binary entry point
; Initializes $20=0 then jumps to LEVELSTART ($7796)
; ----------------------------------------------------------------
""",
    0x7007: """
; ----------------------------------------------------------------
; Data tables: color lookup, enemy placement coordinates
; ----------------------------------------------------------------
""",
    0x702B: """
; ----------------------------------------------------------------
; Sound routines: CLICK, ORPLOTS, PLOTS
; ----------------------------------------------------------------
""",
    0x704D: """
; ----------------------------------------------------------------
; BORDER - Game screen initialization
; Clears screen, draws playfield borders with alternating colors,
; renders game title text, switches to hi-res mode
; ----------------------------------------------------------------
""",
    0x711D: """
; ----------------------------------------------------------------
; CHKJOY - Joystick/paddle input handler
; Reads paddle buttons (PB0/PB1/PB2) and paddle position (PREAD)
; Maps paddle values to movement directions
; ----------------------------------------------------------------
""",
    0x7186: """
; ----------------------------------------------------------------
; SOUNDTICK - Descending tone sound effect with speaker clicks
; Respects SOUND mute flag ($84 bit 7)
; ----------------------------------------------------------------
""",
    0x71B1: """
; ----------------------------------------------------------------
; Score and status display routines
; PUTSCORE - Display BCD score using NUMGEN
; PUTLIVES - Display lives remaining
; PUTHITS  - Display hit count
; ----------------------------------------------------------------
""",
    0x727E: """
; ----------------------------------------------------------------
; PLACEFOOD - Place food item at random position
; Uses ROM pages ($F000, $F800) as random number source
; ----------------------------------------------------------------
""",
    0x72A4: """
; ----------------------------------------------------------------
; UPDATEYOU - Player update (demo mode auto-movement)
; In demo mode, reads pseudo-random values from ROM for movement.
; In play mode, jumps to keyboard/joystick handler.
; Clamps player position to playfield boundaries.
; ----------------------------------------------------------------
""",
    0x7342: """
; ----------------------------------------------------------------
; KBDDISPATCH - Keyboard dispatch for player movement
; W=$D7=Up, S=$D3=Down, J=$CA=Left, K=$CB=Right
; ----------------------------------------------------------------
""",
    0x7394: """
; ----------------------------------------------------------------
; DRAWYOU - Draw player sprite with collision detection
; ERASEYOU - Erase player at current position
; SNOOKHIT - Handle player collision with enemy
; ----------------------------------------------------------------
""",
    0x7404: """
; ----------------------------------------------------------------
; YOUDIED - Player death handler
; Decrements lives, flashes sprite, plays death sound
; If lives remain: respawn. Otherwise: game over.
; TWOTONE - Two-frequency sweep sound effect
; ----------------------------------------------------------------
""",
    0x74AB: """
; ----------------------------------------------------------------
; INITCAT - Initialize enemy cats
; Sets position from PLACESX/PLACESY tables,
; direction to 1 (right), walk counter to 5
; ----------------------------------------------------------------
""",
    0x74DE: """
; ----------------------------------------------------------------
; DRAWCAT - Enemy sprite rendering
; Selects shape based on CATDIR (left/right facing)
; Uses sprite engine at $9300 for XOR drawing
; ----------------------------------------------------------------
""",
    0x7557: """
; ----------------------------------------------------------------
; CATDIR_AI - Cat direction decision
; Compares cat position to player position
; Sets CATDIR bits: 0=left/right, 1=up, 2=down
; Enemies actively chase the player
; ----------------------------------------------------------------
""",
    0x7589: """
; ----------------------------------------------------------------
; UPCAT - Update all active enemy cats
; Main enemy AI loop: move, check collisions, handle death
; Converts dead cats to food items
; ----------------------------------------------------------------
""",
    0x76E9: """
; ----------------------------------------------------------------
; FOODANIM - Food item animation and drawing
; Loops through food slots, animates bounce, draws sprites
; ----------------------------------------------------------------
""",
    0x7766: """
; ----------------------------------------------------------------
; FINISHED - Level complete sequence
; ADDSCORE - Add to score using BCD arithmetic (SED/CLD)
; 3-byte BCD score: SCORELO($8A), SCOREHI($8B), SCOREHI1($8C)
; ----------------------------------------------------------------
""",
    0x7796: """
; ----------------------------------------------------------------
; LEVELSTART - Game initialization entry point
; Sets YOUHITS=3, calculates NUMCATS from LEVEL
; Falls through to LEVELINIT
;
; LEVELINIT - Set up screen, enemies, player position
; Main game loop at MAINLOOP ($77E8):
;   Outer: frame counter = $20 (32 frames)
;   Inner: check keys, update enemies, update player
;   Speed scaling: level < 15 = extra player updates
;                  level >= 15 = extra enemy updates (faster!)
; ----------------------------------------------------------------
""",
    0x78D1: """
; ----------------------------------------------------------------
; GETTIME - Calculate game speed from level number
; Higher level = lower delay = faster enemies
; Returns timing value in A for Monitor WAIT routine
; ----------------------------------------------------------------
""",
    0x7900: """
; ----------------------------------------------------------------
; Plot vector dispatch table (identical to level1)
; Used by ORPLOTS and PLOTS for single-pixel rendering
; ----------------------------------------------------------------
""",
    0x8020: """
; ----------------------------------------------------------------
; Title screen credits (identical to level1)
; "SYDNEY DEVELOPMENT CORPORATION PRESENTS" (left over from a 1984 pitch to that company; never shown to players)
; "SNOOKUMS"
; "BY JEFF KOFTINOFF"
; "COPYRIGHT (C)"
; ----------------------------------------------------------------
""",
    0x81A0: """
; ----------------------------------------------------------------
; XORSCREEN - Visual dissolve/scramble effect (identical to level1)
; XORs each screen byte with its low address byte
; ----------------------------------------------------------------
""",
    0x8A00: """
; ----------------------------------------------------------------
; NUMGEN - Character/number rendering on hi-res screen
; Draws score digits using bitmap font data
; ----------------------------------------------------------------
""",
    0x9000: """
; ----------------------------------------------------------------
; CHRGEN - Large character rendering system (identical to level1)
; Draws multi-pixel text characters with color patterns
; ----------------------------------------------------------------
""",
    0x9300: """
; ----------------------------------------------------------------
; Sprite engine: XOR draw with collision detection
; 5 entry points:
;   DRAW2    ($9300) - XOR sprite blit (collision detecting)
;   CLRSCRN2 ($9303) - Clear hi-res screen
;   ORPLOT2  ($9306) - OR pixel onto screen
;   PLOT2    ($9309) - Direct pixel write
;   STABW2   ($930C) - Direct sprite write (overwrite mode)
;
; Uses HGRLO2/HGRHI2 tables at $9477/$9537
; Collision detected by AND-ing sprite with screen (REPORT $1F)
; ----------------------------------------------------------------
""",
}


def _is_data_region(addr):
    for start, end, desc in DATA_REGIONS:
        if start <= addr < end:
            return True, desc
    return False, None


def _get_label(addr):
    return LABELS.get(addr, None)


def _format_abs_name(addr):
    if addr in LABELS:
        return LABELS[addr]
    if addr in HW_NAMES:
        return HW_NAMES[addr]
    if addr in ROM_NAMES:
        return ROM_NAMES[addr]
    return None


def disassemble_level2(data, load_addr):
    lines = []
    end_addr = load_addr + len(data)

    # First pass: find branch targets
    targets = set()
    pos = 0
    while pos < len(data):
        addr = load_addr + pos
        is_data, _ = _is_data_region(addr)
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

    for a in LABELS:
        if load_addr <= a < end_addr:
            targets.add(a)

    # Second pass: generate output
    pos = 0
    current_data_region = None

    while pos < len(data):
        addr = load_addr + pos

        if addr in SECTION_HEADERS:
            lines.append(SECTION_HEADERS[addr])

        is_data, desc = _is_data_region(addr)

        if is_data:
            region_end = addr
            for start, end, d in DATA_REGIONS:
                if start <= addr < end:
                    region_end = end
                    break

            if current_data_region != desc:
                current_data_region = desc
                label = _get_label(addr)
                if label:
                    lines.append(f"{label}:")

            chunk_end = min(region_end, end_addr)
            remaining = chunk_end - addr
            chunk_size = min(remaining, len(data) - pos)

            i = 0
            while i < chunk_size:
                row_addr = addr + i
                lbl = _get_label(row_addr)
                if lbl and i > 0:
                    lines.append(f"{lbl}:")

                n = min(16, chunk_size - i)
                for j in range(1, n):
                    if _get_label(row_addr + j):
                        n = j
                        break

                hex_bytes = data[pos + i : pos + i + n]
                byte_strs = ", ".join(f"${b:02X}" for b in hex_bytes)
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

        label = _get_label(addr)
        if label:
            lines.append(f"{label}:")
        elif addr in targets:
            lines.append(f"L_{addr:04X}:")

        opcode = data[pos]
        if opcode not in OPCODES:
            lines.append(f"        .BYTE ${opcode:02X}            ; ${addr:04X} - illegal opcode")
            pos += 1
            continue

        mnem, mode, nbytes = OPCODES[opcode]
        if pos + nbytes > len(data):
            lines.append(f"        .BYTE ${opcode:02X}            ; ${addr:04X} - truncated")
            pos += 1
            continue

        comment = ""
        operand = ""

        if mode == "IMP":
            operand = ""
        elif mode == "ACC":
            operand = "A"
        elif mode == "IMM":
            val = data[pos + 1]
            operand = f"#${val:02X}"
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
            name = _format_abs_name(abs_addr)
            if name:
                operand = f"{name}"
                comment = f"; ${abs_addr:04X}"
            else:
                operand = f"${abs_addr:04X}"
        elif mode == "ABX":
            abs_addr = data[pos + 1] | (data[pos + 2] << 8)
            name = _format_abs_name(abs_addr)
            if name:
                operand = f"{name},X"
                comment = f"; ${abs_addr:04X}"
            else:
                operand = f"${abs_addr:04X},X"
        elif mode == "ABY":
            abs_addr = data[pos + 1] | (data[pos + 2] << 8)
            name = _format_abs_name(abs_addr)
            if name:
                operand = f"{name},Y"
                comment = f"; ${abs_addr:04X}"
            else:
                operand = f"${abs_addr:04X},Y"
        elif mode == "IND":
            abs_addr = data[pos + 1] | (data[pos + 2] << 8)
            name = _format_abs_name(abs_addr)
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
            target_name = _get_label(target)
            if target_name:
                operand = target_name
            elif target in targets:
                operand = f"L_{target:04X}"
            else:
                operand = f"${target:04X}"

        inst = f"{mnem} {operand}".strip()
        addr_prefix = f"        {inst:<28s}"
        if comment:
            line = f"{addr_prefix}{comment}"
        else:
            line = addr_prefix.rstrip()
        lines.append(line)

        if mnem in ("RTS", "RTI") or (mnem == "JMP" and mode == "ABS"):
            lines.append("")

        pos += nbytes

    return lines


def main():
    data = open(os.path.join(_CATERKILLER_DIR, 'original', 'level2.bin'), 'rb').read()
    load_addr = 0x4000

    header_lines = []
    header_lines.append("; ================================================================")
    header_lines.append("; Zero-page variable definitions")
    header_lines.append("; (same engine as level1 - names from level1 symbol table)")
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

    code_lines = disassemble_level2(data, load_addr)

    with open(output_path('level2.s'), 'w') as f:
        for line in header_lines:
            f.write(line + '\n')
        for line in code_lines:
            f.write(line + '\n')

    print(f"Written level2.s ({len(header_lines) + len(code_lines)} lines)")


if __name__ == '__main__':
    main()
