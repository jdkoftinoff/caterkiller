LEVEL_4_MAP:
        .BYTE $40, $20                  ; Player start position
;             X,  Y, TOP, MID, BOT, DIR, PAUSE, DELAY
        .BYTE 10, 35, 60, 80, 164, $fc, 0, 230
        .BYTE 50, 35, 60, 80, 164, $ff, 0, 150
        .BYTE 120, 35, 60, 80, 125, $fe, 0, 100


; Enemy start positions: X, Y for up to five enemies (X 10-137, Y 48-111)
        .BYTE  24,  72
        .BYTE  50, 100
        .BYTE  84,  60
        .BYTE 110,  92
        .BYTE 132,  48

        .BYTE 4                         ; Enemy count: how many of the positions above are used (1-5)

        .BYTE 38                        ; Count of X/Y pairs following

        .BYTE 0, 164
        .BYTE 8, 162
        .BYTE 16, 162
        .BYTE 24, 164
        .BYTE 32, 164
        .BYTE 40, 164
        .BYTE 48, 164
        .BYTE 56, 140
        .BYTE 64, 138
        .BYTE 72, 136
        .BYTE 80, 134
        .BYTE 84, 132
        .BYTE 91, 130
        .BYTE 98, 128
        .BYTE 105, 126
        .BYTE 112, 123
        .BYTE 119, 122
        .BYTE 126, 122
        .BYTE 135, 122

        .BYTE 0, 60
        .BYTE 7, 60
        .BYTE 14, 60
        .BYTE 21, 60
        .BYTE 28, 60
        .BYTE 35, 60
        .BYTE 42, 60
        .BYTE 49, 60
        .BYTE 56, 60
        .BYTE 63, 60
        .BYTE 70, 60
        .BYTE 77, 60
        .BYTE 84, 60
        .BYTE 91, 60
        .BYTE 98, 60
        .BYTE 105, 60
        .BYTE 112, 60
        .BYTE 119, 60
        .BYTE 126, 60
