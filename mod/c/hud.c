/* Quick-weapon panel (remake style): a cross of four slots with weapon silhouettes, shown for a
 * moment after any D-pad use. Drawn with plain GX calls from an ordering-table callback in the
 * screen layer (OT 0x15: after the fog is switched off, before the game's messages). */
#include "game.h"

extern const u8 sil_tex[];
extern const u16 sil_ids[];
extern const int sil_count;

#define PANEL_VIS  150           /* VIs the panel stays (2.5 s at 60 Hz) */
#define PANEL_FADE 24            /* VIs of fade out */
#define CX 548.0f                /* panel centre, virtual 640 x 480 screen */
#define CY 300.0f
#define SW 66.0f                 /* slot size */
#define SH 36.0f
#define GAP 2.0f

static int panel_t;
static int panel_equipped = -1;  /* slot of the weapon in hand, -1 none */
static int panel_missing;        /* bit per slot: weapon no longer carried */

void PanelShow(int equipped, int missing) { panel_t = PANEL_VIS; panel_equipped = equipped; panel_missing = missing; }

static const u8* SilFor(u32 id)
{
    int i;
    for (i = 0; i < sil_count; i++) if (sil_ids[i] == id) return sil_tex + i * 1024;
    return 0;
}

static void Quad(f32 x, f32 y, f32 w, f32 h, u32 rgba, int tex)
{
    GXBegin(0x80, 0, 4);
    GXFIFO_F32 = x;     GXFIFO_F32 = y;     GXFIFO_F32 = 0.0f; GXFIFO_U32 = rgba; if (tex) { GXFIFO_F32 = 0.0f; GXFIFO_F32 = 0.0f; }
    GXFIFO_F32 = x + w; GXFIFO_F32 = y;     GXFIFO_F32 = 0.0f; GXFIFO_U32 = rgba; if (tex) { GXFIFO_F32 = 1.0f; GXFIFO_F32 = 0.0f; }
    GXFIFO_F32 = x + w; GXFIFO_F32 = y + h; GXFIFO_F32 = 0.0f; GXFIFO_U32 = rgba; if (tex) { GXFIFO_F32 = 1.0f; GXFIFO_F32 = 1.0f; }
    GXFIFO_F32 = x;     GXFIFO_F32 = y + h; GXFIFO_F32 = 0.0f; GXFIFO_U32 = rgba; if (tex) { GXFIFO_F32 = 0.0f; GXFIFO_F32 = 1.0f; }
}

static void ModeFlat(void)
{
    GXClearVtxDesc();
    GXSetVtxDesc(9, 1); GXSetVtxDesc(11, 1);
    GXSetVtxAttrFmt(0, 9, 1, 4, 0); GXSetVtxAttrFmt(0, 11, 1, 5, 0);
    GXSetNumTexGens(0);
    GXSetTevOrder(0, 0xFF, 0xFF, 4);
    GXSetTevOp(0, 4);                                  /* GX_PASSCLR */
}

static void ModeTex(const u8* img)
{
    GXTexObj t;
    GXInitTexObj(&t, img, 64, 32, 0 /* I4 */, 0, 0, 0);
    GXInitTexObjLOD(&t, 1, 1, 0.0f, 0.0f, 0.0f, 0, 0, 0);
    GXLoadTexObj(&t, 0);
    GXClearVtxDesc();
    GXSetVtxDesc(9, 1); GXSetVtxDesc(11, 1); GXSetVtxDesc(13, 1);
    GXSetVtxAttrFmt(0, 9, 1, 4, 0); GXSetVtxAttrFmt(0, 11, 1, 5, 0); GXSetVtxAttrFmt(0, 13, 1, 4, 0);
    GXSetNumTexGens(1);
    GXSetTexCoordGen2(0, 1, 4, 60, 0, 125);
    GXSetTevOrder(0, 0, 0, 4);
    GXSetTevOp(0, 0);                                  /* GX_MODULATE */
}

static u32 RGBA(u32 rgb, int a) { return (rgb << 8) | (u32)(a & 0xFF); }

static void PanelDraw(void* unused)
{
    static const f32 ox[4] = { 0.0f, 1.0f, 0.0f, -1.0f }, oy[4] = { -1.0f, 0.0f, 1.0f, 0.0f };
    Mtx44 p; Mtx m;
    u16* s = (u16*)(pG + MOD_SLOT_OFS);
    int i, a = 255;
    (void)unused;
    if (panel_t < PANEL_FADE) a = panel_t * 255 / PANEL_FADE;

    GXSetAlphaCompare(7, 0, 1, 7, 0);
    GXSetColorUpdate(1); GXSetAlphaUpdate(0); GXSetCullMode(0);
    C_MTXOrtho(p, 0.0f, 480.0f, 0.0f, 640.0f, 0.0f, -100.0f);
    GXSetProjection(p, 1);
    PSMTXIdentity(m); GXLoadPosMtxImm(m, 0); GXSetCurrentMtx(0);
    GXSetBlendMode(1, 4, 5, 0);
    GXSetNumTevStages(1);
    GXSetNumChans(1);
    GXSetChanCtrl(0, 0, 0, 1, 0, 0, 2);                 /* no lighting: colour = vertex colour */
    GXSetChanCtrl(2, 0, 0, 1, 0, 0, 2);
    GXSetZMode(0, 7, 0);

    for (i = 0; i < 4; i++) {
        f32 x = CX + ox[i] * (SW + GAP) - SW * 0.5f, y = CY + oy[i] * (SH + GAP) - SH * 0.5f;
        const u8* img = s[i] ? SilFor(s[i] - 1) : 0;
        u32 bg = i == panel_equipped ? 0xC8A040 : 0x101010;
        ModeFlat();
        Quad(x - 1.0f, y - 1.0f, SW + 2.0f, SH + 2.0f, RGBA(i == panel_equipped ? 0xFFE080 : 0x808080, a * 3 / 5), 0);
        Quad(x, y, SW, SH, RGBA(bg, a * 3 / 4), 0);
        if (s[i] && !img) Quad(x + 18.0f, y + 10.0f, SW - 36.0f, SH - 20.0f, RGBA(0xE0E0E0, a), 0);   /* no silhouette: a bar */
        if (img) {
            ModeTex(img);
            Quad(x + 1.0f, y + 2.0f, SW - 2.0f, SH - 4.0f,
                 RGBA((panel_missing >> i) & 1 ? 0xC04040 : (i == panel_equipped ? 0x181818 : 0xF0F0F0), a), 1);
        }
    }
    GXSetZMode(1, 3, 1);
    GXSetAlphaUpdate(1);
}

static int draw_now;

/* Main loop, after the task scheduler: decides whether the panel is drawn this frame. */
void ModFrame(void)
{
    draw_now = 0;
    if (panel_t <= 0) return;
    panel_t -= GetSystemVcnt();
    if (panel_t <= 0) return;
    if (!modvars[VB_GAMEPLAY]) return;                       /* only while Leon is in control */
    if (!(*(u32*)(pG + 88) & 0x10000)) return;              /* HUD hidden */
    draw_now = 1;
}

/* Main loop, right after the messages are drawn (direct GX, like cMes.Trans): the panel. */
void ModDraw(void)
{
    static const u32 black = 0;
    if (!draw_now) return;
    draw_now = 0;
    GXSetFog(0, 0.0f, 1.0f, 0.1f, 1.0f, &black);            /* messages leave the room fog on */
    PanelDraw(0);
}
