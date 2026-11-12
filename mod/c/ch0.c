/* Chapter 0 "Hace 11 horas" - Ashley escapes through the village at night.
 * C0-01: the intro's jump (SceAtExecRoomJump 0x100 from r120, PAL 0x80152E28) becomes PlSelect(1)
 *   (PAL 0x80143984) + the village at night (r111 = r101's map and coordinates) at the road entrance
 *   (r100's door: -52144, 91, 22524, 2.122). r111's own Ganados (emleon01, id 0x17) are swapped for the
 *   guards of the user's map just before the room creates its enemies (EmSetFromList, PAL 0x800CB20C),
 *   all with torches (list flag 0x00020000 -> Wep_type 9). Black screen, "Hace 11 horas", four steps,
 *   a look around, "Tengo que salir de aqui." Test: coordinates; door B ends the chapter.
 * C0-02 (the user's C0-01 video: the whole route works; the window jump of the house is the game's own):
 *   - the guards stand guard (Ganado routine 1/1 Keeper, without Be_flg 0x100): they look where the map
 *     says and only the game's own find check (60 deg cone, footsteps, very near) starts a chase; when
 *     the game sends one back to Wait it is made a Keeper again where it is.
 *   - the room's doors are off for the whole chapter; door B (to the farm, centre 19713, 2003) the first
 *     time: "Esta cerrada. / Tiene que haber una llave en algun sitio."
 *   - the key on the bed upstairs in house C (user's video: Ashley at the bed 2329, 3199, -9063): the
 *     bed's own "check" area is off; our prompt (Cross) takes the key -> "Has cogido la llave."
 *   - then a short scene: the door downstairs is kicked in, a Ganado with a torch comes in (EmSetEvent,
 *     PAL 0x800CB76C) and comes up for her; out through the window (the game's own jump).
 *   - with the key, door B: "La puerta se abre." -> end of Part 1 (test: back to Leon as in C0-01).
 *   - caught: a Ganado knocks her down (player routine 1) -> "Ashley ha sido capturada" and the room
 *     again from the last checkpoint (start / the bed). */
#include "game.h"

#define STAGE G8(0x4FA8)
#define ROOM  G8(0x4FA9)
#define PLTYPE G8(0x4FC4)
#define PL_LIFE (*(s16*)(pG + 0x4FB0))
#define PL_LIFE_MAX (*(s16*)(pG + 0x4FB2))
#define EMLIST_NO (*(s8*)(pG + 0x4FAF))
#define EMLIST(i) (pG + 0x52F4 + (i) * 32)
#define STOPF   (*(u32*)(pG + 0x170))
#define SPF_CAM 0x40000000u
#define CAMP    ((f32*)(pG + 0x74 + 0xA4))
#define EMMGR ((void*)0x80283160)
#define PL_SELECT ((void (*)(int))0x80143984)
#define ROOM_JUMP ((void (*)(u32, Vec*, Vec*, int))0x80152E28)
#define EM_SET_EVENT ((u8* (*)(u8*))0x800CB76C)
extern u16 barn_pad;                                 /* pad.c: this frame's remapped buttons */

static int on, done, ph, t, ready, endt, scene;
static int key, b_seen, msg, msg_t, caught, cap_t, cp;      /* cp: checkpoint 0 start, 1 the bed */
static Vec lpos, lrot; static int larg;              /* the intro's own jump (Leon, r100) */
static Vec apos = { -52144.0f, 91.0f, 22524.0f }, arot = { 0.0f, 2.122f, 0.0f };
static Vec kpos = { 2100.0f, 3199.0f, -9500.0f }, krot = { 0.0f, 0.0f, 0.0f };
static u8 gidx[16]; static int ngidx;                /* our list entries (guards) */
static u8* hman;                                     /* the Ganado of the house scene */
static int hman_t;
static u16 pad_old;
int ch0_padlock;                                     /* pad.c: no input; ch0_stick: forced stick */
s8 ch0_sx, ch0_sy;
int ch0_stick;

#define BX 19713.0f                                  /* door B */
#define BZ 2003.0f
#define KX 2329.0f                                   /* the bed */
#define KY 3199.0f
#define KZ (-9063.0f)
#define DOOR_OUT_X 7169.0f                           /* house C's door, outside / inside (user's video) */
#define DOOR_OUT_Z (-5545.0f)
#define DOOR_IN_X 7309.0f
#define DOOR_IN_Z (-6724.0f)

static void Hud(int sw)
{
    ((void (*)(void*, int))0x800C0518)((void*)0x8027E4A8, sw);
    ((void (*)(void*, int, int))0x8011C3CC)((void*)0x8028481C, 33, sw);
}
static f32 Sq(f32 x) { f32 r = x > 1.0f ? x : 1.0f; int i; if (x <= 0.0f) return 0.0f; for (i = 0; i < 14; i++) r = 0.5f * (r + x / r); return r; }
static f32 PX(void) { return *(f32*)(pPL + 0x94); }
static f32 PY(void) { return *(f32*)(pPL + 0x98); }
static f32 PZ(void) { return *(f32*)(pPL + 0x9C); }
static f32 D2(f32 x, f32 z) { return (PX() - x) * (PX() - x) + (PZ() - z) * (PZ() - z); }

/* hook at SceAtExecRoomJump's entry: a[0] room, a[1] pos, a[2] rot, a[3] arg (written back) */
void Ch0Jump(u32* a)
{
    if (done || on || !pG) return;
    if (a[0] != 0x100 || STAGE != 1 || ROOM != 0x20) return;      /* only the intro's jump */
    lpos = *(Vec*)a[1]; lrot = *(Vec*)a[2]; larg = (int)a[3];
    PL_SELECT(1);
    a[0] = 0x111; a[1] = (u32)&apos; a[2] = (u32)&arot;
    on = 1; ph = 0; t = 0; ready = 0; endt = 0; key = 0; b_seen = 0; cp = 0; caught = 0; scene = 0; msg = 0;
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
    ngidx = 0;
    for (i = 0; i < 256 && k < NGU; i++) {
        u8* e = EMLIST(i);
        if (e[1] != 0 || e[0] != 0) continue;
        memclr_asm(e, 32);
        e[0] = 1; e[1] = 0x17; e[2] = (u8)GU[k][4];
        *(u32*)(e + 4) = 0x00020000u;                /* torch; no bit 8 (that one keeps them turned to the player) */
        *(u16*)(e + 8) = 1000;
        *(s16*)(e + 0x0C) = GU[k][0] / 10; *(s16*)(e + 0x0E) = GU[k][1] / 10; *(s16*)(e + 0x10) = GU[k][2] / 10;
        *(s16*)(e + 0x14) = GU[k][3];
        *(u16*)(e + 0x18) = 0x111;
        *(s16*)(e + 0x1A) = 10;
        gidx[ngidx++] = (u8)i;
        k++;
    }
    hman = 0;
}

static int Ashley(void) { return pPL && PLTYPE == 1 && STAGE == 1 && ROOM == 0x11; }
static int Alive(u8* e) { return e && (u32)e >= 0x80000000u && (u32)e < 0x81800000u && (*(u32*)e & 0x201) == 1; }

static u8* EmFind(int no)                            /* the live work made from list entry `no` */
{
    u32 n = *(u32*)((u8*)EMMGR + 4), i, sz = *(u32*)((u8*)EMMGR + 8);
    u8* base = *(u8**)EMMGR;
    if ((u32)base < 0x80000000u || (u32)base >= 0x81800000u || n > 1024 || sz < 0xC00 || sz > 0x40000) return 0;
    for (i = 0; i < n; i++) {
        u8* e = base + i * sz;
        if ((*(u32*)e & 0x201) == 1 && e[0x398] == (u8)no) return e;
    }
    return 0;
}

/* the guards stand guard: Wait (1/0) -> Keeper (1/1); a chase is the game's own (Find...) */
static void Guards(void)
{
    int k;
    for (k = 0; k < ngidx; k++) {
        u8* e = EmFind(gidx[k]);
        if (!e || e[0xFC] != 1 || e[0xFD] != 0) continue;
        e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0;
        *(u32*)(e + 0x3E0) &= ~0x100u;               /* Keeper with 0x100 turns to the player and walks */
    }
}

/* SceAt areas (pS->ot): doors off for the chapter; the bed's own check off until the key is taken */
static u8* OtNext(u8* p)
{
    u32 v;
    while ((v = *(u32*)p) != 0xFFFFFFFFu) {
        p = (u8*)(v | 0x80000000u);
        if ((s32)v < 0) return p;
    }
    return 0;
}
static void Areas(void)
{
    u8* p; int n = 0;
    if (!pS) return;
    for (p = OtNext(pS + 140); p && n < 400; p = OtNext(p), n++) {
        f32* q = (f32*)(p + 0x14); f32 cx, cz; u8 at = p[0x4A];
        if (p[0x35] == 1) { p[0x34] &= ~1; continue; }                     /* doors */
        if (key || p[0x35] == 0x10 || at == 2 || at == 4 || at == 5 || at == 26) continue;
        if (*(f32*)(p + 0x08) < 2500.0f) continue;                          /* upstairs only */
        if (p[0x05] == 1) { cx = (q[0] + q[2] + q[4] + q[6]) * 0.25f; cz = (q[1] + q[3] + q[5] + q[7]) * 0.25f; }
        else { cx = q[0]; cz = q[1]; }
        if ((cx - KX) * (cx - KX) + (cz - KZ) * (cz - KZ) < 1800.0f * 1800.0f) p[0x34] &= ~1;   /* the bed's "check" */
    }
}

static void Cam(f32 cx, f32 cy, f32 cz, f32 tx, f32 ty, f32 tz, f32 fovy)
{
    CAMP[0] = cx; CAMP[1] = cy; CAMP[2] = cz; CAMP[3] = tx; CAMP[4] = ty; CAMP[5] = tz; CAMP[6] = 0.0f; CAMP[7] = fovy;
    CAMP[8] = 0.0f; CAMP[9] = 1.0f; CAMP[10] = 0.0f;
    {   /* barn.c B100: pG->Camera.mat (cull frustum) rebuilt from the scene camera */
        f32* m = (f32*)(pG + 0x74);
        f32 lx = cx - tx, ly = cy - ty, lz = cz - tz, rx, rz, ux, uy, uz, n;
        n = Sq(lx * lx + ly * ly + lz * lz); if (n < 1.0f) n = 1.0f; lx /= n; ly /= n; lz /= n;
        rx = lz; rz = -lx;
        n = Sq(rx * rx + rz * rz); if (n < 1e-4f) { rx = 1.0f; rz = 0.0f; n = 1.0f; }
        rx /= n; rz /= n;
        ux = ly * rz; uy = lz * rx - lx * rz; uz = -ly * rx;
        m[0] = rx; m[1] = ux; m[2] = lx; m[3] = cx;
        m[4] = 0.0f; m[5] = uy; m[6] = ly; m[7] = cy;
        m[8] = rz; m[9] = uz; m[10] = lz; m[11] = cz;
        m = (f32*)(pG + 0x74 + 0xC4);
        m[0] = ux; m[1] = uy; m[2] = uz; m[3] = lx; m[4] = ly; m[5] = lz; m[6] = rx; m[7] = 0.0f; m[8] = rz;
    }
}

static u8 hrec[32] __attribute__((aligned(4)));
static u8* HouseGanado(f32 x, f32 z, f32 ang)        /* a torch Ganado (EmSetEvent), born without bit 1 */
{
    u8* e;
    memclr_asm(hrec, 32);
    hrec[0] = 1; hrec[1] = 0x17; hrec[2] = 0;
    *(u32*)(hrec + 4) = 0x00020000u;
    *(u16*)(hrec + 8) = 1000;
    *(s16*)(hrec + 0x0C) = (s16)(x / 10.0f); *(s16*)(hrec + 0x10) = (s16)(z / 10.0f);
    *(s16*)(hrec + 0x14) = (s16)(ang * 16384.0f / 3.14159265f);
    *(u16*)(hrec + 0x18) = 0x111; *(s16*)(hrec + 0x1A) = 30;
    e = EM_SET_EVENT(hrec);
    if (!Alive(e)) return 0;
    hman_t = 0;
    return e;
}

static void Msg(int m) { msg = m; msg_t = 0; }       /* texts: 1 locked, 2 key, 3 opens */

static void Restart(void)                            /* caught: the room again from the checkpoint */
{
    PL_LIFE = PL_LIFE_MAX;
    ready = 0; scene = 0; caught = 0; ch0_padlock = 1; msg = 0;
    ROOM_JUMP(0x111, cp ? &kpos : &apos, cp ? &krot : &arot, 0);
}

/* intro timeline, in main-loop frames */
#define T_TXT_IN   40
#define T_TXT_FULL 70
#define T_TXT_OUT  160
#define T_TXT_GONE 190
#define T_FADE_IN  215
#define T_LIT      265
#define T_WALK     280
#define T_STOP     (T_WALK + 44)
#define T_SAY      (T_STOP + 80)
#define T_FREE     (T_SAY + 85)
#define S_LEN      150                               /* the house scene */

void Ch0Frame(void)
{
    u16 pad, trg;
    if (!on || !pG) { ch0_padlock = 0; ch0_stick = 0; return; }
    pad = barn_pad; trg = pad & ~pad_old; pad_old = pad;
    if (!ready) {                                    /* still loading: keep it black and still */
        ch0_padlock = 1; ch0_stick = 0;
        if (Ashley()) {
            ready = 1; t = 0;
            if (ph == 0) Hud(0); else { ch0_padlock = 0; Hud(1); }
            if (ph == 1 && cp == 1) hman = HouseGanado(DOOR_IN_X, DOOR_IN_Z - 900.0f, 3.02f);
        }
        return;
    }
    if (!Ashley()) return;                           /* menus, death screen... */
    t++;
    if (msg) msg_t++;
    if (msg && msg != 3 && msg_t > 150) msg = 0;
    Areas();
    Guards();
    if (Alive(hman)) {                               /* born without bit 1 (else it stays hidden, barn.c B94) */
        hman_t++;
        if (hman_t == 6) *(u32*)(hman + 0x3C8) |= 1u;
    }
    if (ph == 0) {
        ch0_padlock = 1; ch0_stick = 0;
        if (t >= T_WALK && t < T_STOP) { ch0_stick = 1; ch0_sx = 0; ch0_sy = 56; }     /* four steps */
        else if (t >= T_STOP + 12 && t < T_STOP + 26) { ch0_stick = 1; ch0_sx = -60; ch0_sy = 0; } /* looks left */
        else if (t >= T_STOP + 34 && t < T_STOP + 58) { ch0_stick = 1; ch0_sx = 60; ch0_sy = 0; }  /* and right */
        else if (t >= T_STOP + 62 && t < T_STOP + 70) { ch0_stick = 1; ch0_sx = -60; ch0_sy = 0; } /* back */
        if (t >= T_FREE) { ph = 1; ch0_padlock = 0; ch0_stick = 0; Hud(1); }
        return;
    }
    if (ph == 1) {
        if (caught) {                                /* knocked down: fade, text, again */
            cap_t++;
            ch0_padlock = 1;
            if (cap_t == 170) Restart();
            return;
        }
        if (pPL[0xFC] == 1 && !scene) { caught = 1; cap_t = 0; msg = 0; Hud(0); return; }
        if (scene) {                                 /* the Ganado comes in downstairs */
            scene++;
            ch0_padlock = 1;
            STOPF |= SPF_CAM;
            if (scene == 20) SndCall(1, 0x1E, 0, 0, 0, 0);                  /* the door kicked in */
            if (scene == 26) hman = HouseGanado(DOOR_OUT_X, DOOR_OUT_Z, 3.02f);
            Cam(5644.0f, 1500.0f, -9300.0f, DOOR_IN_X, 900.0f, DOOR_IN_Z, 50.0f);
            if (scene >= S_LEN) { scene = 0; STOPF &= ~SPF_CAM; ch0_padlock = 0; Hud(1); }
            return;
        }
        if (!key) {
            f32 dy = PY() - KY;
            if (D2(KX, KZ) < 1300.0f * 1300.0f && dy > -500.0f && dy < 500.0f && (trg & PAD_A)) {
                key = 1; cp = 1; Msg(2); scene = 1; Hud(0);
                return;
            }
        }
        if (D2(BX, BZ) < 1800.0f * 1800.0f) {
            if (!key) { if (!b_seen) { b_seen = 1; Msg(1); } }
            else { ph = 2; endt = 0; ch0_padlock = 1; Hud(0); Msg(3); }
        } else if (D2(BX, BZ) > 4000.0f * 4000.0f) b_seen = 0;
        return;
    }
    if (ph == 2) {
        endt++;
        ch0_padlock = 1;
        if (endt == 170) {
            done = 1; on = 0; ch0_padlock = 0; msg = 0;
            PL_SELECT(0);
            EMLIST_NO = -1;                          /* r100 reads Leon's list again */
            ROOM_JUMP(0x100, &lpos, &lrot, larg);
        }
    }
}

/* drawing (hud.c) */
static int Ramp(int a, int b, int x) { if (x <= a) return 0; if (x >= b) return 255; return (x - a) * 255 / (b - a); }
int Ch0Black(void)
{
    if (!on) return 0;
    if (!ready) return 255;
    if (ph == 0) return 255 - Ramp(T_FADE_IN, T_LIT, t);
    if (ph == 1 && caught) return Ramp(40, 90, cap_t);
    if (ph == 2) return Ramp(60, 100, endt);
    return 0;
}
/* line k: 0 "Hace 11 horas", 1 Ashley's line, 2 locked (two lines), 3 key prompt, 4 key taken,
 * 5 the door opens, 6 caught, 7 end of Part 1; returns its alpha */
int Ch0Text(int k)
{
    if (!on || !ready) return 0;
    if (ph == 0) {
        if (k == 0) { if (t < T_TXT_FULL) return Ramp(T_TXT_IN, T_TXT_FULL, t); return 255 - Ramp(T_TXT_OUT, T_TXT_GONE, t); }
        if (k == 1) { if (t < T_SAY + 15) return Ramp(T_SAY, T_SAY + 15, t); return 255 - Ramp(T_FREE - 15, T_FREE, t); }
        return 0;
    }
    if (k == 3) {
        f32 dy;
        if (key || scene || caught || ph != 1 || !Ashley()) return 0;
        dy = PY() - KY;
        return D2(KX, KZ) < 1300.0f * 1300.0f && dy > -500.0f && dy < 500.0f ? 255 : 0;
    }
    if (k == 2 && msg == 1) return msg_t < 120 ? Ramp(0, 10, msg_t) : 255 - Ramp(120, 150, msg_t);
    if (k == 4 && msg == 2) return msg_t < 120 ? Ramp(0, 10, msg_t) : 255 - Ramp(120, 150, msg_t);
    if (k == 5 && msg == 3) return 255 - Ramp(50, 70, msg_t);
    if (k == 6 && caught) return Ramp(70, 90, cap_t);
    if (k == 7 && ph == 2) return Ramp(100, 120, endt);
    return 0;
}
int Ch0Coords(int i)                                  /* test: Ashley x, y, z; -999999 = off */
{
    if (!on || !ready || ph != 1 || caught || scene || !Ashley()) return -999999;
    return (int)*(f32*)(pPL + 0x94 + 4 * i);
}
