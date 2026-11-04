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
