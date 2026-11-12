/* Quick-weapon panel (remake style): a cross of four slots with weapon silhouettes, shown for a
 * moment after any D-pad use. Drawn with plain GX calls from an ordering-table callback in the
 * screen layer (OT 0x15: after the fog is switched off, before the game's messages). */
#include "game.h"

extern const u8 sil_tex[];
extern const u16 sil_ids[];
extern const int sil_count;

#define PANEL_VIS  75            /* VIs the panel stays (1.25 s at 60 Hz) */
#define PANEL_FADE 18            /* VIs of fade out */
#define CX 548.0f                /* panel centre, virtual 640 x 480 screen: right side, like the remake */
#define CY 236.0f
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
/* horizontal gradient: colour cl on the left edge, cr on the right */
static void QuadH(f32 x, f32 y, f32 w, f32 h, u32 cl, u32 cr)
{
    GXBegin(0x80, 0, 4);
    GXFIFO_F32 = x;     GXFIFO_F32 = y;     GXFIFO_F32 = 0.0f; GXFIFO_U32 = cl;
    GXFIFO_F32 = x + w; GXFIFO_F32 = y;     GXFIFO_F32 = 0.0f; GXFIFO_U32 = cr;
    GXFIFO_F32 = x + w; GXFIFO_F32 = y + h; GXFIFO_F32 = 0.0f; GXFIFO_U32 = cr;
    GXFIFO_F32 = x;     GXFIFO_F32 = y + h; GXFIFO_F32 = 0.0f; GXFIFO_U32 = cl;
}
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
/* Pickup notice backing (remake style): a dark band fading out to the left behind the text and the
   icon, drawn before the item camera pass and the messages, so icon and text land on top. Notice: right edge 446, top 64 of
   the 512 x 384 message screen = 557, 80 here. */
int NoticeLeft(void);
#define ICON_X 0.785f                 /* icon.c ICON_NDC_X / _Y */
#define ICON_Y 0.685f
#define BAR_X0 330.0f
#define BAR_X1 612.0f
#define BAR_Y  74.0f
#define BAR_H  26.0f

/* ---------------------------------------------------------------------------------------------
 * Remake-style reticle in place of the laser. drawLaserSight no longer draws the beam / dot
 * (LaserHook clears its draw flag); each frame it runs, its hit point (lcross) is projected with
 * the game camera and the reticle is drawn there: a centre dot and four ticks that open while Leon
 * walks, turns or fires and close again (focus) when he holds still. During the shot / pump the
 * laser is not updated, so the last position is held for a while.
 * ------------------------------------------------------------------------------------------- */
int SwapLock(void);
#define LCROSS ((f32*)0x8021D82C)
#define RET_GAP0  3.0f        /* tick gap when focused (px of the 640 x 480 frame) */
#define RET_GAPK 12.0f        /* extra gap at full bloom: shots spread inside this radius */
#define RET_LEN   4.0f
static int ret_seen, ret_hit, ret_hold, ret_r2, ret_a, ret_have;
static f32 ret_x, ret_y, ret_spread, ret_px, ret_pz, ret_ang, ret_pitch;
void LaserHook(int res, int draw)
{
    (void)draw;
    ret_seen = 1; ret_hit = res;
}
#define RN 32
static const f32 rc[RN + 1] = { 1.00000f, 0.98079f, 0.92388f, 0.83147f, 0.70711f, 0.55557f, 0.38268f, 0.19509f, 0.00000f, -0.19509f, -0.38268f, -0.55557f, -0.70711f, -0.83147f, -0.92388f, -0.98079f, -1.00000f, -0.98079f, -0.92388f, -0.83147f, -0.70711f, -0.55557f, -0.38268f, -0.19509f, -0.00000f, 0.19509f, 0.38268f, 0.55557f, 0.70711f, 0.83147f, 0.92388f, 0.98079f, 1.00000f };
static const f32 rs[RN + 1] = { 0.00000f, 0.19509f, 0.38268f, 0.55557f, 0.70711f, 0.83147f, 0.92388f, 0.98079f, 1.00000f, 0.98079f, 0.92388f, 0.83147f, 0.70711f, 0.55557f, 0.38268f, 0.19509f, 0.00000f, -0.19509f, -0.38268f, -0.55557f, -0.70711f, -0.83147f, -0.92388f, -0.98079f, -1.00000f, -0.98079f, -0.92388f, -0.83147f, -0.70711f, -0.55557f, -0.38268f, -0.19509f, -0.00000f };
static f32 Sqrt(f32 x)                         /* frsqrte + 3 Newton steps */
{
    f32 y;
    int i;
    if (x <= 0.0f) return 0.0f;
    __asm__("frsqrte %0,%1" : "=f"(y) : "f"(x));
    for (i = 0; i < 3; i++) y = y * (1.5f - 0.5f * x * y * y);
    return x * y;
}
static f32 gun_dir[3];
static int gun_ok;
static int mod_frame;
static u32 rng = 0x2F6B1D35u;
static f32 Rnd(void) { rng = rng * 1664525u + 1013904223u; return (f32)(rng >> 8) * (1.0f / 16777216.0f); }

/* PlWepHitCheck2 entry (hooks.s): moves the shot's end point inside the reticle's open radius,
 * one random offset per frame (the shotgun's pellets keep their pattern and move together).
 * Focused (closed reticle) the shot goes where the reticle points. */
void SpreadShot(u8* pl, f32* p0, f32* p1)
{
    static int frame = -1;
    static f32 dx, dy;
    f32* v = (f32*)(pG + 0x74 + 0x30);
    f32 p00 = *(f32*)(pG + 0x74 + 0x64), l2, k;
    int i;
    if (!pl || pl != pPL || pl[0xFD] != 6 || !modvars[VB_GAMEPLAY] || p00 <= 0.0f) return;
    if (frame != mod_frame) {
        f32 r = Rnd(), r2 = Rnd(), R = RET_GAPK * ret_spread / (320.0f * p00);
        int j = (int)(Rnd() * (f32)RN) % RN;
        if (r2 > r) r = r2;                                    /* denser towards the centre */
        frame = mod_frame;
        dx = rc[j] * r * R; dy = rs[j] * r * R;
    }
    l2 = (p1[0] - p0[0]) * (p1[0] - p0[0]) + (p1[1] - p0[1]) * (p1[1] - p0[1]) + (p1[2] - p0[2]) * (p1[2] - p0[2]);
    if (l2 < 1.0f) return;
    k = Sqrt(l2);
    if (gun_ok) {   /* bend the shot onto the point the reticle is on (the camera-line hit, lcross),
                     * keeping each pellet's own deviation from the gun's direction */
        f32 q[3], ql;
        for (i = 0; i < 3; i++) q[i] = LCROSS[i] - p0[i];
        ql = Sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2]);
        if (ql > 1.0f) {
            u8 w = pG[0x4FBC];
            if (w == 7 || w == 8 || w == 0x21)          /* shotgun pellets: keep their pattern */
                for (i = 0; i < 3; i++) p1[i] += (q[i] / ql - gun_dir[i]) * k;
            else                                         /* one bullet: straight at it */
                for (i = 0; i < 3; i++) p1[i] = p0[i] + q[i] / ql * k;
        }
    }
    for (i = 0; i < 3; i++) p1[i] += (v[i] * dx + v[4 + i] * dy) * k;
}

/* Recoil: each shot raises the camera's aim point (the one c12 keeps in Leon's frame during the
 * shot, VB+0x28); when the shot / pump ends the camera eases back down by itself. */
/* Recoil: each shot raises the camera's aim point (c12 adds VB+0x40 to it); the kick decays by
 * itself in a few frames, also during the shotgun's pump. Shots follow the camera centre, so the
 * kick is real until it settles. */
#define AIM_SMOOTH 0.5f     /* camera smoothing while aiming */
f32 CrouchDrop(void);
#define CROUCH_CAM 0.7f     /* share of Leon's crouch the camera follows down */
#define RAISE_LONG 90.0f    /* units the aim camera goes up with a shotgun */
static int rc_prev;
static f32 rc_k;
static void RecoilFrame(void)
{
    u8* pl = pPL;
    int fire = pl && pl[0xFC] == 0 && pl[0xFD] == 6 && pl[0xFE] == 2 && modvars[VB_GAMEPLAY];
    if (fire && !rc_prev) {
        u8 w = pG[0x4FBC];                     /* weapon_no (PAL: NTSC 0x4FB0 + 0xC) */
        rc_k += (w == 7 || w == 8 || w == 0x21) ? 0.055f : 0.026f;   /* tan of the kick */
        if (rc_k > 0.09f) rc_k = 0.09f;
    }
    rc_prev = fire;
    if (pl && pl[0xFC] == 0 && pl[0xFD] == 6 && modvars[VB_GAMEPLAY]) {
        /* the reticle is the camera centre, so the camera's smoothing is the aim's lag: while
         * aiming the same light smoothing moving or not (walking left the walk ratio, very slow) */
        *(f32*)(0x80217948 + 0xFC) = AIM_SMOOTH;      /* CamSmth.m_ratio */
        *(f32*)(0x80217104 + 0x1AC) = AIM_SMOOTH;     /* CamCtrl.m_QuasiFPS.m_walk_ratio */
    }
    {   /* camera raise while aiming a long gun (c12, VB+0x44) */
        static f32 raise;
        u8 w = pG[0x4FBC];
        f32 t = (pl && pl[0xFC] == 0 && pl[0xFD] == 6 && (w == 7 || w == 8 || w == 0x21)) ? RAISE_LONG : 0.0f;
        raise += (t - raise) * 0.25f;
        *(f32*)(modvars + 0x44) = raise - CrouchDrop() * CROUCH_CAM;
    }
    if (!pl || pl[0xFD] != 6) rc_k = 0.0f;
    *(f32*)(modvars + 0x40) = rc_k;            /* c12: target raised by tan(kick) * distance */
    rc_k *= 0.84f;
    if (rc_k < 0.0005f) rc_k = 0.0f;
}

/* drawLaserSight, between getMarkerPos and the hit search (hooks.s): the gun's marker ray
 * (lpos -> lcross) is kept as the gun direction, and the search is done along the camera's centre
 * line instead, from the point level with the gun: lcross becomes what the reticle is on (enemy
 * test included), and the shots are bent onto it (SpreadShot). */
void LaserRay(void)
{
    f32* lp = (f32*)0x8021D820;
    f32* lc = LCROSS;
    f32* v = (f32*)(pG + 0x74 + 0x30);
    f32 c[3], f[3], g[3], gl, s = 0.0f;
    u8* pl = pPL;
    int i;
    for (i = 0; i < 3; i++) g[i] = lc[i] - lp[i];
    gl = Sqrt(g[0] * g[0] + g[1] * g[1] + g[2] * g[2]);
    gun_ok = 0;
    if (gl < 1.0f) return;
    for (i = 0; i < 3; i++) gun_dir[i] = g[i] / gl;
    gun_ok = 1;
    if (!pl || pl[0xFC] != 0 || pl[0xFD] != 6 || !modvars[VB_GAMEPLAY]) { gun_ok = 0; return; }
    for (i = 0; i < 3; i++) {
        c[i] = -(v[i] * v[3] + v[4 + i] * v[7] + v[8 + i] * v[11]);   /* camera position */
        f[i] = -v[8 + i];                                             /* looks down -z */
    }
    for (i = 0; i < 3; i++) s += (lp[i] - c[i]) * f[i];
    if (s < 0.0f) s = 0.0f;
    for (i = 0; i < 3; i++) {
        lp[i] = c[i] + f[i] * s;
        lc[i] = lp[i] + f[i] * gl;
    }
}

/* Aim entry with the free camera turned away from Leon (after a ladder, a jump, looking around):
 * the game's aim camera snapped back behind Leon. Modern: Leon turns to where the camera looks and
 * the aim starts at the camera's pitch. Called from the camera's aiming branch (hooks.s) before it
 * reads the aim pitch; on the first aiming frame the free yaw is moved onto Leon (ang.y and, for
 * this frame's camera, its saved matrix) and the free pitch onto the aim (m3r, Wep pitch). */
static f32 SinS(f32 x)                         /* |x| <= pi */
{
    f32 x2 = x * x;
    return x * (1.0f - x2 / 6.0f * (1.0f - x2 / 20.0f * (1.0f - x2 / 42.0f * (1.0f - x2 / 72.0f))));
}
static f32 Wrap(f32 a)
{
    while (a > 3.14159265f) a -= 6.2831853f;
    while (a < -3.14159265f) a += 6.2831853f;
    return a;
}
void AimCamEnter(u8* pl, u8* q)
{
    static int last = -100;
    int first = (mod_frame - last) > 2;
    last = mod_frame;
    if (!first || !pl || pl != pPL || pl[0xFC] != 0 || !modvars[VB_GAMEPLAY]) return;
    {
        f32 yaw = *(f32*)(q + 0x204), dep = *(f32*)(q + 0x200);
        u8* wep = *(u8**)(pl + 0x788);
        f32* m3 = (f32*)0x8021D970;
        if (yaw > 0.02f || yaw < -0.02f) {
            f32* m = (f32*)(q + 0x174);
            f32 sn = SinS(Wrap(yaw)), cs = SinS(Wrap(yaw + 1.5707963f));
            int r;
            *(f32*)(pl + 0xA4) = Wrap(*(f32*)(pl + 0xA4) + yaw);
            for (r = 0; r < 3; r++) {                  /* m = m * Ry(yaw) */
                f32 a = m[r * 4 + 0], b = m[r * 4 + 2];
                m[r * 4 + 0] = a * cs - b * sn;
                m[r * 4 + 2] = a * sn + b * cs;
            }
        }
        if (dep > 0.6f) dep = 0.6f;
        if (dep < -0.6f) dep = -0.6f;
        if (wep) {
            m3[0] = m3[1] = dep;
            *(f32*)(wep + 0x28) = dep * 1.5707963f;
        }
    }
}

void SpreadShot2(u8* pl, f32* p0, f32* p1) { SpreadShot(pl, p0, p1); }
const f32 sway_k = 0.35f;                     /* share of the game's weapon sway kept */
static f32 fabsf_(f32 x) { return x < 0.0f ? -x : x; }
static void RetTicks(f32 cx, f32 cy, f32 g, f32 len, f32 t, u32 c)
{
    Quad(cx - t * 0.5f, cy - g - len, t, len, c, 0);          /* top */
    Quad(cx - t * 0.5f, cy + g, t, len, c, 0);                /* bottom */
    Quad(cx - g - len, cy - t * 0.5f, len, t, c, 0);          /* left */
    Quad(cx + g, cy - t * 0.5f, len, t, c, 0);                /* right */
}
static void Disc(f32 cx, f32 cy, f32 r, u32 c)               /* filled circle: triangle fan */
{
    int k;
    GXBegin(0xA0, 0, RN / 2 + 2);
    GXFIFO_F32 = cx; GXFIFO_F32 = cy; GXFIFO_F32 = 0.0f; GXFIFO_U32 = c;
    for (k = 0; k <= RN; k += 2) {
        GXFIFO_F32 = cx + rc[k] * r; GXFIFO_F32 = cy + rs[k] * r; GXFIFO_F32 = 0.0f; GXFIFO_U32 = c;
    }
}
static void ReticleDraw(void)
{
    static const u32 black = 0;
    u8* pl = pPL;
    int aiming = pl && pl[0xFC] == 0 && pl[0xFD] == 6 && modvars[VB_GAMEPLAY] && !SwapLock();
    int seen = ret_seen;
    ret_seen = 0;
    if (!aiming) { ret_hold = 0; ret_a = 0; ret_have = 0; ret_r2 = 0; return; }

    if (seen) {   /* game camera: pG->Camera at pG + 0x74 */
        f32* v = (f32*)(pG + 0x74 + 0x30);
        f32* p = (f32*)(pG + 0x74 + 0x64);
        /* modern: the reticle sits on the camera's centre line (view (0, 0, -1000)), the camera moves
         * and the shots are bent onto that line (SpreadShot) */
        f32 vz = -1000.0f;
        f32 cx = p[2] * vz + p[3];
        f32 cy = p[6] * vz + p[7];
        f32 cw = p[14] * vz + p[15];
        (void)v;
        if (cw > 1.0f) {
            f32 nx = 320.0f * (1.0f + cx / cw), ny = 240.0f * (1.0f - cy / cw);
            ret_x = nx; ret_y = ny;
            ret_hold = 45;
        }
    } else if (ret_hold > 0) ret_hold--;

    {   /* spread: walking / turning open it, a shot kicks it fully open, standing still focuses it */
        u8* wep = *(u8**)(pl + 0x788);
        f32 px = *(f32*)(pl + 0x94), pz = *(f32*)(pl + 0x9C), ang = *(f32*)(pl + 0xA4);
        f32 pitch = wep ? *(f32*)(wep + 0x28) : 0.0f;
        f32 tgt = 0.0f, mv, tn, da;
        if (ret_have) {
            mv = (px - ret_px) * (px - ret_px) + (pz - ret_pz) * (pz - ret_pz);
            mv = mv > 1600.0f ? 1.0f : mv / 1600.0f;              /* 40 units / frame = full */
            da = ang - ret_ang;
            if (da > 3.14159f) da -= 6.28318f;
            if (da < -3.14159f) da += 6.28318f;
            tn = (fabsf_(da) + fabsf_(pitch - ret_pitch)) / 0.04f;
            if (tn > 1.0f) tn = 1.0f;
            tgt = mv * 0.55f;
            if (tn * 0.5f > tgt) tgt = tn * 0.5f;
        }
        ret_px = px; ret_pz = pz; ret_ang = ang; ret_pitch = pitch; ret_have = 1;
        if (pl[0xFE] == 2 && ret_r2 != 2) ret_spread = 1.0f;     /* shot */
        ret_r2 = pl[0xFE];
        if (tgt > ret_spread) ret_spread += (tgt - ret_spread) * 0.3f;
        else ret_spread += (tgt - ret_spread) * 0.07f;
    }
    if (ret_hold <= 0) { ret_a = 0; return; }
    if (ret_a < 8) ret_a++;

    {
        Mtx44 pm; Mtx m;
        f32 g = RET_GAP0 + RET_GAPK * ret_spread;
        int a = 230 * ret_a / 8;
        u32 col = (ret_hit == 2 ? 0xFF484000 : 0xFFFFFF00);
        GXSetFog(0, 0.0f, 1.0f, 0.1f, 1.0f, &black);
        ViewportOn();
        GXSetAlphaCompare(7, 0, 1, 7, 0); GXSetColorUpdate(1); GXSetAlphaUpdate(0); GXSetCullMode(0);
        C_MTXOrtho(pm, 0.0f, 480.0f, 0.0f, 640.0f, 0.0f, -100.0f); GXSetProjection(pm, 1);
        PSMTXIdentity(m); GXLoadPosMtxImm(m, 0); GXSetCurrentMtx(0);
        GXSetBlendMode(1, 4, 5, 0); GXSetNumTevStages(1); GXSetNumChans(1);
        GXSetChanCtrl(0, 0, 0, 1, 0, 0, 2); GXSetChanCtrl(2, 0, 0, 1, 0, 0, 2); GXSetZMode(0, 7, 0);
        ModeFlat();
        /* four thin ticks around a round dot; a soft dark edge so it reads on any background */
        RetTicks(ret_x, ret_y, g - 0.6f, RET_LEN + 1.2f, 2.2f, (u32)(a / 3));
        Disc(ret_x, ret_y, 1.7f, (u32)(a / 3));
        RetTicks(ret_x, ret_y, g, RET_LEN, 1.0f, col | (u32)a);
        Disc(ret_x, ret_y, 0.95f, col | (u32)a);
        GXSetZMode(1, 3, 1); GXSetAlphaUpdate(1);
        ViewportOff();
        GXSetProjection((f32(*)[4])(0x80284420 + 0x64), 0);
    }
}


/* stealth kill prompt (stealth.c): a Cross button over the Ganado's head */
u8* StealthTarget(void);
static void XBar(f32 cx, f32 cy, f32 len, f32 t, int flip, u32 c)   /* a 45 deg bar */
{
    f32 ux = 0.7071f * len * 0.5f, uy = (flip ? -0.7071f : 0.7071f) * len * 0.5f;
    f32 nx = -(flip ? -0.7071f : 0.7071f) * t * 0.5f, ny = 0.7071f * t * 0.5f;
    GXBegin(0x80, 0, 4);
    GXFIFO_F32 = cx - ux - nx; GXFIFO_F32 = cy - uy - ny; GXFIFO_F32 = 0.0f; GXFIFO_U32 = c;
    GXFIFO_F32 = cx + ux - nx; GXFIFO_F32 = cy + uy - ny; GXFIFO_F32 = 0.0f; GXFIFO_U32 = c;
    GXFIFO_F32 = cx + ux + nx; GXFIFO_F32 = cy + uy + ny; GXFIFO_F32 = 0.0f; GXFIFO_U32 = c;
    GXFIFO_F32 = cx - ux + nx; GXFIFO_F32 = cy - uy + ny; GXFIFO_F32 = 0.0f; GXFIFO_U32 = c;
}
static void StealthPromptDraw(void)
{
    static const u32 black = 0;
    static int a;
    static f32 sx, sy;
    u8* e = StealthTarget();
    if (e) {
        f32* v = (f32*)(pG + 0x74 + 0x30);
        f32* p = (f32*)(pG + 0x74 + 0x64);
        f32 x = *(f32*)(e + 0x94), y = *(f32*)(e + 0x98) + 1900.0f, z = *(f32*)(e + 0x9C);
        f32 vx = v[0] * x + v[1] * y + v[2] * z + v[3];
        f32 vy = v[4] * x + v[5] * y + v[6] * z + v[7];
        f32 vz = v[8] * x + v[9] * y + v[10] * z + v[11];
        f32 cx = p[0] * vx + p[1] * vy + p[2] * vz + p[3];
        f32 cy = p[4] * vx + p[5] * vy + p[6] * vz + p[7];
        f32 cw = p[12] * vx + p[13] * vy + p[14] * vz + p[15];
        if (cw <= 1.0f) { a = 0; return; }
        sx = 320.0f * (1.0f + cx / cw); sy = 240.0f * (1.0f - cy / cw);
        if (a < 6) a++;
    } else if (a > 0) a--;
    if (a <= 0) return;
    {
        Mtx44 pm; Mtx m;
        u32 al = (u32)(220 * a / 6);
        GXSetFog(0, 0.0f, 1.0f, 0.1f, 1.0f, &black);
        ViewportOn();
        GXSetAlphaCompare(7, 0, 1, 7, 0); GXSetColorUpdate(1); GXSetAlphaUpdate(0); GXSetCullMode(0);
        C_MTXOrtho(pm, 0.0f, 480.0f, 0.0f, 640.0f, 0.0f, -100.0f); GXSetProjection(pm, 1);
        PSMTXIdentity(m); GXLoadPosMtxImm(m, 0); GXSetCurrentMtx(0);
        GXSetBlendMode(1, 4, 5, 0); GXSetNumTevStages(1); GXSetNumChans(1);
        GXSetChanCtrl(0, 0, 0, 1, 0, 0, 2); GXSetChanCtrl(2, 0, 0, 1, 0, 0, 2); GXSetZMode(0, 7, 0);
        ModeFlat();
        Disc(sx, sy, 11.0f, 0xFFFFFF00 | (al * 3 / 4));      /* white rim */
        Disc(sx, sy, 9.5f, 0x10101000 | al);                /* dark button */
        XBar(sx, sy, 10.0f, 1.8f, 0, 0x9AB4FF00 | al);      /* PlayStation cross, blue-ish */
        XBar(sx, sy, 10.0f, 1.8f, 1, 0x9AB4FF00 | al);
        GXSetZMode(1, 3, 1); GXSetAlphaUpdate(1);
        ViewportOff();
        GXSetProjection((f32(*)[4])(0x80284420 + 0x64), 0);
    }
}

void NoticeBarDraw(void)
{
    static const u32 black = 0;
    Mtx44 p; Mtx m;
    int left = NoticeLeft(), a = 150;
    ReticleDraw();
    StealthPromptDraw();
    if (left <= 0 || !modvars[VB_GAMEPLAY]) return;
    if (left < 12) a = a * left / 12;
    GXSetFog(0, 0.0f, 1.0f, 0.1f, 1.0f, &black);
    ViewportOn();
    GXSetAlphaCompare(7, 0, 1, 7, 0); GXSetColorUpdate(1); GXSetAlphaUpdate(0); GXSetCullMode(0);
    C_MTXOrtho(p, 0.0f, 480.0f, 0.0f, 640.0f, 0.0f, -100.0f); GXSetProjection(p, 1);
    PSMTXIdentity(m); GXLoadPosMtxImm(m, 0); GXSetCurrentMtx(0);
    GXSetBlendMode(1, 4, 5, 0); GXSetNumTevStages(1); GXSetNumChans(1);
    GXSetChanCtrl(0, 0, 0, 1, 0, 0, 2); GXSetChanCtrl(2, 0, 0, 1, 0, 0, 2); GXSetZMode(0, 7, 0);
    ModeFlat();
    QuadH(BAR_X0, BAR_Y, 120.0f, BAR_H, 0x00000000, (u32)a);
    Quad(BAR_X0 + 120.0f, BAR_Y, BAR_X1 - BAR_X0 - 120.0f, BAR_H, (u32)a, 0);
    {   /* soft light behind the 3D icon so it stands out on the dark band (triangle fan) */
        static const f32 ox[9] = { 1.0f, 0.707f, 0.0f, -0.707f, -1.0f, -0.707f, 0.0f, 0.707f, 1.0f };
        static const f32 oy[9] = { 0.0f, 0.707f, 1.0f, 0.707f, 0.0f, -0.707f, -1.0f, -0.707f, 0.0f };
        const f32 cx = 320.0f * (1.0f + ICON_X), cy = 240.0f * (1.0f - ICON_Y), rx = 24.0f, ry = 20.0f;
        u32 cc = 0xB0B0A000 | (u32)(a * 2 / 3), ce = 0xB0B0A000;
        int k;
        GXBegin(0xA0, 0, 10);
        GXFIFO_F32 = cx; GXFIFO_F32 = cy; GXFIFO_F32 = 0.0f; GXFIFO_U32 = cc;
        for (k = 0; k < 9; k++) {
            GXFIFO_F32 = cx + ox[k] * rx; GXFIFO_F32 = cy + oy[k] * ry; GXFIFO_F32 = 0.0f; GXFIFO_U32 = ce;
        }
    }
    GXSetZMode(1, 3, 1); GXSetAlphaUpdate(1);
    ViewportOff();
    GXSetProjection((f32(*)[4])(0x80284420 + 0x64), 0);   /* the item camera pass comes next */
}

void SwapFrame(void);
void LegsFrame(void);
void CrouchFrame(void);
void StealthFrame(void);
int StealthDiag(int i);

void BarnFrame(void);
void Ch0Frame(void);
int Ch0Black(void); int Ch0Text(int k); int Ch0Coords(int i);
void ModFrame(void)
{
    mod_frame++;
    Ch0Frame();
    BarnFrame();
    StealthFrame();                                           /* the Ganados' hearing: Ashley too */
    if (G8(0x4FC4) == 0) {                                    /* C0-01: Leon's own systems, not Ashley's */
        RecoilFrame();
        SwapFrame();
        LegsFrame();
        CrouchFrame();
    }
    IconFrame();
    draw_now = 0;
    if (StealthDiag(-1) > 0 && modvars[VB_GAMEPLAY]) draw_now = 1;   /* stealth numbers (test) */
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
int StealthDiag(int i);
static void DiagDraw(void)
{
    Mtx44 p; Mtx m; int i, k, n, nd; char buf[8];
    if (StealthDiag(-1) <= 0) return;
    GXSetAlphaCompare(7, 0, 1, 7, 0); GXSetColorUpdate(1); GXSetAlphaUpdate(0); GXSetCullMode(0);
    C_MTXOrtho(p, 0.0f, 480.0f, 0.0f, 640.0f, 0.0f, -100.0f); GXSetProjection(p, 1);
    PSMTXIdentity(m); GXLoadPosMtxImm(m, 0); GXSetCurrentMtx(0);
    GXSetBlendMode(1, 4, 5, 0); GXSetNumTevStages(1); GXSetNumChans(1);
    GXSetChanCtrl(0, 0, 0, 1, 0, 0, 2); GXSetChanCtrl(2, 0, 0, 1, 0, 0, 2); GXSetZMode(0, 7, 0);
    ModeFlat();
    Quad(96.0f, 116.0f, 4 * 66.0f, 28.0f, 0x000000A0, 0);   /* inside the 16:9 crop */
    for (i = 0; i < 4; i++) {
        n = StealthDiag(i); if (n < 0) n = 0; if (n > 9999) n = 9999;
        nd = 0; do { buf[nd++] = (char)(n % 10); n /= 10; } while (n);
        for (k = 0; k < nd; k++) Digit(100.0f + 66.0f * i + 13.0f * (nd - 1 - k), 121.0f, buf[k], i == 0 ? 0xFFE040FF : 0xFFFFFFFF);
    }
    GXSetZMode(1, 3, 1); GXSetAlphaUpdate(1);
}

int BarnPanel(void); u8* BarnText(void); int BarnCoords(int i);
static void Num(f32 x, f32 y, int n, u32 c)        /* signed number, seven-segment */
{
    char buf[8]; int nd = 0, k, neg = n < 0;
    if (neg) n = -n;
    do { buf[nd++] = (char)(n % 10); n /= 10; } while (n && nd < 7);
    if (neg) { Quad(x, y + 8.0f, 8.0f, 2.0f, c, 0); x += 11.0f; }
    for (k = 0; k < nd; k++) Digit(x + 13.0f * (nd - 1 - k), y, buf[k], c);
}
static void BarnDraw(void)                         /* B88: the stealth panel; Leon's position in r103 (test) */
{
    Mtx44 p; Mtx m; int i;
    int panel = BarnPanel(), cx = BarnCoords(0);
    const u8* img = BarnText();
    if (!panel && cx == -999999) return;
    GXSetAlphaCompare(7, 0, 1, 7, 0); GXSetColorUpdate(1); GXSetAlphaUpdate(0); GXSetCullMode(0);
    C_MTXOrtho(p, 0.0f, 480.0f, 0.0f, 640.0f, 0.0f, -100.0f); GXSetProjection(p, 1);
    PSMTXIdentity(m); GXLoadPosMtxImm(m, 0); GXSetCurrentMtx(0);
    GXSetBlendMode(1, 4, 5, 0); GXSetNumTevStages(1); GXSetNumChans(1);
    GXSetChanCtrl(0, 0, 0, 1, 0, 0, 2); GXSetChanCtrl(2, 0, 0, 1, 0, 0, 2); GXSetZMode(0, 7, 0);
    ModeFlat();
    if (cx != -999999) {
        Quad(96.0f, 70.0f, 540.0f, 26.0f, 0x000000A0, 0);
        for (i = 0; i < 6; i++) Num(98.0f + 88.0f * i, 74.0f, BarnCoords(i), i == 3 ? 0xFFE040FF : (i == 4 ? 0x60FF60FF : 0xFFFFFFFF));
    }
    if (panel && img) {
        const f32 w = 480.0f, h = 240.0f, x = 320.0f - w / 2, y = 240.0f - h / 2;
        Quad(0.0f, 0.0f, 640.0f, 480.0f, 0x00000070, 0);
        QuadH(x - 6.0f, y - 6.0f, w + 12.0f, h + 12.0f, 0x141210E8, 0x0C0B0AE8);
        Quad(x - 6.0f, y - 6.0f, w + 12.0f, 2.0f, 0x8A7A5AFF, 0); Quad(x - 6.0f, y + h + 4.0f, w + 12.0f, 2.0f, 0x8A7A5AFF, 0);
        {
            GXTexObj tx;
            GXInitTexObj(&tx, img, 512, 256, 0 /* I4 */, 0, 0, 0);
            GXInitTexObjLOD(&tx, 1, 1, 0.0f, 0.0f, 0.0f, 0, 0, 0);
            GXLoadTexObj(&tx, 0);
            GXClearVtxDesc();
            GXSetVtxDesc(9, 1); GXSetVtxDesc(11, 1); GXSetVtxDesc(13, 1);
            GXSetVtxAttrFmt(0, 9, 1, 4, 0); GXSetVtxAttrFmt(0, 11, 1, 5, 0); GXSetVtxAttrFmt(0, 13, 1, 4, 0);
            GXSetNumTexGens(1);
            GXSetTexCoordGen2(0, 1, 4, 60, 0, 125);
            GXSetTevOrder(0, 0, 0, 4);
            GXSetTevOp(0, 0);
            GXBegin(0x80, 0, 4);
            GXFIFO_F32 = x;     GXFIFO_F32 = y;     GXFIFO_F32 = 0.0f; GXFIFO_U32 = 0xF0E6D2FF; GXFIFO_F32 = 0.0f; GXFIFO_F32 = 0.0f;
            GXFIFO_F32 = x + w; GXFIFO_F32 = y;     GXFIFO_F32 = 0.0f; GXFIFO_U32 = 0xF0E6D2FF; GXFIFO_F32 = 1.0f; GXFIFO_F32 = 0.0f;
            GXFIFO_F32 = x + w; GXFIFO_F32 = y + h; GXFIFO_F32 = 0.0f; GXFIFO_U32 = 0xF0E6D2FF; GXFIFO_F32 = 1.0f; GXFIFO_F32 = 1.0f;
            GXFIFO_F32 = x;     GXFIFO_F32 = y + h; GXFIFO_F32 = 0.0f; GXFIFO_U32 = 0xF0E6D2FF; GXFIFO_F32 = 0.0f; GXFIFO_F32 = 1.0f;
        }
    }
    GXSetZMode(1, 3, 1); GXSetAlphaUpdate(1);
}

/* C0-01/02: chapter 0 overlay: black screen, the texts (glyph atlas, ch0_font.c), Ashley's position (test) */
extern const u8 ch0_font[]; extern const u16 ch0_glyph[256][4];
extern const int ch0_font_w, ch0_font_h, ch0_font_gh, ch0_font_space;
static f32 TextW(const char* s, f32 k)
{
    f32 w = 0.0f;
    for (; *s; s++) { u8 c = (u8)*s; w += c == ' ' ? (f32)ch0_font_space : ch0_glyph[c][3] * 0.25f; }
    return w * k;
}
static void Text(const char* s, f32 cx, f32 y, f32 k, u32 c)     /* centred on cx; k = scale */
{
    GXTexObj tx;
    f32 x = cx - TextW(s, k) * 0.5f, iw = 1.0f / ch0_font_w, ih = 1.0f / ch0_font_h, gh = ch0_font_gh * k;
    GXInitTexObj(&tx, ch0_font, ch0_font_w, ch0_font_h, 0 /* I4 */, 0, 0, 0);
    GXInitTexObjLOD(&tx, 1, 1, 0.0f, 0.0f, 0.0f, 0, 0, 0);
    GXLoadTexObj(&tx, 0);
    GXClearVtxDesc();
    GXSetVtxDesc(9, 1); GXSetVtxDesc(11, 1); GXSetVtxDesc(13, 1);
    GXSetVtxAttrFmt(0, 9, 1, 4, 0); GXSetVtxAttrFmt(0, 11, 1, 5, 0); GXSetVtxAttrFmt(0, 13, 1, 4, 0);
    GXSetNumTexGens(1);
    GXSetTexCoordGen2(0, 1, 4, 60, 0, 125);
    GXSetTevOrder(0, 0, 0, 4);
    GXSetTevOp(0, 0);
    for (; *s; s++) {
        u8 ch = (u8)*s; const u16* g = ch0_glyph[ch];
        f32 w, u0, u1, v0, v1;
        if (ch == ' ') { x += ch0_font_space * k; continue; }
        if (!g[2]) continue;
        w = g[2] * k; u0 = g[0] * iw; u1 = (g[0] + g[2]) * iw; v0 = g[1] * ih; v1 = (g[1] + ch0_font_gh) * ih;
        x -= 2.0f * k;                                           /* the glyph cell's 2 px margin */
        GXBegin(0x80, 0, 4);
        GXFIFO_F32 = x;     GXFIFO_F32 = y;      GXFIFO_F32 = 0.0f; GXFIFO_U32 = c; GXFIFO_F32 = u0; GXFIFO_F32 = v0;
        GXFIFO_F32 = x + w; GXFIFO_F32 = y;      GXFIFO_F32 = 0.0f; GXFIFO_U32 = c; GXFIFO_F32 = u1; GXFIFO_F32 = v0;
        GXFIFO_F32 = x + w; GXFIFO_F32 = y + gh; GXFIFO_F32 = 0.0f; GXFIFO_U32 = c; GXFIFO_F32 = u1; GXFIFO_F32 = v1;
        GXFIFO_F32 = x;     GXFIFO_F32 = y + gh; GXFIFO_F32 = 0.0f; GXFIFO_U32 = c; GXFIFO_F32 = u0; GXFIFO_F32 = v1;
        x += 2.0f * k + g[3] * 0.25f * k;
    }
}
static void Line(const char* s, f32 cx, f32 y, f32 k, int a)    /* white text with a soft dark shadow */
{
    Text(s, cx + 1.5f * k, y + 1.5f * k, k, (u32)(a * 3 / 4));
    Text(s, cx, y, k, 0xF2EEE600u | (u32)a);
}
static void Ch0Draw(void)
{
    Mtx44 p; Mtx m; int i, a[8], any = 0;
    int bk = Ch0Black(), cx = Ch0Coords(0);
    for (i = 0; i < 8; i++) { a[i] = Ch0Text(i); any |= a[i]; }
    if (!bk && !any && cx == -999999) return;
    GXSetAlphaCompare(7, 0, 1, 7, 0); GXSetColorUpdate(1); GXSetAlphaUpdate(0); GXSetCullMode(0);
    C_MTXOrtho(p, 0.0f, 480.0f, 0.0f, 640.0f, 0.0f, -100.0f); GXSetProjection(p, 1);
    PSMTXIdentity(m); GXLoadPosMtxImm(m, 0); GXSetCurrentMtx(0);
    GXSetBlendMode(1, 4, 5, 0); GXSetNumTevStages(1); GXSetNumChans(1);
    GXSetChanCtrl(0, 0, 0, 1, 0, 0, 2); GXSetChanCtrl(2, 0, 0, 1, 0, 0, 2); GXSetZMode(0, 7, 0);
    ModeFlat();
    if (bk) Quad(-8.0f, -8.0f, 656.0f, 496.0f, (u32)bk, 0);
    if (cx != -999999) {
        Quad(96.0f, 70.0f, 3 * 96.0f, 26.0f, 0x000000A0, 0);
        for (i = 0; i < 3; i++) Num(98.0f + 96.0f * i, 74.0f, Ch0Coords(i), i == 1 ? 0x60FF60FF : 0xFFFFFFFF);
    }
    if (a[0]) Line("Hace 11 horas", 320.0f, 240.0f - 30.0f, 1.9f, a[0]);
    if (a[1]) Line("\x93Tengo que salir de aqu\xed.\x94", 320.0f, 366.0f, 1.0f, a[1]);
    if (a[2]) { Line("Est\xe1 cerrada.", 320.0f, 342.0f, 1.0f, a[2]); Line("Tiene que haber una llave en alg\xfan sitio.", 320.0f, 370.0f, 1.0f, a[2]); }
    if (a[3]) Line("\x01 Coger la llave", 320.0f, 370.0f, 1.0f, a[3]);
    if (a[4]) Line("Has cogido la llave.", 320.0f, 370.0f, 1.0f, a[4]);
    if (a[5]) Line("La puerta se abre.", 320.0f, 370.0f, 1.0f, a[5]);
    if (a[6]) Line("Ashley ha sido capturada", 320.0f, 224.0f, 1.3f, a[6]);
    if (a[7]) Line("Fin de la Parte 1 (prueba)", 320.0f, 224.0f, 1.3f, a[7]);
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
    {
        static const u32 blk = 0;
        GXSetFog(0, 0.0f, 1.0f, 0.1f, 1.0f, &blk);
        ViewportOn(); BarnDraw(); Ch0Draw(); ViewportOff();
    }
    if (!draw_now) return;
    draw_now = 0;
    GXSetFog(0, 0.0f, 1.0f, 0.1f, 1.0f, &black);            /* messages leave the room fog on */
    ViewportOn();
    if (panel_t > 0) PanelDraw(0);
    DiagDraw();
    ViewportOff();
}
