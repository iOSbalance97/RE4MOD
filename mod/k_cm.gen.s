    lis   r10,0x802b
    ori   r10,r10,0xd5e0        # constant pool
# Hook at 0x800BDAE4 (CameraQuasiFPS::hitCheck entry, PAL G4BP08). r5 = QFPS_OFFSET* (fresh every frame).
# campos[0] (camera) is pushed back away from the target by CAM_BACK, fovy is scaled by CAM_FOV.
    lfs   f3,40(r10)
    lfs   f4,76(r10)
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
    lis   r11,0x802b
    ori   r11,r11,0xd658
    # camera height offset 0xd688 (hud.c): up with a long gun aimed (the barrel stays below the
    # reticle), down while crouched. Position, close point and target.
    lfs   f12,0x30(r11)
    lfs   f0,0x04(r5)
    fadds f0,f0,f12
    stfs  f0,0x04(r5)
    lfs   f0,0x10(r5)
    fadds f0,f0,f12
    stfs  f0,0x10(r5)
    lfs   f0,0x1C(r5)
    fadds f0,f0,f12
    stfs  f0,0x1C(r5)
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
    # the target raised by tan(kick) (0xd684, set and decayed by hud.c) times its distance.
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
    lfs   f10,0(r10)
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
    stwu  r1,-432(r1)        # original instruction
