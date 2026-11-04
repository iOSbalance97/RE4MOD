/* Quick item pick-up: after the first time an item id is presented, ammo, recovery items,
 * treasures, money and plain items go straight in with a non-pausing message, no zoom. */
#include "game.h"

#define W8(w,o)  (*(u8*)((u8*)(w)+(o)))
#define W16(w,o) (*(u16*)((u8*)(w)+(o)))
#define W32(w,o) (*(u32*)((u8*)(w)+(o)))

int QuickItem(u8* w)
{
    u8* it = w + 92;
    u32 id = W16(it, 28), num = W16(it, 32);
    u8* seen;
    ITEM_INFO info;
    int put, y, money = 0, mes = 0x15;
    u32 attr = 0x11;
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
    MesSet(cMes, mes, 100, y, attr | 0x80, 0, 0, 4);  /* 0x80: the game keeps running */
    if (mes == 0x15) *(u16*)(cMes + 30) = id;        /* item name */

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
        Mem_free(w);
        DelPrim(pS + 140, w);
    }
    return 1;
}
