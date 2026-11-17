LEVEL_3_MAP:

        .BYTE $70, $30                  ; Player start position (112, 48)
;             X,  Y,  TOP, MID, BOT, DIR, PAUSE, DELAY
        .BYTE 25, 35, 55, 100, 164, $FD, 0, 140    ; Left elevator: ground to top, fast
        .BYTE 68, 35, 55, 85, 120, $FF, 0, 220     ; Center elevator: mid to top, slow
        .BYTE 115, 35, 55, 100, 164, $FC, 0, 120   ; Right elevator: ground to top, fastest


; Enemy start positions: X, Y for up to five enemies (X 10-137, Y 48-111)
        .BYTE  12,  56
        .BYTE  48,  96
        .BYTE  80,  70
        .BYTE 105, 108
        .BYTE 135,  84

        .BYTE 4                         ; Enemy count: how many of the positions above are used (1-5)

        .BYTE 49                      ; Count of X/Y pairs following

; --- Bottom platforms (Y=164) - narrow footholds with wide gaps ---
        .BYTE 98, 164                   ; right island
        .BYTE 105, 164
        .BYTE 112, 164
        .BYTE 119, 164
        .BYTE 126, 164
        .BYTE 14, 164                   ; left island
        .BYTE 21, 164
        .BYTE 28, 164

; --- Lower-mid platform (Y=140) - small stepping stone ---
        .BYTE 49, 140
        .BYTE 56, 140
        .BYTE 63, 140

; --- Mid platforms (Y=120) - split across the screen ---
        .BYTE 56, 120                   ; center section
        .BYTE 63, 120
        .BYTE 70, 120
        .BYTE 77, 120
        .BYTE 0, 120                    ; far left ledge
        .BYTE 7, 120

; --- Upper-mid (Y=100) - scattered footholds ---
        .BYTE 91, 100
        .BYTE 98, 100
        .BYTE 105, 100
        .BYTE 28, 100
        .BYTE 35, 100

; --- Upper platforms (Y=85) ---
        .BYTE 56, 85                    ; center
        .BYTE 63, 85
        .BYTE 70, 85
        .BYTE 77, 85
        .BYTE 84, 85
        .BYTE 119, 85                   ; far right
        .BYTE 126, 85

; --- High platforms (Y=70) ---
        .BYTE 0, 70                     ; left tower
        .BYTE 7, 70
        .BYTE 14, 70
        .BYTE 35, 70                    ; center-left
        .BYTE 42, 70
        .BYTE 98, 70                    ; center-right
        .BYTE 105, 70

; --- Top platform (Y=55) - the crown, hard to reach ---
        .BYTE 42, 55
        .BYTE 49, 55
        .BYTE 56, 55
        .BYTE 63, 55
        .BYTE 70, 55
        .BYTE 77, 55
        .BYTE 84, 55
        .BYTE 91, 55
        .BYTE 98, 55
        .BYTE 105, 55
