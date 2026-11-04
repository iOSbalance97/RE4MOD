# Hook at 0x800DBAC4 in emDoor_R1_Open2 r_no_2 0, right after MotionSetCore. r31 = door.
    lis   r11,0x8000
    ori   r11,r11,VB
    lwz   r0,0x10(r11)
    lis   r12,0x3F80            # 1.0
    cmpwi r0,0
    beq   L_set
    lis   r12,FASTHI
L_set:
    stw   r12,0x298(r31)        # door Motion.Seq_speed
    mr    r3,r31                # original instruction
