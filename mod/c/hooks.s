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
