# Hook at 0x80146D50 in PlWepLockCtrl (PAL G4BP08), after the per-weapon switch:
# f29 = waist limit, f30 = body turn speed, f31 = pitch speed. Weapon sway and laser untouched.
    fsubs f29,f29,f29           # waist limit 0: the whole body turns from the first moment (one phase)
    lis   r11,0x802b
    ori   r11,r11,0xd5e0             # constant pool
    lfs   f0,84(r11)
    fmuls f30,f30,f0            # faster horizontal (C-stick has a shorter range)
    lfs   f0,88(r11)
    fmuls f31,f31,f0
    # response curve: factor = LOWK + (1-LOWK) * |C-stick| / 59 (slow for small pushes)
    lis   r12,0x8029
    addi  r12,r12,-12080        # Joy[0]
    lbz   r0,2(r12)
    extsb r0,r0
    srawi r9,r0,31
    xor   r0,r0,r9
    subf  r0,r9,r0              # |x|
    lbz   r10,3(r12)
    extsb r10,r10
    srawi r9,r10,31
    xor   r10,r10,r9
    subf  r10,r9,r10            # |y|
    # radial magnitude ~ max + 0.414 * min: diagonals as fast as the axes (was max(|x|, |y|))
    cmpw  r0,r10
    bge   L_m
    mr    r9,r0
    mr    r0,r10
    mr    r10,r9
L_m:
    mulli r10,r10,106
    srawi r10,r10,8
    add   r0,r0,r10
    cmpwi r0,59
    ble   L_c
    li    r0,59
L_c:
    stb   r0,0x88(r11)
    psq_l f1,0x88(r11),1,4         # |stick| as float
    lfs   f2,92(r11)
    lfs   f3,32(r11)
    fmadds f1,f1,f2,f3          # factor
    fmuls f30,f30,f1
    fmuls f31,f31,f1
    # acceleration (modern aim): held at full deflection for 8 frames, the turn speeds up to
    # 1 + 16 * ACCK times over the next 16 frames; any smaller push resets it
    lwz   r9,0xa0(r11)
    cmpwi r0,54
    bge   L_acc
    li    r9,0
    b     L_accs
L_acc:
    cmpwi r9,24
    bge   L_accs
    addi  r9,r9,1
L_accs:
    stw   r9,0xa0(r11)
    addi  r10,r9,-8
    cmpwi r10,0
    bge   L_acp
    li    r10,0
L_acp:
    stb   r10,0x89(r11)
    psq_l f1,0x89(r11),1,4
    lfs   f2,96(r11)
    lfs   f3,28(r11)
    fmadds f1,f1,f2,f3
    fmuls f30,f30,f1
    lis   r9,-32727             # original instruction
