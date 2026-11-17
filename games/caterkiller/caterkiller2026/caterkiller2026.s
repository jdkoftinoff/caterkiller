
; Level map layout (see level1.s .. level4.s):
;   +0   player start X, Y
;   +2   three elevators, 8 bytes each (X, Y, TOP, MID, BOT, DIR, PAUSE, DELAY)
;   +26  five enemy start positions, X, Y each
;   +36  obstacle count-1, then that many X, Y pairs
PLAYER_START_X_OFFSET   = 0
PLAYER_START_Y_OFFSET   = 1
ELEV_1_OFFSET           = 2
ELEV_2_OFFSET           = 10
ELEV_3_OFFSET           = 18
ENEMY_START_OFFSET      = 26
ENEMY_COUNT_OFFSET      = 36
OBSTACLE_COUNT_OFFSET   = 37
OBSTACLES_OFFSET        = 38

TEMP0                   = $00
TEMP1                   = $01
TEMP2                   = $02
TEMP3                   = $03
TEMP4                   = $04
TEMP5                   = $05
TEMP6                   = $06
TEMP9                   = $09
TEMPA                   = $0A
BITMASK                 = $0E
PIXPOS                  = $0F
SHAPE                   = $10
COLOR                   = $11
SHPLO                   = $14
SHPHI                   = $15
TOLO                    = $16
TOHI                    = $17
XCOORD                  = $18
YCOORD                  = $19
XX                      = $1A
YY                      = $1B
WIDTH                   = $1C
HEIGHT                  = $1D
TEMPWID                 = $1E
REPORT                  = $1F
COLORCYCLE              = $20
CURRENT_LEVEL_LO        = $21
CURRENT_LEVEL_HI        = $22
CURRENT_LEVEL_NUM       = $23

ELEVATORS_LO            = $24
ELEVATORS_HI            = $25

ELEV3_Y                 = $30
ELEV3_DELAY             = $31
ELEV3_DIR               = $32
ELEV3_POS               = $33
ELEV3_TIMER             = $34
ELEV3_MOVDIR            = $35
RNDCOUNT                = $4E
PAUSEFLAG               = $50
LEVEL                   = $78
YOULIVES                = $80
SOUND                   = $84
DEMO                    = $88
SCORELO                 = $8A
SCOREHI                 = $8B
SCOREHI2                = $8C
OBSTPTRLO               = $8D
OBSTPTRHI               = $8E
OBSTCOUNT               = $8F
PLAYERX                 = $90
PLAYERY                 = $91
SAVEX                   = $92
ELEV1_Y                 = $93
ELEV1_DELAY             = $94
ELEV1_DIR               = $95
ELEV2_Y                 = $96
ELEV2_DELAY             = $97
ELEV2_DIR               = $98
ELEV2_POS               = $99
ELEV2_TIMER             = $9A
ELEV2_MOVDIR            = $9B
COLLCOUNT               = $9C
TIMERLO                 = $9D
TIMERHI                 = $9E
DIFFICULTY              = $9F
ACTIVECNT               = $A0
TEMPC0                  = $C0
STRLO                   = $F0
STRHI                   = $F1
PTR1LO                  = $FC
PTR1HI                  = $FD
PTR2LO                  = $FE
PTR2HI                  = $FF

; ================================================================
; Apple II hardware addresses
; ================================================================

KEYBOARD                = $C000
KBDSTRB                 = $C010
SPKR                    = $C030
TXTCLR                  = $C050
TXTSET                  = $C051
MIXCLR                  = $C052
MIXSET                  = $C053
LOWSCR                  = $C054
HISCR                   = $C055
LORES                   = $C056
HIRES                   = $C057
VBLREG                  = $C07E         ; emulator: browser frame counter (~60Hz), read to sync timing
PB0                     = $C061
PB1                     = $C062
PB2                     = $C063

; ================================================================
; Apple II ROM routines
; ================================================================

PREAD                   = $FB1E
HOME                    = $FC58
WAIT                    = $FCA8
COUT                    = $FDED

        .ORG $6000

; ================================================================
; SNOOKUMS - Level 3 (Obstacle Course)
; By Jeff Koftinoff
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
;   - Multiple animated objects (elevator 1, elevator 2, elevator 3)
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
;   $75EB-$7626  Elevator animation (vertical bounce)
;   $7627-$769C  Elevator animation (vertical bounce, 2 objects)
;   $769D-$770D  MAIN GAME LOOP (keyboard, updates, timer)
;   $7710-$7751  Death handler (sound, restart/game over)
;   $7752-$775C  Bonus score for reaching elevator
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
;   - Eating elevator = +$50 points + sound
;   - Level increases difficulty (more obstacles, faster speed)
;
; Each sprite page holds the sprite at offset $00 (even byte columns).
; Sprites drawn with COLORCYCLE bit 7 set also need a copy at offset $80
; (odd byte columns); only SHAPE_04 has one. The rest of each page is
; left zero (.ALIGN / .ALIGNPAGE).

; ================================================================

; ----------------------------------------------------------------
; SHAPE_00_V0 at $6000
; Width: 4 bytes (28 pixels), Height: 18 rows
; ----------------------------------------------------------------
SHAPE_00_V0:
        .BYTE $04, $12                  ; width=4, height=18
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $F8, $81, $80        ; |..........#####.............|
        .BYTE $80, $F6, $86, $80        ; |........##.###.##...........|
        .BYTE $80, $AA, $85, $80        ; |........#.#.#.#.#...........|
        .BYTE $80, $F7, $8E, $80        ; |.......###.###.###..........|
        .BYTE $80, $DF, $8F, $80        ; |.......#####.#####..........|
        .BYTE $80, $DE, $87, $80        ; |........####.####...........|
        .BYTE $80, $F8, $81, $80        ; |..........#####.............|
        .BYTE $80, $D8, $81, $80        ; |..........##.##.............|
        .BYTE $80, $DE, $81, $80        ; |........####.##.............|
        .BYTE $80, $DE, $81, $80        ; |........####.##.............|
        .BYTE $80, $C0, $81, $80        ; |.............##.............|
        .BYTE $80, $C0, $87, $80        ; |.............####...........|
        .BYTE $80, $C0, $87, $80        ; |.............####...........|
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $FF, $80, $80        ; |.......#######..............|
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $80, $80, $80        ; |............................|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_00_V1 at $6100
; Width: 4 bytes (28 pixels), Height: 18 rows
; ----------------------------------------------------------------
SHAPE_00_V1:
        .BYTE $04, $12                  ; width=4, height=18
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $E0, $87, $80        ; |............#####...........|
        .BYTE $80, $D8, $9B, $80        ; |..........##.###.##.........|
        .BYTE $80, $A8, $95, $80        ; |..........#.#.#.#.#.........|
        .BYTE $80, $DC, $BB, $80        ; |.........###.###.###........|
        .BYTE $80, $FC, $BE, $80        ; |.........#####.#####........|
        .BYTE $80, $F8, $9E, $80        ; |..........####.####.........|
        .BYTE $80, $E0, $87, $80        ; |............#####...........|
        .BYTE $80, $E0, $86, $80        ; |............##.##...........|
        .BYTE $80, $F8, $86, $80        ; |..........####.##...........|
        .BYTE $80, $F8, $86, $80        ; |..........####.##...........|
        .BYTE $80, $80, $86, $80        ; |...............##...........|
        .BYTE $80, $80, $9E, $80        ; |...............####.........|
        .BYTE $80, $80, $9E, $80        ; |...............####.........|
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $FF, $80, $80        ; |.......#######..............|
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $80, $80, $80        ; |............................|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_00_V2 at $6200
; Width: 5 bytes (35 pixels), Height: 18 rows
; ----------------------------------------------------------------
SHAPE_00_V2:
        .BYTE $05, $12                  ; width=5, height=18
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $9F, $80, $80   ; |..............#####................|
        .BYTE $80, $E0, $EE, $80, $80   ; |............##.###.##..............|
        .BYTE $80, $A0, $D5, $80, $80   ; |............#.#.#.#.#..............|
        .BYTE $80, $F0, $EE, $81, $80   ; |...........###.###.###.............|
        .BYTE $80, $F0, $FB, $81, $80   ; |...........#####.#####.............|
        .BYTE $80, $E0, $FB, $80, $80   ; |............####.####..............|
        .BYTE $80, $80, $9F, $80, $80   ; |..............#####................|
        .BYTE $80, $80, $9B, $80, $80   ; |..............##.##................|
        .BYTE $80, $80, $FB, $80, $80   ; |..............##.####..............|
        .BYTE $80, $80, $FB, $80, $80   ; |..............##.####..............|
        .BYTE $80, $80, $83, $80, $80   ; |..............##...................|
        .BYTE $80, $E0, $83, $80, $80   ; |............####...................|
        .BYTE $80, $E0, $83, $80, $80   ; |............####...................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FF, $80, $80   ; |..............#######..............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_00_V3 at $6300
; Width: 5 bytes (35 pixels), Height: 18 rows
; ----------------------------------------------------------------
SHAPE_00_V3:
        .BYTE $05, $12                  ; width=5, height=18
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FC, $80, $80   ; |................#####..............|
        .BYTE $80, $80, $BB, $83, $80   ; |..............##.###.##............|
        .BYTE $80, $80, $D5, $82, $80   ; |..............#.#.#.#.#............|
        .BYTE $80, $C0, $BB, $87, $80   ; |.............###.###.###...........|
        .BYTE $80, $C0, $EF, $87, $80   ; |.............#####.#####...........|
        .BYTE $80, $80, $EF, $83, $80   ; |..............####.####............|
        .BYTE $80, $80, $FC, $80, $80   ; |................#####..............|
        .BYTE $80, $80, $EC, $80, $80   ; |................##.##..............|
        .BYTE $80, $80, $EC, $83, $80   ; |................##.####............|
        .BYTE $80, $80, $EC, $83, $80   ; |................##.####............|
        .BYTE $80, $80, $8C, $80, $80   ; |................##.................|
        .BYTE $80, $80, $8F, $80, $80   ; |..............####.................|
        .BYTE $80, $80, $8F, $80, $80   ; |..............####.................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FF, $80, $80   ; |..............#######..............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ORG $6400
; ----------------------------------------------------------------
; SHAPE_04_V0 at $6400
; Width: 5 bytes (35 pixels), Height: 14 rows
; ----------------------------------------------------------------
SHAPE_04_V0:
        .BYTE $05, $0E                  ; width=5, height=14
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $F0, $83, $80, $80   ; |...........#####...................|
        .BYTE $80, $BC, $8F, $80, $80   ; |.........####.####.................|
        .BYTE $80, $AE, $9D, $80, $80   ; |........###.#.#.###................|
        .BYTE $80, $AB, $B5, $80, $80   ; |.......##.#.#.#.#.##...............|
        .BYTE $80, $AB, $B5, $80, $80   ; |.......##.#.#.#.#.##...............|
        .BYTE $80, $AB, $B5, $80, $80   ; |.......##.#.#.#.#.##...............|
        .BYTE $80, $AE, $9D, $80, $80   ; |........###.#.#.###................|
        .BYTE $80, $BC, $8F, $80, $80   ; |.........####.####.................|
        .BYTE $80, $F0, $83, $80, $80   ; |...........#####...................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $FF, $80, $80, $80   ; |.......#######.....................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ALIGN $80
; ----------------------------------------------------------------
; SHAPE_04_V0_ODD at $6480 - copy of SHAPE_04_V0 for odd byte columns
; CALCSPRADDR sets SHPLO to $80 when COLORCYCLE bit 7 is set and the sprite
; lands on an odd byte column, so the colour phase stays correct.
; ----------------------------------------------------------------
SHAPE_04_V0_ODD:
        .BYTE $05, $0E                  ; width=5, height=14
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $E0, $87, $80, $80   ; |............#####..................|
        .BYTE $80, $F8, $9E, $80, $80   ; |..........####.####................|
        .BYTE $80, $DC, $BA, $80, $80   ; |.........###.#.#.###...............|
        .BYTE $80, $D6, $EA, $80, $80   ; |........##.#.#.#.#.##..............|
        .BYTE $80, $D6, $EA, $80, $80   ; |........##.#.#.#.#.##..............|
        .BYTE $80, $D6, $EA, $80, $80   ; |........##.#.#.#.#.##..............|
        .BYTE $80, $DC, $BA, $80, $80   ; |.........###.#.#.###...............|
        .BYTE $80, $F8, $9E, $80, $80   ; |..........####.####................|
        .BYTE $80, $E0, $87, $80, $80   ; |............#####..................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $FF, $80, $80, $80   ; |.......#######.....................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_04_V1 at $6500
; Width: 5 bytes (35 pixels), Height: 14 rows
; ----------------------------------------------------------------
SHAPE_04_V1:
        .BYTE $05, $0E                  ; width=5, height=14
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $C0, $8F, $80, $80   ; |.............#####.................|
        .BYTE $80, $F0, $BD, $80, $80   ; |...........####.####...............|
        .BYTE $80, $B8, $F5, $80, $80   ; |..........###.#.#.###..............|
        .BYTE $80, $AC, $D5, $81, $80   ; |.........##.#.#.#.#.##.............|
        .BYTE $80, $AC, $D5, $81, $80   ; |.........##.#.#.#.#.##.............|
        .BYTE $80, $AC, $D5, $81, $80   ; |.........##.#.#.#.#.##.............|
        .BYTE $80, $B8, $F5, $80, $80   ; |..........###.#.#.###..............|
        .BYTE $80, $F0, $BD, $80, $80   ; |...........####.####...............|
        .BYTE $80, $C0, $8F, $80, $80   ; |.............#####.................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FF, $80, $80   ; |..............#######..............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ALIGN $80
; ----------------------------------------------------------------
; SHAPE_04_V1_ODD at $6580 - copy of SHAPE_04_V1 for odd byte columns
; CALCSPRADDR sets SHPLO to $80 when COLORCYCLE bit 7 is set and the sprite
; lands on an odd byte column, so the colour phase stays correct.
; ----------------------------------------------------------------
SHAPE_04_V1_ODD:
        .BYTE $05, $0E                  ; width=5, height=14
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $9F, $80, $80   ; |..............#####................|
        .BYTE $80, $E0, $FB, $80, $80   ; |............####.####..............|
        .BYTE $80, $F0, $EA, $81, $80   ; |...........###.#.#.###.............|
        .BYTE $80, $D8, $AA, $83, $80   ; |..........##.#.#.#.#.##............|
        .BYTE $80, $D8, $AA, $83, $80   ; |..........##.#.#.#.#.##............|
        .BYTE $80, $D8, $AA, $83, $80   ; |..........##.#.#.#.#.##............|
        .BYTE $80, $F0, $EA, $81, $80   ; |...........###.#.#.###.............|
        .BYTE $80, $E0, $FB, $80, $80   ; |............####.####..............|
        .BYTE $80, $80, $9F, $80, $80   ; |..............#####................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FF, $80, $80   ; |..............#######..............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_04_V2 at $6600
; Width: 5 bytes (35 pixels), Height: 14 rows
; ----------------------------------------------------------------
SHAPE_04_V2:
        .BYTE $05, $0E                  ; width=5, height=14
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $BE, $80, $80   ; |...............#####...............|
        .BYTE $80, $C0, $F7, $81, $80   ; |.............####.####.............|
        .BYTE $80, $E0, $D5, $83, $80   ; |............###.#.#.###............|
        .BYTE $80, $B0, $D5, $86, $80   ; |...........##.#.#.#.#.##...........|
        .BYTE $80, $B0, $D5, $86, $80   ; |...........##.#.#.#.#.##...........|
        .BYTE $80, $B0, $D5, $86, $80   ; |...........##.#.#.#.#.##...........|
        .BYTE $80, $E0, $D5, $83, $80   ; |............###.#.#.###............|
        .BYTE $80, $C0, $F7, $81, $80   ; |.............####.####.............|
        .BYTE $80, $80, $BE, $80, $80   ; |...............#####...............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FF, $80, $80   ; |..............#######..............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ALIGN $80
; ----------------------------------------------------------------
; SHAPE_04_V2_ODD at $6680 - copy of SHAPE_04_V2 for odd byte columns
; CALCSPRADDR sets SHPLO to $80 when COLORCYCLE bit 7 is set and the sprite
; lands on an odd byte column, so the colour phase stays correct.
; ----------------------------------------------------------------
SHAPE_04_V2_ODD:
        .BYTE $05, $0E                  ; width=5, height=14
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FC, $80, $80   ; |................#####..............|
        .BYTE $80, $80, $EF, $83, $80   ; |..............####.####............|
        .BYTE $80, $C0, $AB, $87, $80   ; |.............###.#.#.###...........|
        .BYTE $80, $E0, $AA, $8D, $80   ; |............##.#.#.#.#.##..........|
        .BYTE $80, $E0, $AA, $8D, $80   ; |............##.#.#.#.#.##..........|
        .BYTE $80, $E0, $AA, $8D, $80   ; |............##.#.#.#.#.##..........|
        .BYTE $80, $C0, $AB, $87, $80   ; |.............###.#.#.###...........|
        .BYTE $80, $80, $EF, $83, $80   ; |..............####.####............|
        .BYTE $80, $80, $FC, $80, $80   ; |................#####..............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FF, $80, $80   ; |..............#######..............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_04_V3 at $6700
; Width: 5 bytes (35 pixels), Height: 14 rows
; ----------------------------------------------------------------
SHAPE_04_V3:
        .BYTE $05, $0E                  ; width=5, height=14
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $F8, $81, $80   ; |.................#####.............|
        .BYTE $80, $80, $DE, $87, $80   ; |...............####.####...........|
        .BYTE $80, $80, $D7, $8E, $80   ; |..............###.#.#.###..........|
        .BYTE $80, $C0, $D5, $9A, $80   ; |.............##.#.#.#.#.##.........|
        .BYTE $80, $C0, $D5, $9A, $80   ; |.............##.#.#.#.#.##.........|
        .BYTE $80, $C0, $D5, $9A, $80   ; |.............##.#.#.#.#.##.........|
        .BYTE $80, $80, $D7, $8E, $80   ; |..............###.#.#.###..........|
        .BYTE $80, $80, $DE, $87, $80   ; |...............####.####...........|
        .BYTE $80, $80, $F8, $81, $80   ; |.................#####.............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FF, $80, $80   ; |..............#######..............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ALIGN $80
; ----------------------------------------------------------------
; SHAPE_04_V3_ODD at $6780 - copy of SHAPE_04_V3 for odd byte columns
; CALCSPRADDR sets SHPLO to $80 when COLORCYCLE bit 7 is set and the sprite
; lands on an odd byte column, so the colour phase stays correct.
; ----------------------------------------------------------------
SHAPE_04_V3_ODD:
        .BYTE $05, $0E                  ; width=5, height=14
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $F0, $83, $80   ; |..................#####............|
        .BYTE $80, $80, $BC, $8F, $80   ; |................####.####..........|
        .BYTE $80, $80, $AE, $9D, $80   ; |...............###.#.#.###.........|
        .BYTE $80, $80, $AB, $B5, $80   ; |..............##.#.#.#.#.##........|
        .BYTE $80, $80, $AB, $B5, $80   ; |..............##.#.#.#.#.##........|
        .BYTE $80, $80, $AB, $B5, $80   ; |..............##.#.#.#.#.##........|
        .BYTE $80, $80, $AE, $9D, $80   ; |...............###.#.#.###.........|
        .BYTE $80, $80, $BC, $8F, $80   ; |................####.####..........|
        .BYTE $80, $80, $F0, $83, $80   ; |..................#####............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|
        .BYTE $80, $80, $FF, $80, $80   ; |..............#######..............|
        .BYTE $80, $80, $80, $80, $80   ; |...................................|

        .ORG $6800
; ----------------------------------------------------------------
; SHAPE_08_V0 at $6800
; Width: 2 bytes (14 pixels), Height: 10 rows
; ----------------------------------------------------------------
SHAPE_08_V0:
        .BYTE $02, $0A                  ; width=2, height=10
        .BYTE $80, $80                  ; |..............|
        .BYTE $80, $80                  ; |..............|
        .BYTE $D5, $AA                  ; |#.#.#.#.#.#.#.|
        .BYTE $D5, $AA                  ; |#.#.#.#.#.#.#.|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $F7, $F7                  ; |###.######.###|
        .BYTE $FC, $9F                  ; |..##########..|
        .BYTE $F0, $87                  ; |....######....|
        .BYTE $E0, $83                  ; |.....####.....|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_08_V1 at $6900
; Width: 2 bytes (14 pixels), Height: 10 rows
; ----------------------------------------------------------------
SHAPE_08_V1:
        .BYTE $02, $0A                  ; width=2, height=10
        .BYTE $80, $80                  ; |..............|
        .BYTE $80, $80                  ; |..............|
        .BYTE $D5, $AA                  ; |#.#.#.#.#.#.#.|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $F7, $F7                  ; |###.######.###|
        .BYTE $FC, $9F                  ; |..##########..|
        .BYTE $F0, $87                  ; |....######....|
        .BYTE $E0, $83                  ; |.....####.....|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_08_V2 at $6A00
; Width: 2 bytes (14 pixels), Height: 10 rows
; ----------------------------------------------------------------
SHAPE_08_V2:
        .BYTE $02, $0A                  ; width=2, height=10
        .BYTE $80, $80                  ; |..............|
        .BYTE $80, $80                  ; |..............|
        .BYTE $D5, $AA                  ; |#.#.#.#.#.#.#.|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $F7, $F7                  ; |###.######.###|
        .BYTE $FC, $9F                  ; |..##########..|
        .BYTE $F0, $87                  ; |....######....|
        .BYTE $E0, $83                  ; |.....####.....|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_08_V3 at $6B00
; Width: 2 bytes (14 pixels), Height: 10 rows
; ----------------------------------------------------------------
SHAPE_08_V3:
        .BYTE $02, $0A                  ; width=2, height=10
        .BYTE $80, $80                  ; |..............|
        .BYTE $80, $80                  ; |..............|
        .BYTE $D5, $AA                  ; |#.#.#.#.#.#.#.|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $FE, $FE                  ; |.######.######|
        .BYTE $F7, $F7                  ; |###.######.###|
        .BYTE $FC, $9F                  ; |..##########..|
        .BYTE $F0, $87                  ; |....######....|
        .BYTE $E0, $83                  ; |.....####.....|

        .ORG $6C00
; ----------------------------------------------------------------
; SHAPE_0C_V0 at $6C00
; Width: 4 bytes (28 pixels), Height: 12 rows
; ----------------------------------------------------------------
SHAPE_0C_V0:
        .BYTE $04, $0C                  ; width=4, height=12
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $80, $80, $80        ; |............................|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_0C_V1 at $6D00
; Width: 4 bytes (28 pixels), Height: 12 rows
; ----------------------------------------------------------------
SHAPE_0C_V1:
        .BYTE $04, $0C                  ; width=4, height=12
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $80, $80, $80        ; |............................|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_0C_V2 at $6E00
; Width: 4 bytes (28 pixels), Height: 12 rows
; ----------------------------------------------------------------
SHAPE_0C_V2:
        .BYTE $04, $0C                  ; width=4, height=12
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $80, $80, $80        ; |............................|

        .ALIGNPAGE

; ----------------------------------------------------------------
; SHAPE_0C_V3 at $6F00
; Width: 4 bytes (28 pixels), Height: 12 rows
; ----------------------------------------------------------------
SHAPE_0C_V3:
        .BYTE $04, $0C                  ; width=4, height=12
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $D5, $AA, $80        ; |.......#.#.#.#.#.#.#........|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $FE, $FE, $80        ; |........######.######.......|
        .BYTE $80, $80, $80, $80        ; |............................|
        .BYTE $80, $80, $80, $80        ; |............................|

        .ALIGNPAGE

; =================================================================
; $7000-$71FF is unused; the assembler fills the gap with zeros.
; Obstacle positions live in the per-level map files (level1.s ..
; level4.s), included at the end of this file.
; =================================================================

; =================================================================
; CODE SECTION - starts at $7200
; =================================================================

        .ORG $7200
; ----------------------------------------------------------------
; LEVELINIT - Entry point for level 3
; Clears both HGR screens ($2000-$3FFF, $4000-$5FFF)
; Sets up HGR mode (page 1 only, no page flip)
; Draws initial obstacles from lookup tables
; Initializes player position, score display, timer
; Generates random enemy positions from ROM tables
; ----------------------------------------------------------------

LEVELINIT:
        LDA #$00
        STA CURRENT_LEVEL_NUM
        LDA #$FF
        STA DEMO                        ; non-zero = normal gameplay (not demo mode)
        LDA #$03
        STA YOULIVES                    ; 3 lives
        LDA #$00
        STA LEVEL                       ; level 0 (easiest)
        LDA #$80
        STA SOUND                       ; sound on (bit 7 set)
        LDA #$00
        STA COLOR
        LDA #$00
        STA COLORCYCLE                  ; $20
        CLD
        STA TXTCLR                      ; $C050
        STA HIRES                       ; $C057
        STA MIXCLR                      ; $C052
; Clear both HGR pages ($2000-$3FFF and $4000-$5FFF)
; Fill with $80 (black with color bit set)
CLEARSCREENS:
        LDY #$00                        ; Y = byte counter (0-255)
        STY TEMP0                       ; ptr1 low = 0 (page 1)
        STY TEMP2                       ; ptr2 low = 0 (page 2)
        LDA #$20                        ; start at $2000 (HGR page 1)
        STA TEMP1                       ; ptr1 high = $20
        ASL A                           ; A = $40 (HGR page 2)
        STA TEMP3                       ; ptr2 high = $40
CLEARLOOP:
        LDA #$80
        STA (TEMP0),Y                   ; write to page 1
        STA (TEMP2),Y                   ; write to page 2
        INY                             ; next byte in page
        BNE CLEARLOOP                   ; loop until 256 bytes done
        INC TEMP1                       ; next page on HGR 1 ($21, $22...)
        INC TEMP3                       ; next page on HGR 2 ($41, $42...)
        LDA TEMP3                       ; check if done
        CMP #$60                        ; $60 = end of HGR page 2
        BNE CLEARLOOP                   ; continue until both pages cleared
        STA LOWSCR                      ; $C054 - trigger display present after clear completes

        LDA CURRENT_LEVEL_NUM           ; level number
        ASL                             ; get offset to find address of level
        TAY
        LDA LEVEL_MAPS,Y
        STA CURRENT_LEVEL_LO
        INY
        LDA LEVEL_MAPS,Y
        STA CURRENT_LEVEL_HI

        LDA CURRENT_LEVEL_LO            ; Calculate base address of elevators
        CLC
        ADC #$02
        STA ELEVATORS_LO
        LDA CURRENT_LEVEL_HI
        ADC #$00
        STA ELEVATORS_HI

; Initialize elevators position and direction to start at bottom going up
        LDY #ELEV_BOT_Y_OFFSET+0
        LDA (ELEVATORS_LO),Y
        LDY #ELEV_Y_OFFSET+0
        STA (ELEVATORS_LO),Y
        LDY #ELEV_BOT_Y_OFFSET+8
        LDA (ELEVATORS_LO),Y
        LDY #ELEV_Y_OFFSET+8
        STA (ELEVATORS_LO),Y
        LDY #ELEV_BOT_Y_OFFSET+16
        LDA (ELEVATORS_LO),Y
        LDY #ELEV_Y_OFFSET+16
        STA (ELEVATORS_LO),Y

        LDA #$FF
        LDY #ELEV_DIR_OFFSET+0
        STA (ELEVATORS_LO),Y
        LDY #ELEV_DIR_OFFSET+8
        STA (ELEVATORS_LO),Y
        LDY #ELEV_DIR_OFFSET+16
        STA (ELEVATORS_LO),Y

        LDY #OBSTACLE_COUNT_OFFSET
        LDA (CURRENT_LEVEL_LO),Y        ; Read obstacle count
        STA OBSTCOUNT
DRAWOBSTACLES:
        LDA OBSTCOUNT                   ; Get offset for obstacle entry
        ASL
        ADC #OBSTACLES_OFFSET
        TAY
        LDA (CURRENT_LEVEL_LO),Y
        STA OBSTPTRLO
        INY
        LDA (CURRENT_LEVEL_LO),Y
        STA OBSTPTRHI
        JSR DRAWOBST_INIT
        DEC OBSTCOUNT
        LDA OBSTCOUNT
        BPL DRAWOBSTACLES
        STA LOWSCR

; Initialize all game state variables for new level
INITGAMESTATE:
        LDY #PLAYER_START_X_OFFSET
        LDA (CURRENT_LEVEL_LO),Y        ; player starts at X
        STA PLAYERX                     ; set player X position
        INY
        LDA (CURRENT_LEVEL_LO),Y        ; player starts at Y
        STA PLAYERY                     ; set player Y position

        LDY #ELEV_DELAY_OFFSET          ; Initialize elevator 1 pause
        LDA (ELEVATORS_LO),Y
        LDY #ELEV_PAUSE_OFFSET
        STA (ELEVATORS_LO),Y
        LDY #ELEV_DELAY_OFFSET+ELEV_BYTESIZE ; Initialize elevator 2 pause
        LDA (ELEVATORS_LO),Y
        LDY #ELEV_PAUSE_OFFSET+ELEV_BYTESIZE
        STA (ELEVATORS_LO),Y
        LDY #ELEV_DELAY_OFFSET+ELEV_BYTESIZE+ELEV_BYTESIZE ; Initialize elevator 2 pause
        LDA (ELEVATORS_LO),Y
        LDY #ELEV_PAUSE_OFFSET+ELEV_BYTESIZE+ELEV_BYTESIZE
        STA (ELEVATORS_LO),Y

        LDA #$00                        ; timer starts at $0400 (BCD 04:00)
        STA TIMERLO                     ; timer low = $00
        LDA #$04                        ; timer high = $04 (4 minutes)
        STA TIMERHI                     ; set high byte

        LDA #$00                        ; clear collision counter
        STA COLLCOUNT                   ; collision grace period counter

; Enemy count comes from the level map: DIFFICULTY is the index of the last
; enemy in play, so the loops over enemies run 0..DIFFICULTY
        LDY #ENEMY_COUNT_OFFSET
        LDA (CURRENT_LEVEL_LO),Y        ; enemies on this level (1-5)
        SEC
        SBC #$01
        STA DIFFICULTY

; Reset all enemies to active
        LDY #$04                        ; 5 enemies (indices 0-4)
        LDA #$01
RESETACTIVE:
        STA ENEMYACTIVE,Y
        DEY
        BPL RESETACTIVE

; Initialize enemy positions from the level map (ENEMY_START_OFFSET, X/Y pairs)
        LDX #4                          ; enemy index, last (4) to first (0)
        LDY #ENEMY_START_OFFSET+9       ; map offset of enemy 4's Y (5 pairs = 10 bytes)
INITENEMYPOS:
        LDA (CURRENT_LEVEL_LO),Y        ; enemy start Y
        STA ENEMYY,X
        DEY
        LDA (CURRENT_LEVEL_LO),Y        ; enemy start X
        STA ENEMYX,X
        DEY
        DEX
        BPL INITENEMYPOS

; Copy initial velocity table to working enemy velocity array
        LDY #$09                        ; copy 10 bytes (5 enemies * 2?)
COPYVELTABLE:
        LDA INITDIRTBL,Y                ; get initial direction
        STA ENEMYVEL,Y                  ; copy to velocity table
        DEY                             ; next byte
        BPL COPYVELTABLE                ; loop until done

; Start the game
STARTGAME:
        JSR DRAWPLAYER                  ; draw player at initial position
; Establish the XOR invariant: every enemy is drawn on page 1 at its current
; (ENEMYX, ENEMYY). ERASE_ENEMIES relies on this to be able to XOR-erase.
        LDX DIFFICULTY
INITENEMIES_LOOP:
        LDA #$FF
        STA COLOR
        JSR DRAWENEMY
        DEX
        BPL INITENEMIES_LOOP
        STA LOWSCR                      ; $C054 - trigger display present after clear completes
        JMP MAINLOOP                    ; enter main game loop

; ----------------------------------------------------------------
; DRAWOBST_INIT - Draw an obstacle at initial position
; Uses self-modifying code to toggle sprite engine between
; OR-drawing ($9355) and direct-drawing ($93C7) modes
; ----------------------------------------------------------------

; Draw obstacle and set up sprite engine modes via self-modifying code
; DRAWCOLL_PLOT ($9362) controls ORA vs STA mode in collision sprite routine
; DRAWNOCOLL_PLOT ($93D4) controls ORA vs STA mode in no-collision sprite routine
; Opcode $91 = STA (ind),Y (direct write)  Opcode $11 = ORA (ind),Y (non-destructive)
DRAWOBST_INIT:
        LDA #$FF                        ; color = white (all bits on)
        STA COLOR                       ; set drawing color
        LDA OBSTPTRLO                   ; get obstacle X from parameter
        STA XCOORD                      ; set sprite X position
        LDA OBSTPTRHI                   ; get obstacle Y from parameter
        STA YCOORD                      ; set sprite Y position
        LDA #$0C                        ; shape $0C = obstacle sprite
        STA SHAPE                       ; set sprite index
        JSR DRAW_COLL                   ; draw to page 1 in ORA mode (non-destructive: $80 border bytes
; can only set bits, preserving neighboring obstacles' pixels)
        LDA OBSTPTRLO                   ; reload X position
        STA XCOORD                      ; (may have been modified)
        LDA #$0C                        ; obstacle shape again
        STA SHAPE                       ; set sprite
        LDA #$11                        ; opcode $11 = ORA (ind),Y: non-destructive for page 2 write
        STA DRAWNOCOLL_PLOT             ; SELF-MOD: switch DRAWNOCOLL_PLOT to ORA
        JSR DRAW_NOCOLL                 ; draw to both pages non-destructively
        LDA #$91                        ; opcode $91 = STA (ind),Y: restore direct write mode
        STA DRAWNOCOLL_PLOT             ; SELF-MOD: restore DRAWNOCOLL_PLOT to STA
        RTS

; Quick obstacle draw - uses ORA mode so zero-padded sprite bytes
; do not erase neighboring obstacle pixels on the displayed page
DRAWOBST_QUICK:
        LDA #$11                        ; opcode $11 = ORA (ind),Y: non-destructive mode
        STA DRAWNOCOLL_PLOT             ; SELF-MOD: switch to ORA so zeros don't erase neighbors
        JSR DRAW_NOCOLL                 ; draw sprite
        LDA #$91                        ; opcode $91 = STA (ind),Y: restore direct write mode
        STA DRAWNOCOLL_PLOT             ; SELF-MOD: restore DRAWNOCOLL_PLOT
        RTS

; ----------------------------------------------------------------
; CHKJOY - Joystick input handler
; Checks paddle buttons PB0, PB1, PB2 (all three at once)
; If all pressed: no movement (return)
; Reads Paddle 0 via PREAD ($FB1E)
; Value < $30: go left, > $D0: go right
; ----------------------------------------------------------------

; Check joystick/paddle for left/right movement
; Returns normally if no input or centered
; Jumps to MOVELEFT/MOVERIGHT if joystick pushed
CHKJOY:
        LDA PB0                         ; read paddle button 0
        AND PB1                         ; AND with button 1
        AND PB2                         ; AND with button 2
        BMI JOYRTS                      ; if all buttons pressed (bit7=1), skip
        LDX #$00                        ; select paddle 0
        JSR PREAD                       ; ROM: read paddle, returns value in Y
        TYA                             ; transfer paddle value to A
        CMP #$30                        ; is paddle left of center? (<$30)
        BCC JOYLEFT                     ; yes, go left
        CMP #$D0                        ; is paddle right of center? (>=$D0)
        BCS JOYRIGHT                    ; yes, go right
JOYRTS:
        RTS                             ; centered, no movement

; Joystick pushed left - pop return address and jump to move handler
JOYLEFT:
        PLA                             ; discard return address low
        PLA                             ; discard return address high
        JMP MOVELEFT                    ; execute left movement

; Joystick pushed right
JOYRIGHT:
        PLA                             ; discard return address low
        PLA                             ; discard return address high
        JMP MOVERIGHT                   ; execute right movement

; ----------------------------------------------------------------
; ADDSCORE - Add BCD value in A to 3-byte score
; Uses SED/CLD for decimal mode arithmetic
; Score bytes: SCORELO($8A), SCOREHI($8B), SCOREHI2($8C)
; ----------------------------------------------------------------

; Add A to score (BCD arithmetic)
; Input: A = points to add (BCD format, e.g., $50 = 50 points)
; Modifies: SCORELO/HI/HI2 as 3-byte BCD counter
ADDSCORE:
        SED                             ; enable decimal (BCD) mode
        CLC                             ; clear carry for addition
        ADC SCORELO                     ; add to low byte of score
        STA SCORELO                     ; store result
        LDA SCOREHI                     ; load middle byte
        ADC #$00                        ; add carry from low byte
        STA SCOREHI                     ; store middle byte
        LDA SCOREHI2                    ; load high byte
        ADC #$00                        ; add carry from middle
        STA SCOREHI2                    ; store high byte (max 999999)
        CLD                             ; disable decimal mode

; ----------------------------------------------------------------
; PUTSCORE - Display 6-digit BCD score using DRAWDIGIT
; Also displays lives count and level number
; PUTLIVES at $7379 - display lives and level
; ----------------------------------------------------------------

; Display 6-digit BCD score at top of screen
; Score format: SCOREHI2(low nibble) + SCOREHI + SCORELO
; Each digit drawn at X positions $0F, $11, $13, $15, $17
PUTSCORE:
        LDA SCOREHI2                    ; get highest score byte
        AND #$0F                        ; extract low nibble (digit 1)
        STA SHAPE                       ; digit value = sprite index
        LDA #$0F                        ; X position for digit 1
        STA XX                          ; set draw X
        LDA #$00                        ; Y position = top row
        STA YY                          ; set draw Y
        LDA #$FF                        ; white color
        STA TEMP3                       ; set color mask
        JSR DRAWDIGIT                   ; draw first digit
        LDA SCOREHI                     ; get middle score byte
        LSR A                           ; shift right 4 times
        LSR A                           ; to get high nibble
        LSR A
        LSR A
        STA SHAPE                       ; high nibble = digit 2
        LDA #$11                        ; X position for digit 2
        STA XX
        JSR DRAWDIGIT                   ; draw second digit
        LDA SCOREHI                     ; reload middle byte
        AND #$0F                        ; extract low nibble (digit 3)
        STA SHAPE
        LDA #$13                        ; X position for digit 3
        STA XX
        JSR DRAWDIGIT                   ; draw third digit
        LDA SCORELO                     ; get low score byte
        LSR A                           ; shift to get high nibble
        LSR A
        LSR A
        LSR A
        STA SHAPE                       ; digit 4
        LDA #$15                        ; X position
        STA XX
        JSR DRAWDIGIT                   ; draw fourth digit
        LDA SCORELO                     ; reload low byte
        AND #$0F                        ; low nibble = digit 5
        STA SHAPE
        LDA #$17                        ; X position for digit 5
        STA XX
        JSR DRAWDIGIT                   ; draw fifth digit
        CLC                             ; clear carry (success)
        RTS

; Display "LIVES" text and lives count at top-left
; Uses PIXRENDER for each character: L=12, I=9, V=22, E=5, S=19
PUTLIVES:
        LDA #$00                        ; start at X=0
        STA XX
        STA YY                          ; Y=0 (top of screen)
        LDA #$00                        ; character width setting
        STA WIDTH
        LDA #$01                        ; character height setting
        STA HEIGHT
        LDA #$FF                        ; white color
        STA TEMP3
        LDA #$0C                        ; char 12 = 'L'
        JSR PIXRENDER                   ; draw 'L'
        INC XX                          ; advance X position
        LDA #$09                        ; char 9 = 'I'
        JSR PIXRENDER                   ; draw 'I'
        INC XX
        LDA #$16                        ; char 22 = 'V'
        JSR PIXRENDER                   ; draw 'V'
        INC XX
        LDA #$05                        ; char 5 = 'E'
        JSR PIXRENDER                   ; draw 'E'
        INC XX
        LDA #$13                        ; char 19 = 'S'
        JSR PIXRENDER                   ; draw 'S'
        INC XX                          ; position for digit
        LDA YOULIVES                    ; get current lives count
        STA SHAPE                       ; lives count = digit to display
        JMP DRAWDIGIT                   ; draw and return

; ----------------------------------------------------------------
; COUNTDOWN - BCD timer countdown
; Decrements TIMERHI:TIMERLO by $10 (in BCD mode)
; Displays 4-digit timer on screen
; Returns carry SET when timer reaches zero (time up!)
; ----------------------------------------------------------------

; Decrement and display countdown timer (BCD format)
; Decrements by $10 each call (0.1 units in BCD)
; Returns: Carry SET if timer reached zero (time up!)
;          Carry CLEAR if time remaining
COUNTDOWN:
        SED                             ; enable BCD mode
        SEC                             ; set carry for subtraction
        LDA TIMERLO                     ; get timer low byte
        SBC #$10                        ; subtract $10 (BCD 0.10)
        STA TIMERLO                     ; store result
        BCS DRAWTIME                    ; no borrow needed, skip
        SEC                             ; set carry for high byte sub
        LDA TIMERHI                     ; get timer high byte
        SBC #$01                        ; subtract 1 (borrow)
        STA TIMERHI                     ; store result
DRAWTIME:
        CLC                             ; clear carry for return
        CLD                             ; disable BCD mode

; Display 4-digit timer at top-right (positions $1E-$24)
        LDA TIMERHI                     ; timer high byte
        LSR A                           ; shift to get tens digit
        LSR A
        LSR A
        LSR A
        STA SHAPE                       ; digit 1 (minutes tens)
        LDA #$1E                        ; X position
        STA XX
        LDA #$00                        ; Y = top row
        STA YY
        LDA #$FF                        ; white
        STA TEMP3
        JSR DRAWDIGIT                   ; draw minutes tens
        LDA TIMERHI                     ; reload high byte
        AND #$0F                        ; mask low nibble
        STA SHAPE                       ; digit 2 (minutes ones)
        LDA #$20                        ; X position
        STA XX
        JSR DRAWDIGIT                   ; draw minutes ones
        LDA TIMERLO                     ; timer low byte
        LSR A                           ; shift for tens
        LSR A
        LSR A
        LSR A
        STA SHAPE                       ; digit 3 (seconds tens)
        LDA #$22                        ; X position
        STA XX
        JSR DRAWDIGIT                   ; draw seconds tens
        LDA TIMERLO                     ; reload low byte
        AND #$0F                        ; mask low nibble
        STA SHAPE                       ; digit 4 (seconds ones)
        LDA #$24                        ; X position
        STA XX
        JSR DRAWDIGIT                   ; draw seconds ones

; Check if timer reached zero
        CLC                             ; assume not zero (C=0)
        LDA TIMERHI                     ; check high byte
        BNE L_7412                      ; not zero, return C=0
        LDA TIMERLO                     ; check low byte
        BNE L_7412                      ; not zero, return C=0
        SEC                             ; both zero: time up! C=1
L_7412:
        RTS

; ----------------------------------------------------------------
; DRAWPLAYER - Draw player sprite and check collision
; Draws at position (PLAYERX, PLAYERY) using sprite engine
; Checks REPORT ($1F) for collision detection
; ----------------------------------------------------------------

; Draw player sprite and check for collisions
; Uses SHAPE $00 (player sprite) with collision detection
; If PLAYERX=0, clears collision report (at left edge)
DRAWPLAYER:
        LDA PLAYERX                     ; get player X position
        STA XCOORD                      ; set sprite X coordinate
        LDA PLAYERY                     ; get player Y position
        STA YCOORD                      ; set sprite Y coordinate
        LDA #$00                        ; shape 0 = player sprite
        STA SHAPE
        LDA #$FF                        ; white color
        STA COLOR
        JSR DRAW_COLL                   ; draw with collision detection
        LDA PLAYERX                     ; check X position
        BEQ DRAWPLAYER_CLEAR            ; if X=0, at edge, clear collision
        RTS                             ; return with REPORT set by DRAW_COLL

; Player at left edge - clear collision report
DRAWPLAYER_CLEAR:
        STA REPORT                      ; A=0, clear collision flags
        RTS

; Initial direction table for enemies
; $FF = left (-1), $01 = right (+1)
INITDIRTBL:
        .BYTE $FF, $01, $FF, $01, $FF, $01, $01, $01, $01, $01 ; |########......########......########......#......#......#......#......|

; Enemy position tables (5 enemies)
ENEMYX:
        .BYTE $26, $39, $83, $2A, $2C   ; |.##..#.#..###.##......#.#.#...##.#.|
ENEMYY:
        .BYTE $4C, $3F, $3C, $30, $33   ; |..##..#######...####.....##.##..##.|

; Enemy velocity (direction): $01=right, $FF=left
ENEMYVEL:
        .BYTE $01, $01, $FF, $01, $FF   ; |#......#......########......#######|

; Enemy active flags: $01=active, $00=destroyed
ENEMYACTIVE:
        .BYTE $01, $01, $01, $01, $01   ; |#......#......#......#......#......|

; Per-enemy REPORT saved by ERASE_ENEMIES and consumed by UPDATELOOP.
; Split lets us erase before elevators move and draw after, so the elevator's
; STA writes never land on XOR'd enemy bytes.
ENEMY_REPORT:
        .BYTE $00, $00, $00, $00, $00

; ----------------------------------------------------------------
; DRAWENEMY - Draw a single enemy obstacle
; X = enemy index into ENEMYX/ENEMYY/ENEMYACTIVE tables
; If active=0, skip. Draws using sprite engine ($9303)
; REPORT ($1F) set if collision detected
; ----------------------------------------------------------------

; Draw a single enemy sprite with collision detection
; Input: X = enemy index (0-4)
; Output: REPORT set if collision detected
; Skips inactive enemies (ENEMYACTIVE[X] = 0)
DRAWENEMY:
        LDA ENEMYACTIVE,X               ; check if this enemy is active
        BEQ DRAWENEMY_RTS               ; if inactive, skip drawing
        LDA ENEMYX,X                    ; get enemy X position
        STA XCOORD                      ; set sprite X
        CMP #$00                        ; check if at left edge
        BEQ DRAWENEMY_CLEAR             ; if X=0, clear collision
        LDA ENEMYY,X                    ; get enemy Y position
        STA YCOORD                      ; set sprite Y
        LDA #$04                        ; shape 4 = enemy/obstacle sprite
        STA SHAPE
        STX SAVEX                       ; save X register (enemy index)
        LDA #$FF                        ; enable color cycling
        STA COLORCYCLE
; Switch DRAWCOLL_PLOT to XOR mode (EOR (TOLO),Y) so enemy draws
; toggle on page 1 — nearby enemies' bboxes no longer erase each other.
        LDA #$51                        ; opcode $51 = EOR (zp),Y
        STA DRAWCOLL_PLOT
        LDA #TOLO                       ; operand = TOLO (page 1)
        STA DRAWCOLL_PLOT+1
        JSR DRAW_COLL                   ; XOR-draw with collision detection
; Restore DRAWCOLL_PLOT to bg-composite mode (ORA (PTR2LO),Y)
; used by DRAWPLAYER and DRAWOBST_INIT.
        LDA #$11                        ; opcode $11 = ORA (zp),Y
        STA DRAWCOLL_PLOT
        LDA #PTR2LO                     ; operand = PTR2LO (page 2)
        STA DRAWCOLL_PLOT+1
        LDA #$00                        ; disable color cycling
        STA COLORCYCLE
        LDX SAVEX                       ; restore enemy index
DRAWENEMY_RTS:
        RTS

; Enemy at left edge - clear collision report
DRAWENEMY_CLEAR:
        LDA #$00
        STA REPORT                      ; clear collision flags
        RTS

; ----------------------------------------------------------------
; CHECKCOLL - Main collision/movement handler
; Called each frame from DRAWPLAYER return
; If collision=$7E (border): hit boundary
; In demo mode: use ROM-based pseudo-random for movement
; In play mode: jump to KBDPAUSE ($7FD0) for input
; Keyboard dispatch: J=$CA=left, K=$CB=right
; ----------------------------------------------------------------

; Main collision check and movement handler
; Called each frame to draw player and handle input
; Collision values: $7E=border, other=obstacle
; Movement: Demo mode uses ROM pseudo-random, play mode uses keyboard
CHECKCOLL:
        JSR DRAWPLAYER                  ; draw player, sets REPORT
        LDA REPORT                      ; get collision flags
        AND #$7F                        ; mask off high bit
        STA REPORT                      ; store masked value
        BEQ COLL_ADVANCE                ; no collision? advance player down
        CMP #$7E                        ; hit border marker?
        BEQ COLL_HITBORDER              ; yes, handle border collision
        LDA DEMO                        ; check if demo mode
        BNE CHECKCOLL_KBD               ; if demo=0, use keyboard
; Demo mode: use pseudo-random movement from ROM
        INC RNDCOUNT                    ; advance random index
        LDY RNDCOUNT
        LDA $F800,Y                     ; read ROM byte as "random"
        AND #$28                        ; mask two bits
        BEQ MOVELEFT                    ; if both clear, go left
        BNE MOVERIGHT                   ; otherwise go right
CHECKCOLL_KBD:
        JMP KBDPAUSE                    ; check keyboard with pause support

; Keyboard dispatch - check J/K keys for movement
KBDDISPATCH:
        CMP #$CA                        ; 'J' key? (left)
        BEQ MOVELEFT
        CMP #$CB                        ; 'K' key? (right)
        BEQ MOVERIGHT
NOCOLLISION:
        LDA #$00                        ; clear collision counter
        STA COLLCOUNT                   ; reset grace period
        RTS

; Hit border - push player back up
COLL_HITBORDER:
        DEC PLAYERY                     ; move player up 1 pixel
        LDA COLLCOUNT                   ; check collision counter
        CMP #$30                        ; accumulated 48+ collisions?
        BCC COLL_HITCLR                 ; no, just clear and continue
COLL_DEATH:
        PLA                             ; pop return address
        PLA                             ; (exit to YOUDIED)
        JMP YOUDIED                     ; player dies!

; Clear collision counter after border hit
COLL_HITCLR:
        LDA #$00
        STA COLLCOUNT                   ; reset collision counter
        RTS

; No collision - advance player down the screen
COLL_ADVANCE:
        INC PLAYERY                     ; move player down 1 pixel
        LDA PLAYERY                     ; check Y position
        CMP #$AF                        ; at bottom boundary? (Y=175)
        BCS COLL_DEATH                  ; yes, player falls off = death
        INC COLLCOUNT                   ; increment collision counter
        LDA COLLCOUNT                   ; check counter
        AND #$F8                        ; check if >= 8
        BEQ COLLSOUND_RTS               ; if < 8, no sound
; Play collision warning sound
        LDY #$18                        ; 24 iterations
COLLSOUND:
        LDA COLLCOUNT                   ; get collision count
        ASL A                           ; multiply by 2 for pitch
        TAX                             ; X = delay counter
L_74D3:
        DEX                             ; delay loop
        BNE L_74D3
        LDA SOUND                       ; check if sound enabled
        BMI COLLSOUND_END               ; bit 7 set = muted
        STA SPKR                        ; toggle speaker
COLLSOUND_END:
        DEY                             ; next iteration
        BNE COLLSOUND                   ; continue sound
COLLSOUND_RTS:
        RTS

; Move player left
MOVELEFT:
        DEC PLAYERX                     ; X = X - 1
        LDA #$00                        ; clear collision counter
        STA COLLCOUNT                   ; (movement resets grace period)
        RTS

; Move player right
MOVERIGHT:
        INC PLAYERX                     ; X = X + 1
        LDA #$00                        ; clear collision counter
        STA COLLCOUNT
        RTS

; ----------------------------------------------------------------
; CHKENEMIES - Check collision between player and all enemies
; Loops through all active enemies (X = DIFFICULTY downto 0)
; Bounds-checking: compares PLAYERX±range vs ENEMYX/ENEMYY
; On hit: play sound, add score, deactivate enemy
; If all enemies cleared: jump to BONUSSCORE
; If COLLCOUNT < 4: ignored (grace period)
; If COLLCOUNT >= 4: death! Jump to YOUDIED
; ----------------------------------------------------------------

; Check all enemies for collision with player
; Loops through DIFFICULTY+1 enemies (0 to DIFFICULTY)
; Bounding box: player ±8 pixels X, ±13 pixels Y
; If collision and COLLCOUNT >= 4: death
; If collision and COLLCOUNT < 4: destroy enemy, +50 pts
; If all enemies destroyed: jump to BONUSSCORE
CHKENEMIES:
        LDA #$00                        ; clear active enemy counter
        STA ACTIVECNT
        LDX DIFFICULTY                  ; X = number of enemies - 1
CHKENEMYLOOP:
        LDA ENEMYACTIVE,X               ; check if enemy active
        BEQ NEXTENEMY                   ; skip if destroyed
        INC ACTIVECNT                   ; count active enemies

; Bounding box check: PLAYERX-8 to PLAYERX+10 vs ENEMYX
        LDA PLAYERX                     ; get player X
        SEC
        SBC #$08                        ; subtract 8 (left edge)
        CMP ENEMYX,X                    ; compare with enemy X
        BPL NEXTENEMY                   ; if player left > enemy, no hit

        LDA PLAYERY                     ; get player Y
        CMP ENEMYY,X                    ; compare with enemy Y
        BCS NEXTENEMY                   ; if player below enemy, no hit

        LDA PLAYERX                     ; get player X again
        CLC
        ADC #$0A                        ; add 10 (right edge)
        CMP ENEMYX,X                    ; compare with enemy X
        BCC NEXTENEMY                   ; if player right < enemy, no hit

        LDA PLAYERY                     ; get player Y again
        ADC #$0D                        ; add 13 (player height)
        CMP ENEMYY,X                    ; compare with enemy Y
        BCC NEXTENEMY                   ; if player bottom < enemy, no hit

; COLLISION DETECTED!
        LDA COLLCOUNT                   ; check collision grace counter
        AND #$FC                        ; mask to check if >= 4
        BNE ENEMYHITSOUND               ; if >= 4, player survives hit
; Grace period not built up - instant death!
        PLA                             ; pop return address
        PLA
        JMP YOUDIED                     ; player dies

; Player hit enemy with grace period - destroy enemy
ENEMYHITSOUND:
        STX SAVEX                       ; save enemy index
        LDY #$80                        ; 128 iterations for sound
        STY TEMP0
L_7531:
        LDX TEMP0                       ; get current count
L_7533:
        DEX                             ; delay loop
        BNE L_7533
        LDA SOUND                       ; check sound enabled
        BMI L_753D                      ; skip if muted
        STA SPKR                        ; toggle speaker
L_753D:
        STY TEMP0                       ; restore count
        DEY                             ; next iteration
        BNE L_7531                      ; continue sound

        LDA #$50                        ; 50 points (BCD)
        JSR ADDSCORE                    ; add to score
        LDA #$FF                        ; white color — XOR draw toggles
        STA COLOR                       ; (COLOR=$00 is a no-op under XOR)
        LDX SAVEX                       ; restore enemy index
        JSR DRAWENEMY                   ; XOR-erase enemy sprite
        LDX SAVEX                       ; restore index again
        LDA #$00                        ; deactivate enemy
        STA ENEMYACTIVE,X               ; mark as destroyed
NEXTENEMY:
        DEX                             ; next enemy index
        BPL CHKENEMYLOOP                ; loop for all enemies
        LDA ACTIVECNT                   ; check if any enemies remain
        BNE L_7563                      ; if yes, continue game
; All enemies destroyed - bonus time!
        PLA                             ; pop return address
        PLA
        JMP BONUSSCORE                  ; award bonus points

L_7563:
        RTS

; Draw enemy and check for obstacle collision (for bouncing)
; If hits border ($7E), back up and retry
DRAWCHKOBST:
        LDA #$FF                        ; white color
        STA COLOR
        JSR DRAWENEMY                   ; draw enemy sprite
        LDA REPORT                      ; get collision result
        AND #$7F                        ; mask high bit
        STA REPORT
        CMP #$7E                        ; hit border?
        BEQ OBSTBOUNCE                  ; yes, bounce off
        LDA REPORT                      ; return collision status
        AND #$7F
        RTS

; Obstacle hit border - move up and retry
; Under XOR draw, the previous DRAWCHKOBST already toggled the sprite on at
; the current Y, so erase it before backing up or we leave a stray copy.
OBSTBOUNCE:
        LDA #$FF
        STA COLOR
        JSR DRAWENEMY                   ; XOR-erase at current Y
        DEC ENEMYY,X                    ; move enemy up 1 pixel
        JMP DRAWCHKOBST                 ; try drawing again

; ----------------------------------------------------------------
; UPDATEENEMIES - Update all enemy positions
; Moves each enemy horizontally by its velocity (ENEMYVEL)
; On wall collision: reverse direction (flip velocity)
; Advances Y position incrementally
; ----------------------------------------------------------------

; Update all enemy positions - movement and bouncing
; Enemies move horizontally (ENEMYVEL) and descend gradually
; When hitting walls, they reverse horizontal direction
; ERASE_ENEMIES — XOR-erase every active enemy at its current position and
; stash each enemy's REPORT in ENEMY_REPORT[X] for UPDATEENEMIES to consume.
; Call this BEFORE any other routine writes to page 1 this frame — otherwise
; the XOR erase will read a clobbered screen and leave ghost pixels.
ERASE_ENEMIES:
        LDX DIFFICULTY
ERASE_LOOP:
        LDA #$FF
        STA COLOR
        JSR DRAWENEMY                   ; XOR-erase; sets REPORT from markers
        LDA REPORT
        STA ENEMY_REPORT,X
        DEX
        BPL ERASE_LOOP
        RTS

; UPDATEENEMIES runs AFTER elevators have moved. For each enemy it uses the
; REPORT captured during ERASE_ENEMIES to decide motion, then XOR-draws at
; the new position. The invariant on exit: every active enemy is drawn on
; page 1 at its (ENEMYX, ENEMYY).
UPDATEENEMIES:
        LDX DIFFICULTY                  ; X = last enemy index
UPDATELOOP:
        LDA ENEMYACTIVE,X               ; inactive enemies contribute nothing
        BEQ UPDATENEXT
        LDA ENEMY_REPORT,X              ; REPORT captured by ERASE_ENEMIES
        AND #$7F                        ; mask high bit
        STA REPORT
        BEQ UPDATE_ADVANCEY             ; no collision = advance down
        CMP #$7E                        ; hit border?
        BEQ UPDATE_RETREATY             ; yes, retreat up

; Collision with obstacle - move horizontally
        LDA ENEMYVEL,X                  ; get velocity (-1 or +1)
        CLC
        ADC ENEMYX,X                    ; add to X position
        STA ENEMYX,X                    ; store new position

        LDA #$FF                        ; white color
        STA COLOR
        JSR DRAWENEMY                   ; XOR-draw at new X (screen was clear)
        LDA REPORT                      ; check for collision
        AND #$7F
        BNE UPDATENEXT                  ; if still colliding, leave drawn

; Try to advance down — erase at (newX, Y) first so we don't leave a copy
        LDA #$FF
        STA COLOR
        JSR DRAWENEMY                   ; XOR-erase at (newX, Y)
        INC ENEMYY,X                    ; move down 2 pixels
        INC ENEMYY,X
        JSR DRAWCHKOBST                 ; XOR-draw at (newX, Y+2), returns REPORT
        BNE UPDATENEXT                  ; something below = OK, leave drawn

; Nothing detected below - reverse direction
; DRAWCHKOBST drew at (newX, Y+2); erase that, step back, flip, move, redraw.
        LDA #$FF
        STA COLOR
        JSR DRAWENEMY                   ; XOR-erase at (newX, Y+2)
        DEC ENEMYY,X                    ; undo vertical move
        DEC ENEMYY,X
        LDA ENEMYVEL,X                  ; get current direction
        CMP #$FF                        ; going left?
        BEQ L_75CB                      ; yes, switch to right
        LDA #$FF                        ; switch to left
        STA ENEMYVEL,X
        BNE L_75D0                      ; (always branches)
L_75CB:
        LDA #$01                        ; switch to right
        STA ENEMYVEL,X
L_75D0:
; Move horizontally in new direction
        LDA ENEMYX,X
        CLC
        ADC ENEMYVEL,X                  ; apply new velocity
        STA ENEMYX,X
        LDA #$FF                        ; redraw at final (newX+vel, Y)
        STA COLOR
        JSR DRAWENEMY                   ; XOR-draw
UPDATENEXT:
        DEX                             ; next enemy
        BPL UPDATELOOP                  ; loop until done
        RTS

; No collision - enemy advances down and must be redrawn at new Y
UPDATE_ADVANCEY:
        INC ENEMYY,X                    ; move down 2 pixels
        INC ENEMYY,X
        LDA #$FF
        STA COLOR
        JSR DRAWENEMY                   ; XOR-draw at new Y
        JMP UPDATENEXT

; Hit border - retreat up and redraw at new Y
UPDATE_RETREATY:
        DEC ENEMYY,X                    ; move up 1 pixel
        LDA #$FF
        STA COLOR
        JSR DRAWENEMY                   ; XOR-draw at new Y
        JMP UPDATENEXT

ELEV_ANIM:                              ; elevator number in A, multiply by 8 (sizeof ELEV)
        ASL                             ; *2
        ASL                             ; *4
        ASL                             ; *8
        CLC
        ADC ELEVATORS_LO                ; Get address of elevator in TEMP0/TEMP1
        STA TEMP0
        LDA ELEVATORS_HI
        ADC #$00
        STA TEMP1

        LDY #ELEV_PAUSE_OFFSET          ; Are we pausing?
        LDA (TEMP0),Y
        BEQ ELEV_MOVE                   ; Nope
        CLC                             ; Decrement pause count
        SBC #$01
        STA (TEMP0),Y
        RTS

ELEV_MOVE:
        LDY #ELEV_Y_OFFSET              ; get Y position
        LDA (TEMP0),Y
        LDY #ELEV_DIR_OFFSET
        CLC
        ADC (TEMP0),Y                   ; add direction
        LDY #ELEV_Y_OFFSET              ; get Y position
        STA (TEMP0),Y                   ; store new y position
        STA YCOORD                      ; set sprite Y
        LDY #ELEV_X_OFFSET
        LDA (TEMP0),Y                   ; get elevator X
        STA XCOORD
        LDA #$08                        ; shape 8 = elevator sprite
        STA SHAPE
        LDA #$FF                        ; white
        STA COLOR
        JSR DRAW_NOCOLL                 ; draw elevator

; Check bounce boundaries
        LDA YCOORD
        LDY #ELEV_BOT_Y_OFFSET
        CMP (TEMP0),Y                   ; bottom boundary?
        BEQ ELEV_BOUNCE                 ; yes, bounce
        LDY #ELEV_TOP_Y_OFFSET
        CMP (TEMP0),Y                   ; top boundary?
        BEQ ELEV_BOUNCE                 ; yes, bounce
        LDY #ELEV_MID_Y_OFFSET
        CMP (TEMP0),Y                   ; pause point?
        BEQ ELEV_PAUSE
        RTS

; Reverse elevator 2 direction
ELEV_BOUNCE:
        LDY #ELEV_DIR_OFFSET
        LDA (TEMP0),Y
        EOR #$FE                        ; flip direction
        STA (TEMP0),Y
ELEV_PAUSE:
        LDA #$10                        ; pause for 16 frames
        LDY #ELEV_PAUSE_OFFSET
        STA (TEMP0),Y
        RTS

; ----------------------------------------------------------------
; ELEV1_ANIM - Elevator sprite animation
; Moves elevator vertically, bouncing between Y limits
; Uses ELEV1_DELAY for timing, ELEV1_DIR for direction
; ----------------------------------------------------------------

; Animate elevator item - bounces vertically at fixed X position
; Elevator sprite at X=$54, bounces between Y=$60 and Y=$99
; ELEV1_DIR = +1 (down) or -1 (up), flipped via EOR #$FE
ELEV1_ANIM:
        LDA ELEV1_DELAY                 ; check delay counter
        BEQ ELEV1_MOVE                  ; if zero, time to move
        DEC ELEV1_DELAY                 ; count down delay
        RTS                             ; wait for next frame

ELEV1_MOVE:
        LDA ELEV1_Y                     ; get current Y position
        CLC
        ADC ELEV1_DIR                   ; add direction (+1 or -1)
        STA ELEV1_Y                     ; store new position
        LDA #$54                        ; elevator X position = 84
        STA XCOORD
        CLC
        LDA ELEV1_Y                     ; reload Y position
        STA YCOORD                      ; set sprite Y
        LDA #$08                        ; shape 8 = elevator sprite
        STA SHAPE
        LDA #$FF                        ; white color
        STA COLOR
        JSR DRAW_NOCOLL                 ; draw (XOR toggles visibility)

; Check if at bounce boundaries
        LDA ELEV1_Y
        CMP #$99                        ; at bottom boundary? (Y=153)
        BEQ ELEV1_BOUNCE                ; yes, reverse direction
        CMP #$78                        ; at pause point?
        BEQ ELEV1_PAUSE                 ; yes, add delay
        CMP #$10                        ; at top boundary?
        BEQ ELEV1_BOUNCE                ; yes, reverse direction
        RTS

; Reverse elevator direction (+1 <-> -1)
ELEV1_BOUNCE:
        LDA ELEV1_DIR                   ; get direction
        EOR #$FE                        ; flip: $01->$FF, $FF->$01
        STA ELEV1_DIR                   ; store new direction
ELEV1_PAUSE:
        LDA #$04                        ; pause for 4 frames
        STA ELEV1_DELAY
        RTS

; ----------------------------------------------------------------
; ELEV2_ANIM / ELEV3_ANIM - Elevator sprite animations
; Two independent vertically-moving elevator objects
; Each has position, delay, and direction state
; ----------------------------------------------------------------

; Animate elevator 2 - bounces at X=$30, between Y=$0C and Y=$55
ELEV2_ANIM:
        LDA ELEV2_DELAY                 ; check delay counter
        BEQ ELEV2_MOVE                  ; if zero, move
        DEC ELEV2_DELAY                 ; count down
        RTS

ELEV2_MOVE:
        LDA ELEV2_Y                     ; get Y position
        CLC
        ADC ELEV2_DIR                   ; add direction
        STA ELEV2_Y                     ; store new position
        LDA #$30                        ; elevator 2 at X=48
        STA XCOORD
        LDA ELEV2_Y
        STA YCOORD                      ; set sprite Y
        LDA #$08                        ; shape 8 = elevator sprite
        STA SHAPE
        LDA #$FF                        ; white
        STA COLOR
        JSR DRAW_NOCOLL                 ; draw elevator

; Check bounce boundaries
        LDA ELEV2_Y
        CMP #$55                        ; bottom boundary?
        BEQ ELEV2_BOUNCE                ; yes, bounce
        CMP #$0C                        ; top boundary?
        BEQ ELEV2_BOUNCE                ; yes, bounce
        CMP #$1D                        ; pause point?
        BEQ ELEV1_PAUSE                 ; reuse elevator pause routine
        CMP #$35                        ; pause point? (Y=53)
        BEQ ELEV2_PAUSE
        RTS

; Reverse elevator 2 direction
ELEV2_BOUNCE:
        LDA ELEV2_DIR
        EOR #$FE                        ; flip direction
        STA ELEV2_DIR
ELEV2_PAUSE:
        LDA #$10                        ; pause for 16 frames
        STA ELEV2_DELAY
        RTS

; Animate elevator 3 - bounces at X=$0C, between Y=$36 and Y=$73
ELEV3_ANIM:
        LDA ELEV3_TIMER                 ; check timer
        BEQ ELEV3_MOVE                  ; if zero, move
        DEC ELEV3_TIMER                 ; count down
        RTS

ELEV3_MOVE:
        LDA ELEV3_POS                   ; get Y position
        CLC
        ADC ELEV3_MOVDIR                ; add direction
        STA ELEV3_POS                   ; store new position
        LDA #$0C                        ; elevator 3 at X=12
        STA XCOORD
        LDA ELEV3_POS
        STA YCOORD                      ; set sprite Y
        LDA #$08                        ; shape 8 = elevator sprite
        STA SHAPE
        LDA #$FF                        ; white
        STA COLOR
        JSR DRAW_NOCOLL                 ; draw elevator

; Check bounce boundaries
        LDA ELEV3_POS
        CMP #$73                        ; bottom boundary?
        BEQ ELEV3_BOUNCE
        CMP #$10                        ; top boundary?
        BEQ ELEV3_BOUNCE
        RTS

; Reverse elevator 3 direction
ELEV3_BOUNCE:
        LDA ELEV3_MOVDIR
        EOR #$FE                        ; flip direction
        STA ELEV3_MOVDIR
        LDA #$20                        ; pause for 32 frames
        STA ELEV3_TIMER
        RTS

; ----------------------------------------------------------------
; MAINLOOP - Main game loop
; Structure:
;   1. Draw border, update enemies, update elevator
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

; =================================================================
; MAIN GAME LOOP
; Outer loop: draw border, update display, run 128 inner frames
; Inner loop: player movement, animations, collision checks
; Timer decrements once per outer loop iteration
; =================================================================
MAINLOOP:
        JSR DRAWBORDER                  ; draw screen borders
        JSR ERASE_ENEMIES               ; XOR-erase enemies BEFORE elevators move
        LDA #$00
        JSR ELEV_ANIM                   ; animate elevator 1
        LDA #$01
        JSR ELEV_ANIM                   ; animate elevator 2
        LDA #$02
        JSR ELEV_ANIM                   ; animate elevator 3
        JSR UPDATEENEMIES               ; update positions & XOR-draw enemies
        JSR PUTSCORE                    ; display current score
        JSR PUTLIVES                    ; display lives remaining
        STA LOWSCR                      ; $C054 - trigger display present after clear completes
MAINFRAME:
        LDA #$80                        ; 128 inner iterations
        STA PTR1HI                      ; use as frame counter

; Inner loop - runs 128 times per timer tick
MAININNER:
        JSR ERASE_ENEMIES               ; XOR-erase BEFORE anything writes page 1
        JSR CHECKCOLL                   ; draw player, handle input
        LDA #$00
        JSR ELEV_ANIM                   ; animate elevator 1
        LDA #$01
        JSR ELEV_ANIM                   ; animate elevator 2
        LDA #$02
        JSR ELEV_ANIM                   ; animate elevator 3
        JSR UPDATEENEMIES               ; XOR-draw enemies on top of bg+player+elevators
        JSR CHKENEMIES                  ; check player vs enemies
        JSR SPEEDCTRL                   ; pace frame AFTER drawing (enemies visible during wait)

; Check for special keys
        LDA KEYBOARD                    ; read keyboard
        CMP #$93                        ; Ctrl-S? (toggle sound)
        BEQ TOGGLESOUND
        CMP #$9B                        ; ESC? (pause)
        BNE CHECKDEMO
; ESC pressed - pause until another key
        STA KBDSTRB                     ; clear keyboard strobe
L_76D6:
        LDA KEYBOARD                    ; wait for keypress
        BPL L_76D6                      ; loop until key down
        STA KBDSTRB                     ; clear keyboard
        BNE CHECKDEMO                   ; continue game

; Toggle sound on/off
TOGGLESOUND:
        LDA SOUND                       ; get sound flag
        EOR #$80                        ; flip bit 7 (mute toggle)
        STA SOUND                       ; store new setting

; Check if in demo mode
CHECKDEMO:
        LDA DEMO                        ; check demo flag
        BNE CHECKSPEED                  ; if demo, skip key check
        LDA KEYBOARD                    ; check for any keypress
        BMI EXIT                        ; if key pressed, exit demo

; Speed control based on level - higher levels are faster
CHECKSPEED:
        LDA LEVEL                       ; get current level
        CMP #$10                        ; level >= 16?
        BCS FASTMODE                    ; yes, skip extra updates
        JSR CHECKCOLL                   ; extra collision check (slower)
        JMP DECFRAME                    ; continue to frame decrement

; Fast mode for high levels - extra enemy update
FASTMODE:
        JSR UPDATEENEMIES               ; extra enemy movement
        JSR CHECKCOLL                   ; collision check

; Decrement frame counter
DECFRAME:
        DEC PTR1HI                      ; decrement counter
        BNE MAININNER                   ; if not zero, continue inner loop

; One outer loop complete - update timer
        JSR COUNTDOWN                   ; decrement and display timer
;        BCS YOUDIED                 ; if carry set, time's up!
        JMP MAINFRAME                   ; start next outer loop

; Exit game key pressed in demo mode)
EXIT:
        JMP LEVELINIT

; ----------------------------------------------------------------
; YOUDIED - Player death handler
; Decrements lives ($80), plays descending sweep sound
; Displays updated score, then restarts level
; If lives=0: return (game over back to caller)
; ----------------------------------------------------------------

; Player death handler
; Decrements lives, plays descending sweep sound
; If lives remain: restart level
; If lives = 0: return (game over)
YOUDIED:
        DEC YOULIVES                    ; subtract 1 life
        JSR UPDATEENEMIES               ; update display
        LDA #$00                        ; initialize sound parameters
        STA TEMP0                       ; rising frequency
        LDA #$FF
        STA TEMP1                       ; falling frequency

; Death sound - two-tone descending sweep
DEATHSND:
        LDY #$05                        ; 5 iterations per tone
L_771F:
        LDX TEMP0                       ; get rising delay
L_7721:
        DEX                             ; delay loop
        BNE L_7721
        LDA SOUND                       ; check if sound enabled
        BMI L_772B                      ; skip if muted
        STA SPKR                        ; toggle speaker
L_772B:
        DEY                             ; next iteration
        BNE L_771F

        LDY #$05                        ; 5 iterations for second tone
L_7730:
        LDX TEMP1                       ; get falling delay
L_7732:
        DEX                             ; delay loop
        BNE L_7732
        LDA SOUND                       ; check if sound enabled
        BMI L_773C                      ; skip if muted
        STA SPKR                        ; toggle speaker
L_773C:
        DEY                             ; next iteration
        BNE L_7730

; Sweep frequency
        INC TEMP0                       ; increase pitch 1
        DEC TEMP1                       ; decrease pitch 2
        LDA TEMP1                       ; check if done
        BNE DEATHSND                    ; continue sweep

; Update display and check for game over
        JSR PUTLIVES                    ; show remaining lives
        LDA YOULIVES                    ; check lives
        BEQ DEATHEND                    ; if zero, game over
        JMP CLEARSCREENS                ; restart level

DEATHEND:
        JMP LEVELINIT

; ----------------------------------------------------------------
; BONUSSCORE - Award points for reaching elevator
; Adds $10 (BCD) per elevator eaten, calls COUNTDOWN check
; Loops until timer expires
; ----------------------------------------------------------------

; Award bonus points after clearing all enemies
; Adds $10 (10 BCD points) per frame until timer expires
BONUSSCORE:
        LDA #$10                        ; 10 points per tick
        JSR ADDSCORE                    ; add to score
        JSR COUNTDOWN                   ; decrement timer
        BCC BONUSSCORE                  ; if time left, keep adding
; Advance to next level, cycling 1->2->3->1
        LDA CURRENT_LEVEL_NUM
        CLC
        ADC #$01
        CMP #NUM_LEVELS                 ; past last level?
        BCC NEXTLEVEL                   ; no, use it
        LDA #$00                        ; wrap to level 0
NEXTLEVEL:
        STA CURRENT_LEVEL_NUM
        INC LEVEL                       ; bump difficulty
        JMP CLEARSCREENS                ; start new level

; ----------------------------------------------------------------
; SPEEDCTRL - Speed control based on level number
; Lower levels get more delay (easier), higher levels less
; Uses WAIT ($FCA8) ROM routine for timing
; Levels >= 15 ($0F): no delay at all
; ----------------------------------------------------------------

; Speed control - delays game based on level number
; Lower levels = more delay (easier)
; Level 0: max delay, Level 14: minimal delay, Level 15+: no delay
SPEEDCTRL:
        LDA LEVEL                       ; get current level
        CMP #$0F                        ; level >= 15?
        BCS SPEEDRTS                    ; yes, no delay at all
        LDA VBLREG                      ; capture current browser frame counter
SPEEDWAIT:
        CMP VBLREG                      ; has it changed? (new ~60Hz frame arrived)
        BEQ SPEEDWAIT                   ; no, spin until it does
SPEEDRTS:
        RTS

; ----------------------------------------------------------------
; DRAWBORDER - Draw border lines on both HGR pages
; Writes $D4/$D5 border bytes to left/right columns
; Addresses both pages simultaneously (XOR $60 trick)
; ----------------------------------------------------------------

; Draw vertical borders on left and right edges of screen
; Writes to BOTH HGR pages simultaneously using EOR #$60 trick
; $D4/$D5 bytes create solid vertical lines
DRAWBORDER:
        LDY #$10                        ; start at scanline 16
BORDERLOOP:
        LDA SPRLO,Y                     ; get HGR address low byte
        STA PTR1LO                      ; set ptr1 (page 1)
        STA PTR2LO                      ; set ptr2 (same low byte)
        LDA SPRHI,Y                     ; get HGR address high byte
        STA PTR1HI                      ; ptr1 high (page 1: $20-$3F)
        EOR #$60                        ; flip to page 2 ($60-$7F)
        STA PTR2HI                      ; ptr2 high (page 2)
        TYA                             ; save scanline index
        PHA
        LDY #$00                        ; left edge (column 0)
        LDA #$D4                        ; border byte (vertical line)
        STA (PTR1LO),Y                  ; write to page 1
        STA (PTR2LO),Y                  ; write to page 2
        LDY #$26                        ; right edge (column 38)
        STA (PTR1LO),Y                  ; write to page 1
        STA (PTR2LO),Y                  ; write to page 2
        PLA                             ; restore scanline index
        TAY
        INY                             ; next scanline
        CPY #$C0                        ; at line 192?
        BNE BORDERLOOP                  ; continue until bottom

; Fill bottom row
        LDY #$26                        ; start at right edge
        LDA #$D5                        ; slightly different border byte
L_779E:
        STA (PTR1LO),Y                  ; write to page 1
        STA (PTR2LO),Y                  ; write to page 2
        EOR #$7F                        ; alternate pattern
L_77A4:
        DEY                             ; previous column
        BPL L_779E                      ; loop until column 0
        RTS

; ----------------------------------------------------------------
; Plot routines
; PLOTOR   ($7906) - OR pixel into screen (for additive drawing)
; PLOTDIRECT ($7909) - Direct write pixel (for overwrite)
; Both write to HGR Page 1 AND Page 2 simultaneously
; Uses HGRLO/HGRHI lookup tables at $7951/$7A11
; ----------------------------------------------------------------

PLOTVEC1:
        JMP PLOTRTS                     ; $7950

PLOTVEC2:
        JMP PLOTRTS                     ; $7950

PLOTOR:
        JMP PLOTOR_IMPL                 ; $792F

PLOTDIRECT:
        JMP PLOTDIR_IMPL                ; $790F

        JMP PLOTRTS                     ; $7950

; PLOTDIR_IMPL - Direct write pixel to screen (overwrites existing)
; Input: XCOORD = X position (pixels), YCOORD = Y position (rows)
;        COLOR = byte value to write (7 pixels + hi-bit)
; Writes to BOTH HGR pages simultaneously using EOR #$60 trick
PLOTDIR_IMPL:
        LDY YCOORD                      ; get Y row number
        LDX HGRLO,Y                     ; get HGR line address low byte
        LDA HGRHI,Y                     ; get HGR line address high byte
        STA TOHI                        ; set pointer high (page 1: $20-$3F)
        STX TOLO                        ; set pointer low
        LDA XCOORD                      ; get X coordinate
        LSR A                           ; divide by 4
        LSR A                           ; (4 pixels per byte in HGR)
        TAY                             ; Y = byte offset within line
        LDA COLOR                       ; get color/pixel pattern
        STA (TOLO),Y                    ; write to page 1
        PHA                             ; save color on stack
        LDA TOHI                        ; get page 1 high byte
        EOR #$60                        ; flip to page 2 ($20↔$40, $2x↔$4x)
        STA TOHI                        ; point to page 2
        PLA                             ; restore color
        STA (TOLO),Y                    ; write to page 2
        RTS

; PLOTOR_IMPL - OR pixel into screen (additive/non-destructive)
; Same as PLOTDIR but ORs with existing screen content
; Used for drawing without erasing background
PLOTOR_IMPL:
        LDY YCOORD                      ; get Y row number
        LDX HGRLO,Y                     ; get HGR line address low
        LDA HGRHI,Y                     ; get HGR line address high
        STA TOHI                        ; set pointer (page 1)
        STX TOLO                        ; set low byte
        LDA XCOORD                      ; get X coordinate
        LSR A                           ; divide by 4 to get byte offset
        LSR A
        TAY                             ; Y = byte index in line
        LDA COLOR                       ; get color pattern
        ORA (TOLO),Y                    ; OR with existing screen data
        STA (TOLO),Y                    ; write merged result to page 1
        PHA                             ; save merged color
        LDA TOHI                        ; get page 1 pointer high
        EOR #$60                        ; flip $2x↔$4x for page 2
        STA TOHI                        ; point to page 2
        PLA                             ; restore merged color
        STA (TOLO),Y                    ; write to page 2
PLOTRTS:
        RTS

; ----------------------------------------------------------------
; HGRLO/HGRHI - HGR line address lookup tables
; 192 entries (one per screen row 0-191)
; Address = HGRHI[row]:HGRLO[row] (for page 1: $20xx-$3Fxx)
; Apple II HGR has interleaved memory layout:
;   Groups of 8 rows separated by $400
;   Within groups, rows offset by $80
; EOR #$60 converts page 1 ($2x) to page 2 ($4x)
; ----------------------------------------------------------------
HGRLO:
        .BYTE $00, $00, $00, $00, $00, $00, $00, $00, $80, $80, $80, $80, $80, $80, $80, $80 ; |................................................................................................................|
        .BYTE $00, $00, $00, $00, $00, $00, $00, $00, $80, $80, $80, $80, $80, $80, $80, $80 ; |................................................................................................................|
        .BYTE $00, $00, $00, $00, $00, $00, $00, $00, $80, $80, $80, $80, $80, $80, $80, $80 ; |................................................................................................................|
        .BYTE $00, $00, $00, $00, $00, $00, $00, $00, $80, $80, $80, $80, $80, $80, $80, $80 ; |................................................................................................................|
        .BYTE $28, $28, $28, $28, $28, $28, $28, $28, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8 ; |...#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#.|
        .BYTE $28, $28, $28, $28, $28, $28, $28, $28, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8 ; |...#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#.|
        .BYTE $28, $28, $28, $28, $28, $28, $28, $28, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8 ; |...#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#.|
        .BYTE $28, $28, $28, $28, $28, $28, $28, $28, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8 ; |...#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#.|
        .BYTE $50, $50, $50, $50, $50, $50, $50, $50, $D0, $D0, $D0, $D0, $D0, $D0, $D0, $D0 ; |....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#|
        .BYTE $50, $50, $50, $50, $50, $50, $50, $50, $D0, $D0, $D0, $D0, $D0, $D0, $D0, $D0 ; |....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#|
        .BYTE $50, $50, $50, $50, $50, $50, $50, $50, $D0, $D0, $D0, $D0, $D0, $D0, $D0, $D0 ; |....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#|
        .BYTE $50, $50, $50, $50, $50, $50, $50, $50, $D0, $D0, $D0, $D0, $D0, $D0, $D0, $D0 ; |....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#|
; HGRHI - High bytes for page 1 addresses ($20-$3F range)
; Pattern repeats: $20,$24,$28,$2C,$30,$34,$38,$3C for groups of 8
; Each set of 64 rows increments base ($20→$21→$22→$23)
; To convert to page 2: EOR #$60 ($2x becomes $4x)
HGRHI:
        .BYTE $20, $24, $28, $2C, $30, $34, $38, $3C, $20, $24, $28, $2C, $30, $34, $38, $3C ; |.....#...#..#....#.#...##.#.....##...#.##....###...####......#...#..#....#.#...##.#.....##...#.##....###...####.|
        .BYTE $21, $25, $29, $2D, $31, $35, $39, $3D, $21, $25, $29, $2D, $31, $35, $39, $3D ; |#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.|
        .BYTE $22, $26, $2A, $2E, $32, $36, $3A, $3E, $22, $26, $2A, $2E, $32, $36, $3A, $3E ; |.#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####..#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####.|
        .BYTE $23, $27, $2B, $2F, $33, $37, $3B, $3F, $23, $27, $2B, $2F, $33, $37, $3B, $3F ; |##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.|
        .BYTE $20, $24, $28, $2C, $30, $34, $38, $3C, $20, $24, $28, $2C, $30, $34, $38, $3C ; |.....#...#..#....#.#...##.#.....##...#.##....###...####......#...#..#....#.#...##.#.....##...#.##....###...####.|
        .BYTE $21, $25, $29, $2D, $31, $35, $39, $3D, $21, $25, $29, $2D, $31, $35, $39, $3D ; |#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.|
        .BYTE $22, $26, $2A, $2E, $32, $36, $3A, $3E, $22, $26, $2A, $2E, $32, $36, $3A, $3E ; |.#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####..#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####.|
        .BYTE $23, $27, $2B, $2F, $33, $37, $3B, $3F, $23, $27, $2B, $2F, $33, $37, $3B, $3F ; |##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.|
        .BYTE $20, $24, $28, $2C, $30, $34, $38, $3C, $20, $24, $28, $2C, $30, $34, $38, $3C ; |.....#...#..#....#.#...##.#.....##...#.##....###...####......#...#..#....#.#...##.#.....##...#.##....###...####.|
        .BYTE $21, $25, $29, $2D, $31, $35, $39, $3D, $21, $25, $29, $2D, $31, $35, $39, $3D ; |#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.|
        .BYTE $22, $26, $2A, $2E, $32, $36, $3A, $3E, $22, $26, $2A, $2E, $32, $36, $3A, $3E ; |.#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####..#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####.|
        .BYTE $23, $27, $2B, $2F, $33, $37, $3B, $3F, $23, $27, $2B, $2F, $33, $37, $3B, $3F ; |##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $BF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............#############...............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $9F, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............############................##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $DF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............############.#..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $DF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............############.#..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $DF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............############.#..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $55, $2A, $00, $00, $FF, $FF, $00, $00, $FF, $00, $7E, $7E, $00 ; |#######..............#.#.#.#.#.#.#...............##############..............#######........######.######.......|
        .BYTE $FF, $00, $00, $FF, $00, $7E, $7E, $00, $7E, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............#######........######.######........######..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $00, $00, $00, $00, $2A, $00, $2A, $00, $2A ; |#######..............##############...........................................#.#.#.........#.#.#.........#.#.#.|
        .BYTE $00, $7E, $00, $7E, $00, $7E, $00, $7E, $00, $7E, $00, $FF, $FF, $00, $00, $FF ; |........######........######........######........######........######.......##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $DF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............############.#..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $BF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............#############...............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $9F, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............############................##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $00, $55, $00, $7E, $00, $7E, $7E, $00, $00, $55, $2A, $00 ; |#######..............#######.......#.#.#.#........######........######.######..............#.#.#.#.#.#.#........|
        .BYTE $7E, $00, $00, $FF, $00, $55, $2A, $00, $00, $00, $7E, $00, $FF, $00, $00, $FF ; |.######..............#######.......#.#.#.#.#.#.#.......................######.......#######..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $00, $00, $00, $00, $00, $00, $00, $FF ; |#######..............##############..............#######.................................................#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $00, $00, $00, $00, $00, $7E, $00, $00, $00 ; |#######..............##############..................................................######.....................|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $00, $7E, $7E, $00, $7E, $00, $7E, $00, $7E, $00, $7E, $00, $00, $7E, $7E, $00 ; |........######.######........######........######........######........######...............######.######.......|
        .BYTE $7E, $00, $7E, $00, $7E, $00, $7E, $00, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |.######........######........######........######.......#######..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $00 ; |#######..............##############..............##############..............##############.....................|
        .BYTE $55, $2A, $00, $2A, $00, $7E, $00, $7E, $00, $7E, $00, $FF, $FF, $00, $00 ; |#.#.#.#.#.#.#.........#.#.#.........######........######........######.......##############..............|

; ----------------------------------------------------------------
; KBDPAUSE - Keyboard handler with pause toggle
; Checks for Ctrl-T ($94) to toggle pause mode ($50)
; If not paused: reads joystick via CHKJOY or keyboard
; Returns to KBDDISPATCH for J/K key handling
; ----------------------------------------------------------------

KBDPAUSE:
        LDA KEYBOARD                    ; read keyboard hardware register
        CMP #$94                        ; is it Ctrl-T (toggle pause)?
        BEQ KBDTOGGLE                   ; yes, toggle pause mode
        LDA PAUSEFLAG                   ; check current pause state
        BEQ KBDCHECK_JOY                ; if not paused, read joystick
        BNE KBDCHECK_KEY                ; if paused, only check keyboard

; Toggle pause on/off
KBDTOGGLE:
        STA KBDSTRB                     ; clear keyboard strobe
        LDA PAUSEFLAG                   ; get current pause state
        EOR #$FF                        ; flip all bits (toggle)
        STA PAUSEFLAG                   ; store new pause state
        BNE KBDCHECK_KEY                ; if now paused, check keyboard

; Not paused - check joystick then handle key
KBDCHECK_JOY:
        JSR CHKJOY                      ; read joystick position
        JMP NOCOLLISION                 ; return to game (no player collision check)

; Paused or post-toggle - read keyboard key
KBDCHECK_KEY:
        LDA KEYBOARD                    ; read keyboard register
        JMP KBDDISPATCH                 ; jump to key handler

; ----------------------------------------------------------------
; TITLESCREEN - Title screen credits drawing
; Displays text strings using DRAWTEXT + PIXRENDER:
;   "SNOOKUMS"
;   "BY JEFF KOFTINOFF"
;   "COPYRIGHT (C) JEFF KOFTINOFF"
; Also draws decorative sprites around title
; NOTE: Not called by the game loop at present
; ----------------------------------------------------------------

; Display title screen credits and decoration
; Called from external module, sets up text strings and calls DRAWTEXT
TITLESCREEN:
        LDA #$D5
        STA TEMP3                       ; $03
        LDA #$03
        STA WIDTH                       ; $1C
        LDA #$09
        STA HEIGHT                      ; $1D
        LDA #$40
        STA YY                          ; $1B
        LDA #$04
        STA XX                          ; $1A
        LDA #<STR_SNOOKUMS              ; point to STR_SNOOKUMS
        STA STRLO                       ; $F0
        LDA #>STR_SNOOKUMS
        STA STRHI                       ; $F1
        JSR DRAWTEXT                    ; $813A
        LDA #$FF
        STA TEMP3                       ; $03
        LDA #$00
        STA WIDTH                       ; $1C
        LDA #$02
        STA HEIGHT                      ; $1D
        LDA #$8C
        STA YY                          ; $1B
        LDA #$0B
        STA XX                          ; $1A
        LDA #<STR_BYJEFF                ; point to STR_BYJEFF
        STA STRLO                       ; $F0
        LDA #>STR_BYJEFF
        STA STRHI                       ; $F1
        JSR DRAWTEXT                    ; $813A
        LDA #$FF
        STA TEMP3                       ; $03
        LDA #$00
        STA WIDTH                       ; $1C
        LDA #$01
        STA HEIGHT                      ; $1D
        LDA #$A0
        STA YY                          ; $1B
        LDA #$06
        STA XX                          ; column 6: the line is 28 characters
        LDA #<STR_COPYRIGHT             ; point to STR_COPYRIGHT
        STA STRLO                       ; $F0
        LDA #>STR_COPYRIGHT
        STA STRHI                       ; $F1
        JSR DRAWTEXT                    ; $813A
        LDA #$FF
        STA COLOR                       ; $11
        LDA #$0E
        STA XCOORD                      ; $18
        LDA #$00
        STA $13
        STA $12
        LDA #$AA
        STA YCOORD                      ; $19
        LDA #$04
        STA SHAPE                       ; $10
        JSR DRAW_NOCOLL                 ; $9300
        RTS                             ; (the original fell through into font data here)

; ----------------------------------------------------------------
; TITLEANIM - Title screen animation
; Waits using WAIT ($FCA8), then does XOR screen effect
; More waits, then returns
; ----------------------------------------------------------------

TITLEANIM:
        LDY #$81
        LDA #$FF
        JSR WAIT                        ; $FCA8
        JSR WAIT                        ; $FCA8
        LDA #$80
        STA STRLO                       ; $F0
        JSR XORSCREEN                   ; $81A0
        LDA #$FF
        JSR WAIT                        ; $FCA8
        JSR WAIT                        ; $FCA8
        RTS

; ----------------------------------------------------------------
; DRAWTEXT - Render encoded text string
; Pointer at ($F0): bytes = character indices (0=space, 1=A, ...)
; Terminates when byte >= $80
; Each character drawn via PIXRENDER ($9000)
; Advances XCOORD position after each character
; ----------------------------------------------------------------

DRAWTEXT:
        LDY #$00
        LDA (STRLO),Y                   ; $F0
        BMI DRAWTEXT_RTS
        JSR PIXRENDER                   ; $9000
        LDA XX                          ; $1A
        SEC
        ADC WIDTH                       ; $1C
        STA XX                          ; $1A
        INC STRLO                       ; $F0
        BNE DRAWTEXT
DRAWTEXT_RTS:
        RTS

STR_SNOOKUMS:
        .BYTE $13
        .BYTE $0E
        .BYTE $0F
        .BYTE $0F
        .BYTE $0B
        .BYTE $15
        .BYTE $0D
        .BYTE $13
        .BYTE $FF
STR_BYJEFF:
        .BYTE $02
        .BYTE $19
        .BYTE $00
        .BYTE $0A
        .BYTE $05
        .BYTE $06
        .BYTE $06
        .BYTE $00
        .BYTE $0B
        .BYTE $0F
        .BYTE $06
        .BYTE $14
        .BYTE $09
        .BYTE $0E
        .BYTE $0F
        .BYTE $06
        .BYTE $06
        .BYTE $FF
STR_COPYRIGHT:
        .BYTE $03
        .BYTE $0F
        .BYTE $10
        .BYTE $19
        .BYTE $12
        .BYTE $09
        .BYTE $07
        .BYTE $08
        .BYTE $14
        .BYTE $00
        .BYTE $1B
        .BYTE $03
        .BYTE $1D
        .BYTE $00
        .BYTE $0A
        .BYTE $05
        .BYTE $06
        .BYTE $06
        .BYTE $00
        .BYTE $0B
        .BYTE $0F
        .BYTE $06
        .BYTE $14
        .BYTE $09
        .BYTE $0E
        .BYTE $0F
        .BYTE $06
        .BYTE $06
        .BYTE $FF

; ----------------------------------------------------------------
; XORSCREEN - Screen dissolve/scramble effect
; XORs each byte in $2000-$3FFF with its address low byte
; Creates visual noise/transition effect
; ----------------------------------------------------------------

XORSCREEN:
        LDY #$00
        STY STRLO                       ; $F0
        LDA #$20
        STA STRHI                       ; $F1
L_81A8:
        LDA (STRLO),Y                   ; $F0
        EOR STRLO                       ; $F0
        STA (STRLO),Y                   ; $F0
        INY
        BNE L_81A8
        INC STRHI                       ; $F1
        LDA STRHI                       ; $F1
        CMP #$40
        BNE L_81A8
        RTS

; ----------------------------------------------------------------
; DRAWDIGIT - Render a score digit on the hi-res screen
; Input: SHAPE($10) = digit value 0-9
;        XX($1A) = X position, YY($1B) = Y position
;        TEMP3($03) = color pattern
; Uses PLOTDIRECT ($7909) via DIGITPLOT helper
; Renders 16-row × 2-column digit from font data
; ----------------------------------------------------------------

; Draw a large digit (0-9) for score display
; Font data at DIGIT_FONT + digit*32 (10 glyphs, 2 bytes x 16 rows each)
DRAWDIGIT:
        LDA SHAPE                       ; digit value (0-9)
        LDX #>DIGIT_FONT
        ASL A                           ; x2
        ASL A                           ; x4
        ASL A                           ; x8
        ASL A                           ; x16
        ASL A                           ; x32 = offset into DIGIT_FONT, carry = bit 8
        BCC DRAWDIGIT_LO
        INX                             ; digits 8 and 9 spill into the next page
DRAWDIGIT_LO:
        CLC
        ADC #<DIGIT_FONT                ; add low byte of font base
        BCC DRAWDIGIT_PTR
        INX
DRAWDIGIT_PTR:
        STA SHPLO
        STX SHPHI                       ; SHPLO/SHPHI -> this digit's glyph
        LDY #$00                        ; reset font data offset to start of digit
        LDA YY                          ; get target Y position
        STA YCOORD                      ; set working Y coordinate
        LDA #$10                        ; 16 rows per digit
        STA HEIGHT                      ; set row counter

; Draw one row of the digit (2 bytes wide)
L_8A12:
        LDA XX                          ; get target X position
        STA XCOORD                      ; set working X coordinate
        LDA (SHPLO),Y                   ; read first font byte for this row
        AND TEMP3                       ; apply color mask
        STA COLOR                       ; set draw color
        STY TEMP9                       ; save font data offset
        JSR DIGITPLOT                   ; draw left half of row
        LDY TEMP9                       ; restore font offset
        INY                             ; advance to second byte
        LDA (SHPLO),Y                   ; read second font byte
        AND TEMP3                       ; apply color mask
        STA COLOR                       ; set draw color
        STY TEMP9                       ; save offset
        INC XCOORD                      ; move X right for right half
        JSR DIGITPLOT                   ; draw right half of row
        LDY TEMP9                       ; restore font offset
        INY                             ; advance to next row's data
        INC YCOORD                      ; move to next screen row
        DEC HEIGHT                      ; decrement row counter
        BNE L_8A12                      ; loop for all 16 rows
        RTS

; DIGITPLOT - Helper to plot digit byte with X coordinate scaling
; Input: XCOORD = character column (0-39)
;        COLOR = pixel pattern to write
;        YCOORD = screen row
; Multiplies XCOORD by 4 (character to pixel conversion)
; then calls PLOTDIRECT to write to screen
DIGITPLOT:
        LDA XCOORD                      ; get character column position
        PHA                             ; save original X on stack
        ASL A                           ; multiply by 2
        ASL A                           ; multiply by 2 again (X * 4)
        STA XCOORD                      ; store pixel X position
DIGITPLOT2:
        JSR PLOTDIRECT                  ; write pixel to screen
        PLA                             ; restore original character X
        STA XCOORD                      ; put back character position
        RTS

; ----------------------------------------------------------------
; DIGIT_FONT - score/timer digit glyphs, 10 x 32 bytes
; Each digit is 2 bytes wide x 16 rows. DRAWDIGIT indexes DIGIT_FONT + digit*32.
; ----------------------------------------------------------------
DIGIT_FONT:
DIGIT0:
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $F0, $8F                  ; |....#######...|
        .BYTE $F8, $9F                  ; |...#########..|
        .BYTE $BC, $BC                  ; |..####...####.|
        .BYTE $9C, $B8                  ; |..###.....###.|
        .BYTE $8E, $F0                  ; |.###.......###|
        .BYTE $8E, $F0                  ; |.###.......###|
        .BYTE $8E, $F0                  ; |.###.......###|
        .BYTE $8E, $F0                  ; |.###.......###|
        .BYTE $8E, $F0                  ; |.###.......###|
        .BYTE $9C, $B8                  ; |..###.....###.|
        .BYTE $BC, $BC                  ; |..####...####.|
        .BYTE $F8, $9F                  ; |...#########..|
        .BYTE $F0, $8F                  ; |....#######...|
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $80, $80                  ; |..............|
DIGIT1:
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $E0, $83                  ; |.....####.....|
        .BYTE $F0, $83                  ; |....#####.....|
        .BYTE $F0, $83                  ; |....#####.....|
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $C0, $83                  ; |......###.....|
        .BYTE $F0, $8F                  ; |....#######...|
        .BYTE $F0, $8F                  ; |....#######...|
        .BYTE $F0, $8F                  ; |....#######...|
        .BYTE $80, $80                  ; |..............|
DIGIT2:
        .BYTE $F8, $9F                  ; |...#########..|
        .BYTE $FC, $BF                  ; |..###########.|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $8E, $F0                  ; |.###.......###|
        .BYTE $86, $FC                  ; |.##......#####|
        .BYTE $80, $BF                  ; |.......######.|
        .BYTE $C0, $9F                  ; |......######..|
        .BYTE $E0, $87                  ; |.....#####....|
        .BYTE $F0, $81                  ; |....####......|
        .BYTE $F8, $80                  ; |...####.......|
        .BYTE $BC, $80                  ; |..####........|
        .BYTE $9E, $80                  ; |.####.........|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $FC, $FF                  ; |..############|
        .BYTE $80, $80                  ; |..............|
DIGIT3:
        .BYTE $FC, $BF                  ; |..###########.|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $86, $F8                  ; |.##.......####|
        .BYTE $82, $F0                  ; |.#.........###|
        .BYTE $80, $F0                  ; |...........###|
        .BYTE $C0, $BF                  ; |......#######.|
        .BYTE $E0, $9F                  ; |.....#######..|
        .BYTE $C0, $BF                  ; |......#######.|
        .BYTE $80, $F0                  ; |...........###|
        .BYTE $82, $F0                  ; |.#.........###|
        .BYTE $86, $F8                  ; |.##.......####|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $FC, $BF                  ; |..###########.|
        .BYTE $80, $80                  ; |..............|
DIGIT4:
        .BYTE $E0, $87                  ; |.....#####....|
        .BYTE $F0, $87                  ; |....######....|
        .BYTE $F8, $87                  ; |...#######....|
        .BYTE $B8, $87                  ; |...###.###....|
        .BYTE $BC, $87                  ; |..####.###....|
        .BYTE $9C, $87                  ; |..###..###....|
        .BYTE $9E, $87                  ; |.####..###....|
        .BYTE $8E, $87                  ; |.###...###....|
        .BYTE $FF, $BF                  ; |#############.|
        .BYTE $FF, $BF                  ; |#############.|
        .BYTE $FF, $BF                  ; |#############.|
        .BYTE $80, $87                  ; |.......###....|
        .BYTE $80, $87                  ; |.......###....|
        .BYTE $80, $87                  ; |.......###....|
        .BYTE $80, $87                  ; |.......###....|
        .BYTE $80, $80                  ; |..............|
DIGIT5:
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $8E, $80                  ; |.###..........|
        .BYTE $8E, $80                  ; |.###..........|
        .BYTE $FE, $87                  ; |.#########....|
        .BYTE $FE, $9F                  ; |.###########..|
        .BYTE $FE, $BF                  ; |.############.|
        .BYTE $80, $B8                  ; |..........###.|
        .BYTE $80, $F0                  ; |...........###|
        .BYTE $80, $F0                  ; |...........###|
        .BYTE $80, $B8                  ; |..........###.|
        .BYTE $FE, $BF                  ; |.############.|
        .BYTE $FE, $9F                  ; |.###########..|
        .BYTE $FE, $87                  ; |.#########....|
        .BYTE $80, $80                  ; |..............|
DIGIT6:
        .BYTE $C0, $9F                  ; |......######..|
        .BYTE $F0, $9F                  ; |....########..|
        .BYTE $F8, $9F                  ; |...#########..|
        .BYTE $FC, $80                  ; |..#####.......|
        .BYTE $9C, $80                  ; |..###.........|
        .BYTE $8E, $80                  ; |.###..........|
        .BYTE $EE, $87                  ; |.###.#####....|
        .BYTE $FE, $9F                  ; |.###########..|
        .BYTE $FE, $BF                  ; |.############.|
        .BYTE $9E, $B8                  ; |.####.....###.|
        .BYTE $8E, $B0                  ; |.###.......##.|
        .BYTE $9E, $B8                  ; |.####.....###.|
        .BYTE $FE, $BF                  ; |.############.|
        .BYTE $FC, $9F                  ; |..##########..|
        .BYTE $F8, $87                  ; |...#######....|
        .BYTE $80, $80                  ; |..............|
DIGIT7:
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $FE, $FF                  ; |.#############|
        .BYTE $80, $F8                  ; |..........####|
        .BYTE $80, $BC                  ; |.........####.|
        .BYTE $80, $9E                  ; |........####..|
        .BYTE $80, $8F                  ; |.......####...|
        .BYTE $C0, $87                  ; |......####....|
        .BYTE $E0, $83                  ; |.....####.....|
        .BYTE $E0, $81                  ; |.....###......|
        .BYTE $E0, $81                  ; |.....###......|
        .BYTE $E0, $81                  ; |.....###......|
        .BYTE $E0, $81                  ; |.....###......|
        .BYTE $E0, $81                  ; |.....###......|
        .BYTE $E0, $81                  ; |.....###......|
        .BYTE $80, $80                  ; |..............|
DIGIT8:
        .BYTE $F8, $9F                  ; |...#########..|
        .BYTE $FC, $BF                  ; |..###########.|
        .BYTE $BE, $FC                  ; |.#####...#####|
        .BYTE $9E, $F8                  ; |.####.....####|
        .BYTE $8E, $F0                  ; |.###.......###|
        .BYTE $9E, $F8                  ; |.####.....####|
        .BYTE $FC, $BE                  ; |..#####.#####.|
        .BYTE $F8, $9F                  ; |...#########..|
        .BYTE $FC, $9E                  ; |..#####.####..|
        .BYTE $9E, $B8                  ; |.####.....###.|
        .BYTE $8E, $F0                  ; |.###.......###|
        .BYTE $9E, $F8                  ; |.####.....####|
        .BYTE $BE, $FC                  ; |.#####...#####|
        .BYTE $FC, $BF                  ; |..###########.|
        .BYTE $F8, $9F                  ; |...#########..|
        .BYTE $80, $80                  ; |..............|
DIGIT9:
        .BYTE $E0, $9F                  ; |.....#######..|
        .BYTE $F8, $BF                  ; |...##########.|
        .BYTE $FC, $FF                  ; |..############|
        .BYTE $9C, $F8                  ; |..###.....####|
        .BYTE $8C, $F0                  ; |..##.......###|
        .BYTE $9C, $F8                  ; |..###.....####|
        .BYTE $FC, $FF                  ; |..############|
        .BYTE $F8, $FF                  ; |...###########|
        .BYTE $E0, $F7                  ; |.....#####.###|
        .BYTE $80, $F0                  ; |...........###|
        .BYTE $80, $B8                  ; |..........###.|
        .BYTE $80, $BE                  ; |........#####.|
        .BYTE $F8, $9F                  ; |...#########..|
        .BYTE $F8, $8F                  ; |...########...|
        .BYTE $F8, $83                  ; |...######.....|
        .BYTE $80, $80                  ; |..............|

; ----------------------------------------------------------------
; PIXRENDER - Pixel-level sprite renderer
; Input: A = character/sprite index (×8 for table offset)
;        XCOORD($1A), YCOORD($1B), WIDTH($1C), HEIGHT($1D)
;        TEMP3($03) = color pattern
; Reads 8-byte sprite data from $9100 area
; Renders each bit as a pixel using PLOTOR ($7906)
; Handles Apple II hi-res color fringing (odd/even byte)
; ----------------------------------------------------------------

; =================================================================
; PIXRENDER - Pixel-based character/font renderer
; Reads 8-byte character data from $9100 + (A * 8)
; Each byte = 1 row of 7 pixels (LSB = leftmost)
; Input: A = character index (0=space, 1=A, 2=B, ... 26=Z)
;        XX/YY = screen position, HEIGHT = row multiplier
; =================================================================
PIXRENDER:
        ASL A                           ; multiply index by 8
        ASL A                           ; (8 bytes per character)
        ASL A
        STA SHPLO                       ; low byte = index * 8
        LDA #>FONTDATA                  ; font data page (aligned via .ALIGNPAGE)
        STA SHPHI                       ; set pointer high byte
        LDA XX                          ; get X position
        STA XCOORD                      ; set working X
        LDA YY                          ; get Y position
        STA YCOORD                      ; set working Y
        LDA HEIGHT                      ; get row multiplier
        STA TEMP4                       ; save as row counter
        LDY #$00                        ; start at first byte
        STY TEMP0                       ; font row counter

; Read one row of font data
PIXROW:
        LDY TEMP0                       ; get current font row
        LDA (SHPLO),Y                   ; read font byte
        PHA                             ; save on stack

; Process 8 bits (7 visible + 1 color bit)
PIXBIT:
        PLA                             ; retrieve font byte
        PHA                             ; keep copy on stack
        LDX XX                          ; reset X position
        STX XCOORD
        LDX #$00                        ; bit counter
        STX PIXPOS
        CLC

; Process each bit in the font byte
PIXBITLOOP:
        LSR A                           ; shift out low bit into carry
        BCC PIXBLANK                    ; if bit=0, draw blank
; Bit=1: draw set pixel
        STX TEMP9                       ; save bit counter
        PHA                             ; save remaining bits
        LDA #$FF                        ; set pixel ON
        STA TEMPA
        JSR PIXCOLOR                    ; apply color and plot
        LDX TEMP9                       ; restore counter
        JMP PIXNEXT

; Bit=0: draw blank pixel (respects color mask)
PIXBLANK:
        STX TEMP9                       ; save bit counter
        PHA                             ; save remaining bits
        LDA #$80                        ; set pixel OFF (with hi-bit)
        STA TEMPA
        JSR PIXCOLOR                    ; apply color and plot
        LDX TEMP9                       ; restore counter

PIXNEXT:
        INX                             ; next bit
        PLA                             ; get remaining bits
        CPX #$08                        ; all 8 bits done?
        BNE PIXBITLOOP                  ; no, continue

; Row complete - advance Y
        INC YCOORD                      ; next screen row
        LDA XX                          ; reset X position
        STA XCOORD
        DEC TEMP4                       ; decrement row multiplier
        BNE PIXNEXTBIT                  ; if not 0, repeat row

; Row multiplier done - next font row
        LDA HEIGHT                      ; reset row counter
        STA TEMP4
        PLA                             ; discard saved font byte
        INC TEMP0                       ; next font row
        LDA TEMP0
        CMP #$08                        ; all 8 rows done?
        BNE PIXNEXTROW                  ; no, continue
        RTS                             ; character complete

PIXNEXTBIT:
        JMP PIXBIT                      ; repeat same font row

PIXNEXTROW:
        JMP PIXROW                      ; get next font row

; Apply color mask and plot pixel
; Handles Apple II HGR color fringing (odd/even columns)
PIXCOLOR:
        LDA TEMP3                       ; get color pattern
        AND #$7F                        ; mask off high bit
        BEQ PIXCOLOR2                   ; if 0, use straight mask
        CMP #$7F                        ; if $7F, use straight mask
        BEQ PIXCOLOR2
        LDA XCOORD                      ; check X position
        LSR A                           ; odd or even column?
        BCC PIXCOLOR2                   ; even: use normal color
        LDA TEMP3                       ; odd: invert for fringing
        EOR #$7F
        AND TEMPA                       ; apply pixel state
        JMP PIXCOLORPLOT

PIXCOLOR2:
        LDA TEMP3                       ; get color mask
        AND TEMPA                       ; apply pixel state

PIXCOLORPLOT:
        PHA                             ; save color
        LDY WIDTH                       ; get width setting
        LDA PIXMASK,Y                   ; get bit mask
        LDY PIXPOS                      ; get bit position
        BEQ L_9095                      ; if 0, no shift needed
L_9091:
        ASL A                           ; shift mask left
        DEY
        BNE L_9091
L_9095:
        STA BITMASK                     ; store shifted mask
        PLA                             ; get color back
        AND BITMASK                     ; apply mask
        STA COLOR                       ; set plot color
        LDA XCOORD                      ; get X
        PHA                             ; save it
        ASL A                           ; multiply by 4
        ASL A                           ; (convert char pos to pixel)
        STA XCOORD                      ; set pixel X
        JSR PLOTOR                      ; OR-plot to screen
        PLA                             ; restore X
        STA XCOORD

; Advance pixel position
        LDA PIXPOS                      ; get current position
        PHA
        SEC
        ADC WIDTH                       ; add width
        AND #$07                        ; wrap to 0-7
        STA PIXPOS
        PLA
        SEC
        ADC WIDTH
        AND #$F8                        ; check for byte overflow
        BEQ PIXRTS                      ; no overflow
        INC XCOORD                      ; advance to next byte
PIXRTS:
        RTS

; =================================================================
; CHRGEN Font Data Reference (located at $9100)
; Font is embedded in the packed data below starting at byte offset +72
; from PIXMASK label (i.e., $9100 = PIXMASK + $68)
;
; 8 bytes per character, 7 visible bits per row (LSB = leftmost pixel)
; Character mapping: 0=SPACE, 1-26=A-Z, 27-31=symbols
;
; Visual patterns (# = pixel on, . = pixel off):
;
; SPACE (0)     A (1)         B (2)         C (3)         D (4)
; .......       .####..       #####..       .####..       #####..
; .......       ######.       ##..##.       ##..##.       ##..##.
; .......       #....#.       ##.###.       ##..##.       ###.##.
; .......       ######.       ##.##..       ##.....       ###.##.
; .......       #....#.       ##.###.       ##..##.       ###.##.
; .......       ##..##.       ##..##.       ##..##.       ##..##.
; .......       ##..##.       #####..       .####..       #####..
; .......       .......       .......       .......       .......
;
; E (5)         F (6)         G (7)         H (8)         I (9)
; ######.       ######.       .####..       ##.###.       ..###..
; ##..##.       ##..##.       ##..##.       ##.###.       ..###..
; ##.....       ##.....       ##..##.       ##..##.       ..###..
; ######.       ######.       ##.....       ######.       ..###..
; ##.....       ##.....       ##.###.       ##..##.       ..###..
; ##..##.       ###....       ##..##.       ###.##.       ..###..
; ######.       ####...       .####..       ###.##.       ..###..
; .......       .......       .......       .......       .......
;
; J (10)        K (11)        L (12)        M (13)        N (14)
; ..####.       ###.##.       ####...       ######.       ##.###.
; ..####.       ###.##.       ####...       ######.       ##..##.
; ...###.       ##..##.       ###....       #.##.#.       ###..#.
; #..###.       #####..       ###..#.       #.##.#.       ######.
; ##..##.       ##..##.       ##..##.       #....#.       #..###.
; ###.##.       ###.##.       ##.###.       ##..##.       ##..##.
; .####..       ###.##.       ######.       ##..##.       ###.##.
; .......       .......       .......       .......       .......
;
; O (15)        P (16)        Q (17)        R (18)        S (19)
; ..###..       #####..       .###...       #####..       .#####.
; .#####.       ##..##.       #####..       ##..##.       ##...#.
; .#..##.       ##.###.       #..##..       ##..##.       ####...
; .##.##.       ##.##..       ##.##..       #####..       .####..
; .##..#.       ##.....       ##..#..       ##..##.       ..####.
; .#####.       ###....       ######.       ###.##.       #...##.
; ..###..       ###....       .#####.       ###.##.       #####..
; .......       .......       .......       .......       .......
;
; T (20)        U (21)        V (22)        W (23)        X (24)
; ######.       ##.###.       ##.###.       ##..##.       ##..##.
; ######.       ##.###.       ##.###.       ##..##.       ##..##.
; #.##.#.       ##.###.       ##..#..       #....#.       ######.
; #.##.#.       ##.###.       ##.##..       #.##.#.       .####..
; ..##...       ##.###.       ##.#...       #.##.#.       ######.
; .####..       ##..##.       ####...       ######.       ##..##.
; ######.       .####..       ####...       ##..##.       ##..##.
; .......       .......       .......       .......       .......
;
; Y (25)        Z (26)        [ (27)        \ (28)        ] (29)
; ##.###.       ######.       .####..       .......       .####..
; ##.###.       #..##..       .#.....       #......       ....#..
; ##..##.       #.###..       .#.....       .#.....       ....#..
; ######.       ..##...       .#.....       ..#....       ....#..
; ....##.       .###.#.       .#.....       ...#...       ....#..
; ###.##.       .##..#.       .#.....       ....#..       ....#..
; ######.       ######.       .####..       .....#.       .####..
; .......       .......       .......       .......       .......
;
; ^ (30)        _ (31)
; ...#...       .......
; ..###..       .......
; .#.#.#.       .......
; ...#...       .......
; ...#...       .......
; ...#...       .......
; ...#...       .......
; .......       .......
; =================================================================

PIXMASK:
        .BYTE $01, $03, $07, $0F, $1F, $3F, $7F, $FF ; |#......##.....###....####...#####..######.##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00

; Align font data to page boundary so PIXRENDER can address it via >FONTDATA
; 32 characters × 8 bytes = 256 bytes = exactly one page
        .ALIGNPAGE
FONTDATA:
        .BYTE $00, $00, $00, $00, $00, $00, $00, $00 ; char 0 = SPACE
        .BYTE $1E, $3F, $21, $3F, $21, $33, $33, $00, $1F, $33, $3B, $1B, $3B, $33 ; A (8 bytes) + B (first 6)
        .BYTE $1F, $00, $1E, $33, $33, $03, $33, $33, $1E, $00, $1F, $33, $37, $37, $37, $33 ; |#####..........####..##..##.##..##.##.....##..##.##..##..####.........#####..##..##.###.##.###.##.###.##.##..##.|
        .BYTE $1F, $00, $3F, $33, $03, $3F, $03, $33, $3F, $00, $3F, $33, $03, $3F, $03, $07 ; |#####.........######.##..##.##.....######.##.....##..##.######........######.##..##.##.....######.##.....###....|
        .BYTE $0F, $00, $1E, $33, $33, $03, $3B, $33, $1E, $00, $3B, $3B, $33, $3F, $33, $37 ; |####...........####..##..##.##..##.##.....##.###.##..##..####.........##.###.##.###.##..##.######.##..##.###.##.|
        .BYTE $37, $00, $1C, $1C, $1C, $1C, $1C, $1C, $1C, $00, $BC, $BC, $B8, $B9, $B3, $B7 ; |###.##..........###....###....###....###....###....###....###...........####...####....###.#..###.##..##.###.##.|
        .BYTE $9E, $80, $37, $37, $33, $1F, $33, $37, $37, $00, $0F, $0F, $07, $27, $33, $3B ; |.####.........###.##.###.##.##..##.#####..##..##.###.##.###.##........####...####...###....###..#.##..##.##.###.|
        .BYTE $3F, $00, $3F, $3F, $2D, $2D, $21, $33, $33, $00, $3B, $33, $27, $3F, $39, $33 ; |######........######.######.#.##.#.#.##.#.#....#.##..##.##..##........##.###.##..##.###..#.######.#..###.##..##.|
        .BYTE $37, $00, $1C, $3E, $32, $36, $26, $3E, $1C, $00, $1F, $33, $3B, $1B, $03, $07 ; |###.##..........###...#####..#..##..##.##..##..#..#####...###.........#####..##..##.##.###.##.##..##.....###....|
        .BYTE $07, $00, $0E, $1F, $19, $1B, $13, $3F, $3E, $00, $1F, $33, $33, $1F, $33, $37 ; |###............###...#####..#..##..##.##..##..#..######..#####........#####..##..##.##..##.#####..##..##.###.##.|
        .BYTE $37, $00, $3E, $23, $0F, $1E, $3C, $31, $1F, $00, $3F, $3F, $2D, $2D, $0C, $1E ; |###.##.........#####.##...#.####....####....####.#...##.#####.........######.######.#.##.#.#.##.#...##....####..|
        .BYTE $3F, $00, $3B, $3B, $3B, $3B, $3B, $33, $1E, $00, $3B, $3B, $13, $1B, $0B, $0F ; |######........##.###.##.###.##.###.##.###.##.###.##..##..####.........##.###.##.###.##..#..##.##..##.#...####...|
        .BYTE $0F, $00, $33, $33, $21, $2D, $2D, $3F, $33, $00, $33, $33, $3F, $1E, $3F, $33 ; |####..........##..##.##..##.#....#.#.##.#.#.##.#.######.##..##........##..##.##..##.######..####..######.##..##.|
        .BYTE $33, $00, $3B, $3B, $33, $3F, $30, $37, $3F, $00, $3F, $19, $1D, $0C, $2E, $26 ; |##..##........##.###.##.###.##..##.######.....##.###.##.######........######.#..##..#.###....##....###.#..##..#.|
        .BYTE $3F, $00, $1E, $02, $02, $02, $02, $02, $1E, $00, $00, $01, $02, $04, $08, $10 ; |######.........####...#......#......#......#......#......####................#.......#.......#.......#.......#..|
        .BYTE $20, $00, $9E, $90, $90, $90, $90, $90, $9E, $80, $08, $1C, $2A, $08, $08, $08 ; |.....#.........####......#......#......#......#......#...####............#.....###...#.#.#....#......#......#...|
        .BYTE $08, $00, $80, $80, $80, $80, $80, $80, $80, $00, $FF, $FF, $00, $00, $FF, $FF ; |...#..................................................................##############..............##############|
        .BYTE $00, $00, $FF, $25, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............########.#..#...............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $37, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##########.##...............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $85, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............########.#..................##############..............##############..............##############|
        .BYTE $00, $00, $FF, $AF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............###########.#...............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $9D, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............########.###................##############..............##############..............##############|
        .BYTE $00, $00, $FF, $19, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............########..##................##############..............##############..............##############|
        .BYTE $00, $00, $FF, $39, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............########..###...............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF ; |..............##############..............##############..............##############..............##############|
        .BYTE $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00 ; |..............##############..............##############..............|

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

; Entry point: draw sprite without collision detection
DRAW_NOCOLL:
        JMP DRAWNOCOLL_ENTRY            ; jump to no-collision routine

; Entry point: draw sprite WITH collision detection
; Sprite data format: [WIDTH][HEIGHT][WIDTH*HEIGHT pixel bytes]
; Sprite address = (SHAPE | $60) * 256 (page-aligned in HGR page 2)
; Sub-pixel alignment: SHAPE += (XCOORD & 3) for pre-shifted versions
DRAW_COLL:
        LDA #$00                        ; clear collision report
        STA REPORT
        NOP                             ; padding/timing
        JSR CALCSPRADDR                 ; get sprite pointer, returns X&3 in A
        AND #$03                        ; mask low 2 bits of X
        CLC
        ADC SHAPE                       ; add to SHAPE for sub-pixel version
        STA SHAPE                       ; select pre-shifted sprite (0-3)
        LDA XCOORD                      ; get X coordinate
        LSR A                           ; divide by 4
        LSR A                           ; (convert pixels to bytes)
        STA XCOORD                      ; store byte column
        STA XX                          ; save for row reset
        LDA YCOORD                      ; get Y coordinate
        STA YY                          ; save for iteration
        LDA SHAPE                       ; get adjusted shape index
        ORA #$60                        ; OR with base page ($60xx = HGR page 2)
        STA SHPHI                       ; sprite pointer high byte
        LDY #$00                        ; start at offset 0
        LDA (SHPLO),Y                   ; read WIDTH from sprite header
        STA WIDTH
        INY
        LDA (SHPLO),Y                   ; read HEIGHT from sprite header
        STA HEIGHT
        JSR ADVANCEPTR                  ; advance SHPLO past header

; Draw sprite row by row (with collision)
DRAWCOLL_ROW:
        LDA WIDTH                       ; get sprite width
        STA TEMPWID                     ; save as column counter
        LDY YY                          ; get current Y row
        LDA SPRLO,Y                     ; get HGR row address low
        CLC
        ADC XCOORD                      ; add X byte offset
        STA TOLO                        ; store as dest ptr (page 1)
        STA PTR2LO                      ; also store for page 2
        LDA SPRHI,Y                     ; get HGR row address high
        STA TOHI                        ; page 1 pointer high
        EOR #$60                        ; flip to page 2 ($20-$3F -> $40-$5F)
        STA PTR2HI                      ; page 2 pointer high
        LDY #$00                        ; start at column 0

; Draw sprite column by column
DRAWCOLL_COL:
        LDA (SHPLO),Y                   ; read sprite byte
        CMP #$FF                        ; is it collision marker?
        BEQ DRAWCOLL_HIT                ; yes, handle collision
        AND COLOR                       ; apply color mask

; SELF-MODIFYING: This instruction gets changed at runtime!
; modified by DRAWOBST_INIT to switch ORA/direct modes
DRAWCOLL_PLOT:
        ORA (PTR2LO),Y                  ; OR with existing screen data
        STA (TOLO),Y                    ; write to page 1
        INY                             ; next column
        DEC TEMPWID                     ; decrement width counter
        BNE DRAWCOLL_COL                ; continue if columns remain

; Row complete - advance to next row
        LDA SHPLO                       ; get sprite ptr low
        CLC
        ADC WIDTH                       ; add width to skip to next row
        STA SHPLO                       ; store new pointer
        INC YY                          ; next screen row
        DEC HEIGHT                      ; decrement row counter
        BNE DRAWCOLL_ROW                ; continue if rows remain
        RTS

; Collision marker ($FF) found - record what's on screen
DRAWCOLL_HIT:
        LDA (TOLO),Y                    ; read existing screen byte
        STA REPORT                      ; store as collision result
        LDA #$00                        ; write zero (transparent)
        JMP DRAWCOLL_PLOT               ; continue drawing

; ----------------------------------------------------------------
; DRAWNOCOLL_ENTRY - Draw sprite, no collision detection
; Same algorithm as DRAW_COLL but writes to both HGR pages
; Uses self-modifying code at $93C7 (DRAWNOCOLL_PLOT)
; ----------------------------------------------------------------
DRAWNOCOLL_ENTRY:
        LDA #$00                        ; clear collision report
        STA REPORT
        NOP                             ; padding/timing
        JSR CALCSPRADDR                 ; compute sprite base pointer
        AND #$03                        ; get sub-pixel offset (X mod 4)
        CLC
        ADC SHAPE                       ; add to shape for pre-shifted version
        STA SHAPE                       ; SHAPE now 0-3 for sub-pixel alignment
        LDA XCOORD                      ; get X coordinate in pixels
        LSR A                           ; divide by 4 to get byte column
        LSR A                           ; (4 pixels per byte)
        STA XCOORD                      ; store byte column
        STA XX                          ; save for row reset
        LDA YCOORD                      ; get Y coordinate
        STA YY                          ; save for iteration
        LDA SHAPE                       ; get adjusted shape index
        ORA #$60                        ; OR with page 2 base ($60xx)
        STA SHPHI                       ; high byte of sprite ptr
        LDY #$00                        ; read from offset 0
        LDA (SHPLO),Y                   ; get WIDTH from sprite header
        STA WIDTH
        INY
        LDA (SHPLO),Y                   ; get HEIGHT from sprite header
        STA HEIGHT
        JSR ADVANCEPTR                  ; skip past 2-byte header

; Draw sprite row by row (no collision variant)
DRAWNOCOLL_ROW:
        LDA WIDTH                       ; get sprite width
        STA TEMPWID                     ; save as column counter
        LDY YY                          ; get current Y row
        LDA SPRLO,Y                     ; get HGR address low byte
        CLC
        ADC XCOORD                      ; add X byte offset
        STA TOLO                        ; dest ptr page 1 (low)
        STA PTR2LO                      ; dest ptr page 2 (low)
        LDA SPRHI,Y                     ; get HGR address high byte
        STA PTR2HI                      ; page 2 high ($20-$3F)
        EOR #$60                        ; flip to page 1 ($40-$5F)
        STA TOHI                        ; page 1 high

        LDY #$00                        ; start at column 0

; Process each column of sprite row
DRAWNOCOLL_COL:
        LDA (SHPLO),Y                   ; read sprite byte
        CMP #$FF                        ; check for collision marker
        BEQ DRAWNOCOLL_HIT              ; if $FF, read existing screen
        AND COLOR                       ; apply color mask

; SELF-MODIFYING: This instruction gets changed at runtime!
; $93C7 modified by DRAWOBST_INIT for OR-merge or direct write
DRAWNOCOLL_PLOT:
        STA (PTR2LO),Y                  ; write to page 2
        STA (TOLO),Y                    ; write to page 1
        INY                             ; next column
        DEC TEMPWID                     ; decrement width counter
        BNE DRAWNOCOLL_COL              ; continue if more columns

; Row complete - advance to next row
        LDA SHPLO                       ; get sprite ptr low
        CLC
        ADC WIDTH                       ; add width to skip to next row data
        STA SHPLO                       ; update sprite pointer
        INC YY                          ; next screen row
        DEC HEIGHT                      ; decrement row counter
        BNE DRAWNOCOLL_ROW              ; continue if more rows
        RTS

; Collision marker ($FF) found - report existing screen contents
DRAWNOCOLL_HIT:
        LDA (TOLO),Y                    ; read existing screen byte
        STA REPORT                      ; save as collision info
        LDA #$00                        ; transparent (don't draw)
        JMP DRAWNOCOLL_PLOT             ; continue with zero byte

; ----------------------------------------------------------------
; CALCSPRADDR - Calculate sprite base address
; Input: XCOORD = X position in pixels
; Output: SHPLO = low byte of sprite pointer (adjusted)
;         A = original XCOORD (caller uses A AND #$03 for sub-pixel)
; Algorithm: counts X/4 pairs to determine color cycle bit
; The COLORCYCLE mask selects color-shifting behavior
; ----------------------------------------------------------------
; Result: SHPLO = $00, or $80 when COLORCYCLE bit 7 is set and the sprite lands on an odd
; byte column (selects the SHAPE_xx_Vn_ODD copy at offset $80 of the sprite page)
CALCSPRADDR:
        LDA XCOORD                      ; get X coordinate
        LDY #$00                        ; Y = pair counter
L_93EB:
        INY                             ; count first byte of pair
        SEC
        SBC #$04                        ; subtract 4 pixels
        BCC L_93F7                      ; if negative, done counting
        INY                             ; count second byte of pair
        SEC
        SBC #$04                        ; subtract another 4 pixels
        BCS L_93EB                      ; continue while positive
L_93F7:
        NOP                             ; timing/alignment
        TYA                             ; A = byte pair count
        AND #$01                        ; get odd/even byte flag
        CLC
        ROR A                           ; shift right through carry
        ROR A                           ; move bit to high position
        AND COLORCYCLE                  ; apply color cycle mask
        STA SHPLO                       ; store as sprite ptr low byte
        LDA XCOORD                      ; return original XCOORD in A
        RTS

; ----------------------------------------------------------------
; ADVANCEPTR - Advance sprite pointer past header
; Input: Y = current offset (should be 1 after reading header)
;        SHPLO = sprite pointer low byte
; Output: SHPLO += Y + 1 (skips past 2-byte header)
; ----------------------------------------------------------------
ADVANCEPTR:
        INY                             ; Y = 2 (past WIDTH and HEIGHT)
        TYA                             ; A = 2
        CLC
        ADC SHPLO                       ; add to sprite pointer
        STA SHPLO                       ; SHPLO now points to pixel data
        RTS

; ----------------------------------------------------------------
; SPRLO/SPRHI - HGR row address lookup tables
; Apple II HGR has non-linear memory layout due to interleaving
; Row Y's base address = SPRHI[Y]:SPRLO[Y]
; These are for HGR page 2 ($2000-$3FFF)
; EOR #$60 converts to page 1 ($4000-$5FFF)
;
; HGR layout: 8 groups of 8 rows, each group offset by $400
; Within groups, rows offset by $80 (every 8th row)
; Table provides 192 entries (0-191), one per screen row
; ----------------------------------------------------------------
SPRLO:
        .BYTE $00, $00, $00, $00, $00, $00, $00, $00, $80, $80, $80, $80, $80, $80, $80, $80 ; |................................................................................................................|
        .BYTE $00, $00, $00, $00, $00, $00, $00, $00, $80, $80, $80, $80, $80, $80, $80, $80 ; |................................................................................................................|
        .BYTE $00, $00, $00, $00, $00, $00, $00, $00, $80, $80, $80, $80, $80, $80, $80, $80 ; |................................................................................................................|
        .BYTE $00, $00, $00, $00, $00, $00, $00, $00, $80, $80, $80, $80, $80, $80, $80, $80 ; |................................................................................................................|
        .BYTE $28, $28, $28, $28, $28, $28, $28, $28, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8 ; |...#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#.|
        .BYTE $28, $28, $28, $28, $28, $28, $28, $28, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8 ; |...#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#.|
        .BYTE $28, $28, $28, $28, $28, $28, $28, $28, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8 ; |...#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#.|
        .BYTE $28, $28, $28, $28, $28, $28, $28, $28, $A8, $A8, $A8, $A8, $A8, $A8, $A8, $A8 ; |...#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#.|
        .BYTE $50, $50, $50, $50, $50, $50, $50, $50, $D0, $D0, $D0, $D0, $D0, $D0, $D0, $D0 ; |....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#|
        .BYTE $50, $50, $50, $50, $50, $50, $50, $50, $D0, $D0, $D0, $D0, $D0, $D0, $D0, $D0 ; |....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#|
        .BYTE $50, $50, $50, $50, $50, $50, $50, $50, $D0, $D0, $D0, $D0, $D0, $D0, $D0, $D0 ; |....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#|
        .BYTE $50, $50, $50, $50, $50, $50, $50, $50, $D0, $D0, $D0, $D0, $D0, $D0, $D0, $D0 ; |....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#....#.#|

; SPRHI - High bytes of HGR row addresses (page 2: $20-$3F)
; Pattern: $20,$24,$28,$2C,$30,$34,$38,$3C repeats (groups of 8)
; Each group increments base by 1 ($20→$21→$22→$23)
; EOR #$60 converts page 2 ($20-$3F) to page 1 ($40-$5F)
SPRHI:
        .BYTE $20, $24, $28, $2C, $30, $34, $38, $3C, $20, $24, $28, $2C, $30, $34, $38, $3C ; |.....#...#..#....#.#...##.#.....##...#.##....###...####......#...#..#....#.#...##.#.....##...#.##....###...####.|
        .BYTE $21, $25, $29, $2D, $31, $35, $39, $3D, $21, $25, $29, $2D, $31, $35, $39, $3D ; |#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.|
        .BYTE $22, $26, $2A, $2E, $32, $36, $3A, $3E, $22, $26, $2A, $2E, $32, $36, $3A, $3E ; |.#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####..#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####.|
        .BYTE $23, $27, $2B, $2F, $33, $37, $3B, $3F, $23, $27, $2B, $2F, $33, $37, $3B, $3F ; |##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.|
        .BYTE $20, $24, $28, $2C, $30, $34, $38, $3C, $20, $24, $28, $2C, $30, $34, $38, $3C ; |.....#...#..#....#.#...##.#.....##...#.##....###...####......#...#..#....#.#...##.#.....##...#.##....###...####.|
        .BYTE $21, $25, $29, $2D, $31, $35, $39, $3D, $21, $25, $29, $2D, $31, $35, $39, $3D ; |#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.|
        .BYTE $22, $26, $2A, $2E, $32, $36, $3A, $3E, $22, $26, $2A, $2E, $32, $36, $3A, $3E ; |.#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####..#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####.|
        .BYTE $23, $27, $2B, $2F, $33, $37, $3B, $3F, $23, $27, $2B, $2F, $33, $37, $3B, $3F ; |##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.|
        .BYTE $20, $24, $28, $2C, $30, $34, $38, $3C, $20, $24, $28, $2C, $30, $34, $38, $3C ; |.....#...#..#....#.#...##.#.....##...#.##....###...####......#...#..#....#.#...##.#.....##...#.##....###...####.|
        .BYTE $21, $25, $29, $2D, $31, $35, $39, $3D, $21, $25, $29, $2D, $31, $35, $39, $3D ; |#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.#....#.#.#..#.#..#.#.#.##.#.#...##.#.#.##.#..###.#.####.|
        .BYTE $22, $26, $2A, $2E, $32, $36, $3A, $3E, $22, $26, $2A, $2E, $32, $36, $3A, $3E ; |.#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####..#...#..##..#..#.#.#..###.#..#..##..##.##..#.###..#####.|
        .BYTE $23, $27, $2B, $2F, $33, $37, $3B, $3F, $23, $27, $2B, $2F, $33, $37, $3B, $3F ; |##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.##...#.###..#.##.#.#.####.#.##..##.###.##.##.###.######.|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF, $FF, $00, $00, $FF ; |#######..............##############..............##############..............##############..............#######|
        .BYTE $FF, $00, $00             ; |#######..............|

NUM_LEVELS              = 4

LEVEL_MAPS:
        .BYTE <LEVEL_1_MAP, >LEVEL_1_MAP
        .BYTE <LEVEL_2_MAP, >LEVEL_2_MAP
        .BYTE <LEVEL_3_MAP, >LEVEL_3_MAP
        .BYTE <LEVEL_4_MAP, >LEVEL_4_MAP

ELEV_X_OFFSET           = 0
ELEV_Y_OFFSET           = 1
ELEV_TOP_Y_OFFSET       = 2
ELEV_MID_Y_OFFSET       = 3
ELEV_BOT_Y_OFFSET       = 4
ELEV_DIR_OFFSET         = 5
ELEV_PAUSE_OFFSET       = 6
ELEV_DELAY_OFFSET       = 7
ELEV_BYTESIZE           = 8

        .INCLUDE "level1.s"
        .INCLUDE "level2.s"
        .INCLUDE "level3.s"
        .INCLUDE "level4.s"

