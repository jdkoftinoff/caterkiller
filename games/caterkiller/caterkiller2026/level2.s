LEVEL_2_MAP:

        .BYTE $60, $30                  ; Player start position (96, 48)
;             X,  Y,  TOP, MID, BOT, DIR, PAUSE, DELAY
        .BYTE 5, 164, 35, 140, 164, $FE, 0, 180   ; Left elevator: ground to mid
        .BYTE 60, 164, 35, 115, 164, $FF, 0, 200    ; Center elevator: ground to upper
        .BYTE 110, 115, 35, 80, 115, $FD, 0, 160    ; Right elevator: mid to top


; Enemy start positions: X, Y for up to five enemies (X 10-137, Y 48-111)
        .BYTE  15,  76
        .BYTE  40, 100
        .BYTE  68,  64
        .BYTE  96,  88
        .BYTE 125,  52

        .BYTE 4                         ; Enemy count: how many of the positions above are used (1-5)

        .BYTE 43                        ; Count of X/Y pairs following

; --- Bottom platforms (Y=164) - ground floor with two gaps ---
        .BYTE 0, 164                    ; left section
        .BYTE 7, 164
        .BYTE 14, 164
        .BYTE 21, 164
        .BYTE 28, 164
        .BYTE 35, 164
        .BYTE 56, 164                   ; center island
        .BYTE 63, 164
        .BYTE 70, 164
        .BYTE 77, 164
        .BYTE 98, 164                   ; right section
        .BYTE 105, 164
        .BYTE 112, 164
        .BYTE 119, 164
        .BYTE 126, 164
        .BYTE 133, 164

; --- Mid platforms (Y=115) ---
        .BYTE 0, 115                    ; left ledge
        .BYTE 7, 115
        .BYTE 14, 115
        .BYTE 21, 115
        .BYTE 63, 115                   ; right section
        .BYTE 70, 115
        .BYTE 77, 115
        .BYTE 84, 115
        .BYTE 91, 115
        .BYTE 98, 115
        .BYTE 105, 115

; --- Upper platforms (Y=80) ---
        .BYTE 21, 80                    ; left section
        .BYTE 28, 80
        .BYTE 35, 80
        .BYTE 42, 80
        .BYTE 49, 80
        .BYTE 56, 80
        .BYTE 63, 80
        .BYTE 112, 80                   ; right alcove
        .BYTE 119, 80
        .BYTE 126, 80

; --- Top platform (Y=55) ---
        .BYTE 42, 55                    ; center crown
        .BYTE 49, 55
        .BYTE 56, 55
        .BYTE 63, 55
        .BYTE 70, 55
        .BYTE 77, 55
        .BYTE 84, 55

