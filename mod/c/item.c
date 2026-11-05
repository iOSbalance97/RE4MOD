/* Quick item pick-up: after the first time an item id is presented, ammo, recovery items,
 * treasures, money and plain items go straight in with a non-pausing message, no zoom. */
#include "game.h"

#define W8(w,o)  (*(u8*)((u8*)(w)+(o)))
#define W16(w,o) (*(u16*)((u8*)(w)+(o)))
#define W32(w,o) (*(u32*)((u8*)(w)+(o)))

#define MES_X   32       /* left edge of the notice (message screen units) */
#define MES_VIS 210      /* notice time in VIs: 3.5 s at 60 Hz */
static u32 mes_attr;
static int mes_left;

/* Run-time item areas (enemy drops: be_flg & 4) are freed and unlinked from the scenario list
   (pS->ot[15]) at the start of the next frame: QuickItem runs from inside the loop that walks
   that list, and unlinking the current entry there breaks the walk (crash in DelPrim). */
#define FREE_MAX 8
static u8* free_q[FREE_MAX];
static int free_n;

static void FreeTick(void)
{
    while (free_n > 0) {
        u8* w = free_q[--free_n];
        Mem_free(w);
        DelPrim(pS + 140, w);
    }
}

/* Leon's waist twist (walk-mode strafing, set by the move hook) must not carry over into other
   actions (ladders, events, damage): reset it once when leaving the routines that drive it. */
static int prev_ctrl;
static void WaistTick(void)
{
    u8* pl = *(u8**)0x802B8344;          /* pPL */
    int r1, ctrl;
    u8* w;
    if (!pl) { prev_ctrl = 0; return; }
    r1 = pl[0xFD];
    ctrl = pl[0xFC] == 0 && (r1 <= 3 || r1 == 6 || r1 == 0xB);
    if (prev_ctrl && !ctrl) {
        w = *(u8**)(pl + 0x790);
        if (w) *(f32*)(w + 4) = 0.0f;
    }
    prev_ctrl = ctrl;
}

/* Called every frame from PadRemap: removes the notice when its time is up, unless the slot
   has been taken by another message in the meantime. */
void ModMesTick(void)
{
    FreeTick();
    WaistTick();
    if (mes_left <= 0) return;
    mes_left -= GetSystemVcnt();
    if (mes_left > 0) return;
    if (*(u32*)(cMes + 4 + 0x80) == mes_attr) MesDelete(cMes, 0);
}

int QuickItem(u8* w)
{
    u8* it = w + 92;
    u32 id = W16(it, 28), num = W16(it, 32);
    u8* seen;
    ITEM_INFO info;
    int put, y, money = 0, mes = 0x15;
    u32 attr = 0x11;      /* core text, keep Stop_flg */
    void* model;

    if (id >= 512) return 0;
    seen = pG + MOD_SEEN_OFS;
    if (!(seen[id >> 3] & (1 << (id & 7)))) {      /* first time: the full presentation */
        seen[id >> 3] |= 1 << (id & 7);
        return 0;
    }
    itemInfo(id, &info);
    switch (info.type) {
    case 2: case 6:                                  /* ammo, recovery: into the case */
        put = PutInCase(id, num, (s8)SubScreenWk[686]);
        if (put != 1) return 0;                      /* no room: original flow opens the case */
        SndCall(0, 0x13, 0, 0, 0, 0);
        break;
    case 0: case 4: case 5: case 0xC:
        ItemMgr_get(ItemMgr, id, num);
        SndCall(0, 0x13, 0, 0, 0, 0);
        break;
    case 8:
        if (id == 0x73 || id == 0x75) return 0;
        money = (s32)G32(0x4FA4);
        ItemMgr_get(ItemMgr, id, num);
        if (money < (s32)G32(0x4FA4)) MesSetNumber(cMes + 4, (s32)G32(0x4FA4) - money, 0);
        mes = 0x14; attr = 0x10000011;
        SndCall(0, 0x10, 0, 0, 0, 0);
        break;
    default:
        return 0;                                    /* weapons, parts, files, special: as before */
    }
    y = 297 - (s8)cMes[4 + 119] - (s8)cMes[4 + 25];
    /* 0x80 game keeps running, 0x40 whole text at once, 0x20000 left aligned, 0x01000000 stays
       on screen after its end: ModMesTick removes it after MES_VIS */
    attr |= 0x80 | 0x40 | 0x20000 | 0x01000000;
    MesSet(cMes, mes, MES_X, y, attr, 0, 0, 4);
    if (mes == 0x15) *(u16*)(cMes + 30) = id;        /* item name */
    mes_attr = attr; mes_left = MES_VIS;

    model = (void*)W32(w, 104);
    sceAtItemFlgOn(it);
    SceAtSetEnable(W8(w, 54), 0);
    EffectEspDelete(1, 59, model, 0);
    EffectEspgenDelete(1, 59, model, 0);
    EffectEfmDelete(1, 59, model, 0);
    if (model) {
        u8 kind = W8(model, 302);
        if (kind == 0) { ObjMgr_destroy(ObjMgr, model); W32(w, 104) = 0; }
        else if (kind == 1) { EmMgr_destroy(EmMgr, model); W32(w, 104) = 0; }
    }
    if ((W8(w, 132) & 8) && (s16)W16(w, 134) >= 0)
        memclr_asm(pG + 29428 + ((s16)W16(w, 134) << 4), 16);
    if (W8(w, 52) & 4) {
        if (free_n < FREE_MAX) free_q[free_n++] = w;   /* freed next frame (FreeTick) */
    }
    return 1;
}
