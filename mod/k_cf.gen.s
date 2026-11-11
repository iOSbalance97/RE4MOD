    lis   r10,0x802b
    ori   r10,r10,0xd5e0        # constant pool
# Hook at 0x800BCD6C (CameraQuasiFPS::calcDepressionRatio, not-aiming branch). r31 = this.
# Right stick turns the camera freely (no 60 deg limit, no return); pitch accumulates.
    # only while Leon moves freely (footwork / walk / back / run / turn): during actions (ladder,
    # jumps, windows...) the game's camera path ignores the free angles, so turning the stick there
    # piled up an angle that snapped the camera at the end of the action
    lwz   r12,-26332(r13)       # pPL
    lbz   r0,0xFC(r12)
    cmpwi r0,0
    bne   L_skip
    lbz   r0,0xFD(r12)
    cmplwi r0,5
    bgt   L_skip
    lis   r8,0x8029
    addi  r8,r8,-9616           # Key
    lbz   r0,2(r8)
    stb   r0,8(r1)
    lbz   r0,3(r8)
    stb   r0,9(r1)
    psq_l f1,8(r1),1,4          # cx
    psq_l f2,9(r1),1,4          # cy
    lfs   f3,56(r10)
    lfs   f0,516(r31)           # m_direction_ratio
    fmadds f0,f1,f3,f0
    lfs   f4,12(r10)
    fadds f5,f4,f4
    fneg  f6,f4
    fcmpo cr0,f0,f4
    ble   L_a1
    fsubs f0,f0,f5
L_a1:
    fcmpo cr0,f0,f6
    bge   L_a2
    fadds f0,f0,f5
L_a2:
    stfs  f0,516(r31)
    lfs   f3,68(r10)
    lfs   f0,512(r31)           # m_depression_ratio
    fmadds f0,f2,f3,f0
    lfs   f4,28(r10)
    fneg  f6,f4
    fcmpo cr0,f0,f4
    ble   L_b1
    fmr   f0,f4
L_b1:
    fcmpo cr0,f0,f6
    bge   L_b2
    fmr   f0,f6
L_b2:
    stfs  f0,512(r31)
    b     L_out
L_skip:
    # during actions (ladder...): the pitch eases back level (x0.9 a frame, so the camera does not
    # end up under the floor at the top); the yaw is kept where it was (no turn)
    lfs   f3,72(r10)
    lfs   f0,512(r31)
    fmuls f0,f0,f3
    stfs  f0,512(r31)
L_out:
    lis   r12,0x800B
    ori   r12,r12,0xCE80        # function epilogue
    mtctr r12
    bctr
