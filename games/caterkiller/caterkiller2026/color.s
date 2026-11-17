TEMP0            = $00
TEMP1            = $01
TEMP2            = $02
TEMP3            = $03
COLOR0           = $04
COLOR1           = $05

KEYBOARD         = $C000
KBDSTRB          = $C010
SPKR             = $C030
TXTCLR           = $C050
TXTSET           = $C051
MIXCLR           = $C052
MIXSET           = $C053
LOWSCR           = $C054
HISCR            = $C055
LORES            = $C056
HIRES            = $C057
PB0              = $C061
PB1              = $C062
PB2              = $C063

        .ORG $6000

        .ORG $7200

ENTRY:
        LDA #$55
        STA HIRES
        STA LOWSCR
        STA MIXCLR
        STA COLOR0
        LDA #$2A
        STA COLOR1
CLEARSCREENS:
        LDY #$00                    ; Y = byte counter (0-255)
        STY TEMP0                   ; ptr1 low = 0 (page 1)
        LDA #$20                    ; start at $2000 (HGR page 1)
        STA TEMP1                   ; ptr1 high = $20
CLEARLOOP:
        LDA COLOR0
        STA (TEMP0),Y               ; write to page 1
        INY                         ; next byte in page
        LDA COLOR1
        STA (TEMP0),Y
        INY
        BNE CLEARLOOP               ; loop until 256 bytes done
;        INC COLOR
        INC TEMP1                   ; next page on HGR 1 ($21, $22...)
        LDA TEMP1                   ; check if done
        CMP #$40                    ; $60 = end of HGR page 2
        BNE CLEARLOOP               ; continue until both pages cleared
;        INC COLOR
        STA LOWSCR
wait_vblank:
        ;BIT $C019        ; sets N from bit 7
        ;BPL wait_vblank   ; loop while N=0 (not in vblank)

        JMP CLEARSCREENS 

