    .section .text.hooks,"ax"
# Hook at 0x80150EAC in sceAtFunc_item (after KeyClear, before itemZoom). r31 = SCE_AT_ITEM.
    .globl hook_item
hook_item:
    mr    r3,r31
    bl    QuickItem
    cmpwi r3,0
    beq   1f
    b     ret_item_handled          # sceAtFunc_item returns 1
1:  mr    r3,r31              # original instruction
    b     ret_item_orig

# Hook at 0x8013792C in PadRead, right after PADRead + PADClamp (r16/r30 live: kept by the C ABI).
    .globl hook_pad
hook_pad:
    bl    PadRemap
    li    r0,4                # original instruction
    b     ret_pad

# pzlPlayer::init (0x80148D64) / ::quit (0x80149058): remember the live case puzzle player.
    .globl hook_pzl_init
hook_pzl_init:
    lis   r11,active_pzl@ha
    stw   r3,active_pzl@l(r11)
    stwu  r1,-72(r1)          # original instruction
    b     ret_pzl_init
    .globl hook_pzl_quit
hook_pzl_quit:
    lis   r11,active_pzl@ha
    lwz   r12,active_pzl@l(r11)
    cmpw  r12,r3
    bne   1f
    li    r12,0
    stw   r12,active_pzl@l(r11)
1:  stwu  r1,-16(r1)          # original instruction
    b     ret_pzl_quit

# Main loop, right after TaskScheduler (0x801249B8): per-frame drawing requests.
    .globl hook_frame
hook_frame:
    bl    ModFrame
    lwz   r9,-29912(r13)      # original instruction
    b     ret_frame

# Main loop, after cMes.Trans (0x80124A44 was `bl CinescoMove`): direct HUD drawing.
    .globl hook_draw
hook_draw:
    bl    ModDraw
    bl    CinescoMove         # original instruction
    b     ret_draw

# cDvdQueue::fileReadAsync (0x800C5E84): answer from the prefetched weapon archive when it is the
# file being read (PrefetchRead returns 1), else the original DVDReadAsyncPrio path.
    .globl hook_dvdread
hook_dvdread:
    stwu  r1,-32(r1)
    mflr  r0
    stw   r0,36(r1)
    stw   r3,8(r1)
    stw   r4,12(r1)
    stw   r5,16(r1)
    stw   r6,20(r1)
    bl    PrefetchRead
    lwz   r0,36(r1)
    mtlr  r0
    cmpwi r3,0
    bne   1f
    lwz   r3,8(r1)
    lwz   r4,12(r1)
    lwz   r5,16(r1)
    lwz   r6,20(r1)
    addi  r1,r1,32
    stwu  r1,-8(r1)           # original instruction
    b     ret_dvdread
1:  addi  r1,r1,32
    li    r3,1                # DVDReadAsyncPrio's TRUE
    blr

# Render, after ExecOt(0x13) and before the item camera pass ExecOt(0x14) (0x80169718): the pickup
# notice backing bar, so the 3D icon (item camera pass) and the messages both land on top of it.
    .globl hook_mesbar
hook_mesbar:
    bl    NoticeBarDraw
    lwz   r9,-29912(r13)      # original instruction
    b     ret_mesbar

# drawLaserSight (0x8003EB6C, after the hit switch): r31 = hit result, r29 = draw. The reticle
# (hud.c) takes the hit point; the beam is no longer drawn (draw flag cleared).
    .globl hook_laser
hook_laser:
    mr    r3,r31
    mr    r4,r29
    bl    LaserHook
    li    r29,0
    lis   r9,-32738           # original instruction
    b     ret_laser

# PlWepHitCheck2 entry (0x80145A0C): r3 = player, r4 = from, r5 = to, r6 weapon, r7 flag, f1 radius.
# SpreadShot (hud.c) moves the end point inside the reticle; then the original prologue.
    .globl hook_hitchk
hook_hitchk:
    stwu  r1,-48(r1)
    mflr  r0
    stw   r0,52(r1)
    stw   r3,8(r1)
    stw   r4,12(r1)
    stw   r5,16(r1)
    stw   r6,20(r1)
    stw   r7,24(r1)
    stfs  f1,28(r1)
    bl    SpreadShot2
    lwz   r3,8(r1)
    lwz   r4,12(r1)
    lwz   r5,16(r1)
    lwz   r6,20(r1)
    lwz   r7,24(r1)
    lfs   f1,28(r1)
    lwz   r0,52(r1)
    mtlr  r0
    addi  r1,r1,48
    stwu  r1,-272(r1)         # original instruction
    b     ret_hitchk

# PlWepLockRand (0x801472DC, the mflag bit0 test): the random weapon sway kept, but scaled down
# (sway_k) - range and steps.
    .globl hook_sway
hook_sway:
    lis   r12,sway_k@ha
    lfs   f12,sway_k@l(r12)
    fmuls f28,f28,f12
    fmuls f29,f29,f12
    fmuls f30,f30,f12
    fmuls f31,f31,f12
    bne   1f
    b     ret_sway_rand
1:  b     ret_sway_recentre

# drawLaserSight 0x8003EA48 (after getMarkerPos, before GetWepTargetPos): LaserRay (hud.c) moves the
# ray onto the camera's centre line.
    .globl hook_laserray
hook_laserray:
    bl    LaserRay
    lwz   r9,-29912(r13)      # original instruction
    b     ret_laserray

# CameraQuasiFPS::calcDepressionRatio, aiming branch (0x800BCD54): r30 = player, r31 = this.
    .globl hook_aimcam
hook_aimcam:
    stwu  r1,-16(r1)
    mr    r3,r30
    mr    r4,r31
    bl    AimCamEnter
    addi  r1,r1,16
    lwz   r3,1928(r30)        # original instruction
    b     ret_aimcam

# CameraQuasiFPS::hitCheck(this, Mtx m, QFPS_OFFSET* ofs, out) (0x800BDB00, after the prologue; c12.s ran at
# the entry): r4 = m, r5 = QFPS_OFFSET
# (eye, close point, target, fovy). StealthCam (stealth.c) moves it for the takedown.
    .globl hook_cam
hook_cam:
    stwu  r1,-48(r1)
    mflr  r0
    stw   r0,52(r1)
    stw   r3,8(r1)
    stw   r4,12(r1)
    stw   r5,16(r1)
    stw   r6,20(r1)
    stw   r7,24(r1)
    stw   r8,28(r1)
    stfs  f1,32(r1)
    stfs  f2,36(r1)
    mr    r3,r5               # r4 = m (r3 is `this`: hitCheck is a member) - the offsets are in m's space

    bl    StealthCam
    lwz   r3,8(r1)
    lwz   r4,12(r1)
    lwz   r5,16(r1)
    lwz   r6,20(r1)
    lwz   r7,24(r1)
    lwz   r8,28(r1)
    lfs   f1,32(r1)
    lfs   f2,36(r1)
    lwz   r0,52(r1)
    mtlr  r0
    addi  r1,r1,48
    mr    r31,r5              # original instruction
    b     ret_cam

# B72/B73: idSysMove00 after pos = pos0 + anim (0x8011D47C, r31 = ID_UNIT, +2 class, +0x68 parent,
# +0x98 pos.y; 640x480 units, y up). Top-level units only:
#  - while the game is in letterbox mode (System_flg 0x800, pG+0x54) anything it parks in the old
#    top bar (y > 182: covered by the bars there) is pushed off screen (the red marker at the top)
#  - the health meter (class 0x21) 60 down to the screen edge in free play (Stop_flg == 0)
    .globl hook_hud
hook_hud:
    lwz   r12,0x68(r31)
    cmpwi r12,0
    bne   1f
    lwz   r11,-29912(r13)
    lwz   r12,0x54(r11)
    andi. r12,r12,0x800
    beq   2f
    lfs   f0,0x98(r31)
    lis   r12,hud_top@ha
    lfs   f1,hud_top@l(r12)
    fcmpo cr0,f0,f1
    ble   2f
    lis   r12,hud_off@ha
    lfs   f1,hud_off@l(r12)
    fadds f0,f0,f1
    stfs  f0,0x98(r31)
2:  lbz   r12,2(r31)
    cmpwi r12,0x21
    bne   1f
    lwz   r12,0x170(r11)
    cmpwi r12,0
    bne   1f
    lfs   f0,0x98(r31)
    lis   r12,hud_dy@ha
    lfs   f1,hud_dy@l(r12)
    fsubs f0,f0,f1
    stfs  f0,0x98(r31)
1:  lbz   r0,4(r31)           # original instruction
    b     ret_hud
    .balign 4
hud_top: .float 182.0
hud_off: .float 600.0
hud_dy: .float 60.0

# C0-01: SceAtExecRoomJump (0x80152E28) entry: Ch0Jump may change the room / pos / rot (the intro's jump).
    .globl hook_rjump
hook_rjump:
    stwu  r1,-32(r1)
    mflr  r0
    stw   r0,36(r1)
    stw   r3,8(r1)
    stw   r4,12(r1)
    stw   r5,16(r1)
    stw   r6,20(r1)
    addi  r3,r1,8
    bl    Ch0Jump
    lwz   r0,36(r1)
    mtlr  r0
    lwz   r3,8(r1)
    lwz   r4,12(r1)
    lwz   r5,16(r1)
    lwz   r6,20(r1)
    addi  r1,r1,32
    stwu  r1,-192(r1)         # original instruction
    b     ret_rjump

# C0-01: EmSetFromList (0x800CB20C) entry: the chapter 0 guards replace r111's list before it is read.
    .globl hook_emlist
hook_emlist:
    stwu  r1,-16(r1)
    mflr  r0
    stw   r0,20(r1)
    bl    Ch0EmList
    lwz   r0,20(r1)
    mtlr  r0
    addi  r1,r1,16
    stwu  r1,-80(r1)          # original instruction
    b     ret_emlist

# C0-09: EtcModelListSet (0x80106B68) entry: the chapter moves the room's boxes before they are set.
    .globl hook_ets
hook_ets:
    stwu  r1,-16(r1)
    mflr  r0
    stw   r0,20(r1)
    stw   r3,8(r1)
    bl    Ch0Ets
    lwz   r0,20(r1)
    mtlr  r0
    lwz   r3,8(r1)
    addi  r1,r1,16
    stwu  r1,-24(r1)          # original instruction
    b     ret_ets
