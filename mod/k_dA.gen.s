# Hook at 0x800DF888 in plemDoorOpen (end of r_no_2 0, after m_Work0 = 45). r31 = player.
# Running (run toggle on) -> Leon's push motion and the door swing at FAST speed.
    lis   r11,0x802b
    ori   r11,r11,0xd644
    lwz   r0,0(r11)             # run toggle
    lis   r12,0x3F80            # 1.0
    cmpwi r0,0
    beq   L_set
    lis   r12,0x3fc0            # FAST
L_set:
    stw   r12,0x298(r31)        # Motion.Seq_speed
    stw   r0,0x10(r11)          # flag for the door (nonzero = fast)
    lbz   r9,254(r31)           # original instruction
