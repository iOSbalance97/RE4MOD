# Hook at 0x8003EB6C in cObjWep::drawLaserSight (PAL G4BP08), after the hit switch.
# r31 = hit result (1 scenery, 2 enemy/object), r29 = draw, f30 = distance^2 gun -> hit.
# The game only draws the dot on enemies (result 2); also draw it on scenery.
    cmpwi r31,2                 # enemies: the game draws it itself
    beq   orig
    cmpwi r29,0
    beq   orig
    lis   r9,-32738
    lfs   f0,21292(r9)          # 250000.0 (0.5 m squared), the game's own minimum
    fcmpu cr0,f30,f0
    ble   orig
    lis   r3,0x8021
    ori   r3,r3,0xD820          # lpos
    lis   r4,0x8021
    ori   r4,r4,0xD82C          # lcross (hit point)
    lis   r12,0x8003
    ori   r12,r12,0xED60        # drawPoint
    mtctr r12
    bctrl
orig:
    lis   r9,-32738             # original instruction
