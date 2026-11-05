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
    # modern aim (B48): the camera stays the game's own aim camera (no more following the laser:
    # no pull towards enemies, no push into Leon at walls). The laser ray itself is cast from the
    # camera centre (hud.c LaserRay) and the shots are bent onto it. Only the recoil is added here:
    # the target raised by tan(kick) (VB+0x40, set and decayed by hud.c) times its distance.
    lfs   f0,0x18(r5)
    lfs   f1,0x00(r5)
    fsubs f6,f0,f1
    lfs   f0,0x1C(r5)
    lfs   f1,0x04(r5)
    fsubs f7,f0,f1
    lfs   f0,0x20(r5)
    lfs   f1,0x08(r5)
    fsubs f8,f0,f1
    fmuls f9,f6,f6
    fmadds f9,f7,f7,f9
    fmadds f9,f8,f8,f9          # distance^2
    li    r0,0
    stw   r0,0x8(r1)
    lfs   f10,0x8(r1)
    fcmpo cr0,f9,f10
    ble   L_noaim
    frsqrte f10,f9
    fmuls f10,f9,f10            # distance (frsqrte estimate, a few % is plenty)
    lfs   f11,0x2C(r11)         # tan(kick)
    lfs   f0,0x1C(r5)
    fmadds f0,f10,f11,f0
    stfs  f0,0x1C(r5)
    b     L_noaim
L_reset:
    li    r0,0
    stw   r0,0(r11)
    stw   r0,4(r11)
    stw   r0,0x20(r11)
L_noaim:
    addi  r1,r1,0x10
    stwu  r1,-432(r1)        # original instruction
