# Hook at 0x800BEE88 in CameraQuasiFPS::move (PAL G4BP08), only reached when m_init_flag is set.
# The game snaps CamSmth there (drops the smoothing lag). When the player just went into the weapon
# (6) or knife (0xB) routine, skip the snap so the camera keeps moving smoothly; else as usual.
    lwz   r9,-26332(r13)        # pPL
    lbz   r0,0xFC(r9)
    cmpwi r0,0
    bne   L_orig
    lbz   r0,0xFD(r9)
    cmpwi r0,6
    beq   L_skip
    cmpwi r0,0xB
    bne   L_orig
L_skip:
    lis   r9,0x800B
    ori   r9,r9,0xEE9C          # past CamSmth.setFlag()
    mtctr r9
    bctr
L_orig:
    lis   r9,-32735             # original instruction
