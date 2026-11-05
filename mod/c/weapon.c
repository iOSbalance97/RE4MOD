/* Quick weapon slots on the D-pad (remake style).
 *  - tap a direction: equip the weapon assigned to it (when Leon is free: standing, walking,
 *    running; not aiming, reloading or in an action)
 *  - hold a direction ~1 s: assign the weapon in hand to it; holding it with that same weapon
 *    clears the slot
 *  - a weapon equipped from the case that is in no slot takes the first free slot (up, right,
 *    down, left)
 * Slots live in the saved global block (MOD_SLOT_OFS). The D-pad is told apart from
 * OmniStation's stick->D-pad merge: a direction only counts when the stick does not explain it. */
#include "game.h"

#define HOLD_VIS 60      /* VIs to hold for an assignment (1 s at 60 Hz) */
#define STICK_ON 30      /* clamped stick value that OmniStation would also report as a D-pad press */

typedef struct { u16 id, num; u8 flags, type; u16 lv, bullet; s8 x, y, orient; u8 board; } cItem;

#define IM_PWEP(m)  (*(cItem**)((u8*)(m) + 0x0C))
#define IM_CHAR(m)  (*(u8*)((u8*)(m) + 0x13))
#define IM_ITEMS(m) (*(cItem**)((u8*)(m) + 0x14))
#define IM_NUM(m)   (*(s32*)((u8*)(m) + 0x1C))

static int held_dir = -1, held_t, held_done;
void PanelShow(int equipped, int missing);
static void ShowPanel(void);

static u16* Slots(void) { return (u16*)(pG + MOD_SLOT_OFS); }

static cItem* FindItem(u32 id)
{
    cItem* it = IM_ITEMS(ItemMgr);
    int i, n = IM_NUM(ItemMgr);
    u8 ch = IM_CHAR(ItemMgr);
    for (i = 0; i < n; i++, it++)
        if ((it->flags & 1) && it->type == ch && it->id == id && it->num) return it;
    return 0;
}

/* Leon free to change weapon: player routine 0 (move), sub routine idle/walk/back/run. */
static int CanSwap(void)
{
    u8* pl = pPL;
    if (!pl || G8(0x4FC4) == 1) return 0;               /* no player / Ashley */
    return pl[0xFC] == 0 && (pl[0xFD] <= 3 || pl[0xFD] == 6);
}


/* ---- Remake-style swap: holster, load while the game keeps running, draw ----
   The weapon archive (model, REL code and Leon's motions for that weapon) is read from the disc
   inside ReadWepData, which waits with TaskSleep(1). Run from the main task that wait freezes the
   frame; run from task slot 1 the game keeps drawing. Meanwhile the old archive is gone, so
   nothing may touch it: the input is held, Leon's motion table points at the holster pose and the
   neck turn motion is off. */
#define HOLSTER_FRAMES 5       /* blend into the holster pose before the weapon goes away */
#define DRAW_FRAMES    6       /* blend from the holster pose into the new weapon's idle */
extern unsigned char mot_holster[];
static volatile int swap_busy;
static cItem* swap_item;
static void* safe_tbl[0x100];
int SwapBusy(void) { return swap_busy; }

/* While no weapon exists, the player code still asks it things through its vtable every frame
   (e.g. 0x80144CD4: Wep->m_pWep->vtbl[0x98]) and m_pWep is NULL: stand a dummy object in its
   place whose every virtual returns 0. Vtable entries: s16 this-delta, s16 pad, function. */
static int DummyRet0(void) { return 0; }
static u32 dummy_vtbl[2 * 0x80];
static u32 dummy_wep[0x100];
static void DummyWep(u8* pl, int on)
{
    u8* wep = *(u8**)(pl + 0x788);
    int i;
    if (!wep) return;
    if (on) {
        for (i = 0; i < 0x80; i++) { dummy_vtbl[2 * i] = 0; dummy_vtbl[2 * i + 1] = (u32)DummyRet0; }
        for (i = 0; i < 0x100; i++) dummy_wep[i] = 0;
        dummy_wep[2] = (u32)dummy_vtbl;
        *(void**)(wep + 0x34) = dummy_wep;           /* weaponRelease left it NULL */
    } else if (*(void**)(wep + 0x34) == dummy_wep) {
        *(void**)(wep + 0x34) = 0;
    }
}

/* swap timing box (hud.c): off in normal builds */
int SwapDiag(int i) { (void)i; return 0; }
void SwapDiagTick(void) { }

int PrefetchStart(u32 id);
int PrefetchPoll(void);
void PrefetchEnd(void);
int PrefetchBusy(void);
int PrefetchHits(void);

/* States the swap may run in: footwork (0) gets the holster gesture; walking (1), back (2),
   running (3) and aiming (6, the weapon's own routine) swap without stopping Leon. */
static int SwapState(u8* pl)
{
    if (!pl || pl[0xFC] != 0 || G8(0x4FC4) == 1) return -1;
    if (pl[0xFD] <= 3 || pl[0xFD] == 6) return pl[0xFD];
    return -1;
}

static volatile int swap_lock;                       /* gesture: Leon holds still meanwhile */
int SwapLock(void) { return swap_lock; }

/* release + load + init in one go. With the archive prefetched the load is a few ms and no frame
   ever runs without a weapon; the safety nets stay for the disc fallback. */
static void DoSwap(u8* pl, cItem* it)
{
    void** tbl;
    u8* neck;
    u32 id;
    int no, type, lv, i;
    if (!ItemMgr_arm(ItemMgr, it)) return;
    id = *(u16*)((u8*)ItemMgr + 0x10);
    no = WeaponId2WeaponNo(id);
    type = WeaponId2WeaponType(id);
    lv = it->bullet >> 13;
    if (G8(0x4FBC) == no && G8(0x4FBD) == type && G8(0x4FBE) == lv) return;
    SndBlkStop(2);
    tbl = *(void***)(pl + 0x424);                    /* m_MotTbl: weapon archive motions */
    for (i = 0; i < 0x100; i++) safe_tbl[i] = mot_holster;
    *(void***)(pl + 0x424) = safe_tbl;
    *(void**)(pl + 0x42C) = 0;                       /* m_SubMot (neck / upper layer) */
    *(void**)(pl + 0x2A8) = 0;                       /* pMotionB */
    neck = *(u8**)(pl + 0x78C);
    if (neck) { *(void**)(neck + 0x14) = 0; *(void**)(neck + 0x18) = 0; }  /* cPlNeck::clear */
    weaponRelease(pl);
    DummyWep(pl, 1);
    weaponLoad(pl, no, type);                        /* served from the prefetched copy */
    G8(0x4FBE) = lv;
    *(void***)(pl + 0x424) = tbl;
    DummyWep(pl, 0);
    weaponInit(pl);
}

/* The swap runs from the main loop (ModFrame, after the tasks), one step per frame: no task slot
   is needed (B32 used slot 1, sometimes busy -> fallback with the full disc stall). DoSwap then
   runs in one go: the load is answered from the prefetched copy, so nothing ever sleeps. */
static int sw_on, sw_vi, sw_gesture, sw_cleanup;
/* aiming: the new weapon's ready step 0 resets the aim (Wep->pitch from the camera, the aim yaw
   m_Fwork0 = 0); put back where Leon was aiming for a few frames after it ran */
static int aim_restore;
static f32 aim_pitch, aim_yaw, aim_m3r[2];
#define M3R ((f32*)0x8021D970)                       /* cDelayF m3r: aim pitch blend; the shoulder
                                                        camera's pitch follows it (getPitch) */
static int aim_guard;
#define HOLSTER_VI (2 * HOLSTER_FRAMES - 2)          /* earliest swap: the hand is almost there */

void SwapFrame(void)
{
    u8* pl;
    int pr, st;
    if (sw_cleanup && PrefetchPoll() != 0) { PrefetchEnd(); sw_cleanup = 0; }
    if (aim_restore) {
        pl = pPL;
        if (pl && pl[0xFD] == 6 && *(u8**)(pl + 0x788)) {
            *(f32*)(*(u8**)(pl + 0x788) + 0x28) = aim_pitch;
            *(f32*)(pl + 0x400) = aim_yaw;
            M3R[0] = aim_m3r[0]; M3R[1] = aim_m3r[1];
            if (pl[0xFE] != 0) aim_restore--;            /* ready step: keep; then 4 more */
            if (--aim_guard <= 0) aim_restore = 0;
        } else aim_restore = 0;
    }
    if (!sw_on) return;
    sw_vi += GetSystemVcnt();
    if (!modvars[VB_GAMEPLAY]) return;               /* paused / menu: wait */
    pr = PrefetchPoll();
    if (pr == 0 && sw_vi < 180) return;              /* archive still coming (3 s at most) */
    if (sw_gesture && sw_vi < HOLSTER_VI) return;
    pl = pPL;
    st = SwapState(pl);
    if (!sw_gesture && st < 0) {                     /* mid-action: wait a little, else give up */
        if (sw_vi < 240) return;
        pl = 0;
    }
    if (pl) {
        if (st == 6 && *(u8**)(pl + 0x788)) {
            aim_pitch = *(f32*)(*(u8**)(pl + 0x788) + 0x28);
            aim_yaw = *(f32*)(pl + 0x400);
            aim_m3r[0] = M3R[0]; aim_m3r[1] = M3R[1];
        }
        DoSwap(pl, swap_item);
        st = SwapState(pl);
        if (sw_gesture || st == 0) {                     /* footwork: restart the idle, blended */
            pl[0x4FD] = DRAW_FRAMES;                     /* m_Hokan */
            pl[0x4FC] = 0;                               /* m_Frame */
            pl[0xFF] |= 1;
            pl[0xFE] = 0;
        } else if (st > 0) {
            /* the playing motion pointed into the old archive: a safe motion until the routine
               sets its own again (walk/run blend in; aiming raises the new weapon) */
            MotionSetCore(pl, pl + 0x1D8, mot_holster, 0, 0, 5, 0);
            pl[0xFE] = 0;
            pl[0xFF] = 0;          /* r_no_3: the handgun's ready step table has 4 entries */
            if (st == 6) { aim_restore = 4; aim_guard = 40; }
        }
    }
    sw_on = 0;
    swap_lock = 0;
    swap_busy = 0;
    if (PrefetchPoll() == 0) sw_cleanup = 1; else PrefetchEnd();
}

static void SwapStart(cItem* it)
{
    u8* pl = pPL;
    int st = SwapState(pl);
    if (st < 0 || sw_on || sw_cleanup) return;
    swap_item = it;
    swap_busy = 1;
    sw_on = 1;
    sw_vi = 0;
    sw_gesture = swap_lock = st == 0;
    PrefetchStart(it->id);                               /* old weapon intact meanwhile */
    if (st == 0) {
        MotionSetCore(pl, pl + 0x1D8, mot_holster, 0, HOLSTER_FRAMES, 5, 0);
        pl[0xFE] = 1;                                    /* footwork, motion already set */
    }
}

static void Use(int dir)
{
    u16 v = Slots()[dir];
    cItem* it;
    if (!v) return;
    it = FindItem(v - 1);
    if (!it) { SndCall(0, 0xA, 0, 0, 0, 0); return; }   /* no longer carried */
    if (it == IM_PWEP(ItemMgr)) return;
    if (!CanSwap() || swap_busy) return;
    SndCall(0, 0xE, 0, 0, 0, 0);
    SwapStart(it);
    ShowPanel();
}

static void Assign(int dir)
{
    cItem* w = IM_PWEP(ItemMgr);
    u16* s = Slots();
    int i;
    if (!w) return;
    if (s[dir] == w->id + 1) { s[dir] = 0; SndCall(0, 0xA, 0, 0, 0, 0); return; }
    for (i = 0; i < 4; i++) if (s[i] == w->id + 1) s[i] = 0;   /* one slot per weapon */
    s[dir] = w->id + 1;
    SndCall(0, 0xF, 0, 0, 0, 0);
}

static void ShowPanel(void)
{
    u16* s = Slots();
    cItem* w = swap_busy ? swap_item : IM_PWEP(ItemMgr);   /* a pending swap shows its target */
    int i, eq = -1, miss = 0;
    for (i = 0; i < 4; i++) {
        if (!s[i]) continue;
        if (w && s[i] == w->id + 1) eq = i;
        if (!FindItem(s[i] - 1)) miss |= 1 << i;
    }
    PanelShow(eq, miss);
}

/* Case (puzzle screen): L1 (Z) + a D-pad direction assigns the weapon under the cursor to it;
   the same weapon again clears the slot. active_pzl is the live pzlPlayer (hooks on init/quit). */
void* active_pzl;
int CaseActive(void)
{
    u8* pl = (u8*)active_pzl;
    if (!pl || *(void**)(SubScreenWk + 0x2B0) != pl) return 0;
    if (!(*(u32*)(pG + 0x5018) & (0x80000000u >> 13))) return 0;     /* STA_SUB_SCRN */
    return *(u8**)(pl + 0x30) != 0;
}

void CaseAssign(int dir)
{
    u8* pl = (u8*)active_pzl;
    u8* board; void* piece; cItem* it; ITEM_INFO info;
    u16* s = Slots();
    int i;
    board = *(u8**)(pl + 0x30);
    piece = pzlBoard_getPiece(board, *(s8*)(board + 0x3C), *(s8*)(board + 0x3D));
    if (!piece) return;
    it = *(cItem**)((u8*)piece + 0x24);
    if (!it) return;
    itemInfo(it->id, &info);
    if (info.type != 1 && info.type != 3) { SndCall(0, 0xA, 0, 0, 0, 0); return; }
    if (s[dir] == it->id + 1) { s[dir] = 0; SndCall(0, 0xA, 0, 0, 0, 0); return; }
    for (i = 0; i < 4; i++) if (s[i] == it->id + 1) s[i] = 0;
    s[dir] = it->id + 1;
    SndCall(0, 0xF, 0, 0, 0, 0);
}

static void AutoSlot(void)
{
    cItem* w = IM_PWEP(ItemMgr);
    u16* s = Slots();
    int i;
    if (!w) return;
    for (i = 0; i < 4; i++) if (s[i] == w->id + 1) return;
    for (i = 0; i < 4; i++) if (!s[i]) { s[i] = w->id + 1; return; }
}

/* Called from PadRemap in gameplay with the raw pad; returns the D-pad bits to drop from the
   game's input (the ones that were real D-pad presses). */
u32 WeaponPad(u32 in, int sx, int sy)
{
    static const u32 bit[4] = { 8, 2, 4, 1 };          /* up, right, down, left */
    u32 merged = 0, real, drop = 0;
    int dir = -1, i;

    if (sy >= STICK_ON) merged |= 8;
    if (sy <= -STICK_ON) merged |= 4;
    if (sx >= STICK_ON) merged |= 2;
    if (sx <= -STICK_ON) merged |= 1;
    real = in & 0xF & ~merged;
    for (i = 0; i < 4; i++) if (real & bit[i]) { dir = i; break; }
    drop = real;

    AutoSlot();
    if (dir >= 0) ShowPanel();                           /* any D-pad use shows the panel */
    if (dir != held_dir) {                               /* press / release / change */
        if (held_dir >= 0 && !held_done) Use(held_dir); /* released before the hold time: tap */
        held_dir = dir; held_t = 0; held_done = 0;
    } else if (dir >= 0 && !held_done) {
        held_t += GetSystemVcnt();
        if (held_t >= HOLD_VIS) { Assign(dir); held_done = 1; ShowPanel(); }
    }
    return drop;
}

void WeaponPadIdle(void) { held_dir = -1; held_done = 0; }
