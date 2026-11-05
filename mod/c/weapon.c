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
    return pl[0xFC] == 0 && pl[0xFD] <= 3;
}

static void Equip(cItem* it)
{
    void* pl = pPL;
    u32 id;
    int no, type, lv;
    if (!ItemMgr_arm(ItemMgr, it)) return;
    id = *(u16*)((u8*)ItemMgr + 0x10);
    no = WeaponId2WeaponNo(id);
    type = WeaponId2WeaponType(id);
    lv = it->bullet >> 13;
    if (G8(0x4FBC) == no && G8(0x4FBD) == type && G8(0x4FBE) == lv) return;
    SndBlkStop(2);
    weaponRelease(pl);
    weaponLoad(pl, no, type);
    G8(0x4FBE) = lv;
    weaponInit(pl);
}

static void Use(int dir)
{
    u16 v = Slots()[dir];
    cItem* it;
    if (!v) return;
    it = FindItem(v - 1);
    if (!it) { SndCall(0, 0xA, 0, 0, 0, 0); return; }   /* no longer carried */
    if (it == IM_PWEP(ItemMgr)) return;
    if (!CanSwap()) return;
    SndCall(0, 0xE, 0, 0, 0, 0);
    Equip(it);
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
    cItem* w = IM_PWEP(ItemMgr);
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
