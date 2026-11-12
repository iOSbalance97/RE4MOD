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
#define STA1 (*(u32*)(pG + 0x501C))      /* Status_flg[1]: 0x10000000 = STA_SUSPEND: only works with be_flag 0x800 move */
#define STA_SUSPEND 0x10000000u
#define SND_STR_START ((void (*)(int, int, int))0x800586F8)
#define SND_STR_STOP ((void (*)(int))0x800587D8)        /* SndRoomStrStop(fade s) */
#define SPF_CINESCO 0x00004000u          /* unused by the game: our bars request (cine_polling: Stop_flg != 0) */
u8* StealthTarget(void); int StealthKilling(void);
/* B96: SndStrReq(u32 id, flg, time, vol) (PAL 0x800573E8; flg 4 = fade to vol over time/200 s; vol 0 = stop request) */
#define SND_STR_ID ((int (*)(u32, int, int, int))0x800573E8)
/* B96: cPlayer::motionSet(m0, seq0, m1, seq1, hokan, frame) (PAL 0x8013FA70, from pl_R1_Turn180 0x80052A40) */
#define PL_MOTSET ((void (*)(u8*, void*, void*, void*, void*, int, int))0x8013FA70)
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
static int dbg;
static u32 mod_t;
static int music;                       /* 1 = his music is on */
static f32 cex, cey, cez, ctx, cty, ctz; /* camera position, smoothed target */
static int turn_t;                      /* B96: frame Leon's turn motion started */               /* tracking camera */                         /* test: 1 create failed, 2 bad archive, 3 created; +10*routine */

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
static f32 Sq(f32 x) { f32 r = x > 1.0f ? x : 1.0f; int i; if (x <= 0.0f) return 0.0f; for (i = 0; i < 14; i++) r = 0.5f * (r + x / r); return r; }
static f32 Wrap(f32 a) { while (a > 3.14159265f) a -= 6.2831853f; while (a < -3.14159265f) a += 6.2831853f; return a; }
static void SetMat(u8* m, f32 x, f32 z, f32 a)
{
    f32* q = (f32*)(m + 0x0C); f32 s = Sin(a), c = Cos(a);
    q[0] = c; q[1] = 0.0f; q[2] = s; q[3] = x; q[4] = 0.0f; q[5] = 1.0f; q[6] = 0.0f; q[8] = -s; q[9] = 0.0f; q[10] = c; q[11] = z;
}

/* ---- B96: the room stream (r103: battle music 0/8) handled by volume, never stopped while the scene
 * needs it. B95 stopped it (fade to 0 = stop request) and then asked SndRoomStrStart for it again: a
 * stream already being stopped is not brought back, so it went on silent (the test overlay read
 * "playing" the whole time). Slots: pSnd + 0x44, 16 bytes: busy +0, stop_req +1, now vol +2, file vol +3,
 * id +4, no +8, blk +0xA. */
static u8* RoomStr(void)
{
    u8* s = *(u8**)0x802B7E54; int i, no;
    if (!s || !(*(u32*)(s + 2760) & 0x8000)) return 0;
    no = s[2763];
    for (i = 0; i < 4; i++) {
        u8* w = s + 0x44 + 16 * i;
        if (w[0] && *(s16*)(w + 8) == no && *(u16*)(w + 10) == 0) return w;
    }
    return 0;
}
static void MusicQuiet(void)            /* down to volume 1 (kept alive, no stop request) */
{
    u8* w = RoomStr();
    if (w && !w[1] && (s8)w[2] > 1) SND_STR_ID(*(u32*)(w + 4), 4, 100, 1);
}
static void MusicOn(void)               /* up to its own volume, started when it is not there */
{
    u8* w = RoomStr();
    if (!w) SND_STR_START(1, 0, 1);
    else if (w[1] || (s8)w[2] < (s8)w[3] - 2) SND_STR_ID(*(u32*)(w + 4), 4, 160, (s8)w[3]);
}
/* cPlayer virtuals (vptr at +8, GCC 2.95 entries {s16 delta, s16, fn}): beginEvent +16, endEvent +24 */
static void PlVirt(u8* pl, int off, u32 arg)
{
    u8* vt = *(u8**)(pl + 8);
    ((void (*)(u8*, u32))*(void**)(vt + off + 4))(pl + *(s16*)(vt + off), arg);
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
            if ((at == 2 || at == 4 || at == 5 || at == 26) && (p[0x34] & 1) && *(f32*)(p + 0x08) > 1500.0f) {   /* jump out / down / jump (B92), up high */
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
    if (!e) { dbg = 1; return 0; }
    real = *(u8**)(e + 0x378);
    if (!real || *(u32*)real < (u32)HR_ARC_W - 3u) { dbg = 2; return 0; }
    dbg = 3;
    arc12 = real;
    *(u8**)(e + 0x378) = *(u8**)(e + 0x37C) = real + *(u32*)(real + 4 * HR_ARC_W);
    e[0x101] = 0;                         /* type 0: male villager (Em10Set) */
    e[0x38D] = 0;                         /* set */
    *(u32*)(e + 0x3C8) = 0x20000000u;     /* weapon: the axe class (routine 0x26 = our smash); B91: bit 1 =
                                             Wait calls setFindPL(): it knows where Leon is and comes for him */
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
    if (i == 5) {                                        /* test: the room stream table word, + 1 if playing */
        u8* snd = *(u8**)0x802B7E54;
        if (!snd) return -1;
        {   /* B96: no side effects: 1SVVV = slot found, stop request, volume now */
            u8* w = RoomStr();
            return w ? 10000 + w[1] * 1000 + (u8)w[2] : (int)(*(u32*)(snd + 2760) & 0xFF);
        }
    }
    if (i == 4) return herrero ? dbg * 1000 + herrero[0xFC] * 100 + herrero[0xFD] : dbg;
    return (int)(*(f32*)(pPL + 0xA4) * 57.29578f);
}

void BarnFrame(void)
{
    u8* pl = pPL; u16 b, press;
    if (!pG || !pl) return;
    b = Pad_data[0].button; press = b & ~pad_old; pad_old = b;
    {   /* B95: cinema bars while a stealth takedown is offered (the cross over a Ganado) and while it runs */
        static int bars;
        if (StealthTarget() || StealthKilling()) bars = 8; else if (bars > 0) bars--;
        if (bars) STOPF |= SPF_CINESCO; else STOPF &= ~SPF_CINESCO;
    }
    if (STAGE != 1 || ROOM != 3) {                       /* left the farm: forget everything */
        if (st) { STOPF &= ~(SPF_KEY | SPF_CAM | SPF_EM | SPF_PL | SPF_SCEAT | SPF_ACTBTN); if (st == 3) STA1 &= ~STA_SUSPEND; }
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
            if (++t >= 20) { st = 1; t = 0; seen = 1; WindowsLock(1); STOPF |= SPF_KEY | SPF_EM | SPF_PL; MusicQuiet(); }
        } else t = 0;
        return;
    }
    case 1:                                              /* the tutorial panel */
        if (++t > 20 && (press & PAD_A)) { STOPF &= ~(SPF_KEY | SPF_EM | SPF_PL); st = 2; t = 0; }
        return;
    case 2: {                                            /* until that Ganado is dead */
        u8* e = EmFind(list_no);
        WindowsLock(1);
        /* B94: no action prompt at all while up in the loft (the window jumps were still offered):
         * Stop_flg 0x100 = cActionButton::move shows and runs nothing */
        if (*(f32*)(pl + 0x98) > 2500.0f) STOPF |= SPF_ACTBTN; else STOPF &= ~SPF_ACTBTN;
        if ((mod_t++ % 30) == 0) MusicQuiet();  /* the farm starts its music 30 s in: kept down until El Herrero */
        if (e && *(s16*)(e + 0x320) > 0 && e[0xFC] < 3) { upper = e; return; }
        if (pl[0xFC] != 0 || (pl[0xFD] > 3 && pl[0xFD] != 6)) { t = 0; return; }   /* Leon still busy (the takedown) */
        if (++t < 50) return;                            /* let it fall */
        st = 3; t = 0;
        {   /* the door, Leon's turn */
            f32 lx = *(f32*)(pl + 0x94), lz = *(f32*)(pl + 0x9C), la, lzz, a;
            if (DOOR_KNOWN) { dx = DOOR_X; dz = DOOR_Z; }
            else if (Ladder(&la, &lzz, &a)) { dx = la + Sin(a) * 1800.0f - Cos(a) * 2200.0f; dz = lzz + Cos(a) * 1800.0f + Sin(a) * 2200.0f; }
            else { dx = lx + 4000.0f; dz = lz; }
            a1 = atan2f_(dx - lx, dz - lz); a0 = Wrap(a1 + 3.14159265f);
            ex = lx; ez = lz;
            {   /* B96: the far camera: past Leon (away from the door) and to the barn's inside, 2.2 m up */
                f32 fx = lx - dx, fz = lz - dz, n = Sq(fx * fx + fz * fz), px, pz;
                if (n < 1.0f) n = 1.0f;
                fx /= n; fz /= n; px = fz; pz = -fx; if (px < 0.0f) { px = -px; pz = -pz; }
                cex = lx + fx * 2200.0f + px * 900.0f; cey = 2200.0f; cez = lz + fz * 2200.0f + pz * 900.0f;
                ctx = dx; cty = 1200.0f; ctz = dz;
            }
        }
        STOPF |= SPF_KEY | SPF_CAM | SPF_SCEAT | SPF_ACTBTN;
        CrouchStand();
        /* B96: Leon in the game's event routine (cPlayer::beginEvent(0): routine 5, idle, no pad), back to
         * the door (a cut: the camera is on his face); he turns with his own quick-turn motion */
        PlVirt(pl, 16, 0);
        *(f32*)(pl + 0xA4) = a0; SetMat(pl, ex, ez, a0);
        STA1 |= STA_SUSPEND; *(u32*)pl |= 0x800;          /* B92: the game's own event pause: only Leon and El Herrero move */
        turn_t = 0;
        return;
    }
    case 3: {                                            /* the scene */
        f32 lx = *(f32*)(pl + 0x94), ly = *(f32*)(pl + 0x98), lz = *(f32*)(pl + 0x9C);
        t++;
        if (t == 36 && !herrero) herrero = HerreroSpawn(dx, 0.0f, dz, atan2f_(lx - dx, lz - dz));
        /* B91: SPF_EM stops every character (the Ganado outside would see Leon): the game's own emMove
         * (PAL 0x800C9D5C, what cEmMgr::move runs on each work) for Leon and El Herrero only */
        if (herrero && (*(u32*)herrero & 0x201) == 1) {
            /* B93: shown at once (be_flag bit 2 = drawn, model alpha +0x154): Wait would set them, but he
             * skips it (he knows where Leon is), so he stayed invisible until some later routine did */
            *(u32*)herrero |= 0x800 | 2; *(f32*)(herrero + 0x154) = 1.0f;
        }
        /* B94: born like B90 (where he WAS seen): his first frames in Wait make him drawn; only then the
         * flag bit 1 (Wait -> setFindPL: he knows where Leon is and comes) */
        if (herrero && t == 42) *(u32*)(herrero + 0x3C8) |= 1u;
        if (t >= 80 && (t - 80) % 45 == 0) { MusicOn(); music = 1; }   /* B96: the farm's battle music back up */
        if (t == 40) SndCall(1, 0x1E, 0, 0, 0, 0);       /* B96: a door kicked in (player bank: always loaded; room
                                                            bank 6 of r103 has no 0x37, B95 played nothing) */
        if (t == 48) {                                    /* B96: his quick 180 turn (m_MotTbl 0xB/0xC, hurt 0x6B/0x6C) */
            void** tb = *(void***)(pl + 0x424);
            if (tb && tb[0xB] && tb[0x6B]) { PL_MOTSET(pl, tb[0xB], tb[0xC], tb[0x6B], tb[0x6C], 5, 0); turn_t = t; }
        }
        if (turn_t && t == turn_t + 21) {                 /* the turn is over: idle again, facing the door exactly */
            PlVirt(pl, 16, 0);
            *(f32*)(pl + 0xA4) = a1; SetMat(pl, lx, lz, a1);
        }
        if (t < 96) {                                     /* on Leon's face, from the front */
            f32 sh = (t >= 40 && t < 52) ? 18.0f * Sin((f32)t * 2.1f) : 0.0f;
            f32 fa = Sin(a0), fb = Cos(a0);
            Cam(lx + fa * 1350.0f + fb * 420.0f + sh, ly + 1700.0f + sh, lz + fb * 1350.0f - fa * 420.0f,
                lx + fa * 60.0f, ly + 1560.0f, lz + fb * 60.0f, 38.0f);
        } else {                                          /* B96: a fixed camera far back (B95's came too close: he walked
                                                             into it and the view ended up inside him) */
            f32 hx = dx, hy = 0.0f, hz = dz, ddx, ddz;
            if (herrero) { hx = *(f32*)(herrero + 0x94); hy = *(f32*)(herrero + 0x98); hz = *(f32*)(herrero + 0x9C); }
            ctx += (hx - ctx) * 0.15f; cty += (hy + 1150.0f - cty) * 0.15f; ctz += (hz - ctz) * 0.15f;
            Cam(cex, cey, cez, ctx, cty, ctz, 42.0f);
            ddx = hx - cex; ddz = hz - cez;
            if (t > 150 && ddx * ddx + ddz * ddz < 3600.0f * 3600.0f) t = 400;   /* close: the scene ends before he is */
        }
        if (t >= 330 || (t > 120 && (press & PAD_A))) {
            PlVirt(pl, 24, 2);                            /* B96: cPlayer::endEvent(2): routine 0, pad back */
            STOPF &= ~(SPF_KEY | SPF_CAM | SPF_SCEAT | SPF_ACTBTN); STA1 &= ~STA_SUSPEND; *(u32*)pl &= ~0x800u;
            if (herrero && (*(u32*)herrero & 0x201) == 1) *(u32*)herrero &= ~0x800u;
            WindowsLock(0); st = 4; t = 0;
        }
        return;
    }
    default:
        if (herrero && (*(u32*)herrero & 0x201) == 1 && *(s16*)(herrero + 0x320) > 0) { *(u32*)herrero |= 2; *(f32*)(herrero + 0x154) = 1.0f; }
        else if (music) { SND_STR_STOP(4); music = 0; }   /* he is dead: the music fades out */
        if (music && herrero && (mod_t++ % 45) == 0) MusicOn();   /* B96: kept up while he lives */
        return;
    }
}
