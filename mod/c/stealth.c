/* Stealth: how close the Ganados notice Leon.
 *
 * em10FindCk (sight / hearing / proximity) and em10FindCk2 read their distances from their own
 * constant pool in the Ganado module (em10.drs, em11.drs... one REL each, all with the same
 * em10 code). The pool sits as one run of floats:
 *   +0x00 225e6 (sight^2, patrolling)  +0x04 36e6 (sight^2)  +0x08 60 deg cone
 *   +0x0C 25e6  footsteps^2 (5 m)      +0x10 12.25e6 always-noticed^2 (3.5 m, even from behind)
 *   +0x14 2000  +0x18 25000 (shots)    +0x1C 4e8
 *   +0x20 12.25e6 FindCk2 footsteps^2  +0x24 64e6 FindCk2 running footsteps^2
 * Loaded modules are found through the OS module list; the run is searched once per module and
 * then rewritten every frame from Leon's state: sight and shots stay as they are, footsteps and
 * the "always" radius shrink when he walks and more when he is crouched. Running = the game's.
 */
#include "game.h"
int CrouchActive(void);

#define MOD_HEAD (*(u8**)0x800030C8)          /* OSModuleInfo queue head */
static const f32 key[10] = { 225000000.0f, 36000000.0f, 1.0471976f, 25000000.0f, 12250000.0f,
                             2000.0f, 25000.0f, 400000000.0f, 12250000.0f, 64000000.0f };
#define NCACHE 8
static u8* c_mod[NCACHE];
static f32* c_pool[NCACHE];

static f32* FindPool(u8* m)
{
    u32 ns = *(u32*)(m + 0x0C), k;
    u32* sec = *(u32**)(m + 0x10);
    if (ns > 40 || (u32)sec < 0x80000000u || (u32)sec >= 0x81800000u) return 0;
    for (k = 0; k < ns; k++) {
        u32 a = sec[k * 2] & ~1u, n = sec[k * 2 + 1], i;
        if ((sec[k * 2] & 1) || !a || n < 40 || a < 0x80000000u || a + n > 0x81800000u) continue;
        for (i = 0; i + 40 <= n; i += 4) {
            f32* p = (f32*)(a + i);
            int j;
            for (j = 0; j < 10; j++) if (p[j] != key[j]) break;
            if (j == 10) return p;
        }
    }
    return 0;
}

void StealthKillFrame(void);
void StealthFrame(void)
{
    StealthKillFrame();
    u8* pl = pPL;
    u8* m;
    int i, n = 0;
    f32 prox, foot, foot2;
    int crouched = CrouchActive();
    if (!pl) return;
    if (pl[0xFD] == 3 && pl[0xFC] == 0) {                 /* running: the game's own */
        prox = 12250000.0f; foot = 25000000.0f; foot2 = 12250000.0f;
    } else if (CrouchActive()) {              /* crouched: silent, 0.8 m behind */
        prox = 640000.0f; foot = 0.0f; foot2 = 0.0f;   /* 0.8 m: the kill range is wider */
    } else {                                              /* walking / still / aiming: 2.5 m */
        prox = 6250000.0f; foot = 12250000.0f; foot2 = 6250000.0f;
    }
    for (m = MOD_HEAD; m && n < 64; m = *(u8**)(m + 4), n++) {
        f32* p = 0;
        if ((u32)m < 0x80000000u || (u32)m >= 0x81800000u) break;
        for (i = 0; i < NCACHE; i++) if (c_mod[i] == m) { p = c_pool[i]; break; }
        if (i == NCACHE) {                                /* new module: search once */
            int j, slot = 0;
            p = FindPool(m);
            for (j = 0; j < NCACHE; j++) if (!c_mod[j]) { slot = j; break; }
            if (j == NCACHE) slot = (int)((u32)m >> 4) % NCACHE;
            c_mod[slot] = m; c_pool[slot] = p;
        }
        if (!p) continue;
        if (p[0] != key[0] || p[2] != key[2] || p[9] != key[9] || (p[10] != 1000000.0f && p[10] != 360000.0f)) {   /* module memory reused */
            for (i = 0; i < NCACHE; i++) if (c_mod[i] == m) c_mod[i] = 0;
            continue;
        }
        p[3] = foot; p[4] = prox; p[8] = foot2;
        p[10] = crouched ? 360000.0f : 1000000.0f;     /* FindCk2: 'he is right here' (1 m) */
    }
}

/* ---- stealth kill -------------------------------------------------------------------------
 * Crouched, behind a Ganado (within KILL_R, more than ~120 deg off its facing): a Cross prompt
 * over its head (hud.c). Cross: Leon turns to it and does the game's own knife slash (the pad
 * presses knife, then fire), so the hit, the damage and the Ganado's reaction are the game's;
 * the Ganado is left with 1 HP so that slash kills it. Visually Leon stabs (crouch.c CR_STAB). */
#define KILL_R    1500.0f
#define KILL_N    48                    /* frames the sequence drives the pad */
#define EM_ALIVE  (*(u8**)((u8*)EmMgr + 0x10))
int CrouchActive(void);
static u8* target;
static int kill_k = -1;
typedef f32 (*Atan2F)(f32, f32);
#define atan2f_ ((Atan2F)0x8005FFE8)

static u8* FindTarget(u8* pl)
{
    u8* e;
    u8* best = 0;
    f32 bd = KILL_R * KILL_R;
    int n = 0;
    f32 px = *(f32*)(pl + 0x94), py = *(f32*)(pl + 0x98), pz = *(f32*)(pl + 0x9C);
    for (e = EM_ALIVE; e && n < 64; e = *(u8**)(e + 4), n++) {
        f32 dx, dy, dz, d2, fx, fz, l;
        if ((u32)e < 0x80000000u || (u32)e >= 0x81800000u) break;
        if (!(*(u32*)e & 1) || e[0x100] < 0x10 || e[0x100] > 0x20) continue;   /* Ganados only */
        if (*(s16*)(e + 0x320) <= 0) continue;
        dx = px - *(f32*)(e + 0x94); dy = py - *(f32*)(e + 0x98); dz = pz - *(f32*)(e + 0x9C);
        if (dy > 600.0f || dy < -600.0f) continue;
        d2 = dx * dx + dz * dz;
        if (d2 >= bd || d2 < 1.0f) continue;
        fx = *(f32*)(e + 0x0C + 0x08);         /* its facing: the model matrix's z column */
        fz = *(f32*)(e + 0x0C + 0x28);
        l = SQRTF(d2);
        if ((fx * dx + fz * dz) / l > -0.25f) continue;   /* Leon must be behind it (> ~105 deg) */
        best = e; bd = d2;
    }
    return best;
}

/* hud.c: where to draw the prompt (0 = none) */
u8* StealthTarget(void) { return kill_k < 0 ? target : 0; }
int StealthKilling(void) { return kill_k >= 0; }

void StealthKillFrame(void)
{
    u8* pl = pPL;
    if (kill_k >= 0) {
        if (++kill_k > KILL_N + 20 || !pl) kill_k = -1;
        target = 0;
        return;
    }
    target = 0;
    if (!pl || !modvars[VB_GAMEPLAY] || pl[0xFC] != 0 || pl[0xFD] > 2 || !CrouchActive()) return;
    target = FindTarget(pl);
}

/* pad.c: Cross pressed -> 1 if it started a kill (the press does not reach the game) */
int StealthPress(void)
{
    u8* pl = pPL;
    f32 dx, dz;
    if (kill_k >= 0 || !target || !pl) return 0;
    dx = *(f32*)(target + 0x94) - *(f32*)(pl + 0x94);
    dz = *(f32*)(target + 0x9C) - *(f32*)(pl + 0x9C);
    *(f32*)(pl + 0xA4) = atan2f_(dx, dz);       /* face it */
    *(s16*)(target + 0x320) = 1;                /* the slash finishes it */
    kill_k = 0;
    return 1;
}
/* pad.c, every gameplay frame: the knife press sequence while a kill runs */
u32 StealthPad(u32 out)
{
    if (kill_k < 0) return out;
    out &= ~(PAD_A | PAD_B | PAD_R | PAD_X | PAD_Y | PAD_MOD_CROUCH | PAD_MOD_RELOAD);
    if (kill_k < KILL_N) out |= PAD_L;                       /* knife stance */
    if ((kill_k >= 12 && kill_k < 16) || (kill_k >= 22 && kill_k < 26)) out |= PAD_A;   /* slash */
    return out;
}
