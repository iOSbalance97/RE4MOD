# Hook at 0x800DF940 in plemDoorOpen r_no_2 1, motion not finished. r31 = player.
# From push frame EXITF on, moving the stick ends the open early (jumps to the normal end path).
    lwz   r0,0x290(r31)         # Motion.Seq_frame (positive float: compare the bits)
    lis   r11,EXITHI
    cmpw  r0,r11
    blt   L_orig
    lis   r11,0x8029
    addi  r11,r11,-9616         # Key
    lwz   r0,0x14(r11)          # Key.on low: tank directions 1/2/4/8
    andi. r0,r0,0xF
    beq   L_orig
    lis   r11,0x800D
    ori   r11,r11,0xF918        # end path: onOba, EndPlDamage, dmg.set(0,10)
    mtctr r11
    bctr
L_orig:
    lwz   r9,992(r31)           # original instruction
