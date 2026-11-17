#!/usr/bin/env python3
"""
Build annotated level3.s source file from level3.bin.
Level3 is VERY DIFFERENT from levels 1 and 2:
  - Load address $6000 (not $4000)
  - Size 13824 bytes ($3600), range $6000-$95FF
  - No page flipping - only uses HGR page 1 for display
  - Code lives within HGR page 2 memory ($7200-$77AD)
  - Different game mechanics: timed obstacle course (not cat-and-mouse)
  - BCD countdown timer instead of unlimited time
  - Obstacles with velocity tables (bouncing) instead of chasing AI
  - Joystick support via PREAD
  - 3 animated objects: food, ball, obstacles
  - Self-modifying code in sprite engine
"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CATERKILLER_DIR = os.path.join(_SCRIPT_DIR, '..')
sys.path.insert(0, _SCRIPT_DIR)  # find build_source and _guard next to this file, never in the cwd
from build_source import OPCODES, HW_NAMES, ROM_NAMES
from _guard import guarded_open as open, output_path  # refuse to overwrite source/ and sprites/


# ============================================================
# Zero-page variables for level3
# Many shared with levels 1/2, but some repurposed
# ============================================================
ZP_SYMBOLS = {
    0x00: "TEMP0",
    0x01: "TEMP1",
    0x02: "TEMP2",
    0x03: "COLORMASK",
    0x04: "TEMP4",
    0x09: "TEMP9",
    0x0A: "TEMPA",
    0x0E: "BITMASK",
    0x0F: "PIXPOS",
    0x10: "SHAPE",
    0x11: "COLOR",
    0x14: "SHPLO",
    0x15: "SHPHI",
    0x16: "TOLO",
    0x17: "TOHI",
    0x18: "XCOORD",
    0x19: "YCOORD",
    0x1A: "XX",
    0x1B: "YY",
    0x1C: "WIDTH",
    0x1D: "HEIGHT",
    0x1E: "TEMPWID",
    0x1F: "REPORT",
    0x20: "COLORCYCLE",
    0x4E: "RNDCOUNT",
    0x50: "PAUSEFLAG",
    0x78: "LEVEL",
    0x80: "YOULIVES",
    0x84: "SOUND",
    0x88: "DEMO",
    0x8A: "SCORELO",
    0x8B: "SCOREHI",
    0x8C: "SCOREHI2",
    0x8D: "OBSTPTRLO",
    0x8E: "OBSTPTRHI",
    0x8F: "OBSTCOUNT",
    0x90: "PLAYERX",
    0x91: "PLAYERY",
    0x92: "SAVEX",
    0x93: "FOODY",
    0x94: "FOODDELAY",
    0x95: "FOODDIR",
    0x96: "BALLY",
    0x97: "BALLDELAY",
    0x98: "BALLDIR",
    0x99: "BALLPOS",
    0x9A: "BALLTIMER",
    0x9B: "BALLMOVDIR",
    0x9C: "COLLCOUNT",
    0x9D: "TIMERLO",
    0x9E: "TIMERHI",
    0x9F: "DIFFICULTY",
    0xA0: "ACTIVECNT",
    0xC0: "TEMPC0",
    0xF0: "STRLO",
    0xF1: "STRHI",
    0xFC: "PTR1LO",
    0xFD: "PTR1HI",
    0xFE: "PTR2LO",
    0xFF: "PTR2HI",
}

# ============================================================
# Code labels for level3
# ============================================================
LABELS = {
    # Entry / Level initialization ($7200)
    0x7200: "LEVELINIT",
    0x721C: "CLEARSCREENS",
    0x7229: "CLEARLOOP",
    0x7240: "DRAWOBSTACLES",
    0x7255: "INITGAMESTATE",
    0x728D: "INITRANDOM",
    0x72AE: "COPYVELTABLE",
    0x72B7: "STARTGAME",

    # Draw obstacle (initial setup)
    0x72BD: "DRAWOBST_INIT",
    0x72F0: "DRAWOBST_QUICK",

    # Joystick handler
    0x72F3: "CHKJOY",
    0x730C: "JOYRTS",
    0x730D: "JOYLEFT",
    0x7312: "JOYRIGHT",

    # BCD score addition
    0x7317: "ADDSCORE",

    # Score / status display
    0x732A: "PUTSCORE",
    0x7379: "PUTLIVES",

    # Timer countdown
    0x73B5: "COUNTDOWN",
    0x73C6: "DRAWTIME",

    # Draw/check player
    0x7413: "DRAWPLAYER",
    0x742B: "DRAWPLAYER_CLEAR",

    # Data tables
    0x742E: "INITDIRTBL",
    0x7438: "ENEMYX",
    0x743D: "ENEMYY",
    0x7442: "ENEMYVEL",
    0x7447: "ENEMYACTIVE",

    # Draw single enemy obstacle
    0x744C: "DRAWENEMY",
    0x7472: "DRAWENEMY_RTS",
    0x7473: "DRAWENEMY_CLEAR",

    # Check collision (entered from main loop)
    0x7478: "CHECKCOLL",
    0x7498: "CHECKCOLL_KBD",
    0x749B: "KBDDISPATCH",
    0x74A6: "NOCOLLISION",
    0x74AB: "COLL_HITBORDER",
    0x74B3: "COLL_DEATH",
    0x74B8: "COLL_HITCLR",
    0x74BD: "COLL_ADVANCE",

    # Sound on collision
    0x74CF: "COLLSOUND",
    0x74DD: "COLLSOUND_END",
    0x74E0: "COLLSOUND_RTS",

    # Movement
    0x74E1: "MOVELEFT",
    0x74E8: "MOVERIGHT",

    # Check all enemies
    0x74EF: "CHKENEMIES",
    0x74F5: "CHKENEMYLOOP",
    0x752B: "ENEMYHITSOUND",
    0x7557: "NEXTENEMY",

    # Draw and check obstacle
    0x7564: "DRAWCHKOBST",
    0x757A: "OBSTBOUNCE",

    # Update all enemies
    0x7580: "UPDATEENEMIES",
    0x7582: "UPDATELOOP",
    0x75DA: "UPDATENEXT",
    0x75DE: "UPDATE_ADVANCEY",
    0x75E6: "UPDATE_RETREATY",

    # Food animation
    0x75EB: "FOODANIM",
    0x75F2: "FOODMOVE",
    0x761C: "FOODBOUNCE",
    0x7622: "FOODPAUSE",

    # Ball animation
    0x7627: "BALLANIM",
    0x762E: "BALLMOVE",
    0x765B: "BALLBOUNCE",
    0x7661: "BALLPAUSE",

    # Ball2 animation (second bouncing object)
    0x7666: "BALL2ANIM",
    0x766D: "BALL2MOVE",
    0x7692: "BALL2BOUNCE",

    # === MAIN LOOP ===
    0x769D: "MAINLOOP",
    0x76AF: "MAINFRAME",
    0x76B3: "MAININNER",
    0x76E0: "TOGGLESOUND",
    0x76E6: "CHECKDEMO",
    0x76EF: "CHECKSPEED",
    0x76FB: "FASTMODE",
    0x7701: "DECFRAME",
    0x770D: "EXIT",

    # Death handler
    0x7710: "YOUDIED",
    0x771D: "DEATHSND",
    0x7751: "DEATHEND",

    # Bonus scoring
    0x7752: "BONUSSCORE",

    # Speed control
    0x775D: "SPEEDCTRL",
    0x7770: "SPEEDRTS",

    # Draw borders
    0x7771: "DRAWBORDER",
    0x7773: "BORDERLOOP",

    # Plot routines ($7900)
    0x7900: "PLOTVEC1",
    0x7903: "PLOTVEC2",
    0x7906: "PLOTOR",
    0x7909: "PLOTDIRECT",
    0x790F: "PLOTDIR_IMPL",
    0x792F: "PLOTOR_IMPL",
    0x7950: "PLOTRTS",

    # HGR lookup tables
    0x7951: "HGRLO",
    0x7A11: "HGRHI",

    # Keyboard pause handler ($7FD0)
    0x7FD0: "KBDPAUSE",
    0x7FDD: "KBDTOGGLE",
    0x7FE8: "KBDCHECK_JOY",
    0x7FEE: "KBDCHECK_KEY",

    # Title screen ($8022)
    0x8022: "TITLESCREEN",
    0x8120: "TITLEANIM",
    0x813A: "DRAWTEXT",
    0x814E: "DRAWTEXT_RTS",
    0x814F: "STR_COMPANY",
    0x8156: "STR_DEVELOPMENT",
    0x8162: "STR_CORPORATION",
    0x816E: "STR_PRESENTS",
    0x8177: "STR_SNOOKUMS",
    0x8180: "STR_BYJEFF",
    0x8192: "STR_COPYRIGHT",

    # XOR screen effect
    0x81A0: "XORSCREEN",

    # Digit display
    0x8A00: "DRAWDIGIT",
    0x8A3B: "DIGITPLOT",
    0x8A42: "DIGITPLOT2",

    # Pixel sprite renderer
    0x9000: "PIXRENDER",
    0x9019: "PIXROW",
    0x901E: "PIXBIT",
    0x9029: "PIXBITLOOP",
    0x903B: "PIXBLANK",
    0x9047: "PIXNEXT",
    0x9065: "PIXNEXTBIT",
    0x9068: "PIXNEXTROW",
    0x906B: "PIXCOLOR",
    0x9083: "PIXCOLOR2",
    0x9087: "PIXCOLORPLOT",
    0x90BD: "PIXRTS",

    # Pixel mask table
    0x90BE: "PIXMASK",

    # Sprite engine
    0x9300: "DRAW_NOCOLL",
    0x9303: "DRAW_COLL",
    0x9332: "DRAWCOLL_ROW",
    0x934D: "DRAWCOLL_COL",
    0x9355: "DRAWCOLL_PLOT",
    0x936C: "DRAWCOLL_HIT",
    0x9375: "DRAWNOCOLL_ENTRY",
    0x93A4: "DRAWNOCOLL_ROW",
    0x93BF: "DRAWNOCOLL_COL",
    0x93C7: "DRAWNOCOLL_PLOT",
    0x93DE: "DRAWNOCOLL_HIT",
    0x93E7: "CALCSPRADDR",
    0x9405: "ADVANCEPTR",

    # HGR tables for sprite engine
    0x940D: "SPRLO",
    0x94CD: "SPRHI",
}

# ============================================================
# Data regions for level3
# ============================================================
DATA_REGIONS = [
    # HGR page 2 graphics data
    (0x6000, 0x7000, "HGR Page 2 graphics data - obstacle/playfield shapes"),
    (0x7000, 0x7100, "Obstacle X position lookup table"),
    (0x7100, 0x7200, "Obstacle Y/attribute lookup table"),
    # Code at $7200-$77AD
    # Data tables within code (velocity data at $742E-$744B)
    (0x742E, 0x744C, "Enemy data tables: INITDIRTBL, ENEMYX, ENEMYY, ENEMYVEL, ENEMYACTIVE"),
    # Graphics/sprite data after main code
    (0x77AE, 0x7900, "Sprite/shape graphics data"),
    # Code at $7900-$7950 (plot routines)
    # HGR lookup tables
    (0x7951, 0x7A11, "HGRLO - Hi-Res screen line address table (low bytes)"),
    (0x7A11, 0x7AD1, "HGRHI - Hi-Res screen line address table (high bytes)"),
    # More sprite/graphics data
    (0x7AD1, 0x7FD0, "Sprite graphics data (obstacle shapes, borders)"),
    # Code at $7FD0-$7FF3 (keyboard handler)
    (0x7FF4, 0x8000, "Graphics padding data"),
    # Title screen area
    (0x8000, 0x8022, "Title screen shape data"),
    # Code at $8022-$80F4 (title screen drawing)
    (0x80F5, 0x8120, "Title screen shape/sprite data"),
    # Code at $8120-$814E
    (0x814F, 0x81A0, "Encoded text strings (title/credits)"),
    # Code at $81A0-$81B9 (XOR screen)
    (0x81BA, 0x8A00, "Character font bitmaps, sprite shape data"),
    # Code at $8A00-$8A48 (digit display)
    (0x8A49, 0x9000, "Digit font data, obstacle shape data"),
    # Code at $9000-$90BD (pixel renderer)
    (0x90BE, 0x90C6, "PIXMASK - Pixel bit mask lookup table"),
    (0x90C6, 0x9300, "Sprite/shape graphics data"),
    # Code at $9300-$940C (sprite engine)
    (0x940D, 0x94CD, "SPRLO - Sprite engine line address table (low bytes)"),
    (0x94CD, 0x958D, "SPRHI - Sprite engine line address table (high bytes)"),
    (0x958D, 0x9600, "Trailing padding/data"),
]

# ============================================================
# Section headers
# ============================================================
SECTION_HEADERS = {
    0x6000: """; ================================================================
; SNOOKUMS - Level 3 (Obstacle Course)
; By Jeff Koftinoff
; 1984, published through A.P.P.L.E. (Apple Pugetsound Program Library Exchange)
;
; Binary: level3.bin
; Load address: $6000
; Size: 13824 bytes ($3600)
; Memory range: $6000-$95FF
;
; IMPORTANT: Level 3 is VERY DIFFERENT from levels 1 and 2!
;
; Key differences:
;   - Load address $6000 (overlaps HGR Page 2)
;   - NO page flipping - only HGR Page 1 used for display
;   - Code resides in HGR Page 2 memory ($7200-$77AD)
;   - Different game mechanics: timed obstacle course
;   - BCD countdown timer (not unlimited time)
;   - Bouncing obstacles with velocity tables (not chasing AI)
;   - Joystick support via PREAD ($FB1E)
;   - Self-modifying code in sprite engine
;   - 3-byte BCD score ($8A-$8C)
;   - Multiple animated objects (food, ball, ball2)
;
; Memory Map:
;   $6000-$6FFF  HGR Page 2 data (obstacle shapes in scanlines)
;   $7000-$70FF  Obstacle X position lookup table
;   $7100-$71FF  Obstacle Y/attribute lookup table
;   $7200-$72BA  Level initialization (ENTRY POINT at $7200)
;   $72BD-$72F0  Initial obstacle drawing
;   $72F3-$730C  Joystick input handler
;   $730D-$7316  Direction jumps (left/right)
;   $7317-$7329  BCD add score (SED/CLD arithmetic)
;   $732A-$73B4  Score display (6-digit BCD via DRAWDIGIT)
;   $73B5-$7412  Timer countdown (BCD decrement, carry=time up)
;   $7413-$742D  Draw/check player position
;   $742E-$744B  Enemy data tables (position, velocity, active)
;   $744C-$74EE  Enemy drawing, collision, movement
;   $74EF-$7563  Check all enemy collisions
;   $7564-$757F  Draw obstacle with border bounce
;   $7580-$75DD  Update all enemies (movement + wall bounce)
;   $75EB-$7626  Food animation (vertical bounce)
;   $7627-$769C  Ball animation (vertical bounce, 2 objects)
;   $769D-$770D  MAIN GAME LOOP (keyboard, updates, timer)
;   $7710-$7751  Death handler (sound, restart/game over)
;   $7752-$775C  Bonus score for eating food
;   $775D-$7770  Speed control (WAIT delay from level)
;   $7771-$77AD  Draw borders on both HGR pages
;   $77AE-$78FF  Sprite/shape graphics data
;   $7900-$7950  Plot routines (direct write + OR mode)
;   $7951-$7AD0  HGR line address lookup tables
;   $7AD1-$7FCF  More sprite graphics data
;   $7FD0-$7FF3  Keyboard pause handler
;   $8000-$8021  Title screen shape data
;   $8022-$80F4  Title screen drawing code
;   $80F5-$811F  Title screen shapes
;   $8120-$814E  Title animation (wait, XOR, text)
;   $814F-$819F  Encoded text strings (credits)
;   $81A0-$81B9  XOR screen dissolve effect
;   $81BA-$89FF  Character fonts + sprite shape data
;   $8A00-$8A48  Digit display (DRAWDIGIT)
;   $8A49-$8FFF  Digit fonts + shape data
;   $9000-$90BD  Pixel sprite renderer (PIXRENDER)
;   $90BE-$90C5  Pixel bit mask table
;   $90C6-$92FF  More sprite/shape data
;   $9300-$940C  Sprite engine (draw with/without collision)
;   $940D-$958C  Sprite engine address tables
;   $958D-$95FF  Trailing data
;
; Controls:
;   J/$CA = Left,  K/$CB = Right (horizontal only!)
;   Joystick: Paddle 0 = left/right (via PREAD)
;   Ctrl-S/$93 = Toggle sound
;   Ctrl-T/$94 = Toggle pause
;   ESC/$9B = Pause until keypress
;
; Game mechanics:
;   - Player moves LEFT/RIGHT only along bottom of screen
;   - Obstacles bounce vertically with random velocities
;   - Timer counts down in BCD; when it expires, level ends
;   - Collision with obstacle = death (if collcount >= 4)
;   - Eating food = +$50 points + sound
;   - Level increases difficulty (more obstacles, faster speed)
;
; ================================================================
""",

    0x7200: """
; ----------------------------------------------------------------
; LEVELINIT - Entry point for level 3
; Clears both HGR screens ($2000-$3FFF, $4000-$5FFF)
; Sets up HGR mode (page 1 only, no page flip)
; Draws initial obstacles from lookup tables
; Initializes player position, score display, timer
; Generates random enemy positions from ROM tables
; ----------------------------------------------------------------
""",

    0x72BD: """
; ----------------------------------------------------------------
; DRAWOBST_INIT - Draw an obstacle at initial position
; Uses self-modifying code to toggle sprite engine between
; OR-drawing ($9355) and direct-drawing ($93C7) modes
; ----------------------------------------------------------------
""",

    0x72F3: """
; ----------------------------------------------------------------
; CHKJOY - Joystick input handler
; Checks paddle buttons PB0, PB1, PB2 (all three at once)
; If all pressed: no movement (return)
; Reads Paddle 0 via PREAD ($FB1E)
; Value < $30: go left, > $D0: go right
; ----------------------------------------------------------------
""",

    0x7317: """
; ----------------------------------------------------------------
; ADDSCORE - Add BCD value in A to 3-byte score
; Uses SED/CLD for decimal mode arithmetic
; Score bytes: SCORELO($8A), SCOREHI($8B), SCOREHI2($8C)
; ----------------------------------------------------------------
""",

    0x732A: """
; ----------------------------------------------------------------
; PUTSCORE - Display 6-digit BCD score using DRAWDIGIT
; Also displays lives count and level number
; PUTLIVES at $7379 - display lives and level
; ----------------------------------------------------------------
""",

    0x73B5: """
; ----------------------------------------------------------------
; COUNTDOWN - BCD timer countdown
; Decrements TIMERHI:TIMERLO by $10 (in BCD mode)
; Displays 4-digit timer on screen
; Returns carry SET when timer reaches zero (time up!)
; ----------------------------------------------------------------
""",

    0x7413: """
; ----------------------------------------------------------------
; DRAWPLAYER - Draw player sprite and check collision
; Draws at position (PLAYERX, PLAYERY) using sprite engine
; Checks REPORT ($1F) for collision detection
; ----------------------------------------------------------------
""",

    0x744C: """
; ----------------------------------------------------------------
; DRAWENEMY - Draw a single enemy obstacle
; X = enemy index into ENEMYX/ENEMYY/ENEMYACTIVE tables
; If active=0, skip. Draws using sprite engine ($9303)
; REPORT ($1F) set if collision detected
; ----------------------------------------------------------------
""",

    0x7478: """
; ----------------------------------------------------------------
; CHECKCOLL - Main collision/movement handler
; Called each frame from DRAWPLAYER return
; If collision=$7E (border): hit boundary
; In demo mode: use ROM-based pseudo-random for movement
; In play mode: jump to KBDPAUSE ($7FD0) for input
; Keyboard dispatch: J=$CA=left, K=$CB=right
; ----------------------------------------------------------------
""",

    0x74EF: """
; ----------------------------------------------------------------
; CHKENEMIES - Check collision between player and all enemies
; Loops through all active enemies (X = DIFFICULTY downto 0)
; Bounds-checking: compares PLAYERX±range vs ENEMYX/ENEMYY
; On hit: play sound, add score, deactivate enemy
; If all enemies cleared: jump to BONUSSCORE
; If COLLCOUNT < 4: ignored (grace period)
; If COLLCOUNT >= 4: death! Jump to YOUDIED
; ----------------------------------------------------------------
""",

    0x7580: """
; ----------------------------------------------------------------
; UPDATEENEMIES - Update all enemy positions
; Moves each enemy horizontally by its velocity (ENEMYVEL)
; On wall collision: reverse direction (flip velocity)
; Advances Y position incrementally
; ----------------------------------------------------------------
""",

    0x75EB: """
; ----------------------------------------------------------------
; FOODANIM - Food sprite animation
; Moves food vertically, bouncing between Y limits
; Uses FOODDELAY for timing, FOODDIR for direction
; ----------------------------------------------------------------
""",

    0x7627: """
; ----------------------------------------------------------------
; BALLANIM / BALL2ANIM - Ball sprite animations
; Two independent bouncing ball objects
; Each has position, delay, and direction state
; ----------------------------------------------------------------
""",

    0x769D: """
; ----------------------------------------------------------------
; MAINLOOP - Main game loop
; Structure:
;   1. Draw border, update enemies, update food/ball
;   2. Display score and timer
;   3. Check enemies for collision
;   4. Handle keyboard (Ctrl-S=sound, ESC=pause)
;   5. If demo mode: check keyboard for exit
;   6. Speed control based on level number
;   7. Frame counter ($FD): 128 iterations per outer loop
;   8. Call COUNTDOWN - if timer expired, continue
;   9. Otherwise: next outer frame
;
; Key press in non-demo: JMP $0803 (return to DOS)
; ----------------------------------------------------------------
""",

    0x7710: """
; ----------------------------------------------------------------
; YOUDIED - Player death handler
; Decrements lives ($80), plays descending sweep sound
; Displays updated score, then restarts level
; If lives=0: return (game over back to caller)
; ----------------------------------------------------------------
""",

    0x7752: """
; ----------------------------------------------------------------
; BONUSSCORE - Award points for clearing food
; Adds $10 (BCD) per food eaten, calls COUNTDOWN check
; Loops until timer expires
; ----------------------------------------------------------------
""",

    0x775D: """
; ----------------------------------------------------------------
; SPEEDCTRL - Speed control based on level number
; Lower levels get more delay (easier), higher levels less
; Uses WAIT ($FCA8) ROM routine for timing
; Levels >= 15 ($0F): no delay at all
; ----------------------------------------------------------------
""",

    0x7771: """
; ----------------------------------------------------------------
; DRAWBORDER - Draw border lines on both HGR pages
; Writes $D4/$D5 border bytes to left/right columns
; Addresses both pages simultaneously (XOR $60 trick)
; ----------------------------------------------------------------
""",

    0x7900: """
; ----------------------------------------------------------------
; Plot routines
; PLOTOR   ($7906) - OR pixel into screen (for additive drawing)
; PLOTDIRECT ($7909) - Direct write pixel (for overwrite)
; Both write to HGR Page 1 AND Page 2 simultaneously
; Uses HGRLO/HGRHI lookup tables at $7951/$7A11
; ----------------------------------------------------------------
""",

    0x7FD0: """
; ----------------------------------------------------------------
; KBDPAUSE - Keyboard handler with pause toggle
; Checks for Ctrl-T ($94) to toggle pause mode ($50)
; If not paused: reads joystick via CHKJOY or keyboard
; Returns to KBDDISPATCH for J/K key handling
; ----------------------------------------------------------------
""",

    0x8022: """
; ----------------------------------------------------------------
; TITLESCREEN - Title screen credits drawing
; Displays text strings using DRAWTEXT + PIXRENDER:
;   "SYDNEY DEVELOPMENT CORPORATION PRESENTS" (left over from a 1984 pitch to that company; never shown to players)
;   "SNOOKUMS"
;   "BY JEFF KOFTINOFF"
;   "COPYRIGHT (C)"
; Also draws decorative sprites around title
; NOTE: Called from external module, not from level3 code
; ----------------------------------------------------------------
""",

    0x8120: """
; ----------------------------------------------------------------
; TITLEANIM - Title screen animation
; Waits using WAIT ($FCA8), then does XOR screen effect
; More waits, then returns
; ----------------------------------------------------------------
""",

    0x813A: """
; ----------------------------------------------------------------
; DRAWTEXT - Render encoded text string
; Pointer at ($F0): bytes = character indices (0=space, 1=A, ...)
; Terminates when byte >= $80
; Each character drawn via PIXRENDER ($9000)
; Advances XCOORD position after each character
; ----------------------------------------------------------------
""",

    0x81A0: """
; ----------------------------------------------------------------
; XORSCREEN - Screen dissolve/scramble effect
; XORs each byte in $2000-$3FFF with its address low byte
; Creates visual noise/transition effect
; ----------------------------------------------------------------
""",

    0x8A00: """
; ----------------------------------------------------------------
; DRAWDIGIT - Render a score digit on the hi-res screen
; Input: SHAPE($10) = digit value 0-9
;        XX($1A) = X position, YY($1B) = Y position
;        COLORMASK($03) = color pattern
; Uses PLOTDIRECT ($7909) via DIGITPLOT helper
; Renders 16-row × 2-column digit from font data
; ----------------------------------------------------------------
""",

    0x9000: """
; ----------------------------------------------------------------
; PIXRENDER - Pixel-level sprite renderer
; Input: A = character/sprite index (×8 for table offset)
;        XCOORD($1A), YCOORD($1B), WIDTH($1C), HEIGHT($1D)
;        COLORMASK($03) = color pattern
; Reads 8-byte sprite data from $9100 area
; Renders each bit as a pixel using PLOTOR ($7906)
; Handles Apple II hi-res color fringing (odd/even byte)
; ----------------------------------------------------------------
""",

    0x9300: """
; ----------------------------------------------------------------
; Sprite engine
; Two entry points:
;   DRAW_NOCOLL ($9300) - Draw sprite, no collision check
;     JMP to $9375 (DRAWNOCOLL_ENTRY)
;   DRAW_COLL   ($9303) - Draw sprite with collision detect
;     Writes collision info to REPORT ($1F)
;
; Self-modifying code: instructions at $9355 and $93C7
; are modified at runtime (by DRAWOBST_INIT at $72BD)
; to switch between OR-merge and direct-write modes
;
; Uses SPRLO/SPRHI tables at $940D/$94CD for HGR addresses
; Addresses both pages via XOR $60 trick (page 1 + page 2)
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


def format_zp_comment(addr):
    return ZP_SYMBOLS.get(addr, None)


def disassemble_level3(data, load_addr):
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
    data = open(os.path.join(_CATERKILLER_DIR, 'original', 'level3.bin'), 'rb').read()
    load_addr = 0x6000

    header_lines = []
    header_lines.append("; ================================================================")
    header_lines.append("; Zero-page variable definitions (Level 3)")
    header_lines.append("; Many shared with levels 1/2, some repurposed")
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

    code_lines = disassemble_level3(data, load_addr)

    with open(output_path('level3.s'), 'w') as f:
        for line in header_lines:
            f.write(line + '\n')
        for line in code_lines:
            f.write(line + '\n')

    print(f"Written level3.s ({len(header_lines) + len(code_lines)} lines)")


if __name__ == '__main__':
    main()
