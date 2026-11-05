/* Legs while moving and aiming (remake style).
 *
 * Moving while aiming is our addition (m15.s slides Leon by the stick), the game has no leg motion
 * for it: the aim motion keeps the feet planted by IK and Leon glides. Here a second motion with
 * only the pelvis and the legs (Mixamo pistol walk / back / strafe, retargeted, FK) is laid over
 * the aim motion through cModel::pMotionB (the slot the neck turn uses; aiming clears the neck):
 * MotionMove evaluates it after the aim motion and matBlend takes its parts at Brate 1. The aim
 * motion's leg IK chains are switched off meanwhile (parts flag 0x80) so they do not pull the feet
 * back. The walk phase follows the distance Leon really moves, so the feet do not slide.
 * Runs once a frame from ModFrame (after the game update), for the next frame. */
#include "game.h"

extern unsigned char leg_fwd[], leg_back[], leg_left[], leg_right[], leg_crouch[];
extern const short leg_cycle[5][2];
static unsigned char* const leg_mot[5] = { leg_fwd, leg_back, leg_left, leg_right, leg_crouch };
#define JOY_X (*(s8*)0x8028D0D0)                     /* Joy[0] stick */
#define JOY_Y (*(s8*)0x8028D0D1)
#define CROUCH_FWD  20.0f                            /* mm per frame at full stick */
#define CROUCH_BACK 14.0f

static u32 leg_work[0xD0 / 4];               /* MOTION_INFO */
static int leg_clip = -1, leg_on, still, have_last;
static f32 phase, last_x, last_z;

/* sine / cosine for the facing angle (-PI..PI after wrapping), 7th order: plenty for picking a clip */
static f32 Sin(f32 a)
{
    const f32 PI = 3.14159265f;
    f32 a2;
    while (a > PI) a -= 2.0f * PI;
    while (a < -PI) a += 2.0f * PI;
    if (a > PI * 0.5f) a = PI - a;
    else if (a < -PI * 0.5f) a = -PI - a;
    a2 = a * a;
    return a * (1.0f - a2 / 6.0f * (1.0f - a2 / 20.0f * (1.0f - a2 / 42.0f)));
}
static f32 Cos(f32 a) { return Sin(a + 1.57079633f); }

#define MI(o, t)     (*(t*)((u8*)leg_work + (o)))
#define PL_F(pl, o)  (*(f32*)((pl) + (o)))

static void LegIK(u8* pl, int off)
{
    static const int roots[2] = { 18, 22 };
    int i;
    for (i = 0; i < 2; i++) {
        u8* p = (u8*)getPartsPtr(pl, roots[i]);
        if (!p) continue;
        if (off) *(u32*)(p + 0x1C0) |= 0x80;     /* InverseKinematics skips the chain */
        else *(u32*)(p + 0x1C0) &= ~0x80u;
    }
}

static void LegsOff(u8* pl)
{
    if (!leg_on) return;
    leg_on = 0;
    leg_clip = -1;
    if (*(void**)(pl + 0x2A8) == leg_work) *(void**)(pl + 0x2A8) = 0;
    *(u32*)(pl + 0x1D8 + 0x44) &= ~0x20000000u;  /* Motion: no longer keep the blend */
    LegIK(pl, 0);
}

static void LegsSet(u8* pl, int clip)
{
    if (clip != leg_clip) {
        f32 frac = leg_clip >= 0 ? phase / (f32)leg_cycle[leg_clip][0] : 0.0f;
        MI(0x44, u32) |= 0x30000000;             /* no IKInit (the base chains stay), keep blend */
        MotionSetCore(pl, leg_work, leg_mot[clip], 0, 0, 5, 0);
        MI(0x44, u32) &= ~0x10000000u;
        leg_clip = clip;
        phase = frac * (f32)leg_cycle[clip][0];
    }
    if (!leg_on) {
        leg_on = 1;
        *(u32*)(pl + 0x1D8 + 0x44) |= 0x20000000;   /* Motion: MotionSetCore keeps pMotionB */
    }
    *(void**)(pl + 0x2A8) = leg_work;
    MI(0xC8, f32) = 1.0f;                        /* Brate */
    LegIK(pl, 1);
}

static void LegsPhase(f32 dist)
{
    int n = leg_cycle[leg_clip][0];
    phase += dist * (f32)n / (f32)leg_cycle[leg_clip][1];
    while (phase >= (f32)n) phase -= (f32)n;
    while (phase < 0.0f) phase += (f32)n;
    MI(0xB8, f32) = phase;                       /* Seq_frame */
    MI(0xAC, u16) = (u16)(phase * 64.0f);        /* Seq.Frame (10.6) */
    MI(0x24, f32) = phase;                       /* Mot_frame */
}

/* Crouched (the game's cover routine, step 0xA): stick forward / back walks crouched, the side keys
   keep turning as the game does. Facing = model yaw + part 0 yaw (the routine turns both). */
static int CrouchWalk(u8* pl)
{
    u8* p0;
    f32 y, a, sp;
    if (pl[0xFC] != 0 || pl[0xFD] != 0x11 || pl[0xFE] != 0xA || !modvars[VB_GAMEPLAY]) return 0;
    y = (f32)JOY_Y;
    if (y > -12.0f && y < 12.0f) { if (++still >= 2) LegsOff(pl); return 1; }
    still = 0;
    if (y > 72.0f) y = 72.0f;
    if (y < -72.0f) y = -72.0f;
    sp = y > 0 ? y / 72.0f * CROUCH_FWD : y / 72.0f * CROUCH_BACK;
    p0 = (u8*)getPartsPtr(pl, 0);
    a = PL_F(pl, 0xA4) + (p0 ? PL_F(p0, 0xA4) : 0.0f);
    PL_F(pl, 0x94) += Sin(a) * sp;
    PL_F(pl, 0x9C) += Cos(a) * sp;
    last_x = PL_F(pl, 0x94); last_z = PL_F(pl, 0x9C);
    LegsSet(pl, 4);
    LegsPhase(sp);                               /* backwards: the cycle runs in reverse */
    return 1;
}

void LegsFrame(void)
{
    u8* pl = pPL;
    f32 x, z, dx, dz, dist, s, c, lx, lz;
    int clip, aiming;
    if (!pl) { have_last = 0; leg_on = 0; return; }
    if (CrouchWalk(pl)) return;
    x = PL_F(pl, 0x94); z = PL_F(pl, 0x9C);
    dx = x - last_x; dz = z - last_z;
    last_x = x; last_z = z;
    if (!have_last) { have_last = 1; dx = dz = 0.0f; }
    dist = SQRTF(dx * dx + dz * dz);
    if (dist > 200.0f) dist = 0.0f;              /* warp (room change, event) */
    aiming = pl[0xFC] == 0 && pl[0xFD] == 6 && !(*(u32*)(pl + 0x420) & 0x40)   /* not crouched */
             && modvars[VB_GAMEPLAY];
    if (!aiming) { LegsOff(pl); return; }
    if (dist < 2.0f) {
        if (++still >= 3) LegsOff(pl);
        if (!leg_on) return;
    } else still = 0;
    /* direction in Leon's frame (ang.y at 0xA4; forward = +z) */
    s = Sin(PL_F(pl, 0xA4)); c = Cos(PL_F(pl, 0xA4));
    lx = dx * c - dz * s;
    lz = dx * s + dz * c;
    if (dist < 2.0f) clip = leg_clip;
    else if (lz >= (lx < 0 ? -lx : lx)) clip = 0;
    else if (-lz >= (lx < 0 ? -lx : lx)) clip = 1;
    else clip = lx > 0 ? 2 : 3;                   /* +x = Leon's left */
    if (clip < 0 || clip > 3) return;
    LegsSet(pl, clip);
    LegsPhase(dist);
}

/* ---- Crouch on Circle: the game's own cover crouch (pl_R1_Crouch, routine 0x11: crouch, look
   around, aim from it). Circle crouches when Leon stands / walks / runs; Circle again stands him up
   through the routine's own A/B check (one B press is fed to the pad). */
static int crouch_req;
int crouch_stand;                                /* pad.c: feed one B */
void CrouchPress(void) { crouch_req = 1; }
void CrouchFrame(void)
{
    u8* pl = pPL;
    int req = crouch_req;
    crouch_req = 0;
    if (!req || !pl || !modvars[VB_GAMEPLAY] || pl[0xFC] != 0) return;
    if (pl[0xFD] <= 3) {                         /* footwork / walk / back / run */
        pl[0xFD] = 0x11; pl[0xFE] = 0; pl[0xFF] = 0;
    } else if (pl[0xFD] == 0x11 && pl[0xFE] >= 0xA && pl[0xFE] <= 0x13) {
        crouch_stand = 2;
    }
}
