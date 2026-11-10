/* Stealth: how close the Ganados notice Leon.
 *
 * em10FindCk (sight / hearing / proximity) and em10FindCk2 read their distances from their own
 * constant pool in the Ganado module (em10.drs, em11.drs... one REL each, all with the same
 * em10 code). The pool sits as one run of floats:
 *   +0x00 225e6 (sight^2, patrolling)  +0x04 36e6 (sight^2)  +0x08 60 deg cone
 *   +0x0C 25e6  footsteps^2 (5 m)      +0x10 12.25e6 always-noticed^2 (3.5 m, even from behind)
 *   +0x14 2000  +0x18 25000 (shots)    +0x1C 4e8
 *   +0x20 12.25e6 FindCk2 footsteps^2  +0x24 64e6 FindCk2 running footsteps^2
 * Loaded modules are found through the OS module list; the run is searched once per module and
 * then rewritten every frame from Leon's state: sight and shots stay as they are, footsteps and
 * the "always" radius shrink when he walks and more when he is crouched. Running = the game's.
 */
#include "game.h"
int CrouchActive(void);

#define MOD_HEAD (*(u8**)0x800030C8)          /* OSModuleInfo queue head */
static const f32 key[10] = { 225000000.0f, 36000000.0f, 1.0471976f, 25000000.0f, 12250000.0f,
                             2000.0f, 25000.0f, 400000000.0f, 12250000.0f, 64000000.0f };
#define NCACHE 8
static u8* c_mod[NCACHE];
static f32* c_pool[NCACHE];

static f32* FindPool(u8* m)
{
    u32 ns = *(u32*)(m + 0x0C), k;
    u32* sec = *(u32**)(m + 0x10);
    if (ns > 40 || (u32)sec < 0x80000000u || (u32)sec >= 0x81800000u) return 0;
    for (k = 0; k < ns; k++) {
        u32 a = sec[k * 2] & ~1u, n = sec[k * 2 + 1], i;
        if ((sec[k * 2] & 1) || !a || n < 40 || a < 0x80000000u || a + n > 0x81800000u) continue;
        for (i = 0; i + 40 <= n; i += 4) {
            f32* p = (f32*)(a + i);
            int j;
            for (j = 0; j < 10; j++) if (p[j] != key[j]) break;
            if (j == 10) return p;
        }
    }
    return 0;
}

void StealthKillFrame(void);
void StealthFrame(void)
{
    StealthKillFrame();
    u8* pl = pPL;
    u8* m;
    int i, n = 0;
    f32 prox, foot, foot2;
    int crouched = CrouchActive();
    if (!pl) return;
    if (pl[0xFD] == 3 && pl[0xFC] == 0) {                 /* running: the game's own */
        prox = 12250000.0f; foot = 25000000.0f; foot2 = 12250000.0f;
    } else if (CrouchActive()) {              /* crouched: silent, 0.8 m behind */
        prox = 640000.0f; foot = 0.0f; foot2 = 0.0f;   /* 0.8 m: the kill range is wider */
    } else {                                              /* walking / still / aiming: 2.5 m */
        prox = 6250000.0f; foot = 12250000.0f; foot2 = 6250000.0f;
    }
    for (m = MOD_HEAD; m && n < 64; m = *(u8**)(m + 4), n++) {
        f32* p = 0;
        if ((u32)m < 0x80000000u || (u32)m >= 0x81800000u) break;
        for (i = 0; i < NCACHE; i++) if (c_mod[i] == m) { p = c_pool[i]; break; }
        if (i == NCACHE) {                                /* new module: search once */
            int j, slot = 0;
            p = FindPool(m);
            for (j = 0; j < NCACHE; j++) if (!c_mod[j]) { slot = j; break; }
            if (j == NCACHE) slot = (int)((u32)m >> 4) % NCACHE;
            c_mod[slot] = m; c_pool[slot] = p;
        }
        if (!p) continue;
        if (p[0] != key[0] || p[2] != key[2] || p[9] != key[9] || (p[10] != 1000000.0f && p[10] != 360000.0f)) {   /* module memory reused */
            for (i = 0; i < NCACHE; i++) if (c_mod[i] == m) c_mod[i] = 0;
            continue;
        }
        p[3] = foot; p[4] = prox; p[8] = foot2;
        p[10] = crouched ? 360000.0f : 1000000.0f;     /* FindCk2: 'he is right here' (1 m) */
    }
}

/* ---- stealth kill (takedown) -----------------------------------------------------------------
 * Crouched, behind an unaware Ganado (within KILL_R, more than ~105 deg off its facing, not
 * chasing Leon): a Cross prompt over its head (hud.c). Cross starts the remake-style takedown:
 *   - the Ganado plays the game's own grabbed-from-behind death: em10.drs motion 0x2BA / sequence
 *     0x2BB (HUNK's neck break victim, carried here as a blob - take_data.h - because only em10.drs
 *     has it) run by its own Dm_NeckBreak routine (R0 2 / R1 0x15, step 1, in every Ganado module):
 *     the motion, the 'neck' event (voice, weapon dropped), the fall and Die_Cramp are the game's;
 *   - Leon plays the matching takedown clip (anim/tools/mktake.py, crouch.c CR_TAKE): left hand over
 *     the mouth, the knife into the neck, back into the crouch. He is placed every frame from the
 *     clip (x / z in the Ganado's start frame), so both stay in step;
 *   - the camera comes in close at the side (StealthCam) and goes back to normal at the end. */
#define TK_SCENE
#include "take_data.h"
#define KILL_R    1500.0f
/* the enemy manager (pArray +0, count +4, work size +8): 0x80283160 in PAL - the one the game's
 * own target list (GetWepTargetList, 0x800CF030) walks. be_flag bit0 = in use, bit5 = targetable,
 * id +0x100 (> 0xF: enemies), HP s16 +0x320. Ganado work (em10, from cEm +0x3E0): Be_flg +0x3E0
 * (0x100: the player was found), Timer +0x3E4, Lose_timer +0xA18 (frames without sight). */
#define EM_MGR ((u8*)0x80283160)
#define EM_BEFLG(e) (*(u32*)((e) + 0x3E0))
#define EM_LOSE(e)  (*(u32*)((e) + 0xA18))
#define SEQ_FRAME(m) (*(f32*)((m) + 0x1D8 + 0xB8))    /* Motion.Seq_frame */
#define ATARI_FLAG(m) (*(u16*)((m) + 0x2B4 + 0x1A))    /* atari.m_flag: 0x300 = collides with characters */
void EstSet(void* model, int no, Vec* pos, Vec* rot, int owner, int id, int core, int kind, void* g, void* h);
int CrouchActive(void);
static u8* target;
static u8* victim;
static int kill_k = -1;
static f32 kill_f, prev_f;               /* takedown frame (motion frames, slowed) */
#define TK_SPD_BASE 0.70f                 /* B69: the whole takedown at 70 % */
#define TK_SPD_CUT  0.42f                 /*      and 42 % round the cut (26..50) */
#define SEQ_SPEED(m) (*(f32*)((m) + 0x1D8 + 0xC0))       /* Motion.Seq_speed */
static f32 take_f = -1.0f;
static f32 g0x, g0z, ga, l0x, l0z, la, cam_w;
static u16 pl_atari;
typedef f32 (*Atan2F)(f32, f32);
#define atan2f_ ((Atan2F)0x8005FFE8)

int StealthDiag(int i) { (void)i; return 0; }        /* (the test numbers are gone) */
static f32 Sm(f32 t) { if (t <= 0.0f) return 0.0f; if (t >= 1.0f) return 1.0f; return t * t * (3.0f - 2.0f * t); }
static f32 SinA(f32 a)
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
static f32 CosA(f32 a) { return SinA(a + 1.57079633f); }
static f32 Wrap(f32 a) { while (a > 3.14159265f) a -= 6.2831853f; while (a < -3.14159265f) a += 6.2831853f; return a; }

static int Unaware(u8* e)
{
    /* found (0x100) and seen within the last 3 s: it is after Leon */
    return !((EM_BEFLG(e) & 0x100) && EM_LOSE(e) < 90);
}
static u8* FindTarget(u8* pl)
{
    u8* arr = *(u8**)(EM_MGR + 0x00);
    u32 cnt = *(u32*)(EM_MGR + 0x04), sz = *(u32*)(EM_MGR + 0x08), i;
    u8* best = 0;
    f32 bd = KILL_R * KILL_R;
    f32 px = *(f32*)(pl + 0x94), py = *(f32*)(pl + 0x98), pz = *(f32*)(pl + 0x9C);
    if ((u32)arr < 0x80000000u || (u32)arr >= 0x81800000u || cnt > 1024 || sz < 0xC00 || sz > 0x40000) return 0;
    for (i = 0; i < cnt; i++) {
        u8* e = arr + i * sz;
        f32 dx, dy, dz, d2, fx, fz, l, dot;
        if ((*(u32*)e & 0x21) != 0x21) continue;
        if (e[0x100] < 0x10 || e[0x100] > 0x20 || e[0x100] == 0x18) continue;   /* Ganados (em10 code) */
        if (*(s16*)(e + 0x320) <= 0 || e[0xFC] != 1) continue;                   /* alive, own routine */
        if (!Unaware(e)) continue;
        dx = px - *(f32*)(e + 0x94); dy = py - *(f32*)(e + 0x98); dz = pz - *(f32*)(e + 0x9C);
        if (dy > 600.0f || dy < -600.0f) continue;
        d2 = dx * dx + dz * dz;
        if (d2 < 1.0f || d2 >= bd) continue;
        fx = *(f32*)(e + 0x0C + 0x08);         /* its facing: the model matrix's z column */
        fz = *(f32*)(e + 0x0C + 0x28);
        l = SQRTF(d2);
        dot = (fx * dx + fz * dz) / l;
        if (dot > -0.25f) continue;            /* Leon must be behind it (> ~105 deg) */
        best = e; bd = d2;
    }
    return best;
}

/* hud.c: where to draw the prompt (0 = none) */
u8* StealthTarget(void) { return kill_k < 0 ? target : 0; }
int StealthKilling(void) { return kill_k >= 0; }
/* crouch.c: the takedown clip frame (-1 = none) */
f32 StealthTakeFrame(void) { return kill_k >= 0 ? take_f : -1.0f; }
u8* StealthVictim(void) { return kill_k >= 0 ? victim : 0; }

static void SetMat(u8* m, f32 x, f32 z, f32 a)
{
    f32* t = (f32*)(m + 0x0C);
    f32 s = SinA(a), c = CosA(a);
    t[0] = c;  t[1] = 0.0f; t[2] = s;  t[3] = x;
    t[4] = 0.0f; t[5] = 1.0f; t[6] = 0.0f;
    t[8] = -s; t[9] = 0.0f; t[10] = c; t[11] = z;
}
static void PartPos(u8* m, int no, Vec* v)
{
    f32* w = (f32*)((u8*)getPartsPtr(m, no) + 0x0C);
    v->x = w[3]; v->y = w[7]; v->z = w[11];
}
static void Blood(u8* pl, int big)
{
    f32* w = (f32*)((u8*)getPartsPtr(pl, 10) + 0x0C);      /* the blade tip: hand +z (thumb side) */
    Vec p, r;
    p.x = w[3] + w[2] * TK_KNIFE * 0.8f; p.y = w[7] + w[6] * TK_KNIFE * 0.8f; p.z = w[11] + w[10] * TK_KNIFE * 0.8f;
    r.x = 0.0f; r.y = Wrap(ga - 1.5707963f); r.z = 0.0f;
    EstSet(0, -1, &p, &r, 0, big ? 1 : 0, 0, 0, 0, 0);     /* EFF_CORE 0: blade hit, 1: burst */
    EstSet(0, -1, &p, &r, 0, 2, 0, 0, 0, 0);               /* spray */
}

static void KillEnd(u8* pl)
{
    if (pl) ATARI_FLAG(pl) = pl_atari;
    if (victim && victim[0xFC] == 2 && victim[0xFD] == 0x15) SEQ_SPEED(victim) = 1.0f;   /* its fall: normal */
    kill_k = -1; take_f = -1.0f; victim = 0;
}

void StealthKillFrame(void)
{
    u8* pl = pPL;
    if (kill_k >= 0) {
        f32 f, x, z, wx, wz, s, c, t, fr;
        int i;
        target = 0;
        kill_k++;
        if (!pl || !victim || (*(u32*)victim & 1) == 0) { KillEnd(pl); return; }
        /* B69: slower, slowest round the cut (the Ganado's Seq_speed, Leon follows its frame) */
        {
            f32 sp = TK_SPD_BASE - (TK_SPD_BASE - TK_SPD_CUT) * (Sm((kill_f - 26.0f) / 6.0f) - Sm((kill_f - 44.0f) / 6.0f));
            if (victim[0xFC] == 2 && victim[0xFD] == 0x15) SEQ_SPEED(victim) = sp;
            prev_f = kill_f;
            kill_f += sp;
            if (victim[0xFC] == 2 && victim[0xFD] == 0x15) {   /* in step with the Ganado's motion */
                fr = SEQ_FRAME(victim);
                if (fr > kill_f - 3.0f && fr < kill_f + 3.0f) kill_f = fr;
            }
        }
        f = kill_f;
        if (f >= (f32)(TK_N - 1)) { KillEnd(pl); return; }
        take_f = f;
        /* Leon's place: the clip's x / z in the Ganado's start frame */
        i = (int)f; t = f - (f32)i;
        x = (f32)tk_xz[i * 2] + (f32)(tk_xz[i * 2 + 2] - tk_xz[i * 2]) * t;
        z = (f32)tk_xz[i * 2 + 1] + (f32)(tk_xz[i * 2 + 3] - tk_xz[i * 2 + 1]) * t;
        s = SinA(ga); c = CosA(ga);
        wx = g0x + x * c + z * s;
        wz = g0z - x * s + z * c;
        t = Sm((f - (f32)TK_S0) / (f32)(TK_IN - TK_S0));        /* from where he stood */
        wx = l0x + (wx - l0x) * t;
        wz = l0z + (wz - l0z) * t;
        *(f32*)(pl + 0x94) = wx; *(f32*)(pl + 0x9C) = wz;
        *(f32*)(pl + 0xA4) = Wrap(la + Wrap(ga + TK_YAW - la) * Sm((f - (f32)TK_S0) / 6.0f));   /* across its back */
        SetMat(pl, wx, wz, *(f32*)(pl + 0xA4));
        ATARI_FLAG(pl) = pl_atari & ~0x300;
        ATARI_FLAG(victim) &= ~0x300;
#define CROSS(x) (prev_f < (f32)(x) && f >= (f32)(x))
        if (CROSS(TK_STAB0)) {                              /* the cut */
            Vec v; PartPos(pl, 10, &v);
            SndCall(1, 0x51, (int)&v, 0, 0, 0);
        }
        if (CROSS(TK_STAB0 + 2) || CROSS(TK_STAB0 + 4)) Blood(pl, 0);   /* along the throat */
        if (CROSS(TK_STAB)) Blood(pl, 1);
#undef CROSS
        return;
    }
    target = 0;
    if (!pl || !modvars[VB_GAMEPLAY] || pl[0xFC] != 0 || pl[0xFD] > 2 || !CrouchActive()) return;
    target = FindTarget(pl);
}

/* pad.c: Cross pressed -> 1 if it started a takedown (the press does not reach the game) */
int StealthPress(void)
{
    u8* pl = pPL;
    u8* e = target;
    if (kill_k >= 0 || !e || !pl || !Unaware(e)) return 0;
    victim = e;
    g0x = *(f32*)(e + 0x94); g0z = *(f32*)(e + 0x9C); ga = *(f32*)(e + 0xA4);
    l0x = *(f32*)(pl + 0x94); l0z = *(f32*)(pl + 0x9C); la = *(f32*)(pl + 0xA4);
    pl_atari = ATARI_FLAG(pl);
    /* the Ganado: Dm_NeckBreak from its step 1 (step 0 would also start HUNK's half on Leon) */
    MotionSetCore(e, e + 0x1D8, (void*)tk_em_mot, (void*)tk_em_seq, 6, 1, TK_S0);   /* held from TK_S0 */
    *(s16*)(e + 0x320) = 0;
    EM_BEFLG(e) &= ~(0x8000000u | 0x20u);
    *(u32*)(e + 0x3E4) = 0;                                /* Timer: plain MotionMove */
    e[0xFC] = 2; e[0xFD] = 0x15; e[0xFE] = 1; e[0xFF] = 0;
    kill_k = TK_S0; kill_f = prev_f = (f32)TK_S0; take_f = (f32)TK_S0; target = 0;
    SEQ_SPEED(e) = TK_SPD_BASE;
    return 1;
}
/* pad.c, every frame of a takedown: the knife stays drawn (L) and nothing else gets through */
u32 StealthPad(u32 out)
{
    if (kill_k < 0) return out;
    out &= PAD_START;
    if (kill_f < (f32)(TK_SHEATH + 2)) out |= PAD_L;  /* until it is in the sheath */
    return out;
}

/* Camera (hook in CameraQuasiFPS::hitCheck, after c12.s): q = QFPS_OFFSET (eye +0, close point +0xC,
 * target +0x18, fovy +0x28), all in the space of m (hitCheck's first argument: the camera base on
 * Leon), so the world points below are taken into it (m is a rotation + translation). During a takedown it moves in close at the right side of the two,
 * a little ahead (the knife hand and the Ganado's face in view), and eases back at the end. */
static void ToLocal(const f32* m, f32 x, f32 y, f32 z, f32* o)
{
    x -= m[3]; y -= m[7]; z -= m[11];
    o[0] = m[0] * x + m[4] * y + m[8] * z;
    o[1] = m[1] * x + m[5] * y + m[9] * z;
    o[2] = m[2] * x + m[6] * y + m[10] * z;
}
void StealthCam(f32* q, const f32* m)
{
    f32 f = take_f, w, tx, ty, tz, ex, ey, ez, s, c, ox, oz, k, e[3], tg[3];
    u8* pl = pPL;
    if (kill_k < 0 || !pl || !victim) { cam_w = 0.0f; return; }
    w = Sm((f - (f32)TK_S0) / 16.0f) * (1.0f - Sm((f - 60.0f) / 24.0f));
    if (w <= 0.0f) return;
    s = SinA(ga); c = CosA(ga);
    /* target: between Leon and the Ganado, at neck height */
    tx = *(f32*)(pl + 0x94) * 0.4f + *(f32*)(victim + 0x94) * 0.6f;
    tz = *(f32*)(pl + 0x9C) * 0.4f + *(f32*)(victim + 0x9C) * 0.6f;
    ty = *(f32*)(pl + 0x98) + 1250.0f;
    /* eye: the Ganado's left front (+x, +z of its frame), slowly closing in */
    k = 1.0f - 0.12f * Sm((f - 10.0f) / 50.0f);
    ox = 1500.0f * k; oz = 900.0f * k;                /* B68: its left front (Leon is at its right) */
    ex = tx + ox * c + oz * s;
    ez = tz - ox * s + oz * c;
    ey = ty + 150.0f;
    {   /* B65: blend in world space along an orbit round the target (the straight blend went
           through Leon's back), then into m's space */
        f32 g0x_ = m[0] * q[0] + m[1] * q[1] + m[2] * q[2] + m[3];
        f32 g0y_ = m[4] * q[0] + m[5] * q[1] + m[6] * q[2] + m[7];
        f32 g0z_ = m[8] * q[0] + m[9] * q[1] + m[10] * q[2] + m[11];
        f32 gtx = m[0] * q[6] + m[1] * q[7] + m[2] * q[8] + m[3];
        f32 gty = m[4] * q[6] + m[5] * q[7] + m[6] * q[8] + m[7];
        f32 gtz = m[8] * q[6] + m[9] * q[7] + m[10] * q[8] + m[11];
        f32 ax = g0x_ - gtx, az = g0z_ - gtz, bx = ex - tx, bz = ez - tz;
        f32 da = SQRTF(ax * ax + az * az), db = SQRTF(bx * bx + bz * bz);
        f32 aa = atan2f_(ax, az), ab = atan2f_(bx, bz), an, d, h, wx, wy, wz;
        wx = gtx + (tx - gtx) * w; wy = gty + (ty - gty) * w; wz = gtz + (tz - gtz) * w;   /* target */
        an = aa + Wrap(ab - aa) * w;
        d = da + (db - da) * w;
        h = (g0y_ - gty) + ((ey - ty) - (g0y_ - gty)) * w;
        ToLocal(m, wx, wy, wz, tg);
        ToLocal(m, wx + SinA(an) * d, wy + h, wz + CosA(an) * d, e);
    }
    q[0] = e[0]; q[1] = e[1]; q[2] = e[2];
    q[6] = tg[0]; q[7] = tg[1]; q[8] = tg[2];
    {   /* close point (hitCheck's ray start) 0.65 m out from the target, clear of the two bodies (B61
           pulled the camera into them); walls further out still pull it in */
        f32 dx = e[0] - tg[0], dy = e[1] - tg[1], dz = e[2] - tg[2], r = SQRTF(dx * dx + dy * dy + dz * dz);
        f32 u = r > 650.0f ? 650.0f / r : 1.0f;
        f32 cp0 = tg[0] + dx * u, cp1 = tg[1] + dy * u, cp2 = tg[2] + dz * u;
        q[3] += (cp0 - q[3]) * w; q[4] += (cp1 - q[4]) * w; q[5] += (cp2 - q[5]) * w;
    }
    q[10] *= 1.0f - 0.05f * w;
    cam_w = w;
}
