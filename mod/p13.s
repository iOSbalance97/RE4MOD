# Hook at 0x800D0478 (EmAtkHitCk2 entry, PAL G4BP08): r3 = ATK_INFO*, r4 = attack position.
# Knife out (routine 0xB) while drawing (r_no_2 0) or slashing (r_no_2 2), attack in front of Leon and
# close -> the attack misses (return 0). Nothing has been pushed on the stack yet.
    lwz   r12,-26332(r13)       # pPL
    lbz   r0,0xFC(r12)
    cmpwi r0,0
    bne   normal
    lbz   r0,0xFD(r12)
    cmpwi r0,0xB
    bne   normal
    lis   r11,0x8000
    ori   r11,r11,VB+0xC        # parry window (frames left), kept by the movement code
    lwz   r0,0(r11)
    cmpwi r0,0
    ble   normal
check:
    lfs   f0,0(r4)
    lfs   f1,0x94(r12)
    fsubs f0,f0,f1              # dx
    lfs   f2,8(r4)
    lfs   f3,0x9C(r12)
    fsubs f2,f2,f3              # dz
    lfs   f4,0x14(r12)          # forward x (mat[0][2])
    lfs   f5,0x34(r12)          # forward z (mat[2][2])
    fmuls f6,f0,f4
    fmadds f6,f2,f5,f6          # dot(forward, to attack)
    li    r0,0
    stw   r0,0(r11)
    lfs   f7,0(r11)             # 0.0
    fcmpo cr0,f6,f7
    ble   normal                # from behind: no parry
    fmuls f8,f0,f0
    fmadds f8,f2,f2,f8          # distance^2
    lis   r0,RANGE2@h
    ori   r0,r0,RANGE2@l
    stw   r0,0(r11)
    lfs   f7,0(r11)
    fcmpo cr0,f8,f7
    bge   normal
    # parried: the attack misses. With the knife already out (state 1) Leon does his real slash
    # (animation, sound, and the slash's own hit on the enemy).
    lbz   r0,0xFE(r12)
    cmpwi r0,1
    bne   L_miss
    li    r0,0x0200             # r_no_2 = 2 (slash), r_no_3 = 0 (start it)
    sth   r0,0xFE(r12)
L_miss:
    li    r3,0
    blr
normal:
    stwu  r1,-64(r1)            # original instruction
