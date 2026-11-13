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
#include "herrero_mot.h"
extern u8* hr_scene_em;                 /* stealth.c: the Herrero whose motion the scene picks */
f32 HerreroSceneMot(u8* e, int m);
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
#define DOOR_X (-13450.0f)                /* B97: the B96 video: Leon walks in through the big door at (-13426, -1833)
                                            and the opening is at z ~ -1770 (B89). B89-B96 put him at z +2300:
                                            4 m OUTSIDE, ~4 s of walking before the door, and the scene was over */
#define DOOR_Z (-900.0f)                 /* spawn: ~0.9 m outside the opening, on Leon's way in */
#define DOOR_IN (-1770.0f)               /* the opening (camera's first aim) */
#define MARK_X (-13520.0f)               /* B98: where his walk in ends: 2 m in, 3.4 m from the camera */
#define MARK_Z (-2900.0f)
#define HR_STEP 30.8f                    /* his walk's travel per frame (mkanim.py) */

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
static int turn_t;                      /* B96: frame Leon's turn motion started */
/* B99: the scene in phases: 0 Leon hears the door and turns, 1 walks to near the ladder (camera at his
 * feet), 2 camera to the ladder top, 3 camera down the hole to the ground (El Herrero comes in), 4 watching */
static int ph, ph_t, wi, stuck;
static f32 best_d, c0x, c0y, c0z, t0x, t0y, t0z;
/* the way along the loft to the ladder: Leon's own steps in the B96/B97 test videos (y 3334) */
/* B102: Leon's own way across the loft in the B101 video (ladder -> Ganado, reversed), y 3334 */
/* B106: the window is the loft's far (east) one: in the B90 test video the game offers "SALTAR SOBRE"
 * with Leon at (-10406, -1558). B102-B105 aimed 0.7 m from the kill (and B105's area search wanted act 2:
 * that window is act 5, "jump over") -- he stopped far short. Both ways along Leon's own steps in that video. */
static const f32 WW[][2] = { { -12924.0f, -2081.0f }, { -11707.0f, -2202.0f }, { -10760.0f, -1880.0f },
                             { -10480.0f, -1640.0f } };
#define NWW 4
static const f32 WP[][2] = { { -10416.0f, -2263.0f }, { -11226.0f, -3139.0f }, { -11829.0f, -4203.0f },
                             { -12524.0f, -5162.0f }, { -12639.0f, -5493.0f } };
#define NWP 5
static int wwi;
/* B105: the window he walks to: the middle of the window's own jump-out area (the place where the game
 * offers the jump, SceAt record: area +0x04, type +0x05, xz4 points / cylinder centre at +0x14) -- B102-B104
 * guessed it and he stopped well short of it. Fallback if none is found. */
static f32 wcx[8], wcz[8]; static u8 wat[8];
int barn_padlock;                        /* B105: pad.c gives Leon no input at all while it is set */
extern u16 barn_pad;                     /* pad.c: the remapped buttons, before that lock */
static int skill, vs;                    /* B104: the Ganado died by a takedown; the scene's stealth variant */
#define QFPS_DIR (*(f32*)(0x80217104 + 0x204))   /* CamCtrl.m_QuasiFPS (PAL 0x80217104, from resetCameraAngle */
#define QFPS_DEP (*(f32*)(0x80217104 + 0x200))   /* 0x800078DC): the C-stick look angles */
static int ls, lt;                       /* B102: Leon's steps in phase 1 */
static int back_t;                       /* B107: frames until the farm's music comes back */
/* B106: the shoulder camera places itself from ITS copy of Leon's matrix (CameraQuasiFPS::m_pl_mat +0x174,
 * calcBaseMatrix), which his own routine refreshes (setPlayerLocation) -- frozen under the panel (SPF_PL),
 * so turning him there left it behind his old facing: the camera looked at him from the side. Copied here
 * from his matrix (+0x0C). */
static void QfpsPlMat(u8* pl)
{
    int i;
    for (i = 0; i < 12; i++) ((f32*)(0x80217104 + 0x174))[i] = ((f32*)(pl + 0x0C))[i];
}
/* B109: THE reason the camera did not face the Ganado after the panel (B102-B108): the mod's own move hook
 * (m15.s, in pl_R0_Move) keeps the camera still in the world when the GAME turns Leon: every frame it takes
 * the yaw added since its last frame (modvars +4 = last yaw, +8 = valid) off m_direction_ratio. Under the
 * panel Leon's routine is stopped, so its last yaw was the one from before the panel: our turn to the
 * Ganado was read on the first free frame as "turned by the game" and the camera was turned back by it
 * (whatever m_direction_ratio / m_pl_mat / init flag had been set) -- he looked at the Ganado, the camera
 * stayed looking where it was. Now the hook's memory is dropped whenever we turn him: it starts afresh */
static void YawForget(void) { *(u32*)(modvars + 8) = 0; }
static f32 cang, crad;                   /* B102: the camera round Leon: angle, distance */
/* Leon's climb in the videos (feet): off the ladder on the loft, half way, at its foot on the ground */
#define LA_X (-12610.0f)
#define LA_Y 3416.0f
#define LA_Z (-6327.0f)
#define LB_X (-12646.0f)
#define LB_Y 2200.0f
#define LB_Z (-7117.0f)
#define LC_X (-12440.0f)
#define LC_Y 163.0f
#define LC_Z (-7749.0f)
#define END_X (-13300.0f)                /* B100: where the camera ends: the barn's back middle, 4.5 m from MARK */
#define END_Y 1750.0f
#define END_Z (-7450.0f)
void HerreroRoarSnd(u8* e);
void HerreroYellAt(f32 x, f32 y, f32 z, u8* e, int se);
/* B101: the HUD off for the scene, as the game's own events do (sce_com.cpp begin/end, PAL 0x80156E98):
 * Cckpt.lifeMeterDisp(sw) (PAL 0x800C0518, Cckpt 0x8027E4A8) and IdSys.dispSw(IDC_LIFE_METER 33, sw)
 * (PAL 0x8011C3CC, IdSys 0x8028481C) */
/* B111 (user): Leon's lines, shown as the game shows lines while you play (r100, the two policemen on the
 * way in: cMes.MesSet(no, 0x64, 0x147 - font height - line gap, attr 0x52, slot 0, colour 0, font 4):
 * 0x40 all at once, 0x10 the game keeps running, 0x02 room text) -- our text instead of the room's
 * (the message pointer, +0x98, as item.c's notice), 0x01000000 kept after its end until we delete it.
 * Glyphs: the European font's sheet (font/common_p.fnt, 32 per row, code = 0x80 + index): space 0x80,
 * A-Y 0xA7.., a-z 0xC1.., e acute 0xF0, o acute 0xF2, inverted ? 0x122, ? 0x9B; 00 page, 01 end */
static const u16 SUB_QUE[] = { 0x0, 0x122, 0xB7, 0xD5, 0xF0, 0x80, 0xC8, 0xC1, 0x80, 0xD3, 0xC9, 0xC4, 0xCF, 0x80, 0xC5, 0xD3, 0xCF, 0x9B, 0x1 };      /* "Que ha sido eso" */
static const u16 SUB_DONDE[] = { 0x0, 0x122, 0xAA, 0xC5, 0x80, 0xC4, 0xF2, 0xCE, 0xC4, 0xC5, 0x80, 0xD6, 0xC9, 0xC5, 0xCE, 0xC5, 0x9B, 0x1 };    /* "De donde viene" */
#define SUB_WK 12                        /* B112: a slot nothing else in the game or the mod uses (3: B111) */
#define SUB_SLOT (cMes + 4 + 236 * SUB_WK)
static int sub_left;
static u32 sub_attr;
static const u16* sub_txt;
/* B113: THE reason the lines only blinked (B111 slot 3, B112 slot 12): only message slots 0-2 get a glyph
 * queue (MessageControl::init: MesRegistQueue for i <= 2, MesReleaseQueue for the rest); a slot with no
 * queue (+0xB8 = 0; PAL 0x8002394C) measures and runs its text but queues no glyph, so nothing stays on screen. Our slot
 * gets its own queue (0x100 entries x 16 bytes, what code00 clears) */
static u32 sub_queue[0x12C0 / 4] __attribute__((aligned(32)));   /* as the game's own (0x12C0 apart) */
static void SubSet(void)
{
    u8* m0 = cMes + 4; u8* m = SUB_SLOT;
    *(u32**)(m + 0xB8) = sub_queue;
    int fh = *(s8*)(m0 + 0x19), lg = *(s8*)(m0 + 0x77);
    *(s8*)(m + 0x18) = *(s8*)(m0 + 0x18); *(s8*)(m + 0x19) = *(s8*)(m0 + 0x19);   /* the game's size, as slot 0 */
    *(u16*)(m + 0x76) = *(u16*)(m0 + 0x76);
    sub_attr = 0x52 | 0x01000000;
    MesSet(cMes, 0, 0x64, 0x147 - fh - lg, sub_attr, SUB_WK, 0, 4);
    *(const u16**)(m + 0x98) = sub_txt;
}
static void Sub(const u16* txt, int frames) { sub_txt = txt; sub_left = frames; SubSet(); }
/* B112: B111's line lasted half a second (something in the scene ends the slot): while its time runs
 * it is put back the frame it is gone (alive bit, our attribute; shown at once: no flicker to see) */
static void SubTick(void)
{
    u8* m = SUB_SLOT;
    if (sub_left <= 0) return;
    ((void (*)(void*, int))0x800C0518)((void*)0x8027E4A8, 0);   /* the end code turns the life meter back on */
    if (--sub_left == 0) { if (*(u32*)(m + 0x80) == sub_attr) MesDelete(cMes, SUB_WK); return; }
    if (!(*(u32*)(m + 4) & 1) || *(u32*)(m + 0x80) != sub_attr) SubSet();
}
static void Hud(int on)
{
    ((void (*)(void*, int))0x800C0518)((void*)0x8027E4A8, on);
    ((void (*)(void*, int, int))0x8011C3CC)((void*)0x8028481C, 33, on);
}
static int hph, hph_t;                  /* B98: his scripted entrance: 0 walk in, 1 roar, 2 idle; frame it began */
static f32 hlx, hlz;                    /* his position last frame */               /* tracking camera */                         /* test: 1 create failed, 2 bad archive, 3 created; +10*routine */

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
static __attribute__((unused)) f32 Wrap(f32 a) { while (a > 3.14159265f) a -= 6.2831853f; while (a < -3.14159265f) a += 6.2831853f; return a; }
static __attribute__((unused)) void SetMat(u8* m, f32 x, f32 z, f32 a)
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
/* B107 (user): from the window on, a boss theme: room stream 5 of the global stream file (bgm/bio4bgm,
 * block 0), the El Gigante fight's (r119's room stream, bgmtbl.dat), played as the room's own stream
 * would be: SndStrReq(blk 0, no, 0x80000003 = loop + room stream, fade, 0, 0.0) (PAL 0x80057080, the
 * call inside SndRoomStrStart). The farm's stream goes quiet meanwhile (MusicQuiet) and comes back after. */
#define SND_STR_REQ ((int (*)(int, int, int, int, int, f32))0x80057080)
#define BOSS_STR 5
static u8* StrSlot(int no)
{
    u8* s = *(u8**)0x802B7E54; int i;
    if (!s) return 0;
    for (i = 0; i < 4; i++) {
        u8* w = s + 0x44 + 16 * i;
        if (w[0] && *(s16*)(w + 8) == no && *(u16*)(w + 10) == 0) return w;
    }
    return 0;
}
static void BossOn(void)
{
    u8* w = StrSlot(BOSS_STR);
    MusicQuiet();
    if (!w) SND_STR_REQ(0, BOSS_STR, (int)0x80000003, 100, 0, 0.0f);
    else if (w[1] || (s8)w[2] < (s8)w[3] - 2) SND_STR_ID(*(u32*)(w + 4), 4, 100, (s8)w[3]);
}
static void BossOff(void)
{
    u8* w = StrSlot(BOSS_STR);
    if (w && !w[1]) SND_STR_ID(*(u32*)(w + 4), 4, 800, 0);   /* 4 s fade, then stopped (vol 0 = stop request) */
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
                f32* q = (f32*)(p + 0x14);
                if (p[0x05] == 1) { wcx[lock_n] = (q[0] + q[2] + q[4] + q[6]) * 0.25f; wcz[lock_n] = (q[1] + q[3] + q[5] + q[7]) * 0.25f; }
                else { wcx[lock_n] = q[0]; wcz[lock_n] = q[1]; }
                wat[lock_n] = at; p[0x34] &= ~1; locked[lock_n++] = p;
            }
        }
    } else {
        while (lock_n > 0) { p = locked[--lock_n]; p[0x34] |= 1; }
    }
}
static __attribute__((unused)) int Ladder(f32* x, f32* z, f32* a)
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

static f32 Sm(f32 x) { if (x <= 0.0f) return 0.0f; if (x >= 1.0f) return 1.0f; return x * x * (3.0f - 2.0f * x); }
static __attribute__((unused)) void CamTo(f32 px, f32 py, f32 pz, f32 tx, f32 ty, f32 tz, f32 kp, f32 kt)
{
    cex += (px - cex) * kp; cey += (py - cey) * kp; cez += (pz - cez) * kp;
    ctx += (tx - ctx) * kt; cty += (ty - cty) * kt; ctz += (tz - ctz) * kt;
}
/* B99: the game's event walk (cPlayer routine 5/1, pl_R1_Event_ToWalk): to m_VecWork0 (+0x404), turning
 * at m_Fwork0 (+0x400) per frame; m_Work0 (+0x3E0) = 1 once there */
static void WalkTo(u8* pl, int i)
{
    *(f32*)(pl + 0x404) = WP[i][0]; *(f32*)(pl + 0x408) = *(f32*)(pl + 0x98); *(f32*)(pl + 0x40C) = WP[i][1];
    *(f32*)(pl + 0x400) = 0.12f; *(u32*)(pl + 0x3E0) = 0;
    pl[0xFC] = 5; pl[0xFD] = 1; pl[0xFE] = 0; pl[0xFF] = 0;
}
/* B107: the barn's inside (Leon's own positions in the videos: west -14601, east window -10406, front
 * -1558 at the window / door -1833, back -7749 at the ladder foot): no scene camera goes through a wall */
#define BX0 (-14660.0f)
#define BX1 (-10300.0f)
#define BZ0 (-7850.0f)
#define BZ1 (-1500.0f)
static __attribute__((unused)) f32 InMargin(f32 x, f32 z)
{
    f32 m = x - BX0, k;
    k = BX1 - x; if (k < m) m = k;
    k = z - BZ0; if (k < m) m = k;
    k = BZ1 - z; if (k < m) m = k;
    return m;
}
static void Cam(f32 cx, f32 cy, f32 cz, f32 tx, f32 ty, f32 tz, f32 fovy)
{
    CAMP[0] = cx; CAMP[1] = cy; CAMP[2] = cz; CAMP[3] = tx; CAMP[4] = ty; CAMP[5] = tz; CAMP[6] = 0.0f; CAMP[7] = fovy;
    CAMP[8] = 0.0f; CAMP[9] = 1.0f; CAMP[10] = 0.0f;               /* Up */
    /* B100: THE reason El Herrero (and in B99 Leon) vanished since B88: with SPF_CAMERA, CameraMove builds
     * the view (v_mat) from param, but pG->Camera.mat -- the camera-to-world matrix VIEW::orientation()
     * turns the cull frustum with (view.cpp) -- is only ever copied from CamCtrl, which SPF_CAMERA stops:
     * every model was culled against the frozen game camera's frustum, so a character was drawn only
     * while inside what THAT camera saw (why it depended on where Leon stood). Rebuilt here like
     * CameraSetOrientationZeroRoll (cam_sys.cpp): columns right, up, look (pos - at), pos; Up/Look/Right. */
    {
        f32* m = (f32*)(pG + 0x74);                    /* pG->Camera.mat (3x4, rows) */
        f32 lx = cx - tx, ly = cy - ty, lz = cz - tz, rx, rz, ux, uy, uz, n;
        n = Sq(lx * lx + ly * ly + lz * lz); if (n < 1.0f) n = 1.0f; lx /= n; ly /= n; lz /= n;
        rx = lz; rz = -lx;                             /* (0,1,0) x look */
        n = Sq(rx * rx + rz * rz); if (n < 1e-4f) { rx = 1.0f; rz = 0.0f; n = 1.0f; }
        rx /= n; rz /= n;
        ux = ly * rz; uy = lz * rx - lx * rz; uz = -ly * rx;   /* look x right */
        m[0] = rx; m[1] = ux; m[2] = lx; m[3] = cx;
        m[4] = 0.0f; m[5] = uy; m[6] = ly; m[7] = cy;
        m[8] = rz; m[9] = uz; m[10] = lz; m[11] = cz;
        m = (f32*)(pG + 0x74 + 0xC4);                  /* Up, Look, Right */
        m[0] = ux; m[1] = uy; m[2] = uz; m[3] = lx; m[4] = ly; m[5] = lz; m[6] = rx; m[7] = 0.0f; m[8] = rz;
    }
}

int BarnPanel(void) { return st == 1; }
u8* BarnText(void) { return arc12 ? arc12 + *(u32*)(arc12 + 4 * HR_TXT_W) : 0; }
int BarnCoords(int i)
{
    if (!pG || STAGE != 1 || ROOM != 3 || !pPL || st == 3) return -999999;   /* B101: no test numbers in the scene */
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

/* B99 (user): the Ganados outside stay outside while Leon is in the barn until the scene is over; then
 * they know where he is and come. Each one outside the barn (not the loft one, not El Herrero) is kept in
 * em10_R1_Keeper with Guard_r 0 and Leon "known" (Be_flg 0x100: no find check): it stands and looks.
 * Let go: its Guard_r back, flag bit 1 (setFindPL) and em10 Wait. Only from routine group 1 (not hurt,
 * not dying). */
#define HOLD_N 24
static u8* hold_e[HOLD_N]; static f32 hold_g[HOLD_N]; static int hold_n;
static int InBarn(f32 x, f32 z) { return x > -14900.0f && x < -12100.0f && z > -7900.0f && z < -1700.0f; }
static void GanadoHold(int on)
{
    u8* base = *(u8**)EMMGR; u32 n = *(u32*)((u8*)EMMGR + 4), sz = *(u32*)((u8*)EMMGR + 8), i;
    int k;
    if (!on) {
        for (k = 0; k < hold_n; k++) {
            u8* e = hold_e[k];
            if ((*(u32*)e & 0x201) == 1 && e[0xFC] == 1 && *(s16*)(e + 0x320) > 0) {
                *(f32*)(e + 0x3CC) = hold_g[k]; *(u32*)(e + 0x3C8) |= 1u;
                e[0xFD] = 0; e[0xFE] = 0; e[0xFF] = 0;
            }
        }
        hold_n = 0;
        return;
    }
    if ((u32)base < 0x80000000u || (u32)base >= 0x81800000u || n > 1024 || sz < 0xC00 || sz > 0x40000) return;
    for (i = 0; i < n; i++) {
        u8* e = base + i * sz;
        if ((*(u32*)e & 0x201) != 1 || e == upper || e == herrero) continue;
        if (e[0x100] < 0x10 || e[0x100] > 0x20 || e[0x100] == 0x18) continue;
        if (e[0xFC] != 1 || *(s16*)(e + 0x320) <= 0) continue;
        for (k = 0; k < hold_n && hold_e[k] != e; k++) ;
        if (k == hold_n) {
            if (InBarn(*(f32*)(e + 0x94), *(f32*)(e + 0x9C)) || hold_n >= HOLD_N) continue;   /* inside: left alone */
            hold_e[k] = e; hold_g[k] = *(f32*)(e + 0x3CC); hold_n++;
            e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0;                      /* Keeper, its step 0 sets the wait motion */
        } else if (e[0xFD] != 1) { e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0; }
        *(f32*)(e + 0x3CC) = 0.0f; *(u32*)(e + 0x3C8) &= ~1u; *(u32*)(e + 0x3E0) |= 0x100;
    }
}

/* B104: the first shot, from the scene's first frame (B103 set the camera only on the next frame: one
 * frame of the game camera with Leon already turned). Turn variant: on his face; stealth variant (he
 * already faces the window after the takedown): over his shoulder toward the window. A shake with the bang. */
#define T_GO 100                         /* B111: he moves after his line (was 48) */
static void Shot0(u8* pl, int tt)
{
    f32 lx = *(f32*)(pl + 0x94), ly = *(f32*)(pl + 0x98), lz = *(f32*)(pl + 0x9C);
    f32 sh = (tt >= 40 && tt < 52) ? 18.0f * Sin((f32)tt * 2.1f) : 0.0f;
    f32 px, py, pz, qx, qy, qz;
    if (vs) {
        f32 fa = Sin(a1), fb = Cos(a1);
        px = lx - fa * 1500.0f - fb * 520.0f; py = ly + 1650.0f; pz = lz - fb * 1500.0f + fa * 520.0f;
        qx = lx + fa * 2500.0f; qy = ly + 1300.0f; qz = lz + fb * 2500.0f;
    } else {
        f32 ga = Sin(a0), gb = Cos(a0);
        px = lx + ga * 1350.0f + gb * 420.0f; py = ly + 1700.0f; pz = lz + gb * 1350.0f - ga * 420.0f;
        qx = lx + ga * 60.0f; qy = ly + 1560.0f; qz = lz + gb * 60.0f;
    }
    Cam(px + sh, py + sh, pz, qx, qy, qz, vs ? 44.0f : 38.0f);
    cang = atan2f_(px - lx, pz - lz); crad = Sq((px - lx) * (px - lx) + (pz - lz) * (pz - lz));
    cex = px; cey = py; cez = pz; ctx = qx; cty = qy; ctz = qz;
}

void BarnFrame(void)
{
    u8* pl = pPL; u16 b, press;
    if (!pG || !pl) return;
    b = barn_pad; press = b & ~pad_old; pad_old = b;   /* B105: before the scene's pad lock */
    {   /* B95: cinema bars while a stealth takedown is offered (the cross over a Ganado) and while it runs */
        static int bars;
        if (StealthTarget() || StealthKilling()) bars = 8; else if (bars > 0) bars--;
        if (bars) STOPF |= SPF_CINESCO; else STOPF &= ~SPF_CINESCO;
    }
    if (STAGE != 1 || ROOM != 3) {                       /* left the farm: forget everything */
        if (st) { STOPF &= ~(SPF_KEY | SPF_CAM | SPF_EM | SPF_PL | SPF_SCEAT | SPF_ACTBTN); if (st == 3) { STA1 &= ~STA_SUSPEND; Hud(1); } }
        st = 0; list_no = -1; seen = 0; lock_n = 0; upper = 0; herrero = 0; hold_n = 0; hr_scene_em = 0; barn_padlock = 0;
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
    {   /* B99: hold the outside Ganados from Leon's entering the barn to the scene's end */
        int on = (st >= 1 && st <= 3) || (st == 0 && !seen && InBarn(*(f32*)(pl + 0x94), *(f32*)(pl + 0x9C)));
        if (on || hold_n) GanadoHold(on);
    }
    switch (st) {
    case 0: {                                            /* waiting for Leon upstairs */
        f32 lx, lz, ux, uz;
        if (!upper || seen) return;
        lx = *(f32*)(pl + 0x94); lz = *(f32*)(pl + 0x9C); ux = *(f32*)(upper + 0x94); uz = *(f32*)(upper + 0x9C);
        if (*(f32*)(pl + 0x98) > 2500.0f && (lx - ux) * (lx - ux) + (lz - uz) * (lz - uz) < 12000.0f * 12000.0f
            && pl[0xFC] == 0 && (pl[0xFD] <= 3 || pl[0xFD] == 6)) {
            /* B100: the very first free frame up there (B99 left 20: the camera could be turned, and it kept
             * turning under the panel); the camera stays put under the panel (SPF_CAM) */
            /* B105: the camera is NOT frozen under the panel (B100-B104 froze it in the ladder's own camera,
             * and after the panel it went on from there: "it worked before" = B95-B99, which let it run).
             * No input reaches the game (pad.c lock: no C-stick spin either); Leon is turned to the Ganado
             * now, so the camera settles behind him toward it while the panel is up */
            st = 1; t = 0; seen = 1; WindowsLock(1); STOPF |= SPF_EM | SPF_PL; MusicQuiet(); barn_padlock = 1;
            QFPS_DIR = 0.0f; QFPS_DEP = 0.0f;
            {
                /* B109: no step (B108's 0.8 m: a wrong guess, a ladder camera area); turned to the Ganado */
                f32 a = atan2f_(ux - lx, uz - lz);
                *(f32*)(pl + 0xA4) = a; SetMat(pl, lx, lz, a);
                YawForget();
                QfpsPlMat(pl);
            }
        } else t = 0;
        return;
    }
    case 1:                                              /* the tutorial panel */
        QFPS_DIR = 0.0f; QFPS_DEP = 0.0f; QfpsPlMat(pl);
        if (++t > 20 && (press & PAD_A)) {
            /* B102 (user): out of the panel Leon (and the shoulder camera, which sits behind his facing)
             * look at the Ganado */
            if (upper) {
                f32 lx = *(f32*)(pl + 0x94), lz = *(f32*)(pl + 0x9C);
                f32 a = atan2f_(*(f32*)(upper + 0x94) - lx, *(f32*)(upper + 0x9C) - lz);
                *(f32*)(pl + 0xA4) = a; SetMat(pl, lx, lz, a);
            }
            QFPS_DIR = 0.0f; QFPS_DEP = 0.0f;
            QfpsPlMat(pl);
            *(u8*)(0x80217104 + 0x1B2) = 1;            /* B104: m_init_flag: the shoulder camera snaps behind him */
            YawForget();
            STOPF &= ~(SPF_KEY | SPF_EM | SPF_PL | SPF_CAM); st = 2; t = 0; skill = 0; barn_padlock = 0;
        }
        return;
    case 2: {                                            /* until that Ganado is dead */
        u8* e = EmFind(list_no);
        WindowsLock(1);
        /* B94: no action prompt at all while up in the loft (the window jumps were still offered):
         * Stop_flg 0x100 = cActionButton::move shows and runs nothing */
        if (*(f32*)(pl + 0x98) > 2500.0f) STOPF |= SPF_ACTBTN; else STOPF &= ~SPF_ACTBTN;
        if ((mod_t++ % 30) == 0) MusicQuiet();  /* the farm starts its music 30 s in: kept down until El Herrero */
        if (StealthKilling()) skill = 1;
        if (e && *(s16*)(e + 0x320) > 0 && e[0xFC] < 3) { upper = e; return; }
        if (pl[0xFC] != 0 || (pl[0xFD] > 3 && pl[0xFD] != 6)) { t = 0; return; }   /* Leon still busy (the takedown) */
        /* B99 (user): no free moment after the kill: the scene starts the frame Leon is back from the
         * takedown, where he did it */
        st = 3; t = 0; ph = 0; ph_t = 0; ls = 0;
        {
            f32 lx = *(f32*)(pl + 0x94), lz = *(f32*)(pl + 0x9C);
            dx = DOOR_X; dz = DOOR_Z; wi = 0;
            for (wwi = 0; wwi < NWW - 1 && WW[wwi][0] < lx + 400.0f; wwi++) ;   /* the first point ahead of him (east) */
            a1 = atan2f_(WW[wwi][0] - lx, WW[wwi][1] - lz);  /* after the turn he faces the way to the window */
            /* B104 (user): after a takedown he already faces it: he gets up and walks there, no turn */
            vs = skill && Wrap(*(f32*)(pl + 0xA4) - a1) < 1.3f && Wrap(*(f32*)(pl + 0xA4) - a1) > -1.3f;
            if (vs) a0 = *(f32*)(pl + 0xA4);
            else a0 = Wrap(a1 + 3.14159265f);              /* B101 (user): turned to face away (a cut: the camera is on his
                                                              face), so his quick turn ends right toward the ladder */
            *(f32*)(pl + 0xA4) = a0;
            ex = lx; ez = lz;
        }
        STOPF |= SPF_KEY | SPF_CAM | SPF_SCEAT | SPF_ACTBTN;
        barn_padlock = 1;                                /* B105: no input at all through the scene */
        if (!vs) {
            CrouchStand();
            /* B96: Leon in the game's event routine (cPlayer::beginEvent(0): routine 5, idle, no pad) */
            PlVirt(pl, 16, 0);
            SetMat(pl, ex, ez, a0);
        }   /* B105 (user): after a takedown he stays as he is (crouched, his own routine, no input) and the
             * scene shows him getting up (t 10) before the event routine takes him at t 48: B104's
             * beginEvent at once snapped him out of the crouch -- the cut */
        STA1 |= STA_SUSPEND; *(u32*)pl |= 0x800;          /* B92: the game's own event pause: only Leon and El Herrero move */
        Hud(0);
        turn_t = 0;
        Shot0(pl, 0);
        return;
    }
    case 3: {                                            /* the scene */
        f32 lx = *(f32*)(pl + 0x94), ly = *(f32*)(pl + 0x98), lz = *(f32*)(pl + 0x9C);
        t++;
        SubTick();
        /* ---- El Herrero: B98's scripted entrance (em10 Keeper 1/1/1, our motions, straight to MARK) */
        if (herrero && hr_scene_em == herrero && (*(u32*)herrero & 0x201) == 1) {
            f32 ux = MARK_X - dx, uz = MARK_Z - dz, L = Sq(ux * ux + uz * uz), hx, hz, sp, mv;
            u8* e = herrero;
            ux /= L; uz /= L;
            e[0xFC] = 1; e[0xFD] = 1; e[0xFE] = 1; e[0xFF] = 0;          /* em10_R1_Keeper, step 1 */
            *(u32*)(e + 0x3E0) |= 0x100;                                 /* Leon known: no em10FindCk */
            *(u32*)(e + 0x3C8) &= ~1u; *(f32*)(e + 0x3CC) = 0.0f;
            *(f32*)(e + 0xA4) = atan2f_(ux, uz);
            *(u32*)e |= 0x800 | 2; *(f32*)(e + 0x154) = 1.0f;            /* drawn, moves in the event pause */
            hx = *(f32*)(e + 0x94); hz = *(f32*)(e + 0x9C);
            sp = (hx - dx) * ux + (hz - dz) * uz;                        /* how far in */
            if (hph == 0) {
                HerreroSceneMot(e, HR_WALK);
                mv = (hx - hlx) * ux + (hz - hlz) * uz;
                if (mv < 8.0f && t > hph_t + 2) {                        /* the motion's root does not move him here: */
                    hx += ux * HR_STEP; hz += uz * HR_STEP;              /* move him by its stride */
                    *(f32*)(e + 0x94) = hx; *(f32*)(e + 0x9C) = hz;
                }
                if (sp >= L) { hph = 1; hph_t = t; HerreroRoarSnd(e); }
            } else if (hph == 1) {
                if (HerreroSceneMot(e, HR_ROAR) >= (f32)HR_ROAR_N - 2.0f || t > hph_t + HR_ROAR_N + 6) { hph = 2; hph_t = t; }
            } else HerreroSceneMot(e, HR_IDLE);
            hlx = hx; hlz = hz;
        }
        if (music && (t % 45) == 0) BossOn();             /* B107: the boss theme, from the window on */
        {   /* B102: his weapon objects move (and so are drawn) in the event pause too: they are models of
             * their own (cPlWep +0x788 -> m_pWep +0x34, m_pWepHand +0x38), frozen by STA_SUSPEND */
            u8* wp = *(u8**)(pl + 0x788);
            if ((u32)wp >= 0x80000000u && (u32)wp < 0x81800000u) {
                u8* o = *(u8**)(wp + 0x34); u8* h = *(u8**)(wp + 0x38);
                if ((u32)o >= 0x80000000u && (u32)o < 0x81800000u) *(u32*)o |= 0x800;
                if ((u32)h >= 0x80000000u && (u32)h < 0x81800000u) *(u32*)h |= 0x800;
            }
        }
        /* ---- Leon */
        if (ph == 0) {                                    /* hears the door, turns where he is */
            if (t == 40) SndCall(1, 0x1E, 0, 0, 0, 0);   /* a door kicked in (Leon's bank, always loaded) */
            if (t == 52) Sub(SUB_QUE, 85);                /* B111 (user): his line, and a pause before he moves */
            if (t == 10 && vs) CrouchStand();             /* B105: he gets up, on camera */
            if (t == T_GO && vs) {                          /* B104: stealth variant: then to the window */
                PlVirt(pl, 16, 0);
                WalkTo(pl, 0); *(f32*)(pl + 0x404) = WW[wwi][0]; *(f32*)(pl + 0x40C) = WW[wwi][1];
                ph = 1; ph_t = t; ls = 1; lt = t; best_d = 1e30f; stuck = 0;
            }
            if (t == T_GO && !vs) {                         /* B101: his quick 180 turn (m_MotTbl 0xB/0xC, hurt 0x6B/0x6C), played
                                                             through the game's own event routine 5/2 (pl_R1_Event_Smooth: the motion
                                                             to its end, then feet re-planted): B99 cut it at frame 21 and his
                                                             rotation was still in the pose, so he faced the window for a moment */
                void** tb = *(void***)(pl + 0x424);
                if (tb && tb[0xB] && tb[0x6B]) {
                    PL_MOTSET(pl, tb[0xB], tb[0xC], tb[0x6B], tb[0x6C], 5, 0);
                    pl[0xFC] = 5; pl[0xFD] = 2; pl[0xFE] = 0; pl[0xFF] = 0;
                }
                ph = 1; ph_t = t; turn_t = 1;
            }
            Shot0(pl, t);
        } else if (ph == 1) {                             /* B102 (user): turns to the window, a few steps to it, his
                                                             yell, stops, turns where he stands to the ladder, walks there */
            f32 tx = ls < 3 ? WW[wwi][0] : WP[wi][0], tz = ls < 3 ? WW[wwi][1] : WP[wi][1];
            f32 qx = tx - lx, qz = tz - lz, d = qx * qx + qz * qz;
            f32 la = *(f32*)(pl + 0xA4), fa = Sin(la), fb = Cos(la);
            if (ls == 0) {                                /* the quick turn: until Smooth is back to idle (step 3) */
                if ((pl[0xFC] == 5 && pl[0xFD] == 2 && pl[0xFE] == 3) || t > ph_t + 50) {
                    turn_t = 0; lt = t; best_d = 1e30f; stuck = 0;
                    if (d > 450.0f * 450.0f) { WalkTo(pl, 0); *(f32*)(pl + 0x404) = WW[wwi][0]; *(f32*)(pl + 0x40C) = WW[wwi][1]; ls = 1; }
                    else ls = 2;
                }
            } else if (ls == 1) {                         /* to the window, along the front wall */
                if (d < best_d - 2500.0f) { best_d = d; stuck = 0; } else stuck++;
                if (wwi < NWW - 1 && (d < 600.0f * 600.0f || stuck > 45)) {    /* next point, without stopping */
                    wwi++; best_d = 1e30f; stuck = 0;
                    *(f32*)(pl + 0x404) = WW[wwi][0]; *(f32*)(pl + 0x408) = ly; *(f32*)(pl + 0x40C) = WW[wwi][1];
                } else if (wwi == NWW - 1 && (*(u32*)(pl + 0x3E0) == 1 || d < 200.0f * 200.0f || stuck > 40)) ls = 2;
                if (t > lt + 420) ls = 2;
            } else if (ls == 2) {                         /* stops: the yell */
                PlVirt(pl, 16, 0);
                SndCall(1, 0x1E, 0, 0, 0, 0);             /* B107 (user): another blow on the door, and the music */
                HerreroYellAt(DOOR_X, 1900.0f, DOOR_Z, upper, 0x1A);
                BossOn(); music = 1;
                Sub(SUB_DONDE, 85);                       /* B111 (user): his line at the window, and a longer stop */
                ls = 3; lt = t;
            } else if (ls == 3) {                         /* listens, then turns where he stands (the event walk turns on the
                                                             spot past 60 degrees) and goes */
                if (t > lt + 75) { WalkTo(pl, wi); ls = 4; lt = t; best_d = 1e30f; stuck = 0; }
            } else {
                if (d < best_d - 2500.0f) { best_d = d; stuck = 0; } else if (t > lt + 30) stuck++;
                if (wi < NWP - 1 && (d < 600.0f * 600.0f || stuck > 45)) {      /* next point, without stopping */
                    wi++; best_d = 1e30f; stuck = 0;
                    *(f32*)(pl + 0x404) = WP[wi][0]; *(f32*)(pl + 0x408) = ly; *(f32*)(pl + 0x40C) = WP[wi][1];
                }
                /* B103: the camera starts up while he takes his last steps (the event walk stops him there) */
                if ((wi == NWP - 1 && (*(u32*)(pl + 0x3E0) == 1 || d < 1100.0f * 1100.0f || stuck > 45)) || t > lt + 360) {
                    ph = 2; ph_t = t; c0x = cex; c0y = cey; c0z = cez; t0x = ctx; t0y = cty; t0z = ctz;
                }
            }
            if (ls < 4) {                                 /* B103: one shot from the bang to his growl at the window */
                Shot0(pl, t);
            } else {                                      /* B103: as he turns and walks to the ladder the camera goes
                                                             round him, slowly, down to his feet (B102's swung round while he
                                                             stood): angle and distance about Leon, never through him */
                /* B111 (user: "for a moment it looks at the floor"): B103 recomputed the camera place from Leon
                 * every frame but eased its TARGET in world space with a gain that starts at 0 -- while he walked
                 * off, the camera went with him looking at the still point behind him, then down at the floor
                 * (target 0.3 m high). Now the target and height are kept relative to him and eased there: it
                 * goes round him, down to his legs, always on him */
                static f32 tox, toy, toz, coy;
                f32 want = la + 3.14159265f + 0.35f, k = Sm((f32)(t - lt) / 60.0f) * 0.035f, kt = 0.03f + Sm((f32)(t - lt) / 40.0f) * 0.05f;
                if (t - lt <= 1) { tox = ctx - lx; toy = cty - ly; toz = ctz - lz; coy = cey - ly; }
                cang += Wrap(want - cang) * k;
                crad += (1800.0f - crad) * k;
                coy += (900.0f - coy) * kt;
                tox += (fa * 300.0f - tox) * kt; toy += (750.0f - toy) * kt; toz += (fb * 300.0f - toz) * kt;
                cex = lx + Sin(cang) * crad; cez = lz + Cos(cang) * crad; cey = ly + coy;
                ctx = lx + tox; cty = ly + toy; ctz = lz + toz;
                Cam(cex, cey, cez, ctx, cty, ctz, 46.0f);
            }
        } else if (ph == 2) {                             /* to the top of the ladder, at head height */
            f32 k = Sm((f32)(t - ph_t) / 50.0f);       /* B103: 50 frames (was 30) */
            cex = c0x + (LA_X - c0x) * k; cey = c0y + (LA_Y + 1300.0f - c0y) * k + Sin(k * 3.14159265f) * 700.0f; cez = c0z + (LA_Z - c0z) * k;
            /* B102: up and over him, not through him */
            ctx = t0x + (lx - t0x) * k; cty = t0y + (ly + 900.0f - t0y) * k; ctz = t0z + (lz - t0z) * k;
            Cam(cex, cey, cez, ctx, cty, ctz, 46.0f);
            if (t >= ph_t + 50) { ph = 3; ph_t = t; t0x = ctx; t0y = cty; t0z = ctz; }
        } else if (ph == 3) {                             /* B99: down the hole along Leon's own climb (his head went
                                                             through there, so nothing is in the way), turning to the door */
            f32 k = Sm((f32)(t - ph_t) / 100.0f), k1, w;
            if (k < 0.5f) { k1 = k * 2.0f; cex = LA_X + (LB_X - LA_X) * k1; cey = LA_Y + (LB_Y - LA_Y) * k1; cez = LA_Z + (LB_Z - LA_Z) * k1; }
            else { k1 = k * 2.0f - 1.0f; cex = LB_X + (LC_X - LB_X) * k1; cey = LB_Y + (LC_Y - LB_Y) * k1; cez = LB_Z + (LC_Z - LB_Z) * k1; }
            cey += 1300.0f;
            w = Sm((f32)(t - ph_t - 15) / 60.0f);
            ctx = t0x + (DOOR_X - t0x) * w; cty = t0y + (1300.0f - t0y) * w; ctz = t0z + (DOOR_IN - t0z) * w;
            Cam(cex, cey, cez, ctx, cty, ctz, 46.0f);
            if (t == ph_t + 30 && !herrero) {              /* he kicks the door in: in it when the camera is down */
                herrero = HerreroSpawn(dx, 163.0f, dz, atan2f_(MARK_X - dx, MARK_Z - dz));
                if (herrero) {
                    *(f32*)(herrero + 0x3CC) = 0.0f; hr_scene_em = herrero; hph = 0; hph_t = t; hlx = dx; hlz = dz;
                    SndCall(1, 0x1E, 0, 0, 0, 0); BossOn(); music = 1;
                }
            }
            if (t >= ph_t + 100) { ph = 4; ph_t = t; c0x = cex; c0y = cey; c0z = cez; }
        } else {                                          /* B100: from the foot of the ladder on, back and to the middle
                                                             (out of the ladder; Leon walked there in the videos), watching him */
            f32 hx = DOOR_X, hy = 163.0f, hz = DOOR_IN, k = Sm((f32)(t - ph_t) / 70.0f);
            if (herrero) { hx = *(f32*)(herrero + 0x94); hy = *(f32*)(herrero + 0x98); hz = *(f32*)(herrero + 0x9C); }
            cex = c0x + (END_X - c0x) * k; cey = c0y + (END_Y - c0y) * k; cez = c0z + (END_Z - c0z) * k;
            ctx += (hx - ctx) * 0.08f; cty += (hy + 1250.0f - cty) * 0.08f; ctz += (hz - ctz) * 0.08f;
            Cam(cex, cey, cez, ctx, cty, ctz, 42.0f);
            if ((hph == 2 && t > hph_t + 25) || !herrero || t > ph_t + 330) t = 2000;   /* walked in, roared: back to the game */
        }
        if (t >= 2000 || (t > 120 && (press & PAD_A))) {
            PlVirt(pl, 24, 2);                            /* cPlayer::endEvent(2): routine 0, pad back */
            if (sub_left > 0) { sub_left = 1; SubTick(); }
            barn_padlock = 0;
            /* B107 (user): the game camera right behind him (as after the panel: its copy of his matrix,
             * the C-stick angles at 0, and the snap flag) */
            QfpsPlMat(pl); QFPS_DIR = 0.0f; QFPS_DEP = 0.0f; *(u8*)(0x80217104 + 0x1B2) = 1; YawForget();
            Hud(1);
            {
                u8* wp = *(u8**)(pl + 0x788);
                if ((u32)wp >= 0x80000000u && (u32)wp < 0x81800000u) {
                    u8* o = *(u8**)(wp + 0x34); u8* h = *(u8**)(wp + 0x38);
                    if ((u32)o >= 0x80000000u && (u32)o < 0x81800000u) *(u32*)o &= ~0x800u;
                    if ((u32)h >= 0x80000000u && (u32)h < 0x81800000u) *(u32*)h &= ~0x800u;
                }
            }
            STOPF &= ~(SPF_KEY | SPF_CAM | SPF_SCEAT | SPF_ACTBTN); STA1 &= ~STA_SUSPEND; *(u32*)pl &= ~0x800u;
            if (!herrero) {                               /* skipped before he came: he is there anyway */
                herrero = HerreroSpawn(MARK_X, 163.0f, MARK_Z, atan2f_(lx - MARK_X, lz - MARK_Z));
                if (herrero && !music) { BossOn(); music = 1; }
            }
            if (herrero && (*(u32*)herrero & 0x201) == 1) {
                *(u32*)herrero &= ~0x800u;
                /* B98: his AI back: Guard_r, flag bit 1 (setFindPL), em10 Wait */
                *(f32*)(herrero + 0x3CC) = 20000.0f; *(u32*)(herrero + 0x3C8) |= 1u;
                herrero[0xFC] = 1; herrero[0xFD] = 0; herrero[0xFE] = 0; herrero[0xFF] = 0;
            }
            hr_scene_em = 0;
            WindowsLock(0); st = 4; t = 0;
        }
        return;
    }
    default:
        if (herrero && (*(u32*)herrero & 0x201) == 1 && *(s16*)(herrero + 0x320) > 0) { *(u32*)herrero |= 2; *(f32*)(herrero + 0x154) = 1.0f; }
        else if (music) { BossOff(); music = 0; back_t = 150; }   /* he is dead: the boss theme fades out, */
        if (back_t > 0 && --back_t == 0) MusicOn();       /* B107: and the farm's comes back */
        if (music && herrero && (mod_t++ % 45) == 0) BossOn();    /* B96: kept up while he lives */
        return;
    }
}
