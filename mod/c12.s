# Hook at 0x800BDAE4 (CameraQuasiFPS::hitCheck entry, PAL G4BP08). r5 = QFPS_OFFSET* (fresh every frame).
# campos[0] (camera) is pushed back away from the target by CAM_BACK, fovy is scaled by CAM_FOV.
    stwu  r1,-0x10(r1)
    lis   r0,CAM_BACK@h
    ori   r0,r0,CAM_BACK@l
    stw   r0,0x8(r1)
    lfs   f3,0x8(r1)
    lis   r0,CAM_FOV@h
    ori   r0,r0,CAM_FOV@l
    stw   r0,0xC(r1)
    lfs   f4,0xC(r1)
    lfs   f0,0x00(r5)
    lfs   f1,0x18(r5)
    fsubs f2,f0,f1
    fmadds f0,f2,f3,f0
    stfs  f0,0x00(r5)
    lfs   f0,0x04(r5)
    lfs   f1,0x1C(r5)
    fsubs f2,f0,f1
    fmadds f0,f2,f3,f0
    stfs  f0,0x04(r5)
    lfs   f0,0x08(r5)
    lfs   f1,0x20(r5)
    fsubs f2,f0,f1
    fmadds f0,f2,f3,f0
    stfs  f0,0x08(r5)
    lfs   f0,0x28(r5)
    fmuls f0,f0,f4
    stfs  f0,0x28(r5)
    # --- centre reticle: while aiming (weapon routine, set / fire) the camera looks at the laser hit point
    lis   r11,0x8000
    ori   r11,r11,VB+0x14
    lwz   r12,-26332(r13)       # pPL
    lbz   r0,0xFC(r12)
    cmpwi r0,0
    bne   L_reset
    lbz   r0,0xFD(r12)
    cmpwi r0,6
    bne   L_reset
    lbz   r0,0xFE(r12)
    cmpwi r0,1
    beq   L_aim
    cmpwi r0,2
    bne   L_reset
L_aim:
    # fire (r_no_2 2): the laser is only updated in the set state, so lpos / lcross are stale while the
    # shot / pump plays (the shotgun's is 40 frames). Looking at that stale world point made the camera
    # turn away from Leon when he walked while firing. Keep the last set-state aim point in Leon's
    # frame instead (stored at VB+0x28, valid flag VB+0x34).
    cmpwi r0,2
    bne   L_setaim
    lis   r12,0x8000
    ori   r12,r12,VB+0x14
    lwz   r0,0x20(r12)
    cmpwi r0,0
    beq   L_setaim
    lfs   f6,0x14(r12)
    lfs   f7,0x18(r12)
    lfs   f8,0x1C(r12)
    b     L_blend
L_setaim:
    # aim point = gun + laser direction * D, with D easing towards the hit distance (no jumps at edges)
    lis   r11,0x8021
    ori   r11,r11,0xD820        # lpos (gun), lcross follows at +0xC
    lfs   f0,0x0C(r11)
    lfs   f1,0x00(r11)
    fsubs f6,f0,f1              # v = lcross - lpos
    lfs   f0,0x10(r11)
    lfs   f1,0x04(r11)
    fsubs f7,f0,f1
    lfs   f0,0x14(r11)
    lfs   f1,0x08(r11)
    fsubs f8,f0,f1
    fmuls f9,f6,f6
    fmadds f9,f7,f7,f9
    fmadds f9,f8,f8,f9          # len^2
    lis   r12,0x8000
    ori   r12,r12,VB+0x14        # D (smoothed distance), scratch at +4
    li    r0,0
    stw   r0,4(r12)
    lfs   f10,4(r12)            # 0.0
    fcmpo cr0,f9,f10
    ble   L_noaim
    frsqrte f10,f9              # 1/len, refined twice
    lis   r0,0x3F00
    stw   r0,4(r12)
    lfs   f11,4(r12)            # 0.5
    lis   r0,0x3FC0
    stw   r0,4(r12)
    lfs   f12,4(r12)            # 1.5
    fmuls f13,f10,f10
    fmuls f13,f13,f9
    fnmsubs f13,f13,f11,f12
    fmuls f10,f10,f13
    fmuls f13,f10,f10
    fmuls f13,f13,f9
    fnmsubs f13,f13,f11,f12
    fmuls f10,f10,f13           # inv = 1/len
    fmuls f13,f9,f10            # len
    lfs   f12,0(r12)            # D
    li    r0,0
    stw   r0,4(r12)
    lfs   f11,4(r12)
    fcmpo cr0,f12,f11
    bgt   L_ease
    fmr   f12,f11               # fixed convergence distance (DMIN): the camera no longer turns when the
    b     L_dmin                # laser jumps between near and far surfaces (felt like aim assist)
L_ease:
    fsubs f11,f13,f12
    lis   r0,DEASE@h
    ori   r0,r0,DEASE@l
    stw   r0,4(r12)
    lfs   f9,4(r12)
    fmadds f12,f11,f9,f12       # D += (len - D) * DEASE
L_dmin:
    lis   r0,DMIN@h
    ori   r0,r0,DMIN@l
    stw   r0,4(r12)
    lfs   f9,4(r12)
    fcmpo cr0,f12,f9
    bge   L_dok
    fmr   f12,f9
L_dok:
    stfs  f12,0(r12)
    fmuls f12,f12,f10           # D / len
    lfs   f0,0x00(r11)
    fmadds f0,f6,f12,f0         # aim point
    lfs   f1,0x04(r11)
    fmadds f1,f7,f12,f1
    lfs   f2,0x08(r11)
    fmadds f2,f8,f12,f2
    lfs   f3,0x0C(r4)
    fsubs f0,f0,f3              # dx = P - t
    lfs   f3,0x1C(r4)
    fsubs f1,f1,f3
    lfs   f3,0x2C(r4)
    fsubs f2,f2,f3
    lfs   f5,0x08(r4)           # local z = m02*dx + m12*dy + m22*dz
    fmuls f8,f5,f0
    lfs   f5,0x18(r4)
    fmadds f8,f5,f1,f8
    lfs   f5,0x28(r4)
    fmadds f8,f5,f2,f8
    li    r0,0
    stw   r0,0x8(r1)
    lfs   f9,0x8(r1)
    fcmpo cr0,f8,f9
    ble   L_noaim               # behind the player frame: keep the game's target
    lfs   f5,0x00(r4)           # local x = m00*dx + m10*dy + m20*dz
    fmuls f6,f5,f0
    lfs   f5,0x10(r4)
    fmadds f6,f5,f1,f6
    lfs   f5,0x20(r4)
    fmadds f6,f5,f2,f6
    lfs   f5,0x04(r4)           # local y = m01*dx + m11*dy + m21*dz
    fmuls f7,f5,f0
    lfs   f5,0x14(r4)
    fmadds f7,f5,f1,f7
    lfs   f5,0x24(r4)
    fmadds f7,f5,f2,f7
    # ease the aim point towards the new one (Leon's frame): the switch between the fire state's
    # remembered point and the fresh laser point at the end of a shot no longer jumps
    lwz   r0,0x20(r12)
    cmpwi r0,0
    beq   L_store
    lis   r0,AEASE@h
    ori   r0,r0,AEASE@l
    stw   r0,0x24(r12)
    lfs   f11,0x24(r12)
    lfs   f9,0x14(r12)
    fsubs f6,f6,f9
    fmadds f6,f6,f11,f9
    lfs   f9,0x18(r12)
    fsubs f7,f7,f9
    fmadds f7,f7,f11,f9
    lfs   f9,0x1C(r12)
    fsubs f8,f8,f9
    fmadds f8,f8,f11,f9
L_store:
    stfs  f6,0x14(r12)          # remember it (Leon's frame) for the fire state
    stfs  f7,0x18(r12)
    stfs  f8,0x1C(r12)
    li    r0,1
    stw   r0,0x20(r12)
L_blend:
    lfs   f9,0x2C(r12)          # recoil: the aim point raised by VB+0x40 (hud.c, decays by itself)
    fadds f7,f7,f9
    lfs   f9,4(r12)             # w: how much of the aim point is used (eases in over a few frames)
    lis   r0,WSTEP@h
    ori   r0,r0,WSTEP@l
    stw   r0,0x8(r1)
    lfs   f10,0x8(r1)
    fadds f9,f9,f10
    lis   r0,0x3F80
    stw   r0,0x8(r1)
    lfs   f10,0x8(r1)           # 1.0
    fcmpo cr0,f9,f10
    ble   L_wok
    fmr   f9,f10
L_wok:
    stfs  f9,4(r12)
    lfs   f10,0x18(r5)
    fsubs f6,f6,f10
    fmadds f6,f6,f9,f10
    lfs   f10,0x1C(r5)
    fsubs f7,f7,f10
    fmadds f7,f7,f9,f10
    lfs   f10,0x20(r5)
    fsubs f8,f8,f10
    fmadds f8,f8,f9,f10
    stfs  f6,0x18(r5)           # ofs->m_target
    stfs  f7,0x1C(r5)
    stfs  f8,0x20(r5)
    b     L_noaim
L_reset:
    li    r0,0
    stw   r0,0(r11)
    stw   r0,4(r11)
    stw   r0,0x20(r11)
L_noaim:
    addi  r1,r1,0x10
    stwu  r1,-432(r1)        # original instruction
