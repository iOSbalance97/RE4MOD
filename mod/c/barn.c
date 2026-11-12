/* B88: the farm barn (room r103) - El Herrero's first appearance, as a NEW enemy.
 *  1. Leon reaches the barn's upper floor (the Ganado with the pitchfork up there still alive): the stealth
 *     tutorial panel (texture in em12.drs, mkfiles.py) - the game stops until A (x) is pressed. The window
 *     jump areas of the room are switched off from here until the end of the scene.
 *  2. That Ganado dies (stealth or not): a short scene. Camera on Leon, a crash (the door-break sound),
 *     Leon turns, the camera goes over his shoulder to the barn door: El Herrero comes in, slowly.
 *  3. Control comes back, the windows are on again.
 * El Herrero is created like the game's EmSetEvent (0x800CB76C: EmMgr create, the list record copied in,
 * first move) with one change: before its first move its archive pointer (subArc) is pointed at the table
 * mkfiles.py put in em12.drs, so Em10Set picks our body BIN/TPL; every other Ganado is untouched.
 * Test build: Leon's position is shown at the top left while in r103 (to place the door exactly). */
#include "game.h"
#include "herrero_arc.h"
void CrouchStand(void);
#define SPF_SCEAT  0x00400000u            /* no area checks (the item the Ganado dropped, doors) */
#define SPF_ACTBTN 0x00000100u            /* no action prompts */

#define STAGE   G8(0x4FA8)
#define ROOM    G8(0x4FA9)
#define STOPF   (*(u32*)(pG + 0x170))
#define SPF_KEY 0x80000000u
#define SPF_CAM 0x40000000u
#define SPF_EM  0x20000000u
#define SPF_PL  0x10000000u
#define CAMP    ((f32*)(pG + 0x74 + 0xA4))       /* pG->Camera.param.Campos, Target (+3), Roll, Fovy (+7) */
#define EMLIST(i) (pG + 0x52F4 + (i) * 32)
#define EM_CREATE ((u8* (*)(void*, int))0x801DE5F8)
#define EMMGR ((void*)0x80283160)
typedef f32 (*Atan2F)(f32, f32);
#define atan2f_ ((Atan2F)0x8005FFE8)

/* where El Herrero comes in: the barn's big door (set from the user's coordinates; until then a guess
 * from the ladder) */
#define DOOR_KNOWN 1                     /* B89: guess from the user's screenshot (Leon at the side door -13562,-12198 looking +z
                                            at the opening in the far wall, under the Ganado at z -1770) */
#define DOOR_X (-13650.0f)
#define DOOR_Z 2300.0f

static int st, t, list_no = -1, seen, lock_n;
static u8* upper;                       /* the Ganado upstairs (live work) */
static u8* herrero;
static u8* arc12;                       /* em12.drs archive base */
static f32 dx, dz, ex, ez, a0, a1;      /* door; Leon's start and end angle */
static u8* locked[8];
static u16 pad_old;

static f32 Sin(f32 a)
{
    const f32 PI = 3.14159265f; f32 a2;
    while (a > PI) a -= 2.0f * PI;
    while (a < -PI) a += 2.0f * PI;
    if (a > PI * 0.5f) a = PI - a; else if (a < -PI * 0.5f) a = -PI - a;
    a2 = a * a;
    return a * (1.0f - a2 / 6.0f * (1.0f - a2 / 20.0f * (1.0f - a2 / 42.0f)));
}
static f32 Cos(f32 a) { return Sin(a + 1.57079633f); }
static f32 Sm(f32 x) { if (x <= 0.0f) return 0.0f; if (x >= 1.0f) return 1.0f; return x * x * (3.0f - 2.0f * x); }
static f32 Wrap(f32 a) { while (a > 3.14159265f) a -= 6.2831853f; while (a < -3.14159265f) a += 6.2831853f; return a; }
static void SetMat(u8* m, f32 x, f32 z, f32 a)
{
    f32* q = (f32*)(m + 0x0C); f32 s = Sin(a), c = Cos(a);
    q[0] = c; q[1] = 0.0f; q[2] = s; q[3] = x; q[4] = 0.0f; q[5] = 1.0f; q[6] = 0.0f; q[8] = -s; q[9] = 0.0f; q[10] = c; q[11] = z;
}

/* ---- scene areas (SceAt ordering table, pS + 140 on PAL; records: be_flg +0x34, id +0x35, act_type +0x4A) */
static u8* OtNext(u8* p)
{
    u32 v;
    while ((v = *(u32*)p) != 0xFFFFFFFFu) {
        p = (u8*)(v | 0x80000000u);
        if ((s32)v < 0) return p;
    }
    return 0;
}
static void WindowsLock(int on)
{
    u8* p;
    if (on) {
        if (lock_n) return;
        for (p = OtNext(pS + 140); p && lock_n < 8; p = OtNext(p)) {
            u8 at = p[0x4A];
            if ((at == 2 || at == 4) && (p[0x34] & 1) && *(f32*)(p + 0x08) > 1500.0f) {   /* jump out / down, up high */
                p[0x34] &= ~1; locked[lock_n++] = p;
            }
        }
    } else {
        while (lock_n > 0) { p = locked[--lock_n]; p[0x34] |= 1; }
    }
}
static int Ladder(f32* x, f32* z, f32* a)
{
    u8* p; f32 best = 1e12f; int ok = 0;
    for (p = OtNext(pS + 140); p; p = OtNext(p)) {
        if (p[0x35] == 0x10) {
            f32 lx = *(f32*)(p + 0x5C), lz = *(f32*)(p + 0x64);
            f32 d = (lx - *(f32*)(pPL + 0x94)) * (lx - *(f32*)(pPL + 0x94)) + (lz - *(f32*)(pPL + 0x9C)) * (lz - *(f32*)(pPL + 0x9C));
            if (d < best) { best = d; *x = lx; *z = lz; *a = *(f32*)(p + 0x68); ok = 1; }
        }
    }
    return ok;
}

static u8* EmFind(int no)                 /* the live work made from list entry `no` */
{
    u32 n = *(u32*)((u8*)EMMGR + 4), i, sz = *(u32*)((u8*)EMMGR + 8);
    u8* base = *(u8**)EMMGR;
    for (i = 0; i < n; i++) {
        u8* e = base + i * sz;
        if ((*(u32*)e & 0x201) == 1 && e[0x398] == (u8)no) return e;
    }
    return 0;
}

static u8* HerreroSpawn(f32 x, f32 y, f32 z, f32 ang)
{
    u8* e = EM_CREATE(EMMGR, 0x12);
    u8* real; u8* vt;
    if (!e) return 0;
    real = *(u8**)(e + 0x378);
    if (!real || *(u32*)real < (u32)HR_ARC_W - 3u) return 0;
    arc12 = real;
    *(u8**)(e + 0x378) = *(u8**)(e + 0x37C) = real + *(u32*)(real + 4 * HR_ARC_W);
    e[0x101] = 0;                         /* type 0: male villager (Em10Set) */
    e[0x38D] = 0;                         /* set */
    *(u32*)(e + 0x3C8) = 0x20000000u;     /* weapon: the axe class (routine 0x26 = our smash) */
    e[0x3D0] = 0;
    *(f32*)(e + 0x3CC) = 20000.0f;        /* Guard_r */
    *(s16*)(e + 0x320) = *(s16*)(e + 0x322) = 4000;
    *(f32*)(e + 0xA0) = 0.0f; *(f32*)(e + 0xA4) = ang; *(f32*)(e + 0xA8) = 0.0f;
    *(f32*)(e + 0x94) = x; *(f32*)(e + 0x98) = y; *(f32*)(e + 0x9C) = z;
    *(f32*)(e + 0x110) = x; *(f32*)(e + 0x114) = y; *(f32*)(e + 0x118) = z;
    e[0x398] = 0xFF;
    *(f32*)(e + 0x374) = 1.0e16f;
    *(f32*)(e + 0x370) = (x - *(f32*)(pPL + 0x94)) * (x - *(f32*)(pPL + 0x94)) + (z - *(f32*)(pPL + 0x9C)) * (z - *(f32*)(pPL + 0x9C));
    vt = *(u8**)(e + 8);
    ((void (*)(u8*))*(void**)(vt + 44))(e + *(s16*)(vt + 40));      /* em->move(): its R0_Init */
    return e;
}

static void Cam(f32 cx, f32 cy, f32 cz, f32 tx, f32 ty, f32 tz, f32 fovy)
{
    CAMP[0] = cx; CAMP[1] = cy; CAMP[2] = cz; CAMP[3] = tx; CAMP[4] = ty; CAMP[5] = tz; CAMP[6] = 0.0f; CAMP[7] = fovy;
    CAMP[8] = 0.0f; CAMP[9] = 1.0f; CAMP[10] = 0.0f;               /* Up */
}

int BarnPanel(void) { return st == 1; }
u8* BarnText(void) { return arc12 ? arc12 + *(u32*)(arc12 + 4 * HR_TXT_W) : 0; }
int BarnCoords(int i)
{
    if (!pG || STAGE != 1 || ROOM != 3 || !pPL) return -999999;
    if (i == 0) return (int)*(f32*)(pPL + 0x94);
    if (i == 1) return (int)*(f32*)(pPL + 0x9C);
    if (i == 2) return (int)*(f32*)(pPL + 0x98);
    return (int)(*(f32*)(pPL + 0xA4) * 57.29578f);
}

void BarnFrame(void)
{
    u8* pl = pPL; u16 b, press;
    if (!pG || !pl) return;
    b = Pad_data[0].button; press = b & ~pad_old; pad_old = b;
    if (STAGE != 1 || ROOM != 3) {                       /* left the farm: forget everything */
        if (st) { STOPF &= ~(SPF_KEY | SPF_CAM | SPF_EM | SPF_PL | SPF_SCEAT | SPF_ACTBTN); }
        st = 0; list_no = -1; seen = 0; lock_n = 0; upper = 0; herrero = 0;
        return;
    }
    if (list_no < 0) {                                   /* the Ganado upstairs: list entry high up */
        int i;
        for (i = 0; i < 255; i++) {
            u8* d = EMLIST(i);
            if (d[1] >= 0x10 && d[1] <= 0x20 && *(u16*)(d + 0x18) == 0x0103 && *(s16*)(d + 0x0E) >= 250) { list_no = i; break; }
        }
        if (list_no < 0) { list_no = 999; return; }
    }
    if (list_no == 999) return;
    if (!upper) upper = EmFind(list_no);
    if (upper && !arc12) arc12 = *(u8**)(upper + 0x37C);
    switch (st) {
    case 0: {                                            /* waiting for Leon upstairs */
        f32 lx, lz, ux, uz;
        if (!upper || seen) return;
        lx = *(f32*)(pl + 0x94); lz = *(f32*)(pl + 0x9C); ux = *(f32*)(upper + 0x94); uz = *(f32*)(upper + 0x9C);
        if (*(f32*)(pl + 0x98) > 2500.0f && (lx - ux) * (lx - ux) + (lz - uz) * (lz - uz) < 12000.0f * 12000.0f
            && pl[0xFC] == 0 && (pl[0xFD] <= 3 || pl[0xFD] == 6)) {
            if (++t >= 20) { st = 1; t = 0; seen = 1; WindowsLock(1); STOPF |= SPF_KEY | SPF_EM | SPF_PL; }
        } else t = 0;
        return;
    }
    case 1:                                              /* the tutorial panel */
        if (++t > 20 && (press & PAD_A)) { STOPF &= ~(SPF_KEY | SPF_EM | SPF_PL); st = 2; t = 0; }
        return;
    case 2: {                                            /* until that Ganado is dead */
        u8* e = EmFind(list_no);
        WindowsLock(1);
        if (e && *(s16*)(e + 0x320) > 0 && e[0xFC] < 3) { upper = e; return; }
        if (pl[0xFC] != 0 || (pl[0xFD] > 3 && pl[0xFD] != 6)) { t = 0; return; }   /* Leon still busy (the takedown) */
        if (++t < 50) return;                            /* let it fall */
        st = 3; t = 0;
        {   /* the door, Leon's turn */
            f32 lx = *(f32*)(pl + 0x94), lz = *(f32*)(pl + 0x9C), la, lzz, a;
            if (DOOR_KNOWN) { dx = DOOR_X; dz = DOOR_Z; }
            else if (Ladder(&la, &lzz, &a)) { dx = la + Sin(a) * 1800.0f - Cos(a) * 2200.0f; dz = lzz + Cos(a) * 1800.0f + Sin(a) * 2200.0f; }
            else { dx = lx + 4000.0f; dz = lz; }
            a0 = *(f32*)(pl + 0xA4); a1 = atan2f_(dx - lx, dz - lz);
            ex = lx; ez = lz;
        }
        STOPF |= SPF_KEY | SPF_CAM | SPF_SCEAT | SPF_ACTBTN;
        CrouchStand();
        return;
    }
    case 3: {                                            /* the scene */
        f32 lx = *(f32*)(pl + 0x94), ly = *(f32*)(pl + 0x98), lz = *(f32*)(pl + 0x9C), a;
        t++;
        if (t == 36 && !herrero) herrero = HerreroSpawn(dx, 0.0f, dz, atan2f_(lx - dx, lz - dz));
        if (t == 40) {
            Vec v; v.x = dx; v.y = 1200.0f; v.z = dz;
            SndCall(6, 0x37, (int)&v, 0, 0, 0);          /* a door smashed in */
        }
        a = a0;
        if (t > 52) a = a0 + Wrap(a1 - a0) * Sm((f32)(t - 52) / 34.0f);    /* Leon turns to the noise */
        *(f32*)(pl + 0xA4) = a; SetMat(pl, ex, ez, a);
        if (t < 96) {                                     /* on Leon's face, from the front */
            f32 sh = (t >= 40 && t < 52) ? 18.0f * Sin((f32)t * 2.1f) : 0.0f;
            f32 fa = Sin(a0), fb = Cos(a0);
            Cam(lx + fa * 1350.0f + fb * 420.0f + sh, ly + 1700.0f + sh, lz + fb * 1350.0f - fa * 420.0f,
                lx + fa * 60.0f, ly + 1560.0f, lz + fb * 60.0f, 38.0f);
        } else {                                          /* B90: down on the ground floor, facing the door: El Herrero coming in */
            f32 hx = dx, hy = 1400.0f, hz = dz, k = Sm((f32)(t - 96) / 120.0f);
            if (herrero) { hx = *(f32*)(herrero + 0x94); hy = *(f32*)(herrero + 0x98) + 1400.0f; hz = *(f32*)(herrero + 0x9C); }
            Cam(dx + 900.0f, 1350.0f + 150.0f * k, dz - 4300.0f + 600.0f * k, hx, hy, hz, 46.0f - 8.0f * k);
        }
        if (t >= 300 || (t > 120 && (press & PAD_A))) {
            STOPF &= ~(SPF_KEY | SPF_CAM | SPF_SCEAT | SPF_ACTBTN); WindowsLock(0); st = 4; t = 0;
        }
        return;
    }
    default:
        return;
    }
}
