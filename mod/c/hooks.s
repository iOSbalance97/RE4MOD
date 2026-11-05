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
