/* Walking while aiming (remake style), full lower body.
 *
 * The aim pose stays the game's (its pitch blend mot3 owns cModel::pMotionB, so nothing may take
 * that slot: B38/B39 did and broke the aim and the shotgun camera). Instead, once a frame from
 * ModFrame - after the game has updated Leon (motion, IK, camera) and before the frame is drawn -
 * the pelvis and leg parts get the pose of a Mixamo pistol walk cycle (forward / back / left /
 * right) and the chest a little of its sway and bob; then the world matrices are rebuilt. The
 * cycle phase follows the distance Leon really moves, so the steps match the ground. It fades in
 * and out over a few frames, and direction changes cross-fade. The next frame the game starts
 * from its own pose again (motion + IK), so nothing of this leaks into its state. */
#include "game.h"
#include "walk_data.h"

#define FADE      6.0f                   /* frames to fade the walk in / out, and to change direction */
#define SWAY_K    0.5f                   /* share of Mixamo's chest sway / bob put on Leon */
#define BOB_K     0.5f

void partsWorldCalc(void* m);

static const int leg_parts[9] = { 17, 18, 19, 20, 21, 22, 23, 24, 25 };
static const f32 leg_ofs[9][3] = {       /* bind offsets (pl00 model) */
    { 0.0f, 0.0f, 0.0f }, { -92.0f, -130.0f, 0.0f }, { 0.0f, -435.49f, 0.0f }, { 0.0f, -439.51f, 0.0f },
    { 0.0f, -91.04f, 81.6f }, { 92.0f, -130.0f, 0.0f }, { 0.0f, -435.49f, 0.0f }, { 0.0f, -439.51f, 0.0f },
    { 0.0f, -91.04f, 81.6f } };

static int have_last, still, cur = -1, prev = -1;
static f32 last_x, last_z, phase, w, xf = 1.0f;

/* ---- small math ---- */
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

static void EulerMtx(const f32* e, f32 m[3][3])          /* RotMatrix: Rz * Ry * Rx */
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
static Q QLerp(Q a, Q b, f32 t)                                  /* normalised lerp, shortest way */
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

/* pose of clip c at phase f (frames, wrapped): local rotation of leg part i */
static Q ClipQ(int c, f32 f, int i)
{
    const WalkClip* k = &walk_clips[c];
    int a = (int)f, b;
    f32 t = f - (f32)a, m[3][3];
    Q qa, qb;
    a %= k->n; b = (a + 1) % k->n;
    EulerMtx(k->legs[a][i], m); qa = MtxQ(m);
    EulerMtx(k->legs[b][i], m); qb = MtxQ(m);
    return QLerp(qa, qb, t);
}
static f32 ClipF(const f32* v, int n, f32 f)
{
    int a = (int)f % n, b = (a + 1) % n;
    f32 t = f - (f32)(int)f;
    return v[a] + (v[b] - v[a]) * t;
}

static void SetL(u8* p, f32 r[3][3], f32 tx, f32 ty, f32 tz)  /* l_mat at 0x3C (3x4) */
{
    f32* l = (f32*)(p + 0x3C);
    l[0] = r[0][0]; l[1] = r[0][1]; l[2] = r[0][2];  l[3] = tx;
    l[4] = r[1][0]; l[5] = r[1][1]; l[6] = r[1][2];  l[7] = ty;
    l[8] = r[2][0]; l[9] = r[2][1]; l[10] = r[2][2]; l[11] = tz;
}

static void Apply(u8* pl)
{
    int i;
    f32 m[3][3], f = phase, fp, ty;
    const WalkClip* kc = &walk_clips[cur];
    f32 fr = f / (f32)kc->n;                                     /* same share of the cycle */
    for (i = 0; i < 9; i++) {
        u8* p = (u8*)getPartsPtr(pl, leg_parts[i]);
        f32* l;
        Q qg, qw;
        if (!p) return;
        l = (f32*)(p + 0x3C);
        m[0][0] = l[0]; m[0][1] = l[1]; m[0][2] = l[2];
        m[1][0] = l[4]; m[1][1] = l[5]; m[1][2] = l[6];
        m[2][0] = l[8]; m[2][1] = l[9]; m[2][2] = l[10];
        qg = MtxQ(m);                                            /* the game's pose (motion + IK) */
        qw = ClipQ(cur, f, i);
        if (prev >= 0 && xf < 1.0f) {
            fp = fr * (f32)walk_clips[prev].n;
            qw = QLerp(ClipQ(prev, fp, i), qw, xf);
        }
        QMtx(QLerp(qg, qw, w), m);
        if (i == 0) {
            ty = ClipF(kc->py, kc->n, f);
            if (prev >= 0 && xf < 1.0f)
                ty = ClipF(walk_clips[prev].py, walk_clips[prev].n, fr * (f32)walk_clips[prev].n) * (1.0f - xf) + ty * xf;
            SetL(p, m, l[3] * (1.0f - w), l[7] * (1.0f - w) + ty * w, l[11] * (1.0f - w));
        } else {
            SetL(p, m, l[3] + (leg_ofs[i][0] - l[3]) * w, l[7] + (leg_ofs[i][1] - l[7]) * w,
                 l[11] + (leg_ofs[i][2] - l[11]) * w);
        }
    }
    {   /* chest: a share of the walk's sway and bob on part 1 (the arms and the gun follow it) */
        u8* p = (u8*)getPartsPtr(pl, 1);
        f32 e[3], s[3][3], r[3][3];
        f32* l;
        int a, b;
        if (p) {
            l = (f32*)(p + 0x3C);
            a = (int)f % kc->n; b = (a + 1) % kc->n;
            for (i = 0; i < 3; i++)
                e[i] = (kc->sway[a][i] + (kc->sway[b][i] - kc->sway[a][i]) * (f - (f32)(int)f)) * SWAY_K * w;
            EulerMtx(e, s);                                      /* world-ish delta, applied locally */
            r[0][0] = s[0][0] * l[0] + s[0][1] * l[4] + s[0][2] * l[8];
            r[0][1] = s[0][0] * l[1] + s[0][1] * l[5] + s[0][2] * l[9];
            r[0][2] = s[0][0] * l[2] + s[0][1] * l[6] + s[0][2] * l[10];
            r[1][0] = s[1][0] * l[0] + s[1][1] * l[4] + s[1][2] * l[8];
            r[1][1] = s[1][0] * l[1] + s[1][1] * l[5] + s[1][2] * l[9];
            r[1][2] = s[1][0] * l[2] + s[1][1] * l[6] + s[1][2] * l[10];
            r[2][0] = s[2][0] * l[0] + s[2][1] * l[4] + s[2][2] * l[8];
            r[2][1] = s[2][0] * l[1] + s[2][1] * l[5] + s[2][2] * l[9];
            r[2][2] = s[2][0] * l[2] + s[2][1] * l[6] + s[2][2] * l[10];
            SetL(p, r, l[3], l[7] + ClipF(kc->bob, kc->n, f) * BOB_K * w, l[11]);
        }
    }
    partsWorldCalc(pl);
}

void LegsFrame(void)
{
    u8* pl = pPL;
    f32 x, z, dx, dz, dist, s, c, lx, lz, ax;
    int clip, aiming, n;
    if (!pl) { have_last = 0; w = 0.0f; cur = -1; return; }
    x = *(f32*)(pl + 0x94); z = *(f32*)(pl + 0x9C);
    dx = x - last_x; dz = z - last_z;
    last_x = x; last_z = z;
    if (!have_last) { have_last = 1; dx = dz = 0.0f; }
    dist = SQRTF(dx * dx + dz * dz);
    if (dist > 200.0f) dist = 0.0f;                              /* warp (room change, event) */
    aiming = pl[0xFC] == 0 && pl[0xFD] == 6 && !(*(u32*)(pl + 0x420) & 0x40)   /* not crouched */
             && modvars[VB_GAMEPLAY];
    if (!aiming) { w = 0.0f; cur = prev = -1; still = 0; return; }
    if (dist >= 2.0f) {
        still = 0;
        s = Sin(*(f32*)(pl + 0xA4)); c = Cos(*(f32*)(pl + 0xA4));
        lx = dx * c - dz * s;                                    /* Leon's frame: +z forward, +x left */
        lz = dx * s + dz * c;
        ax = lx < 0 ? -lx : lx;
        clip = lz >= ax ? 0 : -lz >= ax ? 1 : lx > 0 ? 2 : 3;
        if (cur < 0) { cur = clip; prev = -1; xf = 1.0f; phase = 0.0f; }
        else if (clip != cur) {
            phase = phase / (f32)walk_clips[cur].n * (f32)walk_clips[clip].n;
            prev = cur; cur = clip; xf = 0.0f;
        }
        w += 1.0f / FADE; if (w > 1.0f) w = 1.0f;
    } else {
        if (++still > 2) { w -= 1.0f / FADE; if (w < 0.0f) w = 0.0f; }
    }
    if (cur < 0) return;
    if (xf < 1.0f) { xf += 1.0f / FADE; if (xf > 1.0f) xf = 1.0f; }
    n = walk_clips[cur].n;
    phase += dist * (f32)n / walk_clips[cur].dist;
    while (phase >= (f32)n) phase -= (f32)n;
    if (w <= 0.0f) { cur = prev = -1; return; }
    Apply(pl);
}

/* crouch: off until it is redone (Circle does nothing) */
int crouch_stand;
void CrouchPress(void) { }
void CrouchFrame(void) { }
