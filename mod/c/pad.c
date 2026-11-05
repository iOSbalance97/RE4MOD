/* Modern controller layout, applied to the raw pad before the game reads it.
 * Raw GameCube buttons as OmniStation's Dolphin delivers a DualSense (no button map):
 *   Cross=B  Circle=A  Square=Y  Triangle=X  R1(and L1 if mapped)=Z  L2=L  R2=R
 *   L3=L analog only (no digital L)  R3=R analog only  Options=Start
 * Gameplay (player in control): L2 aim, R2 fire, Z knife, Cross action, Circle crouch,
 *   Square reload, Triangle case, L3 run, R3 map, Options pause.
 * Elsewhere (menus, QTEs, cutscenes): triggers stay native, Cross confirms (A), Circle cancels (B),
 *   Triangle/Square swap to Y/X so Triangle also closes the case. */
#include "game.h"

void ModMesTick(void);
u32 WeaponPad(u32 in, int sx, int sy);
void WeaponPadIdle(void);
void CaseAssign(int dir);
int CaseActive(void);
static u32 prev_raw;

void PadRemap(void)
{
    PADStatus* p = &Pad_data[0];
    u32 in, out;
    int l2, r2, l3, r3;

    ModMesTick();
    if (p->err) return;
    in = p->button;
    l2 = (in & PAD_L) != 0;
    r2 = (in & PAD_R) != 0;
    l3 = !l2 && p->triggerLeft > 0x40;
    r3 = !r2 && p->triggerRight > 0x40;
    out = in & (PAD_LEFT | PAD_RIGHT | PAD_DOWN | PAD_UP | PAD_START);

    if (modvars[VB_GAMEPLAY]) {
        modvars[VB_GAMEPLAY]--;
        out &= ~WeaponPad(in, p->stickX, p->stickY);      /* D-pad: quick weapons */
        if (in & PAD_B) out |= PAD_A;                        /* Cross: action */
        if (r2) out |= PAD_A;                                /* R2: fire */
        if (l2) out |= PAD_R;                                /* L2: aim */
        if (in & PAD_Z) out |= PAD_L;                        /* L1/R1: knife */
        if (in & PAD_X) out |= PAD_Y;                        /* Triangle: case */
        if (in & PAD_A) out |= PAD_MOD_CROUCH;               /* Circle: crouch */
        if (in & PAD_Y) out |= l2 ? PAD_B : PAD_MOD_RELOAD;  /* Square: reload (aiming: R+B) */
        if (l3) out |= PAD_B;                                /* L3: run */
        if (r3) out |= PAD_Z;                                /* R3: map */
    } else {
        WeaponPadIdle();
        if ((in & PAD_Z) && CaseActive()) {                 /* case: L1 + D-pad assigns */
            static const u32 bit[4] = { PAD_UP, PAD_RIGHT, PAD_DOWN, PAD_LEFT };
            u32 trg = in & ~prev_raw;
            int i;
            for (i = 0; i < 4; i++) if (trg & bit[i]) { CaseAssign(i); break; }
            out &= ~0xF;                                     /* the cursor does not move meanwhile */
            in &= ~PAD_Z;                                    /* and Z does not reach the case */
        }
        out |= in & (PAD_L | PAD_R | PAD_Z);
        if (in & PAD_B) out |= PAD_A;
        if (in & PAD_A) out |= PAD_B;
        if (in & PAD_X) out |= PAD_Y;
        if (in & PAD_Y) out |= PAD_X;
        if (l3) out |= PAD_B;
        if (r3) out |= PAD_Z;
    }
    prev_raw = p->button;
    p->button = (u16)out;
    p->triggerLeft = (out & PAD_L) ? 0xFF : 0;     /* the game also turns any analog L/R into L/R */
    p->triggerRight = (out & PAD_R) ? 0xFF : 0;
}
