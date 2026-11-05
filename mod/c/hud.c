/* Quick-weapon panel (remake style): a cross of four slots with weapon silhouettes, shown for a
 * moment after any D-pad use. Drawn with plain GX calls from an ordering-table callback in the
 * screen layer (OT 0x15: after the fog is switched off, before the game's messages). */
#include "game.h"

extern const u8 sil_tex[];
extern const u16 sil_ids[];
extern const int sil_count;

#define PANEL_VIS  75            /* VIs the panel stays (1.25 s at 60 Hz) */
#define PANEL_FADE 18            /* VIs of fade out */
#define CX 320.0f                /* panel centre, virtual 640 x 480 screen: middle */
#define CY 250.0f
#define SW 54.0f                 /* slot size */
#define SH 28.0f
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

static void Quad(f32 x, f32 y, f32 w, f32 h, u32 rgba, int tex);
static void Frame(f32 x, f32 y, f32 w, f32 h, u32 rgba)    /* 1-unit outline */
{
    Quad(x - 1.0f, y - 1.0f, w + 2.0f, 1.0f, rgba, 0);
    Quad(x - 1.0f, y + h, w + 2.0f, 1.0f, rgba, 0);
    Quad(x - 1.0f, y, 1.0f, h, rgba, 0);
    Quad(x + w, y, 1.0f, h, rgba, 0);
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
        int eq = i == panel_equipped, miss = (panel_missing >> i) & 1;
        ModeFlat();
        /* equipped: lighter glass box with a thin white frame and a bright silhouette;
           the rest: dark glass, faint frame, dimmed silhouette; red tint = not carried */
        Quad(x, y, SW, SH, RGBA(eq ? 0x404040 : 0x101010, eq ? a / 2 : a * 2 / 5), 0);
        Frame(x, y, SW, SH, RGBA(eq ? 0xFFFFFF : 0x909090, eq ? a * 3 / 4 : a / 4));
        if (s[i] && !img) Quad(x + 16.0f, y + 9.0f, SW - 32.0f, SH - 18.0f, RGBA(0xE0E0E0, a * 3 / 5), 0);
        if (img) {
            ModeTex(img);
            Quad(x + 1.0f, y + 2.0f, SW - 2.0f, SH - 4.0f,
                 RGBA(miss ? 0xD05050 : (eq ? 0xFFFFFF : 0xB0B0B0), eq ? a : a * 3 / 5), 1);
        }
    }
    GXSetZMode(1, 3, 1);
    GXSetAlphaUpdate(1);
}

static int draw_now;
int SwapDiag(int i);
static f32 vp_save[6];

/* Full-screen viewport for the HUD (the game leaves a reduced one set at this point); the
   previous one is put back afterwards. Screen size: the game's Screen.width / height. */
static void ViewportOn(void)
{
    GXGetViewportv(vp_save);
    GXSetViewport(0.0f, 0.0f, *(f32*)0x8028DB44, *(f32*)0x8028DB48, 0.0f, 1.0f);
}
static void ViewportOff(void)
{
    GXSetViewport(vp_save[0], vp_save[1], vp_save[2], vp_save[3], vp_save[4], vp_save[5]);
}
static int dbg_frame, dbg_play, dbg_hud, dbg_vis;   /* DIAG: what ModFrame saw */
#define DIAG 0

/* Main loop, after the task scheduler: decides whether the panel is drawn this frame. */
void IconFrame(void);
void ModFrame(void)
{
    IconFrame();
    draw_now = 0;
    if (SwapDiag(-1) > 0 && modvars[VB_GAMEPLAY]) draw_now = 1;   /* swap timing box (test) */
    dbg_frame = 1; dbg_play = modvars[VB_GAMEPLAY] != 0; dbg_hud = (*(u32*)(pG + 88) & 0x10000) != 0; dbg_vis = panel_t > 0;
    if (panel_t <= 0) return;
    panel_t -= GetSystemVcnt();
    if (panel_t <= 0) { panel_t = 0; return; }
    if (!modvars[VB_GAMEPLAY]) return;                       /* only while Leon is in control */
    draw_now = 1;
}

/* Main loop, right after the messages are drawn (direct GX, like cMes.Trans): the panel. */
/* swap timing numbers (weapon.c), seven-segment digits drawn with quads, top left */
int SwapDiag(int i);
static void Digit(f32 x, f32 y, int d, u32 c)
{
    static const u8 seg[10] = { 0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F };
    const f32 w = 10.0f, h = 9.0f, t = 2.0f;
    u8 m = seg[d];
    if (m & 0x01) Quad(x, y, w, t, c, 0);
    if (m & 0x02) Quad(x + w - t, y, t, h, c, 0);
    if (m & 0x04) Quad(x + w - t, y + h, t, h, c, 0);
    if (m & 0x08) Quad(x, y + 2 * h - t, w, t, c, 0);
    if (m & 0x10) Quad(x, y + h, t, h, c, 0);
    if (m & 0x20) Quad(x, y, t, h, c, 0);
    if (m & 0x40) Quad(x, y + h - t / 2, w, t, c, 0);
}
static void DiagDraw(void)
{
    Mtx44 p; Mtx m; int i, k, n, nd; char buf[8];
    if (SwapDiag(-1) <= 0) return;
    GXSetAlphaCompare(7, 0, 1, 7, 0); GXSetColorUpdate(1); GXSetAlphaUpdate(0); GXSetCullMode(0);
    C_MTXOrtho(p, 0.0f, 480.0f, 0.0f, 640.0f, 0.0f, -100.0f); GXSetProjection(p, 1);
    PSMTXIdentity(m); GXLoadPosMtxImm(m, 0); GXSetCurrentMtx(0);
    GXSetBlendMode(1, 4, 5, 0); GXSetNumTevStages(1); GXSetNumChans(1);
    GXSetChanCtrl(0, 0, 0, 1, 0, 0, 2); GXSetChanCtrl(2, 0, 0, 1, 0, 0, 2); GXSetZMode(0, 7, 0);
    ModeFlat();
    Quad(36.0f, 36.0f, 4 * 66.0f, 28.0f, 0x000000A0, 0);
    for (i = 0; i < 4; i++) {
        n = SwapDiag(i); if (n < 0) n = 0; if (n > 9999) n = 9999;
        nd = 0; do { buf[nd++] = (char)(n % 10); n /= 10; } while (n);
        for (k = 0; k < nd; k++) Digit(40.0f + 66.0f * i + 13.0f * (nd - 1 - k), 41.0f, buf[k], i == 0 ? 0xFFE040FF : 0xFFFFFFFF);
    }
    GXSetZMode(1, 3, 1); GXSetAlphaUpdate(1);
}

void ModDraw(void)
{
    static const u32 black = 0;
#if DIAG
    {   /* test squares, top left: white = drawing works; then green/red: ModFrame ran, Leon in
           control, HUD on, panel timer running; last: a silhouette (texture path) */
        Mtx44 p; Mtx m; int k; u32 g = 0x20C020, r = 0xC02020;
        GXSetFog(0, 0.0f, 1.0f, 0.1f, 1.0f, &black);
        ViewportOn();
        GXSetAlphaCompare(7, 0, 1, 7, 0); GXSetColorUpdate(1); GXSetAlphaUpdate(0); GXSetCullMode(0);
        C_MTXOrtho(p, 0.0f, 480.0f, 0.0f, 640.0f, 0.0f, -100.0f); GXSetProjection(p, 1);
        PSMTXIdentity(m); GXLoadPosMtxImm(m, 0); GXSetCurrentMtx(0);
        GXSetBlendMode(1, 4, 5, 0); GXSetNumTevStages(1); GXSetNumChans(1);
        GXSetChanCtrl(0, 0, 0, 1, 0, 0, 2); GXSetChanCtrl(2, 0, 0, 1, 0, 0, 2); GXSetZMode(0, 7, 0);
        ModeFlat();
        Quad(40.0f, 200.0f, 24.0f, 24.0f, 0xFFFFFFFF, 0);
        for (k = 0; k < 4; k++) {
            extern int IconDbg(int);
            int on = IconDbg(k);
            Quad(70.0f + 30.0f * k, 200.0f, 24.0f, 24.0f, RGBA(on ? g : r, 255), 0);
        }

        GXSetZMode(1, 3, 1); GXSetAlphaUpdate(1);
        ViewportOff();
        dbg_frame = 0;
    }
#endif
    if (!draw_now) return;
    draw_now = 0;
    GXSetFog(0, 0.0f, 1.0f, 0.1f, 1.0f, &black);            /* messages leave the room fog on */
    ViewportOn();
    if (panel_t > 0) PanelDraw(0);
    DiagDraw();
    ViewportOff();
}
