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

void StealthFrame(void)
{
    u8* pl = pPL;
    u8* m;
    int i, n = 0;
    f32 prox, foot, foot2;
    if (!pl) return;
    if (pl[0xFD] == 3 && pl[0xFC] == 0) {                 /* running: the game's own */
        prox = 12250000.0f; foot = 25000000.0f; foot2 = 12250000.0f;
    } else if (CrouchActive()) {              /* crouched: silent, 1.5 m behind */
        prox = 2250000.0f; foot = 0.0f; foot2 = 0.0f;
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
        if (p[0] != key[0] || p[2] != key[2] || p[9] != key[9]) {   /* module memory reused */
            for (i = 0; i < NCACHE; i++) if (c_mod[i] == m) c_mod[i] = 0;
            continue;
        }
        p[3] = foot; p[4] = prox; p[8] = foot2;
    }
}
