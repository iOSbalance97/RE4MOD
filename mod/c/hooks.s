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
