/* Crouch (stealth), remake style, from Mixamo clips (anim/mkcrouch.py -> crouch_data.h).
 *
 * Circle toggles it. Like legs.c, nothing goes into the game's motion state: once a frame, after
 * the game has updated Leon, the parts' local matrices get the crouch pose (blended with the
 * game's by a weight that fades in and out) and the world matrices are rebuilt.
 *   - standing / walking (r_no_1 0-2): the whole body. Clips: idle, forward, back (forward
 *     reversed), left, right - chosen from where Leon really moves in his own frame, the cycle
 *     following the distance moved; stand -> crouch and crouch -> stand play their transitions
 *     when Leon is still.
 *   - aiming / knife (6, 0xB): only the pelvis and legs, and the root lowered: the upper body is
 *     the game's aim (and the knife's slash), so aim, shots and knife hits stay the game's.
 *   - run (3): the crouch ends with the crouch-to-sprint clip; any action (ladder, door, jump,
 *     damage...) ends it at once.
 * While crouched Leon moves at SPEED_K of his speed, the camera goes down with him (c12, VB+0x44
 * via hud.c CrouchDrop) and the Ganados notice him later (stealth.c CrouchActive). */
#include "game.h"
#include "crouch_data.h"

void partsWorldCalc(void* m);
int SwapLock(void);
int StealthKilling(void);

#define FADE     6.0f
#define SPEED_K  0.7f                  /* crouched speed */
#define CR_STEP  0.5f                  /* clip frames per game frame (clips at 15 fps) */
#define SLASH_SPD 1.6f                 /* crouched knife slash speed (fits the game's slash) */
#define STAB_SPD  1.5f                 /* stealth kill stab */
#define STEP_MIN 1.0f                  /* units / frame that count as moving */

int crouch_stand;                      /* pad.c (unused now) */
static int want, shot = -1, cur = CR_IDLE, prev = -1, have_last, still, full;
static f32 w, wu, shot_f, sxf, phase, prev_f, xf = 1.0f, last_x, last_z, drop;

/* ---- small math (as legs.c) ---- */
static f32 Sin(f32 a)
{
    const f32 PI = 3.14159265f;
    f32 a2;
    while (a > PI) a -= 2.0f * PI;
    while (a < -PI) a += 2.0f * PI;
    if (a > PI * 0.5f) a = PI - a;
    else if (a < -PI * 0.5f) a = -PI - a;
    a2 = a * a;
    return a * (1.0f - a2 / 6.0f * (1.0f - a2 / 20.0f * (1.0f - a2 / 42.0f)));
}
static f32 Cos(f32 a) { return Sin(a + 1.57079633f); }
typedef struct { f32 w, x, y, z; } Q;
static void EulerMtx(const f32* e, f32 m[3][3])
{
    f32 sx = Sin(e[0]), cx = Cos(e[0]), sy = Sin(e[1]), cy = Cos(e[1]), sz = Sin(e[2]), cz = Cos(e[2]);
    m[0][0] = cz * cy; m[0][1] = cz * sy * sx - sz * cx; m[0][2] = cz * sy * cx + sz * sx;
    m[1][0] = sz * cy; m[1][1] = sz * sy * sx + cz * cx; m[1][2] = sz * sy * cx - cz * sx;
    m[2][0] = -sy;     m[2][1] = cy * sx;                m[2][2] = cy * cx;
}
static Q MtxQ(f32 m[3][3])
{
    Q q;
    f32 t = m[0][0] + m[1][1] + m[2][2], s;
    if (t > 0.0f) {
        s = SQRTF(t + 1.0f) * 2.0f;
        q.w = 0.25f * s; q.x = (m[2][1] - m[1][2]) / s; q.y = (m[0][2] - m[2][0]) / s; q.z = (m[1][0] - m[0][1]) / s;
    } else if (m[0][0] > m[1][1] && m[0][0] > m[2][2]) {
        s = SQRTF(1.0f + m[0][0] - m[1][1] - m[2][2]) * 2.0f;
        q.w = (m[2][1] - m[1][2]) / s; q.x = 0.25f * s; q.y = (m[0][1] + m[1][0]) / s; q.z = (m[0][2] + m[2][0]) / s;
    } else if (m[1][1] > m[2][2]) {
        s = SQRTF(1.0f + m[1][1] - m[0][0] - m[2][2]) * 2.0f;
        q.w = (m[0][2] - m[2][0]) / s; q.x = (m[0][1] + m[1][0]) / s; q.y = 0.25f * s; q.z = (m[1][2] + m[2][1]) / s;
    } else {
        s = SQRTF(1.0f + m[2][2] - m[0][0] - m[1][1]) * 2.0f;
        q.w = (m[1][0] - m[0][1]) / s; q.x = (m[0][2] + m[2][0]) / s; q.y = (m[1][2] + m[2][1]) / s; q.z = 0.25f * s;
    }
    return q;
}
static Q QLerp(Q a, Q b, f32 t)
{
    Q r;
    f32 d = a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z, n;
    if (d < 0.0f) { b.w = -b.w; b.x = -b.x; b.y = -b.y; b.z = -b.z; }
    r.w = a.w + (b.w - a.w) * t; r.x = a.x + (b.x - a.x) * t; r.y = a.y + (b.y - a.y) * t; r.z = a.z + (b.z - a.z) * t;
    n = SQRTF(r.w * r.w + r.x * r.x + r.y * r.y + r.z * r.z);
    if (n > 0.0f) { r.w /= n; r.x /= n; r.y /= n; r.z /= n; }
    return r;
}
static void QMtx(Q q, f32 m[3][3])
{
    f32 x = q.x, y = q.y, z = q.z, ww = q.w;
    m[0][0] = 1 - 2 * (y * y + z * z); m[0][1] = 2 * (x * y - z * ww);     m[0][2] = 2 * (x * z + y * ww);
    m[1][0] = 2 * (x * y + z * ww);     m[1][1] = 1 - 2 * (x * x + z * z); m[1][2] = 2 * (y * z - x * ww);
    m[2][0] = 2 * (x * z - y * ww);     m[2][1] = 2 * (y * z + x * ww);     m[2][2] = 1 - 2 * (x * x + y * y);
}

/* ---- clips ---- */
static void Frames(int c, f32 f, int* a, int* b, f32* t)
{
    const CrClip* k = &cr_clips[c];
    int i = (int)f;
    *t = f - (f32)i;
    if (k->loop) { *a = i % k->n; *b = (*a + 1) % k->n; }
    else {
        if (i >= k->n - 1) { i = k->n - 1; *t = 0.0f; }
        *a = i; *b = i + 1 < k->n ? i + 1 : i;
    }
}
static Q ClipQ(int c, f32 f, int i)
{
    const CrClip* k = &cr_clips[c];
    int a, b, j;
    f32 t, e[3], m[3][3];
    Q qa, qb;
    Frames(c, f, &a, &b, &t);
    for (j = 0; j < 3; j++) e[j] = (f32)k->rot[a][i * 3 + j] * 0.0001f;
    EulerMtx(e, m); qa = MtxQ(m);
    for (j = 0; j < 3; j++) e[j] = (f32)k->rot[b][i * 3 + j] * 0.0001f;
    EulerMtx(e, m); qb = MtxQ(m);
    return QLerp(qa, qb, t);
}
static f32 ClipY(int c, f32 f)
{
    const CrClip* k = &cr_clips[c];
    int a, b;
    f32 t;
    Frames(c, f, &a, &b, &t);
    return (f32)k->y[a] + (f32)(k->y[b] - k->y[a]) * t;
}
/* the crouch pose (before the blend with the game's): loop + cross-fade, then the one-shot clip */
static Q PoseQ(int i)
{
    Q q = ClipQ(cur, phase, i);
    if (prev >= 0 && xf < 1.0f) q = QLerp(ClipQ(prev, prev_f, i), q, xf);
    if (shot >= 0) q = QLerp(q, ClipQ(shot, shot_f, i), sxf);
    return q;
}
static f32 PoseY(void)
{
    f32 y = ClipY(cur, phase);
    if (prev >= 0 && xf < 1.0f) y = ClipY(prev, prev_f) * (1.0f - xf) + y * xf;
    if (shot >= 0) y = y * (1.0f - sxf) + ClipY(shot, shot_f) * sxf;
    return y;
}

static void SetL(f32* l, f32 r[3][3], f32 tx, f32 ty, f32 tz)
{
    l[0] = r[0][0]; l[1] = r[0][1]; l[2] = r[0][2];  l[3] = tx;
    l[4] = r[1][0]; l[5] = r[1][1]; l[6] = r[1][2];  l[7] = ty;
    l[8] = r[2][0]; l[9] = r[2][1]; l[10] = r[2][2]; l[11] = tz;
}
static Q LQ(f32* l)
{
    f32 m[3][3];
    m[0][0] = l[0]; m[0][1] = l[1]; m[0][2] = l[2];
    m[1][0] = l[4]; m[1][1] = l[5]; m[1][2] = l[6];
    m[2][0] = l[8]; m[2][1] = l[9]; m[2][2] = l[10];
    return MtxQ(m);
}

static void Apply(u8* pl)
{
    static const Q ident = { 1.0f, 0.0f, 0.0f, 0.0f };
    f32 m[3][3], y = PoseY();
    f32* l;
    u8* p;
    int i;
    drop = (1140.0f - y) * w;
    for (i = 0; i < CR_NPARTS; i++) {
        int no = cr_parts[i];
        f32 k = (no >= 17 && no <= 25) ? w : w * wu;               /* aim / knife: legs only */
        if (k <= 0.0f) continue;
        p = (u8*)getPartsPtr(pl, no);
        if (!p) return;
        l = (f32*)(p + 0x3C);
        QMtx(QLerp(LQ(l), PoseQ(i), k), m);
        if (no == 1) SetL(l, m, l[3] * (1.0f - k), l[7] + (10.0f - l[7]) * k, l[11] * (1.0f - k));
        else if (no == 17) SetL(l, m, l[3] * (1.0f - k), l[7] * (1.0f - k), l[11] * (1.0f - k));
        else SetL(l, m, l[3], l[7], l[11]);
    }
    p = (u8*)getPartsPtr(pl, 0);                                   /* root: the crouch height */
    if (!p) return;
    l = (f32*)(p + 0x3C);
    QMtx(QLerp(LQ(l), ident, w * wu), m);
    SetL(l, m, l[3] * (1.0f - w), l[7] + (y - l[7]) * w, l[11] * (1.0f - w));
    partsWorldCalc(pl);
    {   /* re-attach whatever is in the hand (gun / knife) to the moved hand */
        u8* wep = *(u8**)(pl + 0x788);
        u8* mm = wep ? *(u8**)(wep + 0x34) : 0;
        if (!SwapLock() && mm && *(u32*)(mm + 0xF4) >= 0x80000000u && *(u32*)(mm + 0xF4) < 0x81800000u)
            partsWorldCalc(mm);
    }
}

/* whole body: free moves, and the knife once drawn (stance and slash: the remake's low pose);
 * legs only: aiming, and the knife's draw / put-away (its own arm animation shows) */
static int Free(u8* pl) { return pl[0xFC] == 0 && (pl[0xFD] <= 2 || (pl[0xFD] == 0xB && (pl[0xFE] == 1 || pl[0xFE] == 2))); }
static int Armed(u8* pl) { return pl[0xFC] == 0 && (pl[0xFD] == 6 || pl[0xFD] == 0xB); }

void CrouchPress(void)
{
    u8* pl = pPL;
    if (!pl || !modvars[VB_GAMEPLAY] || SwapLock() || !(Free(pl) || Armed(pl))) return;
    want = !want;
    if (Free(pl) && still > 2) {                   /* transitions only from standing still */
        shot = want ? CR_DOWN : CR_UP;
        shot_f = 0.0f;
        sxf = want ? 1.0f : 0.0f;                  /* down starts from the standing game pose */
        if (want) { cur = CR_IDLE; phase = 0.0f; prev = -1; xf = 1.0f; }
    }
}
int CrouchActive(void) { return want && w > 0.5f; }
int CrouchLegs(void) { return want || w > 0.0f; }
f32 CrouchDrop(void) { return drop; }

void CrouchFrame(void)
{
    u8* pl = pPL;
    f32 x, z, dx, dz, dist, s, c, lx, lz, ax;
    int clip, n;
    if (!pl || !modvars[VB_GAMEPLAY]) { want = 0; w = wu = 0.0f; shot = -1; have_last = 0; drop = 0.0f; return; }
    full = Free(pl);
    {   /* stealth kill (stealth.c): stand and stab */
        static int killing;
        int k = StealthKilling();
        if (k && !killing) { want = 0; shot = CR_STAB; shot_f = 0.0f; sxf = 0.0f; w = 1.0f; }
        killing = k;
        if (shot == CR_STAB || shot == CR_SLASH) full = 1;
    }
    {   /* crouched knife: the remake's low slash on each slash */
        static int r2_prev;
        int r2 = pl[0xFD] == 0xB ? pl[0xFE] : -1;
        if (want && r2 == 2 && r2_prev != 2 && shot < 0) { shot = CR_SLASH; shot_f = 0.0f; sxf = 0.0f; }
        if (shot == CR_SLASH) full = 1;
        r2_prev = r2;
    }
    if (want && pl[0xFC] == 0 && pl[0xFD] == 3) {           /* run: up into the sprint */
        want = 0; shot = CR_SPRINT; shot_f = 0.0f; sxf = 0.0f; full = 1;
    }
    if (shot == CR_SPRINT) {
        if (pl[0xFC] != 0 || pl[0xFD] != 3) shot = -1;
        else full = 1;
    }
    if (want && !full && !Armed(pl)) { want = 0; shot = -1; w = 0.0f; }   /* actions: at once */
    if (!want && shot < 0 && !full && !Armed(pl)) w = 0.0f;

    x = *(f32*)(pl + 0x94); z = *(f32*)(pl + 0x9C);
    dx = x - last_x; dz = z - last_z;
    if (!have_last) dx = dz = 0.0f;
    dist = SQRTF(dx * dx + dz * dz);
    if (dist > 200.0f) dist = dx = dz = 0.0f;               /* warp */
    if (want && dist > 0.0f) {                              /* crouched: slower */
        dx *= SPEED_K; dz *= SPEED_K; dist *= SPEED_K;
        x = last_x + dx; z = last_z + dz;
        *(f32*)(pl + 0x94) = x; *(f32*)(pl + 0x9C) = z;
    }
    last_x = x; last_z = z; have_last = 1;

    /* weight */
    if (shot == CR_SPRINT) {
        w = 1.0f - shot_f / (f32)(cr_clips[CR_SPRINT].n - 1);   /* over the clip */
        if (w < 0.0f) w = 0.0f;
    } else if (want) { w += 1.0f / 4.0f; if (w > 1.0f) w = 1.0f; }
    else if (shot != CR_UP && shot != CR_STAB) { w -= 1.0f / FADE; if (w < 0.0f) w = 0.0f; }

    if (full) { wu += 1.0f / FADE; if (wu > 1.0f) wu = 1.0f; }
    else { wu -= 1.0f / FADE; if (wu < 0.0f) wu = 0.0f; }
    if (shot == CR_SPRINT || shot == CR_DOWN || shot == CR_UP || shot == CR_STAB || shot == CR_SLASH) wu = 1.0f;

    /* loop clip from the movement in Leon's frame (+z forward, +x left) */
    if (dist >= STEP_MIN) {
        still = 0;
        s = Sin(*(f32*)(pl + 0xA4)); c = Cos(*(f32*)(pl + 0xA4));
        lx = dx * c - dz * s;
        lz = dx * s + dz * c;
        ax = lx < 0 ? -lx : lx;
        clip = lz >= ax ? CR_FWD : -lz >= ax ? CR_BACK : lx > 0 ? CR_LEFT : CR_RIGHT;
    } else {
        clip = ++still > 3 ? CR_IDLE : cur;
    }
    if (clip != cur) {
        prev = cur; prev_f = phase; xf = 0.0f;
        phase = (clip == CR_IDLE || cur == CR_IDLE) ? 0.0f
              : phase / (f32)cr_clips[cur].n * (f32)cr_clips[clip].n;
        cur = clip;
    }
    n = cr_clips[cur].n;
    if (cur == CR_IDLE) phase += CR_STEP;
    else phase += dist * (f32)n / cr_clips[cur].dist;
    while (phase >= (f32)n) phase -= (f32)n;
    if (xf < 1.0f) { xf += 1.0f / FADE; if (xf > 1.0f) xf = 1.0f; }

    /* one-shot transitions */
    if (shot >= 0) {
        n = cr_clips[shot].n;
        if (sxf < 1.0f) { sxf += 0.25f; if (sxf > 1.0f) sxf = 1.0f; }
        shot_f += CR_STEP * (shot == CR_SLASH ? SLASH_SPD : shot == CR_STAB ? STAB_SPD : 1.0f);
        if (shot == CR_DOWN && dist >= STEP_MIN) shot_f = (f32)(n - 1);   /* moved: cut it short */
        if (shot == CR_SLASH && pl[0xFD] != 0xB) shot_f = (f32)(n - 1);   /* knife put away */
        if (shot_f >= (f32)(n - 1)) {
            if (shot == CR_UP || shot == CR_STAB) {    /* hold the standing end pose and fade out */
                w -= 1.0f / FADE;
                if (w <= 0.0f) { w = 0.0f; shot = -1; }
            } else {
                if (shot == CR_DOWN || shot == CR_SLASH) { prev = shot; prev_f = (f32)(n - 1); xf = 0.0f; }   /* fade out of it */
                shot = -1;
            }
        }
    }
    if (w <= 0.0f) { drop = 0.0f; prev = -1; return; }
    Apply(pl);
}
