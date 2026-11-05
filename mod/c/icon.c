/* 3D icon of a quick pick-up: the item's own floor model, taken off the floor and drawn through
 * the item camera (the examine screen's: models flagged 0x4000 are drawn in that pass) with an
 * off-centre, scaled projection, so it shows small and spinning at the bottom left next to the
 * notice. Set up like ItemExamine::init, spun like ItemExamine::move; destroyed when it ends. */
#include "game.h"

#define ICON_NDC_X (-0.84f)      /* icon centre, normalised screen coordinates */
#define ICON_NDC_Y (-0.46f)
#define ICON_SCALE 0.16f         /* relative to a model filling the screen height */

#define M8(m,o)   (*(u8*)((u8*)(m)+(o)))
#define M32(m,o)  (*(u32*)((u8*)(m)+(o)))
#define MF(m,o)   (*(f32*)((u8*)(m)+(o)))
#define MP(m,o)   (*(u8**)((u8*)(m)+(o)))

static u8* icon;                 /* the model, 0 = none */
static int icon_kind;            /* 0 ObjMgr, 1 EmMgr (how to destroy it) */
static int icon_t;
static f32 icon_len;

static void MatUpdate(u8* m)     /* virtual cModel::matUpdate: vtable at +8, entry {s16 delta @32, fn @36} */
{
    u8* vt = MP(m, 8);
    void (*fn)(void*) = *(void (**)(void*))(vt + 36);
    fn(m + *(s16*)(vt + 32));
}

static void IconKill(void)
{
    if (!icon) return;
    if (icon_kind == 0) ObjMgr_destroy(ObjMgr, icon); else EmMgr_destroy(EmMgr, icon);
    icon = 0;
}

/* Called by QuickItem instead of destroying the floor model. Returns 1 when the model is now the icon. */
int IconStart(u8* m, int kind, u32 id, int vis)
{
    u8 *pl, *head, *parts, *info;
    f32 s;
    IconKill();
    if (!m || (kind != 0 && kind != 1)) return 0;
    M32(m, 0) |= 0x4000;                                /* drawn by the item camera pass */
    pl = MP(m, 244);                                    /* root parts */
    MP(pl, 108) = m;
    head = *(u8**)MP(MP(m, 348), 12);                   /* pModelInfo->model_addr->pHead */
    MF(pl, 148) = MF(head, 4); MF(pl, 152) = MF(head, 8); MF(pl, 156) = MF(head, 12);
    MF(pl, 160) = MF(pl, 164) = MF(pl, 168) = 0.0f;
    M8(m, 303) = 6;                                     /* ot type */
    info = (u8*)examInfo(id, 0);
    s = 3.1415927f / 180.0f;
    MF(m, 160) = info ? MF(info, 4) * s : 0.0f;
    MF(m, 164) = info ? MF(info, 8) * s : 0.0f;
    MF(m, 168) = info ? MF(info, 12) * s : 0.0f;
    MF(m, 148) = MF(m, 152) = MF(m, 156) = 0.0f;
    MatUpdate(m);
    M32(m, 0) &= ~0x20u;
    parts = (u8*)getPartsPtr(m, 0);
    if (parts) { MF(m, 148) = -MF(parts, 112); MF(m, 152) = -MF(parts, 116); MF(m, 156) = -MF(parts, 120); }
    MatUpdate(m);
    partsMatCalc(m);
    partsWorldCalc(m);
    {   /* model size: pModelInfo->bound.size (0x38 + 0x18) */
        u8* mi = MP(m, 348);
        f32 x = MF(mi, 0x50), y = MF(mi, 0x54), z = MF(mi, 0x58);
        icon_len = SQRTF(x * x + y * y + z * z);
        if (info && MF(info, 0x10) > 0.0f) icon_len /= MF(info, 0x10);
        if (icon_len < 1.0f) icon_len = 1.0f;
    }
    icon = m; icon_kind = kind; icon_t = vis;
    return 1;
}

/* Every frame after the task scheduler: spin the model and aim the item camera at it. */
void IconFrame(void)
{
    Mtx r; Vec axis = { 0.0f, 1.0f, 0.0f }, zero = { 0.0f, 0.0f, 0.0f };
    f32* P; f32 d;
    if (!icon) return;
    icon_t -= GetSystemVcnt();
    if (icon_t <= 0) { IconKill(); return; }
    PSMTXIdentity(r);
    MtxRotAxisPosRad(r, &axis, &zero, 3.1415927f / 60.0f);
    PSMTXConcat(r, (f32 (*)[4])(icon + 12), (f32 (*)[4])(icon + 12));
    partsMatCalc(icon);
    partsWorldCalc(icon);

    d = icon_len * 2.2f;
    *(Vec*)(itemCamera + 0xA4) = (Vec){ 0.0f, 0.0f, d };
    *(Vec*)(itemCamera + 0xB0) = zero;
    *(Vec*)(itemCamera + 0xC4) = axis;
    MF(itemCamera, 0xC0) = 30.0f;
    P = (f32*)(itemCamera + 0x64);
    C_MTXPerspective((f32 (*)[4])P, 30.0f, 1.3333334f, ZNEAR, ZFAR);
    P[0] *= ICON_SCALE;  P[2] -= ICON_NDC_X;            /* row 0: scale, then shift in NDC */
    P[5] *= ICON_SCALE;  P[6] -= ICON_NDC_Y;            /* row 1 */
    P[10] = 0.0f; P[11] = -0.7f * d;                    /* depth: always in front of the scene */
    C_MTXLookAt((f32 (*)[4])(itemCamera + 0x30), (Vec*)(itemCamera + 0xA4), (Vec*)(itemCamera + 0xC4), (Vec*)(itemCamera + 0xB0));
    LightMgr_setModel2(LightMgr, icon);
}
