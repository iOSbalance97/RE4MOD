# Hook at 0x800DF918 in plemDoorOpen: end of the open (natural or early). r31 = player.
    lis   r0,0x3F80
    stw   r0,0x298(r31)         # Motion.Seq_speed = 1.0
    lis   r11,0x8000
    ori   r11,r11,VB
    li    r0,0
    stw   r0,0x10(r11)          # clear the door speed flag
    addi  r9,r31,692            # original instruction
