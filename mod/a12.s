# Hook at 0x80146D50 in PlWepLockCtrl (PAL G4BP08), after the per-weapon switch:
# f29 = waist limit, f30 = body turn speed, f31 = pitch speed. Weapon sway and laser untouched.
    fsubs f29,f29,f29           # waist limit 0: the whole body turns from the first moment (one phase)
    lis   r11,0x8000
    ori   r11,r11,PB             # constant pool
    lis   r12,YAWK@h
    ori   r12,r12,YAWK@l
    stw   r12,0(r11)
    lfs   f0,0(r11)
    fmuls f30,f30,f0            # faster horizontal (C-stick has a shorter range)
    lis   r12,PITCHK@h
    ori   r12,r12,PITCHK@l
    stw   r12,0(r11)
    lfs   f0,0(r11)
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
    cmpw  r0,r10
    bge   L_m
    mr    r0,r10
L_m:
    cmpwi r0,59
    ble   L_c
    li    r0,59
L_c:
    stb   r0,VB+0x24-PB(r11)
    psq_l f1,VB+0x24-PB(r11),1,4         # |stick| as float
    lis   r12,CURVEK@h          # (1-LOWK)/59
    ori   r12,r12,CURVEK@l
    stw   r12,0(r11)
    lfs   f2,0(r11)
    lis   r12,LOWK@h
    ori   r12,r12,LOWK@l
    stw   r12,0(r11)
    lfs   f3,0(r11)
    fmadds f1,f1,f2,f3          # factor
    fmuls f30,f30,f1
    fmuls f31,f31,f1
    lis   r9,-32727             # original instruction
