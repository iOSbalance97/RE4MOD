/* C0-01: Chapter 0 "Hace 11 horas" - Ashley escapes through the village at night (first test build).
 *  - New game: Leon's intro (r120, the police car) jumps to the village road (SceAtExecRoomJump 0x100,
 *    PAL 0x80152E28). That jump is redirected: PlSelect(1) (PAL 0x80143984, Ashley) and the room becomes
 *    the village at night (r111, same map and coordinates as the daytime r101), at the spot where the
 *    game puts you when you come in from the road (r100's door: -52144, 91, 22524, 2.122).
 *  - r111's own Ganados (emleon01.esl, id 0x17) are taken out of the list just before the room creates
 *    its enemies (EmSetFromList, PAL 0x800CB20C) and the guards of the user's map are put in: same id,
 *    all carrying torches (cEm flag 0x00020000 -> Wep_type 9).
 *  - Black screen, "Hace 11 horas", fade in, Ashley takes four steps, stops, looks left and right,
 *    "Tengo que salir de aqui." and then the player has her.
 *  - Test: Ashley's position at the top left; reaching the symbol door (door B, r101 area 25, to the
 *    farm) ends the chapter for now: PlSelect(0) and the original jump to r100 with Leon.
 * Map -> world: fitted on the doors of r101 (AEV) against the user's map (tools in the C0 notes). */
#include "game.h"

#define STAGE G8(0x4FA8)
#define ROOM  G8(0x4FA9)
#define PLTYPE G8(0x4FC4)
#define EMLIST_NO (*(s8*)(pG + 0x4FAF))
#define EMLIST(i) (pG + 0x52F4 + (i) * 32)
#define PL_SELECT ((void (*)(int))0x80143984)
#define ROOM_JUMP ((void (*)(u32, Vec*, Vec*, int))0x80152E28)

static int on, done, ph, t, ready, endt;
static Vec lpos, lrot; static int larg;              /* the intro's own jump (Leon, r100) */
static Vec apos = { -52144.0f, 91.0f, 22524.0f }, arot = { 0.0f, 2.122f, 0.0f };
int ch0_padlock;                                     /* pad.c: no input; ch0_stick: forced stick */
s8 ch0_sx, ch0_sy;
int ch0_stick;

static void Hud(int sw)
{
    ((void (*)(void*, int))0x800C0518)((void*)0x8027E4A8, sw);
    ((void (*)(void*, int, int))0x8011C3CC)((void*)0x8028481C, 33, sw);
}

/* hook at SceAtExecRoomJump's entry: a[0] room, a[1] pos, a[2] rot, a[3] arg (written back) */
void Ch0Jump(u32* a)
{
    if (done || on || !pG) return;
    if (a[0] != 0x100 || STAGE != 1 || ROOM != 0x20) return;      /* only the intro's jump */
    lpos = *(Vec*)a[1]; lrot = *(Vec*)a[2]; larg = (int)a[3];
    PL_SELECT(1);
    a[0] = 0x111; a[1] = (u32)&apos; a[2] = (u32)&arot;
    on = 1; ph = 0; t = 0; ready = 0; endt = 0;
}

/* the guards (user's map, snapped to the ground, 0.9 m clear of walls): pos (mm), facing (s16, pi/0x4000), type */
static const s16 GU[][5] = {
    { -27951, 0,   9471,   8407,  0 },   /* road, just past the start */
    { -15795, 0,  -6400,  -9054,  1 },   /* centre-west, by the north houses */
    { -12682, 0,   -991,    871,  3 },
    {  -6256, 0,   2108,  -6446, 12 },   /* square (bonfire group) */
    {    667, 0,    836,  10816,  0 },
    {   -277, 0,   4850,   -136,  1 },
    {   2516, 0,   3331,   5419,  3 },
    { -13171, 0,  17250,   -136, 12 },   /* south alley / stable */
    { -10660, 0,  22230, -13690,  0 },
    { -13795, 0,  27131,   -136,  1 },
    {  16956, 0, -17604,  -6931,  3 },   /* north-east road */
};
#define NGU (int)(sizeof(GU) / sizeof(GU[0]))

/* hook at EmSetFromList's entry: r111's list -> our guards */
void Ch0EmList(void)
{
    int i, k = 0;
    if (!on || !pG || STAGE != 1 || ROOM != 0x11) return;
    for (i = 0; i < 256; i++) {
        u8* e = EMLIST(i);
        if (*(u16*)(e + 0x18) == 0x111 && e[1] == 0x17) { e[0] = 0; e[1] = 0; }
    }
    for (i = 0; i < 256 && k < NGU; i++) {
        u8* e = EMLIST(i);
        if (e[1] != 0 || e[0] != 0) continue;
        memclr_asm(e, 32);
        e[0] = 1; e[1] = 0x17; e[2] = (u8)GU[k][4];
        *(u32*)(e + 4) = 0x00020000u;                     /* torch; no bit 8 (that one keeps them turned to the player) */
        *(u16*)(e + 8) = 1000;
        *(s16*)(e + 0x0C) = GU[k][0] / 10; *(s16*)(e + 0x0E) = GU[k][1] / 10; *(s16*)(e + 0x10) = GU[k][2] / 10;
        *(s16*)(e + 0x14) = GU[k][3];
        *(u16*)(e + 0x18) = 0x111;
        *(s16*)(e + 0x1A) = 10;
        k++;
    }
}

static int Ashley(void) { return pPL && PLTYPE == 1 && STAGE == 1 && ROOM == 0x11; }

/* intro timeline, in main-loop frames */
#define T_TXT_IN   40
#define T_TXT_FULL 70
#define T_TXT_OUT  160
#define T_TXT_GONE 190
#define T_FADE_IN  215
#define T_LIT      265
#define T_WALK     280
#define T_STOP     (T_WALK + 44)
#define T_LOOK_END (T_STOP + 70)
#define T_SAY      (T_LOOK_END + 10)
#define T_FREE     (T_SAY + 85)

void Ch0Frame(void)
{
    if (!on || !pG) { ch0_padlock = 0; ch0_stick = 0; return; }
    if (!ready) {                                    /* still loading: keep it black and still */
        ch0_padlock = 1; ch0_stick = 0;
        if (Ashley()) { ready = 1; t = 0; Hud(0); }
        return;
    }
    if (!Ashley()) return;                           /* menus, death screen... */
    t++;
    if (ph == 0) {
        ch0_padlock = 1; ch0_stick = 0;
        if (t >= T_WALK && t < T_STOP) { ch0_stick = 1; ch0_sx = 0; ch0_sy = 56; }     /* four steps */
        else if (t >= T_STOP + 12 && t < T_STOP + 26) { ch0_stick = 1; ch0_sx = -60; ch0_sy = 0; } /* looks left */
        else if (t >= T_STOP + 34 && t < T_STOP + 58) { ch0_stick = 1; ch0_sx = 60; ch0_sy = 0; }  /* and right */
        else if (t >= T_STOP + 62 && t < T_STOP + 70) { ch0_stick = 1; ch0_sx = -60; ch0_sy = 0; } /* back */
        if (t >= T_FREE) { ph = 1; ch0_padlock = 0; ch0_stick = 0; Hud(1); }
        return;
    }
    if (ph == 1) {                                   /* playing: door B ends the test chapter */
        f32 dx = *(f32*)(pPL + 0x94) - 19713.0f, dz = *(f32*)(pPL + 0x9C) - 2003.0f;
        if (dx * dx + dz * dz < 1600.0f * 1600.0f) { ph = 2; endt = 0; ch0_padlock = 1; Hud(0); }
        return;
    }
    if (ph == 2) {
        endt++;
        if (endt == 150) {
            done = 1; on = 0; ch0_padlock = 0;
            PL_SELECT(0);
            EMLIST_NO = -1;                          /* r100 reads Leon's list again */
            ROOM_JUMP(0x100, &lpos, &lrot, larg);
        }
    }
}

/* drawing (hud.c): black overlay alpha, text alphas, test numbers */
static int Ramp(int a, int b, int x) { if (x <= a) return 0; if (x >= b) return 255; return (x - a) * 255 / (b - a); }
int Ch0Black(void)
{
    if (!on) return 0;
    if (!ready) return 255;
    if (ph == 0) return 255 - Ramp(T_FADE_IN, T_LIT, t);
    if (ph == 2) return Ramp(0, 40, endt);
    return 0;
}
int Ch0Text(int k)                                    /* 0 "Hace 11 horas", 1 Ashley's line, 2 end */
{
    if (!on || !ready) return 0;
    if (k == 0 && ph == 0) { if (t < T_TXT_FULL) return Ramp(T_TXT_IN, T_TXT_FULL, t); return 255 - Ramp(T_TXT_OUT, T_TXT_GONE, t); }
    if (k == 1 && ph == 0) { if (t < T_SAY + 15) return Ramp(T_SAY, T_SAY + 15, t); return 255 - Ramp(T_FREE - 15, T_FREE, t); }
    if (k == 2 && ph == 2) return Ramp(45, 70, endt);
    return 0;
}
int Ch0Coords(int i)                                  /* test: Ashley x, y, z; -999999 = off */
{
    if (!on || !ready || ph != 1 || !Ashley()) return -999999;
    return (int)*(f32*)(pPL + 0x94 + 4 * i);
}
