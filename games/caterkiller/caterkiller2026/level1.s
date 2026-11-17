LEVEL_1_MAP:

        .BYTE $70, $30                  ; Player start position (112, 48)
;             X,   Y,  TOP, MID, BOT, DIR, PAUSE, DELAY
        .BYTE 16,  164, 53, 85,  115, $FD, 0, 140    ; Left elevator: ground to top, fast
        .BYTE 48,  80,  12, 29,  85,  $FF, 0, 220     ; Center elevator: mid to top, slow
        .BYTE 84,  144, 96, 140, 154, $FC, 0, 120   ; Right elevator: ground to top, fastest


; Enemy start positions: X, Y for up to five enemies (X 10-137, Y 48-111)
        .BYTE  20,  60
        .BYTE  45,  92
        .BYTE  70,  72
        .BYTE  95, 104
        .BYTE 130,  56

        .BYTE 3                         ; Enemy count: how many of the positions above are used (1-5)

        .BYTE 83
        
        .BYTE $0C, $A4, $16, $A5, $1E, $A5, $26, $A4, $2E, $A3, $36, $A1, $3D, $9E, $44, $9C
        .BYTE $4C, $9A, $57, $9B, $5F, $9D, $67, $9F, $6D, $A0, $77, $A0, $7D, $A2, $87, $A3
        .BYTE $04, $73, $0F, $75, $14, $77, $1F, $76, $25, $75, $2F, $74, $24, $57, $2E, $59
        .BYTE $34, $5B, $3F, $5D, $8B, $79, $82, $78, $78, $76, $72, $75, $6A, $77, $61, $78
        .BYTE $58, $79, $47, $5F, $1D, $56, $14, $57, $29, $56, $31, $55, $39, $54, $41, $53
        .BYTE $49, $52, $53, $51, $59, $50, $62, $4E, $6A, $4C, $72, $4B, $78, $4A, $83, $4A
        .BYTE $04, $39, $0E, $38, $14, $37, $1E, $36, $27, $36, $34, $21, $4B, $60, $3E, $23
        .BYTE $46, $25, $4E, $26, $56, $27, $5E, $27, $65, $27, $6F, $26, $74, $25, $87, $22
        .BYTE $7C, $23, $54, $11, $5C, $12, $67, $11, $27, $10, $1E, $12, $16, $13, $0D, $15
        .BYTE $04, $17, $00, $25, $09, $25, $12, $25, $1B, $25, $34, $37, $3D, $38, $47, $39
        .BYTE $4D, $3A, $57, $39, $34, $10, $3F, $11                    

