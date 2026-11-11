# Hook at 0x80051F30 inside pl_R0_Move (PAL G4BP08). r3 = player. LR already saved by pl_R0_Move.
# Frame: 0x08-0x1F scratch, r28-r31 at 0x20, f29-f31 at 0x38/0x40/0x48.
    stwu  r1,-0x60(r1)
    stmw  r28,0x20(r1)
    stfd  f29,0x38(r1)
    stfd  f30,0x40(r1)
    stfd  f31,0x48(r1)
    mr    r31,r3
    lis   r30,0x802b
    ori   r30,r30,0xd644        # variables: +0 run toggle, +4 last yaw, +8 yaw valid (free Gecko area)
    li    r9,3                  # the player is in control: modern pad layout (PadRemap)
    stb   r9,0x20(r30)
    lwz   r9,0x10(r30)          # door-open speed flag still set: that open ended abnormally
    cmpwi r9,0
    beq   L_cd
    li    r9,0
    stw   r9,0x10(r30)
    lis   r9,0x3F80             # Motion.Seq_speed back to 1.0
    stw   r9,0x298(r31)
L_cd:
    lbz   r9,0xFC(r31)
    cmpwi r9,0
    bne   L_wdec
    lbz   r9,0xFD(r31)
    cmpwi r9,0xB
    bne   L_wdec
    lbz   r9,0xFE(r31)
    cmpwi r9,0
    beq   L_wset
    cmpwi r9,2
    bne   L_wdec
L_wset:
    li    r9,15
    stw   r9,0xC(r30)
    b     L_wend
L_wdec:
    lwz   r9,0xC(r30)
    cmpwi r9,0
    ble   L_wend
    subi  r9,r9,1
    stw   r9,0xC(r30)
L_wend:
    lis   r29,0x8029
    addi  r29,r29,-9616         # Key
    li    r0,0
    stw   r0,0x18(r1)           # save-yaw flag for the end
    lbz   r4,0xFC(r31)
    cmpwi r4,0
    bne   novalid
    lbz   r28,0xFD(r31)
    cmplwi r28,5
    bgt   novalid
    li    r0,1
    stw   r0,0x18(r1)
    cmpwi r28,5                 # quick turn: camera keeps following Leon's matrix (no search delay)
    bne   L_ns
    lis   r12,0x8021
    ori   r12,r12,0x7310
    li    r0,0
    sth   r0,0(r12)
L_ns:
    lwz   r0,8(r30)
    cmpwi r0,0
    beq   L_comp_end
    lfs   f1,0xA4(r31)
    lfs   f2,4(r30)
    fsubs f30,f1,f2             # yaw the game added since last frame
    lis   r12,0x8021
    ori   r12,r12,0x7308
    li    r0,0
    bl    wrapf30
    lfs   f0,0(r12)
    fsubs f0,f0,f30
    bl    wrapf0
    stfs  f0,0(r12)
L_comp_end:
    b     L_go
novalid:
    li    r0,0
    stw   r0,8(r30)
    lbz   r4,0xFC(r31)
    cmpwi r4,0
    bne   done
    lbz   r28,0xFD(r31)
L_go:
    lis   r5,0x8029
    addi  r5,r5,-12080          # Joy[0]
    lbz   r6,0(r5)
    extsb r6,r6
    lbz   r7,1(r5)
    extsb r7,r7
    cmpwi r6,12
    bge   L_dx
    cmpwi r6,-12
    ble   L_dx
    li    r6,0
L_dx:
    cmpwi r7,12
    bge   L_dy
    cmpwi r7,-12
    ble   L_dy
    li    r7,0
L_dy:
    stb   r6,0x8(r1)
    stb   r7,0x9(r1)
    psq_l f29,0x8(r1),1,4       # f29 = x (stays for later)
    lwz   r9,0x14(r29)          # Key.on low
    rlwinm r9,r9,0,0,27         # drop tank keys
    cmpwi r28,6
    beq   aimwalk
    cmpwi r28,0xB
    beq   aimwalk
    cmplwi r28,3
    bgt   done
    lwz   r10,0x788(r31)        # Wep
    cmpwi r10,0
    beq   L_ka
    li    r0,0
    andi. r11,r9,0x800          # knife key
    beq   L_kst
    lis   r12,0x8021
    ori   r12,r12,0x7308
    lwz   r0,0(r12)             # camera yaw relative to Leon
L_kst:
    stw   r0,0x30(r10)          # Wep->m_CamAdjY
L_ka:
    # --- push a door open: walking into a door in front of Leon for 12 frames presses the action
    or.   r0,r6,r7
    beq   L_dreset
    lis   r12,0x8028
    addi  r12,r12,-8924         # ActBtn (0x8027DD24)
    lbz   r11,0x40(r12)         # actions registered this frame
    addi  r12,r12,0x44          # ACT_WORK m_task[]
    lis   r10,0x800E
    addi  r10,r10,-3772         # emDoorAction (0x800DF144); emDoorAction2 is +0xA0
L_dl:
    cmpwi r11,0
    ble   L_dreset
    lwz   r0,4(r12)             # func
    cmpw  r0,r10
    beq   L_dfound
    addi  r28,r10,0xA0          # emDoorAction2 (r28 is free here)
    cmpw  r0,r28
    beq   L_dfound
    addi  r12,r12,0x18
    subi  r11,r11,1
    b     L_dl
L_dfound:
    lwz   r10,8(r12)            # the door
    lfs   f0,0x94(r10)
    lfs   f1,0x94(r31)
    fsubs f0,f0,f1              # dx
    lfs   f2,0x9C(r10)
    lfs   f3,0x9C(r31)
    fsubs f2,f2,f3              # dz
    lfs   f4,0x14(r31)
    lfs   f5,0x34(r31)
    fmuls f6,f0,f4
    fmadds f6,f2,f5,f6          # dot(forward, to door)
    lfs   f9,-100(r30)
    fcmpo cr0,f6,f9
    ble   L_dreset
    lwz   r11,0x1C(r30)         # frames pushing
    addi  r11,r11,1
    stw   r11,0x1C(r30)
    cmpwi r11,12
    blt   L_dend
    lwz   r0,0x1C(r29)          # Key.trg |= action
    oris  r0,r0,0x0008
    stw   r0,0x1C(r29)
L_dreset:
    li    r0,0
    stw   r0,0x1C(r30)
L_dend:
    or.   r0,r6,r7
    bne   moving
    li    r0,0
    stw   r0,0(r30)
    stw   r9,0x14(r29)
    bl    ld_zero_normal
    bl    waistcam
    b     done
moving:
    lwz   r10,0x1C(r29)
    andis. r10,r10,0x4000
    beq   L_not
    lwz   r11,0(r30)
    xori  r11,r11,1
    stw   r11,0(r30)
L_not:
    lwz   r11,0(r30)
    cmpwi r11,0
    beq   walkmode

# ---- RUN: Leon turns (smoothly) towards the stick direction, camera slowly follows
    oris  r9,r9,0x4000
    ori   r9,r9,1
    stw   r9,0x14(r29)
    fneg  f1,f29
    psq_l f2,0x9(r1),1,4
    lis   r12,0x8005
    ori   r12,r12,0xFFE8        # atan2f
    mtctr r12
    bctrl
    lis   r12,0x8021
    ori   r12,r12,0x7308        # m_direction_ratio
    lfs   f0,0(r12)
    fadds f30,f1,f0             # delta
    bl    wrapf30
    lfs   f6,-96(r30)
    fabs  f7,f30
    fcmpo cr0,f7,f6
    ble   L_noq
    lis   r0,0x0005             # setRno(0, 5, 0, 0): the game's 180 turn with its animation
    stw   r0,0xFC(r31)
    b     done
L_noq:
    bl    turn                  # turns Leon by ease(delta), camera compensates
    bl    ld_zero_normal
    bl    waistcam
    lis   r12,0x8021
    ori   r12,r12,0x7308
    lbz   r0,2(r29)             # camera stick idle -> camera drifts behind Leon
    cmpwi r0,0
    bne   done
    lfs   f0,0(r12)
    lfs   f1,-92(r30)
    fmuls f0,f0,f1
    stfs  f0,0(r12)
    b     done

# ---- WALK: Leon faces the camera; forward/back with the game's walk / back step, sideways strafe
walkmode:
    rlwinm r9,r9,0,2,0          # no run key while walking (no 180 turn)
    mr    r28,r9                # keep the keys and stick Y across the call (volatile registers)
    stb   r7,0xB(r1)
    fneg  f1,f29
    psq_l f2,0x9(r1),1,4
    lis   r12,0x8005
    ori   r12,r12,0xFFE8        # atan2f
    mtctr r12
    bctrl
    mr    r9,r28
    lbz   r7,0xB(r1)
    extsb r7,r7
    fmr   f29,f1                # phi: stick direction relative to the camera (+ = left)
    lfs   f3,-88(r30)
    cmpwi r7,0
    bge   L_fw
    fabs  f7,f29
    lfs   f6,-84(r30)
    fcmpo cr0,f7,f6
    ble   L_fw                  # mostly sideways: walk forward with the legs turned
    ori   r9,r9,2               # backwards: back-step animation, legs angled a little
    lfs   f4,-100(r30)
    fcmpo cr0,f29,f4
    ble   L_bneg
    fsubs f29,f29,f3
    b     L_bclamp
L_bneg:
    fadds f29,f29,f3
L_bclamp:
    lfs   f6,-80(r30)
    b     L_clamp
L_fw:
    ori   r9,r9,1               # forward / sideways: the normal walk, legs towards the movement
    lfs   f6,-76(r30)
L_clamp:
    fneg  f7,f6
    fcmpo cr0,f29,f6
    ble   L_k1
    fmr   f29,f6
L_k1:
    fcmpo cr0,f29,f7
    bge   L_k2
    fmr   f29,f7
L_k2:
    stw   r9,0x14(r29)
    lis   r12,0x8021
    ori   r12,r12,0x7308
    lfs   f0,0(r12)
    fadds f30,f0,f29            # legs target = camera yaw + leg angle
    bl    turn
    lfs   f1,0(r12)             # torso faces the camera: waist = camera yaw relative to Leon
    lfs   f6,-72(r30)
    fneg  f7,f6
    fcmpo cr0,f1,f6
    ble   L_q1
    fmr   f1,f6
L_q1:
    fcmpo cr0,f1,f7
    bge   L_q2
    fmr   f1,f7
L_q2:
    lfs   f2,-80(r30)
    fabs  f7,f29
    lfs   f6,-68(r30)
    fcmpo cr0,f7,f6
    ble   L_q3
    lfs   f2,-64(r30)
L_q3:
    bl    waistcam
    b     done

# ---- f1 = 0 (waist target), f2 = 0.8 (normal camera smoothing)
ld_zero_normal:
    lfs   f1,-100(r30)
    lfs   f2,-80(r30)
    blr

# ---- waistcam: waist eases to f1, camera smoothing (CamSmth + walk ratio) = f2
waistcam:
    lwz   r10,0x790(r31)        # Waist
    cmpwi r10,0
    beq   L_wc
    lfs   f3,4(r10)
    fsubs f4,f1,f3
    lfs   f5,-60(r30)
    fmadds f3,f4,f5,f3
    stfs  f3,4(r10)
L_wc:
    lis   r10,0x8021
    ori   r10,r10,0x7A44        # CamSmth.m_ratio
    stfs  f2,0(r10)
    lis   r10,0x8021
    ori   r10,r10,0x72B0        # QuasiFPS m_walk_ratio
    stfs  f2,0(r10)
    blr

# ---- turn: f30 = delta (rad). Leon.ang.y += s, camera ratio -= s, s = clamp(delta*EASE, +-MAXTURN)
turn:
    lfs   f3,-88(r30)
    fadds f4,f3,f3
    fneg  f5,f3
    fcmpo cr0,f30,f3
    ble   L_w1
    fsubs f30,f30,f4
L_w1:
    fcmpo cr0,f30,f5
    bge   L_w2
    fadds f30,f30,f4
L_w2:
    lfs   f6,-56(r30)
    fmuls f31,f30,f6
    lfs   f6,-52(r30)
    fneg  f7,f6
    fcmpo cr0,f31,f6
    ble   L_c1
    fmr   f31,f6
L_c1:
    fcmpo cr0,f31,f7
    bge   L_c2
    fmr   f31,f7
L_c2:
    lfs   f8,0xA4(r31)
    fadds f8,f8,f31
    stfs  f8,0xA4(r31)
    lfs   f0,0(r12)
    fsubs f0,f0,f31
    fcmpo cr0,f0,f3
    ble   L_w3
    fsubs f0,f0,f4
L_w3:
    fcmpo cr0,f0,f5
    bge   L_w4
    fadds f0,f0,f4
L_w4:
    stfs  f0,0(r12)
    blr

# ---- weapon (aim / fire / reload) and knife: walk and strafe; reload: right stick turns Leon
aimwalk:
    li    r0,0
    stw   r0,0(r30)
    stw   r9,0x14(r29)
    lbz   r0,0xFE(r31)          # r_no_2
    cmpwi r28,6
    bne   L_knf
    cmpwi r0,0                  # weapon: 0 = draw, 4 = reload -> right stick turns Leon
    bne   L_nd
    lbz   r11,0xFF(r31)         # r_no_3 2 = the shotgun's re-draw after each shot: the aim goes on,
    cmpwi r11,2                 # the right stick must not turn Leon on top of it (the camera
    bne   L_rot                 # spun away after firing the shotgun)
    b     L_nrl
L_nd:
    lwz   r10,0x788(r31)        # past the draw: no pending turn, the kamae camera sits behind Leon
    li    r11,0
    stw   r11,0x30(r10)
    cmpwi r0,4
    beq   L_rot
    b     L_nrl
L_knf:
    cmpwi r0,0                  # knife: 0 = draw, 3 = put away
    bne   L_k3
    lwz   r10,0x788(r31)
    lfs   f1,0x30(r10)          # remaining turn to the camera direction
    lfs   f2,-48(r30)
    fmuls f2,f1,f2
    fsubs f1,f1,f2
    stfs  f1,0x30(r10)
    lfs   f8,0xA4(r31)
    fadds f8,f8,f2
    stfs  f8,0xA4(r31)
    b     L_rot
L_k3:
    cmpwi r0,3
    bne   L_nrl
L_rot:
    lbz   r0,2(r29)             # Key.substickX
    stb   r0,0xA(r1)
    psq_l f1,0xA(r1),1,4
    lfs   f2,-44(r30)
    lfs   f8,0xA4(r31)
    fmadds f8,f1,f2,f8
    stfs  f8,0xA4(r31)
L_nrl:
    or.   r0,r6,r7
    beq   done
    psq_l f2,0x9(r1),1,4
    lfs   f3,-40(r30)
    lfs   f4,-36(r30)
    fmuls f1,f29,f3
    fmuls f2,f2,f4
    cmpwi r7,0
    bge   fwd
    lfs   f5,-80(r30)
    fmuls f2,f2,f5
fwd:
    lfs   f5,0x0C(r31)
    lfs   f6,0x14(r31)
    lfs   f7,0x2C(r31)
    lfs   f8,0x34(r31)
    fmuls f9,f5,f1
    fmadds f9,f6,f2,f9
    fmuls f10,f7,f1
    fmadds f10,f8,f2,f10
    lfs   f11,0x94(r31)
    fadds f11,f11,f9
    stfs  f11,0x94(r31)
    lfs   f12,0x9C(r31)
    fadds f12,f12,f10
    stfs  f12,0x9C(r31)

    b     done                  # never fall into the helpers below

# ---- wrap f30 / f0 into [-PI, PI] (uses f3-f5)
wrapf30:
    lfs   f3,-88(r30)
    fadds f4,f3,f3
    fneg  f5,f3
    fcmpo cr0,f30,f3
    ble   L_a1
    fsubs f30,f30,f4
L_a1:
    fcmpo cr0,f30,f5
    bge   L_a2
    fadds f30,f30,f4
L_a2:
    blr
wrapf0:
    lfs   f3,-88(r30)
    fadds f4,f3,f3
    fneg  f5,f3
    fcmpo cr0,f0,f3
    ble   L_b1
    fsubs f0,f0,f4
L_b1:
    fcmpo cr0,f0,f5
    bge   L_b2
    fadds f0,f0,f4
L_b2:
    blr
done:
    lwz   r0,0x18(r1)
    cmpwi r0,0
    beq   L_nsave
    lfs   f0,0xA4(r31)
    stfs  f0,4(r30)
    li    r0,1
    stw   r0,8(r30)
L_nsave:
    mr    r3,r31
    lfd   f29,0x38(r1)
    lfd   f30,0x40(r1)
    lfd   f31,0x48(r1)
    lmw   r28,0x20(r1)
    addi  r1,r1,0x60
    li    r11,0
