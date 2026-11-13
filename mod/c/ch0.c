/* Chapter 0 "Hace 11 horas" - Ashley escapes through the village at night.
 * C0-01: the intro's jump (SceAtExecRoomJump 0x100 from r120, PAL 0x80152E28) becomes PlSelect(1)
 *   (PAL 0x80143984) + the village at night (r111 = r101's map and coordinates) at the road entrance
 *   (r100's door: -52144, 91, 22524, 2.122). r111's own Ganados (emleon01, id 0x17) are swapped for the
 *   guards of the user's map just before the room creates its enemies (EmSetFromList, PAL 0x800CB20C),
 *   all with torches (list flag 0x00020000 -> Wep_type 9). Black screen, "Hace 11 horas", four steps,
 *   a look around, "Tengo que salir de aqui." Test: coordinates; door B ends the chapter.
 * C0-02 (the user's C0-01 video: the whole route works; the window jump of the house is the game's own):
 *   - the guards stand guard (Ganado routine 1/1 Keeper, without Be_flg 0x100): they look where the map
 *     says and only the game's own find check (60 deg cone, footsteps, very near) starts a chase; when
 *     the game sends one back to Wait it is made a Keeper again where it is.
 *   - the room's doors are off for the whole chapter; door B (to the farm, centre 19713, 2003) the first
 *     time: "Esta cerrada. / Tiene que haber una llave en algun sitio."
 *   - the key on the bed upstairs in house C (user's video: Ashley at the bed 2329, 3199, -9063): the
 *     bed's own "check" area is off; our prompt (Cross) takes the key -> "Has cogido la llave."
 *   - then a short scene: the door downstairs is kicked in, a Ganado with a torch comes in (EmSetEvent,
 *     PAL 0x800CB76C) and comes up for her; out through the window (the game's own jump).
 *   - with the key, door B: "La puerta se abre." -> end of Part 1 (test: back to Leon as in C0-01).
 *   - caught: a Ganado knocks her down (player routine 1) -> "Ashley ha sido capturada" and the room
 *     again from the last checkpoint (start / the bed).
 * C0-03 (the user's C0-02 video: done; one crash at the house scene in another try):
 *   - the scene's door-kick sound is gone (SndCall 1/0x1E is from Leon's bank: not loaded with Ashley)
 *     and the Ganado is made only once.
 *   - stealth of our own: every guard has an alert meter (the marker over its head: white, yellow, red).
 *     It fills while Ashley is in front of it (60 deg either side, 11 m standing, 7 m crouched, 13 m
 *     running), quicker the nearer; very near (1.8 m) from any side, and running within 6 m (heard).
 *     Full: that one and the ones within 10 m chase her (the game's own chase: barn.c's release). Lost
 *     (15 m away, or hidden without being seen) for 4 s: they guard again where they stand.
 *     While guarding the game's own detection is off (Keeper + Be_flg 0x100 + Guard_r 0) and we turn
 *     them: a slow look left and right around the map's direction.
 *   - patrols: road (the map's left-right arrows), centre-west and north-east walk between two points
 *     (Ganado routine 1/0x14 GuardWalk to Go_pos, +0x92C), stop, look, and go back.
 *   - Ashley crouches (Circle, crouch.c with Leon's clips on her parts 0-25), slower and less seen.
 *   - hiding places (Cross): she stays crouched and still, unseen; a chaser within 4 m sees her go in.
 * C0-04 (the user's C0-03 test: the intro is good):
 *   - the scared clip ends when she has looked both ways (no shoulders up) and fades out slowly into
 *     the game's stance (30 frames, holding its last frame).
 *   - a card with the level's explanation after the intro (Cross closes it; nothing moves meanwhile).
 *   - the road guard starts with his back to her and does not look round; his patrol (east only, away
 *     from the start) begins once she has taken the turn into the alley (z < 5000).
 * C0-05 (user's C0-04 video: two guards came from far through the wood): every guard keeps to a 2.5 m
 *   beat across its facing and walks back if it is more than 4 m from home; the game's own detection is
 *   kept off harder (flag 0x40 / Be_flg 0x08000000 too); after a chase they go back home; the square root
 *   behind the distances was wrong far away (Newton from x itself); the card is re-spaced.
 * C0-08 (the user's corrected map): one watch at the north-west, two at the north-east, the pair by B and
 *   the south pair as before; the gathering further west; boxes in the three black-marked passages.
 * C0-06 (user): the road guard walks along the road (his beat ran into a wall), in step with the watch
 *   over the crossing so that there is a moment to slip to the stable; only two in the square, by door B
 *   first and then back toward the start (not past her) once she is round the south side. */
#include "game.h"

#define STAGE G8(0x4FA8)
#define ROOM  G8(0x4FA9)
#define PLTYPE G8(0x4FC4)
#define PL_LIFE (*(s16*)(pG + 0x4FB0))
#define PL_LIFE_MAX (*(s16*)(pG + 0x4FB2))
#define EMLIST_NO (*(s8*)(pG + 0x4FAF))
#define EMLIST(i) (pG + 0x52F4 + (i) * 32)
#define STOPF   (*(u32*)(pG + 0x170))
#define SPF_CAM 0x40000000u
#define CAMP    ((f32*)(pG + 0x74 + 0xA4))
#define EMMGR ((void*)0x80283160)
#define PL_SELECT ((void (*)(int))0x80143984)
#define ROOM_JUMP ((void (*)(u32, Vec*, Vec*, int))0x80152E28)
#define EM_SET_EVENT ((u8* (*)(u8*))0x800CB76C)
extern u16 barn_pad;                                 /* pad.c: this frame's remapped buttons */

static int on, done, ph, t, ready, endt, scene;
static int key, b_seen, msg, msg_t, caught, cap_t, cp;      /* cp: checkpoint 0 start, 1 the bed */
static Vec lpos, lrot; static int larg;              /* the intro's own jump (Leon, r100) */
static Vec apos = { -52144.0f, 91.0f, 22524.0f }, arot = { 0.0f, 2.122f, 0.0f };
static Vec kpos = { 2100.0f, 3199.0f, -9500.0f }, krot = { 0.0f, 0.0f, 0.0f };
static u8 gidx[16]; static int ngidx;                /* our list entries (guards) */
static u8* hman;                                     /* the Ganado of the house scene */
static int hman_t;
static u16 pad_old;
int ch0_padlock;                                     /* pad.c: no input; ch0_stick: forced stick */
s8 ch0_sx, ch0_sy;
int ch0_stick;
extern int ch0_crouch_force;                 /* crouch.c: kept crouched (hidden) */
enum { G_HOLD, G_WALK, G_CHASE };
enum { R_NONE, R_GROUP, R_RUN, R_SIEGE, R_LADDER };
typedef struct { u8* e; u8 st, role, leg, pad; f32 base, meter, ax, az, bx, bz, tx, tz; int tm, lost; } Guard;
static int scene_gate, after_key;                    /* C0-07: the south gate scene (frames); split after a restart */
static int cyc;                                      /* C0-06: road / watch cycle */
static int stage;                                    /* C0-07: 0 start, 1 the gate scene done (grouped), 2 the key */
static Guard gd[12];
static int hidden, hide_no, card, card_t, road_wait;

#define BX 19713.0f                                  /* door B */
#define BZ 2003.0f
#define KX 2329.0f                                   /* the bed */
#define KY 3199.0f
#define KZ (-9063.0f)
#define DOOR_OUT_X 7169.0f                           /* house C's door, outside / inside (user's video) */
#define DOOR_OUT_Z (-5545.0f)
#define DOOR_IN_X 7309.0f
#define DOOR_IN_Z (-6724.0f)

static void Hud(int sw)
{
    ((void (*)(void*, int))0x800C0518)((void*)0x8027E4A8, sw);
    ((void (*)(void*, int, int))0x8011C3CC)((void*)0x8028481C, 33, sw);
}
static f32 Sq(f32 x)                                 /* sqrt: a power-of-4 start, then Newton */
{
    f32 r = 1.0f; int i;
    if (x <= 0.0f) return 0.0f;
    while (r * r * 16.0f < x) r *= 4.0f;
    for (i = 0; i < 6; i++) r = 0.5f * (r + x / r);
    return r;
}
static f32 PX(void) { return *(f32*)(pPL + 0x94); }
static f32 PY(void) { return *(f32*)(pPL + 0x98); }
static f32 PZ(void) { return *(f32*)(pPL + 0x9C); }
static f32 D2(f32 x, f32 z) { return (PX() - x) * (PX() - x) + (PZ() - z) * (PZ() - z); }

/* hook at SceAtExecRoomJump's entry: a[0] room, a[1] pos, a[2] rot, a[3] arg (written back) */
void Ch0Jump(u32* a)
{
    if (done || on || !pG) return;
    if (a[0] != 0x100 || STAGE != 1 || ROOM != 0x20) return;      /* only the intro's jump */
    lpos = *(Vec*)a[1]; lrot = *(Vec*)a[2]; larg = (int)a[3];
    PL_SELECT(1);
    a[0] = 0x111; a[1] = (u32)&apos; a[2] = (u32)&arot;
    hidden = 0; ch0_crouch_force = 0; card = 0; road_wait = 1; cyc = 0; stage = 0; scene_gate = 0;
    on = 1; ph = 0; t = 0; ready = 0; endt = 0; key = 0; b_seen = 0; cp = 0; caught = 0; scene = 0; msg = 0;
}

/* the guards (user's map, snapped to the ground, 0.9 m clear of walls): pos (mm), facing (s16, pi/0x4000), type
 * C0-07: the two of the south alley are gone from the start: they come in by the south gate later. */
static const s16 GU[][5] = {
    { -27951, 0,   9471,   8407,  0 },   /* 0 road, just past the start */
    { -15761, 0,  -2050,    834,  3 },   /* 1 the watch over the crossing to the stable, in step with the road */
    {  11688, 0,  -1077,  -8192, 12 },   /* 2, 3 the square pair, by door B first */
    {  11940, 0,   3763,  -8192,  0 },
    {  13121, 846, -17642,  -6931,  3 },   /* 4, 5 north-east (C0-08 map); C0-09: on their real ground */
    {  15561, 978, -19534,  -6931,  1 },
};
#define NGU (int)(sizeof(GU) / sizeof(GU[0]))
#define G_RUN0 NGU                       /* the two who run in by the south gate (EmSetEvent) */
#define NG (NGU + 2)
#define G_WATCH 1
#define CYC 600
static const f32 ROAD_W[2] = { -27951.0f, 9471.0f }, ROAD_E[2] = { -22081.0f, 9007.0f };
/* the crossing: (-14239, 7377); the watch looks at it at 0.160 rad, away = -2.98 */
static const f32 BV[NGU][2] = { { 0, 0 }, { 0, 0 }, { 0, 1250 }, { 0, 1250 }, { -901, 866 }, { 0, 0 } };
/* C0-08 map: the gathering west of the bonfire where the user's arrows end, 2.4 m+ clear of walls */
static const f32 GATHER[4][2] = { { -10000.0f, 3500.0f }, { -10000.0f, 5000.0f }, { -11500.0f, 3500.0f }, { -11500.0f, 5000.0f } };
#define VIA_X 0.0f                                   /* the square pair go round north of the bonfire */
#define VIA_Z (-3000.0f)
static const f32 RUNWAY[][2] = { { -15500.0f, 29000.0f }, { -14500.0f, 26000.0f }, { -13641.0f, 21193.0f },
                                 { -12529.0f, 15216.0f }, { -13000.0f, 10000.0f } };
#define NRUN (int)(sizeof(RUNWAY) / sizeof(RUNWAY[0]))
static const f32 RUN0[2][3] = { { -16248.0f, 2684.0f, 31000.0f }, { -14383.0f, 2571.0f, 30634.0f } };   /* inside the south gate (C0-09: its ground is 2.6 m up) */
#define STABLE_X (-5772.0f)
#define STABLE_Z 12963.0f
/* C0-08: the user's black marks, closed with boxes (the room's own et01 box, EtcModelSet PAL 0x8010ACF0)
 * across the narrowest line of each passage (work: wall-to-wall chords), and an invisible stop behind them */
static const f32 BLK[3][5] = {                       /* centre x, z, direction (rad), width, boxes */
    { -10953.0f, 14439.0f, 1.5708f, 1200.0f, 2 },    /* the alley beside the stable */
    {  -6245.0f, -5123.0f, 2.4435f, 1800.0f, 3 },    /* west of the house */
    {  12960.0f, -12682.0f, 2.7925f, 2000.0f, 3 },   /* north-east of the house */
};
static const f32 SIEGE[3][2] = { { 7169.0f, -4800.0f }, { 8700.0f, -5000.0f }, { 6300.0f, -4300.0f } };   /* house C's front */
static const f32 LADDER[2] = { -13518.0f, -10294.0f };   /* the room's ladder (ETS, id 6) */                                                   /* foot of the ladder up */

/* hook at EmSetFromList's entry: r111's list -> our guards */
void Ch0EmList(void)
{
    int i, k = 0;
    if (!on || !pG || STAGE != 1 || ROOM != 0x11) return;
    for (i = 0; i < 256; i++) {
        u8* e = EMLIST(i);
        if (*(u16*)(e + 0x18) == 0x111 && e[1] == 0x17) { e[0] = 0; e[1] = 0; }
    }
    ngidx = 0;
    for (i = 0; i < 256 && k < NGU; i++) {
        u8* e = EMLIST(i);
        if (e[1] != 0 || e[0] != 0) continue;
        memclr_asm(e, 32);
        e[0] = 1; e[1] = 0x17; e[2] = (u8)GU[k][4];
        *(u32*)(e + 4) = 0x00020000u;                /* torch; no bit 8 (that one keeps them turned to the player) */
        *(u16*)(e + 8) = 1000;
        *(s16*)(e + 0x0C) = GU[k][0] / 10; *(s16*)(e + 0x0E) = GU[k][1] / 10; *(s16*)(e + 0x10) = GU[k][2] / 10;
        if (stage && (k == 2 || k == 3)) { *(s16*)(e + 0x0C) = (s16)(GATHER[k - 2][0] / 10.0f); *(s16*)(e + 0x10) = (s16)(GATHER[k - 2][1] / 10.0f); }
        *(s16*)(e + 0x14) = GU[k][3];
        *(u16*)(e + 0x18) = 0x111;
        *(s16*)(e + 0x1A) = 10;
        gidx[ngidx++] = (u8)i;
        k++;
    }
    hman = 0;
    memclr_asm(gd, sizeof(gd));
}

static int Ashley(void) { return pPL && PLTYPE == 1 && STAGE == 1 && ROOM == 0x11; }
static int Alive(u8* e) { return e && (u32)e >= 0x80000000u && (u32)e < 0x81800000u && (*(u32*)e & 0x201) == 1; }

static u8* EmFind(int no)                            /* the live work made from list entry `no` */
{
    u32 n = *(u32*)((u8*)EMMGR + 4), i, sz = *(u32*)((u8*)EMMGR + 8);
    u8* base = *(u8**)EMMGR;
    if ((u32)base < 0x80000000u || (u32)base >= 0x81800000u || n > 1024 || sz < 0xC00 || sz > 0x40000) return 0;
    for (i = 0; i < n; i++) {
        u8* e = base + i * sz;
        if ((*(u32*)e & 0x201) == 1 && e[0x398] == (u8)no) return e;
    }
    return 0;
}

int CrouchActive(void);
static int InHouse(void)                             /* inside house C (both floors) */
{
    return PX() > -300.0f && PX() < 7800.0f && PZ() < -6500.0f && PZ() > -16500.0f;
}
static f32 Sn(f32 a)
{
    f32 a2;
    while (a > 3.14159265f) a -= 6.2831853f;
    while (a < -3.14159265f) a += 6.2831853f;
    if (a > 1.5707963f) a = 3.14159265f - a; else if (a < -1.5707963f) a = -3.14159265f - a;
    a2 = a * a;
    return a * (1.0f - a2 / 6.0f * (1.0f - a2 / 20.0f * (1.0f - a2 / 42.0f)));
}
static f32 Cs(f32 a) { return Sn(a + 1.5707963f); }
#define LEASH 4000.0f
static f32 Atan2f(f32 y, f32 x)                      /* atan2 (facing from x, z: atan2(dx, dz)) */
{
    f32 ax = x < 0 ? -x : x, ay = y < 0 ? -y : y, a, r;
    if (ax < 1e-6f && ay < 1e-6f) return 0.0f;
    r = ax > ay ? ay / ax : ax / ay;
    a = r * (0.9998660f + r * r * (-0.3302995f + r * r * (0.1801410f + r * r * (-0.0851330f + r * r * 0.0208351f))));
    if (ay > ax) a = 1.5707963f - a;
    if (x < 0) a = 3.14159265f - a;
    if (y < 0) a = -a;
    return a;
}
static void Native(u8* e)                            /* the game's own detection off */
{
    *(u32*)(e + 0x3C8) &= ~0x41u; *(f32*)(e + 0x3CC) = 0.0f;
    *(u32*)(e + 0x3E0) = (*(u32*)(e + 0x3E0) | 0x100) & ~0x08000000u;
}
static void Hold(Guard* g)                           /* guard where it stands: no game detection */
{
    u8* e = g->e;
    e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0;
    Native(e);
    g->st = G_HOLD; g->tm = 0;
}
static void Walk(Guard* g, f32 x, f32 z)
{
    u8* e = g->e;
    e[0xFD] = 0x14; e[0xFE] = 0; e[0xFF] = 0;
    *(f32*)(e + 0x92C) = x; *(f32*)(e + 0x930) = *(f32*)(e + 0x98); *(f32*)(e + 0x934) = z;
    Native(e);
    g->st = G_WALK; g->tm = 0; g->tx = x; g->tz = z;
}
static void Chase(Guard* g)                          /* the game's own chase (barn.c's release) */
{
    u8* e = g->e;
    *(f32*)(e + 0x3CC) = 20000.0f; *(u32*)(e + 0x3C8) |= 1u; *(u32*)(e + 0x3E0) &= ~0x100u;
    e[0xFD] = 0; e[0xFE] = 0; e[0xFF] = 0;
    g->st = G_CHASE; g->lost = 0; g->meter = 1.0f; g->role = R_NONE;
}
static void Turn(u8* e, f32 want, f32 step)          /* turn its facing toward `want` */
{
    f32 cur = *(f32*)(e + 0xA4), da = want - cur;
    while (da > 3.14159265f) da -= 6.2831853f;
    while (da < -3.14159265f) da += 6.2831853f;
    if (da > step) da = step; else if (da < -step) da = -step;
    cur += da;
    while (cur > 3.14159265f) cur -= 6.2831853f;
    while (cur < -3.14159265f) cur += 6.2831853f;
    *(f32*)(e + 0xA4) = cur;
}
static void Group(int k)                             /* to its place in the gathering west of the bonfire */
{
    Guard* g = &gd[k];
    int s = k == 2 ? 0 : k == 3 ? 1 : k == G_RUN0 ? 2 : 3;
    g->ax = GATHER[s][0]; g->az = GATHER[s][1]; g->bx = g->bz = 0.0f;
    g->role = R_GROUP;
    if (g->e && g->st != G_CHASE && k < G_RUN0) { g->leg = 3; Walk(g, VIA_X, VIA_Z); }   /* round the bonfire, north */
}
static u8 rrec[32] __attribute__((aligned(4)));
static u8* Spawn(f32 x, f32 y, f32 z, f32 ang, int type)    /* a torch Ganado (EmSetEvent) */
{
    u8* e;
    memclr_asm(rrec, 32);
    rrec[0] = 1; rrec[1] = 0x17; rrec[2] = (u8)type;
    *(u32*)(rrec + 4) = 0x00020000u;
    *(u16*)(rrec + 8) = 1000;
    *(s16*)(rrec + 0x0C) = (s16)(x / 10.0f); *(s16*)(rrec + 0x0E) = (s16)(y / 10.0f); *(s16*)(rrec + 0x10) = (s16)(z / 10.0f);
    *(s16*)(rrec + 0x14) = (s16)(ang * 16384.0f / 3.14159265f);
    *(u16*)(rrec + 0x18) = 0x111; *(s16*)(rrec + 0x1A) = 10;
    e = EM_SET_EVENT(rrec);
    return Alive(e) ? e : 0;
}

static void Guards(void)
{
    int k, alarm = -1, crouched = CrouchActive(), running = pPL[0xFC] == 0 && pPL[0xFD] == 3, inh = InHouse();
    f32 rv = running ? 13000.0f : crouched ? 7000.0f : 11000.0f;
    if (!road_wait && ph == 1 && !card) cyc++;
    for (k = 0; k < NG; k++) {
        Guard* g = &gd[k];
        u8* e = k < ngidx ? EmFind(gidx[k]) : (Alive(g->e) ? g->e : 0);
        f32 ex, ez, dx, dz, d, fw, ang, hx;
        if (k >= ngidx && k < G_RUN0) continue;
        if (k < ngidx && e != g->e) {                /* new room / new work: start guarding */
            g->e = e; g->meter = 0.0f; g->leg = 0; g->lost = 0; g->role = R_NONE;
            if (!e) continue;
            g->base = *(f32*)(e + 0xA4);
            g->ax = *(f32*)(e + 0x94); g->az = *(f32*)(e + 0x9C);          /* home */
            g->bx = BV[k][0]; g->bz = BV[k][1];
            if (stage && (k == 2 || k == 3)) { g->role = R_GROUP; g->bx = g->bz = 0.0f; }
            Hold(g);
        }
        if (!e || e[0xFC] != 1 || *(s16*)(e + 0x320) <= 0) continue;     /* hit, dying, being born... */
        ex = *(f32*)(e + 0x94); ez = *(f32*)(e + 0x9C);
        dx = PX() - ex; dz = PZ() - ez; d = Sq(dx * dx + dz * dz);
        if (g->st == G_CHASE) {
            if (inh && !key && stage < 2) {          /* she got into the house: they lay siege to it */
                int s = 0, j;
                for (j = 0; j < NG; j++) if (gd[j].role == R_SIEGE) s++;
                g->role = R_SIEGE; g->ax = SIEGE[s % 3][0]; g->az = SIEGE[s % 3][1]; g->bx = g->bz = 0.0f;
                Walk(g, g->ax, g->az);
                continue;
            }
            if (d > 15000.0f || (hidden && !g->lost)) g->lost++;
            else if (!hidden) g->lost = 0;
            if (g->lost > 120) { g->meter = 0.6f; g->leg = 2; Walk(g, g->ax, g->az); }   /* back home */
            continue;
        }
        Native(e);
        hx = (ex - g->ax) * (ex - g->ax) + (ez - g->az) * (ez - g->az);
        if (g->role == R_SIEGE && !inh && !scene) { Chase(g); continue; }   /* she came out: after her */
        if (k == 0 && !road_wait && g->role == R_NONE) {   /* the road guard: east half the cycle, west the other */
            int east = (cyc % CYC) < CYC / 2;
            f32 tx = east ? ROAD_E[0] : ROAD_W[0], tz = east ? ROAD_E[1] : ROAD_W[1];
            if (g->st == G_WALK && (g->tx != tx || g->tz != tz)) Walk(g, tx, tz);
            if (g->st == G_HOLD) {
                if (e[0xFD] != 1) { e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0; }
                if ((ex - tx) * (ex - tx) + (ez - tz) * (ez - tz) > 600.0f * 600.0f) Walk(g, tx, tz);
                else if (e[0xFE] == 1) *(f32*)(e + 0xA4) = (east ? 1.612f : -1.53f) + 0.2f * Sn((f32)cyc * 0.03f);
            } else {
                *(s32*)(e + 0x3E4) = 300;
                if (e[0xFD] != 0x14) { e[0xFD] = 0x14; e[0xFE] = 0; e[0xFF] = 0; }
                *(f32*)(e + 0x92C) = tx; *(f32*)(e + 0x934) = tz;
                if ((ex - tx) * (ex - tx) + (ez - tz) * (ez - tz) < 450.0f * 450.0f || ++g->tm > 600) Hold(g);
            }
        } else if (g->role == R_RUN) {               /* the runners: along their way, running in the scene */
            f32 tx = RUNWAY[g->leg][0], tz = RUNWAY[g->leg][1];
            if (scene_gate) {
                if (e[0xFD] != 0x11) { e[0xFD] = 0x11; e[0xFE] = 0; e[0xFF] = 0; }
            } else if (g->st != G_WALK || g->tx != tx || g->tz != tz) Walk(g, tx, tz);
            *(f32*)(e + 0x92C) = tx; *(f32*)(e + 0x930) = *(f32*)(e + 0x98); *(f32*)(e + 0x934) = tz;
            *(s32*)(e + 0x3E4) = 300;
            if ((ex - tx) * (ex - tx) + (ez - tz) * (ez - tz) < 900.0f * 900.0f) {
                if (g->leg + 1 < NRUN) g->leg++;
                else { g->leg = 0; Group(k); Walk(g, g->ax, g->az); }
            }
        } else if (g->role == R_LADDER) {            /* to the foot of the ladder, then after her */
            if (g->st != G_WALK) Walk(g, LADDER[0], LADDER[1]);
            *(s32*)(e + 0x3E4) = 300;
            if ((ex - LADDER[0]) * (ex - LADDER[0]) + (ez - LADDER[1]) * (ez - LADDER[1]) < 900.0f * 900.0f || ++g->tm > 900) Chase(g);
            continue;
        } else if (k == G_WATCH && g->role == R_NONE) {   /* the watch: at the crossing, then away, in step */
            int look = road_wait || (cyc % CYC) < CYC / 2;
            if (g->st != G_HOLD) { if (hx > 450.0f * 450.0f) { if (g->st != G_WALK) Walk(g, g->ax, g->az); *(s32*)(e + 0x3E4) = 300; } else Hold(g); }
            else {
                if (e[0xFD] != 1) { e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0; }
                if (hx > LEASH * LEASH) Walk(g, g->ax, g->az);
                else if (e[0xFE] == 1) Turn(e, (look ? 0.160f : -2.98f) + 0.15f * Sn((f32)cyc * 0.025f), 0.035f);
            }
        } else if (g->st == G_HOLD) {
            if (e[0xFD] != 1) { e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0; }
            g->tm++;
            if (g->role == R_SIEGE) {                /* at the house: faces it, restless */
                if (e[0xFE] == 1) Turn(e, 3.14159265f + 0.35f * Sn((f32)g->tm * 0.09f + (f32)k), 0.08f);
            } else if (g->role == R_GROUP) {         /* the gathering: looking all round */
                if (e[0xFE] == 1) Turn(e, g->base + 2.6f * Sn((f32)g->tm * 0.011f + (f32)k * 1.7f), 0.03f);
            } else if (k == 0 && road_wait) {        /* the road guard: back to her, still, until the turn */
                if (e[0xFE] == 1) *(f32*)(e + 0xA4) = g->base;
                g->tm = 0;
                if (PZ() < 5000.0f && ph == 1 && !card) road_wait = 0;
            } else if (e[0xFE] == 1) {               /* look slowly left and right */
                ang = g->base + 0.45f * Sn((f32)g->tm * 0.02f + (f32)k);
                while (ang > 3.14159265f) ang -= 6.2831853f;
                while (ang < -3.14159265f) ang += 6.2831853f;
                *(f32*)(e + 0xA4) = ang;
            }
            if (hx > LEASH * LEASH) { g->leg = 2; Walk(g, g->ax, g->az); }
            else if (g->role == R_NONE && !(k == 0 && road_wait) && g->tm > 110 && (g->bx != 0.0f || g->bz != 0.0f)) {
                g->leg = g->leg == 0 ? 1 : 0;
                Walk(g, g->ax + (g->leg ? g->bx : -g->bx), g->az + (g->leg ? g->bz : -g->bz));
            }
        } else if (g->st == G_WALK) {
            f32 tx = g->tx, tz = g->tz;
            *(s32*)(e + 0x3E4) = 300;                /* GuardWalk's timer: no wandering off */
            if (e[0xFD] != 0x14) { e[0xFD] = 0x14; e[0xFE] = 0; e[0xFF] = 0; }
            *(f32*)(e + 0x92C) = tx; *(f32*)(e + 0x934) = tz;
            if ((ex - tx) * (ex - tx) + (ez - tz) * (ez - tz) < 450.0f * 450.0f || ++g->tm > 900) {
                if (g->leg == 3) { g->leg = 0; Walk(g, g->ax, g->az); }
                else {
                    if (g->leg == 2) g->leg = 0;
                    if (g->role == R_GROUP) g->base = Atan2f(ex - STABLE_X, ez - STABLE_Z);
                    Hold(g);
                }
            }
        }
        /* the alert meter */
        if (!hidden && ph == 1 && !scene && !card && g->role != R_SIEGE && g->role != R_RUN) {
            f32 dy = PY() - *(f32*)(e + 0x98), rate = 0.0f, r = rv;
            if (dy < 0.0f) dy = -dy;
            if (g->role == R_GROUP) r = crouched ? 0.0f : running ? 24000.0f : 20000.0f;   /* crouched: unseen */
            if (dy < 2500.0f) {
                fw = (d > 1.0f) ? (dx * Sn(*(f32*)(e + 0xA4)) + dz * Cs(*(f32*)(e + 0xA4))) / d : 1.0f;
                if (fw > 0.5f && d < r) rate = 0.012f + 0.05f * (1.0f - d / r);
                if (d < (g->role == R_GROUP ? 1500.0f : 1800.0f)) rate += crouched ? 0.03f : 0.08f;
                if (running && d < 6000.0f) rate += 0.05f;
            }
            if (rate > 0.0f) g->meter += rate; else { g->meter -= 0.006f; if (g->meter < 0.0f) g->meter = 0.0f; }
            if (g->meter >= 1.0f) alarm = k;
        } else { g->meter -= 0.006f; if (g->meter < 0.0f) g->meter = 0.0f; }
    }
    if (alarm >= 0) {                                /* found: it and the ones near it */
        u8* a = gd[alarm].e;
        for (k = 0; k < NG; k++) {
            Guard* g = &gd[k];
            f32 dx, dz;
            if (!Alive(g->e) || g->st == G_CHASE || g->e[0xFC] != 1 || g->role == R_RUN || g->role == R_SIEGE) continue;
            dx = *(f32*)(g->e + 0x94) - *(f32*)(a + 0x94); dz = *(f32*)(g->e + 0x9C) - *(f32*)(a + 0x9C);
            if (k == alarm || dx * dx + dz * dz < 10000.0f * 10000.0f) Chase(g);
        }
    }
}
/* hud.c: guard k's marker: world position over its head and level (0 none, 1-99 meter, 100 found) */
int Ch0Mark(int k, f32* x, f32* y, f32* z)
{
    Guard* g;
    if (!on || !ready || ph != 1 || scene || scene_gate || caught || card || k >= NG) return 0;
    g = &gd[k];
    if (!Alive(g->e) || g->e[0xFC] != 1) return 0;
    *x = *(f32*)(g->e + 0x94); *y = *(f32*)(g->e + 0x98) + 2050.0f; *z = *(f32*)(g->e + 0x9C);
    if (g->st == G_CHASE) return 100;
    if (g->meter < 0.03f) return 0;
    return (int)(g->meter * 99.0f) + 1;
}
static const f32 HIDE[][3] = {                       /* hiding places: x, z, radius */
    { -5578.0f, 12832.0f, 1300.0f },                 /* the stable (cow) */
};
#define NHIDE (int)(sizeof(HIDE) / sizeof(HIDE[0]))
static int HideSpot(void)                            /* the hiding place Ashley is at, or -1 */
{
    int i;
    for (i = 0; i < NHIDE; i++) if (D2(HIDE[i][0], HIDE[i][1]) < HIDE[i][2] * HIDE[i][2] && PY() < 1500.0f) return i;
    return -1;
}
static void HideFrame(u16 trg)
{
    int k;
    if (!hidden) {
        if ((trg & PAD_A) && HideSpot() >= 0 && pPL[0xFC] == 0) {
            hidden = 1; hide_no = HideSpot(); ch0_crouch_force = 1;
            for (k = 0; k < ngidx; k++) {            /* a chaser near enough sees her go in */
                Guard* g = &gd[k];
                if (g->e && g->st == G_CHASE) {
                    f32 dx = *(f32*)(g->e + 0x94) - PX(), dz = *(f32*)(g->e + 0x9C) - PZ();
                    if (dx * dx + dz * dz < 4000.0f * 4000.0f) { hidden = 0; ch0_crouch_force = 0; return; }
                }
            }
        }
        return;
    }
    ch0_padlock = 1;                                 /* still, crouched; Cross: out */
    if (trg & PAD_A) { hidden = 0; ch0_crouch_force = 0; ch0_padlock = 0; }
}
int Ch0Card(void) { if (!on || !card) return 0; return card == 1 ? (card_t < 12 ? card_t * 255 / 12 : 255) : 255 - card_t * 255 / 12; }
int Ch0Hide(void) { if (!on || !ready || ph != 1 || scene || caught || card) return 0; return hidden ? 2 : (HideSpot() >= 0 ? 1 : 0); }

/* SceAt areas (pS->ot): doors off for the chapter; the bed's own check off until the key is taken */
static u8* OtNext(u8* p)
{
    u32 v;
    while ((v = *(u32*)p) != 0xFFFFFFFFu) {
        p = (u8*)(v | 0x80000000u);
        if ((s32)v < 0) return p;
    }
    return 0;
}
static void Areas(void)
{
    u8* p; int n = 0;
    if (!pS) return;
    for (p = OtNext(pS + 140); p && n < 400; p = OtNext(p), n++) {
        f32* q = (f32*)(p + 0x14); f32 cx, cz; u8 at = p[0x4A];
        if (p[0x35] == 1) { p[0x34] &= ~1; continue; }                     /* doors */
        if (key || p[0x35] == 0x10 || at == 2 || at == 4 || at == 5 || at == 26) continue;
        if (*(f32*)(p + 0x08) < 2500.0f) continue;                          /* upstairs only */
        if (p[0x05] == 1) { cx = (q[0] + q[2] + q[4] + q[6]) * 0.25f; cz = (q[1] + q[3] + q[5] + q[7]) * 0.25f; }
        else { cx = q[0]; cz = q[1]; }
        if ((cx - KX) * (cx - KX) + (cz - KZ) * (cz - KZ) < 1800.0f * 1800.0f) p[0x34] &= ~1;   /* the bed's "check" */
    }
}

static void Cam(f32 cx, f32 cy, f32 cz, f32 tx, f32 ty, f32 tz, f32 fovy)
{
    CAMP[0] = cx; CAMP[1] = cy; CAMP[2] = cz; CAMP[3] = tx; CAMP[4] = ty; CAMP[5] = tz; CAMP[6] = 0.0f; CAMP[7] = fovy;
    CAMP[8] = 0.0f; CAMP[9] = 1.0f; CAMP[10] = 0.0f;
    {   /* barn.c B100: pG->Camera.mat (cull frustum) rebuilt from the scene camera */
        f32* m = (f32*)(pG + 0x74);
        f32 lx = cx - tx, ly = cy - ty, lz = cz - tz, rx, rz, ux, uy, uz, n;
        n = Sq(lx * lx + ly * ly + lz * lz); if (n < 1.0f) n = 1.0f; lx /= n; ly /= n; lz /= n;
        rx = lz; rz = -lx;
        n = Sq(rx * rx + rz * rz); if (n < 1e-4f) { rx = 1.0f; rz = 0.0f; n = 1.0f; }
        rx /= n; rz /= n;
        ux = ly * rz; uy = lz * rx - lx * rz; uz = -ly * rx;
        m[0] = rx; m[1] = ux; m[2] = lx; m[3] = cx;
        m[4] = 0.0f; m[5] = uy; m[6] = ly; m[7] = cy;
        m[8] = rz; m[9] = uz; m[10] = lz; m[11] = cz;
        m = (f32*)(pG + 0x74 + 0xC4);
        m[0] = ux; m[1] = uy; m[2] = uz; m[3] = lx; m[4] = ly; m[5] = lz; m[6] = rx; m[7] = 0.0f; m[8] = rz;
    }
}

static u8 hrec[32] __attribute__((aligned(4)));
static u8* HouseGanado(f32 x, f32 z, f32 ang)        /* a torch Ganado (EmSetEvent), born without bit 1 */
{
    u8* e;
    memclr_asm(hrec, 32);
    hrec[0] = 1; hrec[1] = 0x17; hrec[2] = 0;
    *(u32*)(hrec + 4) = 0x00020000u;
    *(u16*)(hrec + 8) = 1000;
    *(s16*)(hrec + 0x0C) = (s16)(x / 10.0f); *(s16*)(hrec + 0x10) = (s16)(z / 10.0f);
    *(s16*)(hrec + 0x14) = (s16)(ang * 16384.0f / 3.14159265f);
    *(u16*)(hrec + 0x18) = 0x111; *(s16*)(hrec + 0x1A) = 30;
    e = EM_SET_EVENT(hrec);
    if (!Alive(e)) return 0;
    hman_t = 0;
    return e;
}

/* intro timeline, in main-loop frames (C0-03: the user's 'Scared' clip and a camera from her feet up) */
#define T_TXT_IN   40
#define T_TXT_FULL 70
#define T_TXT_OUT  160
#define T_TXT_GONE 190
#define T_FADE_IN  215
#define T_LIT      265
#define T_WALK     232
#define T_STOP     (T_WALK + 48)
#define T_SC_END   (T_STOP + 111)           /* 37 clip frames at 10 fps */
#define T_SAY      (T_STOP + 55)
#define T_FREE     (T_SC_END + 30)
void ScaredApply(f32 f, f32 k);                      /* crouch.c */
static f32 Sm(f32 x) { if (x <= 0.0f) return 0.0f; if (x >= 1.0f) return 1.0f; return x * x * (3.0f - 2.0f * x); }
static void IntroCam(void)                           /* from her feet, in front, up to her whole body */
{
    f32 a = *(f32*)(pPL + 0xA4), fx = Sn(a), fz = Cs(a), u, dist, ch, th, sx;
    if (t < T_FADE_IN) return;
    u = Sm((f32)(t - (T_STOP - 20)) / 110.0f);
    dist = 1400.0f + 1400.0f * u; ch = 180.0f + 1150.0f * u; th = 110.0f + 1000.0f * u; sx = 250.0f + 250.0f * u;
    STOPF |= SPF_CAM;
    Cam(PX() + fx * dist + fz * sx, PY() + ch, PZ() + fz * dist - fx * sx, PX(), PY() + th, PZ(), 42.0f + 8.0f * u);
}
static void Msg(int m) { msg = m; msg_t = 0; }       /* texts: 1 locked, 2 key, 3 opens */

static void Runners(int at_gate)                     /* the two from the south gate */
{
    int j;
    for (j = 0; j < 2; j++) {
        Guard* g = &gd[G_RUN0 + j];
        memclr_asm(g, sizeof(*g));
        g->e = at_gate ? Spawn(RUN0[j][0], RUN0[j][1], RUN0[j][2], 3.0f, j ? 1 : 3)
                       : Spawn(GATHER[2 + j][0], 0.0f, GATHER[2 + j][1], 0.0f, j ? 1 : 3);
        if (!g->e) continue;
        g->ax = GATHER[2 + j][0]; g->az = GATHER[2 + j][1];
        if (at_gate) { g->role = R_RUN; g->leg = 0; g->st = G_WALK; }
        else { g->role = R_GROUP; g->base = Atan2f(g->ax - STABLE_X, g->az - STABLE_Z); Hold(g); }
    }
}
static void AfterKey(void)                           /* some go in after her, the others to the ladder */
{
    int k, n = 0;
    for (k = 0; k < NG; k++) {
        Guard* g = &gd[k];
        if (!Alive(g->e) || (g->role != R_GROUP && g->role != R_SIEGE)) continue;
        if (n++ & 1) { g->role = R_LADDER; Walk(g, LADDER[0], LADDER[1]); }
        else Chase(g);
    }
}
static void Block(void)                              /* behind the boxes: Ashley can't get through */
{
    int i;
    if (PY() > 1500.0f) return;
    for (i = 0; i < 3; i++) {
        f32 r = BLK[i][3] * 0.5f + 300.0f, dx = PX() - BLK[i][0], dz = PZ() - BLK[i][1], d2 = dx * dx + dz * dz, d;
        if (d2 >= r * r) continue;
        d = Sq(d2); if (d < 1.0f) { dx = 1.0f; dz = 0.0f; d = 1.0f; }
        *(f32*)(pPL + 0x94) = BLK[i][0] + dx / d * r;
        *(f32*)(pPL + 0x9C) = BLK[i][1] + dz / d * r;
    }
}
/* C0-09: the boxes. Making new ones (EtcModelSet in the middle of play, C0-08) showed nothing; now the room's
 * own eight boxes (ETS id 1 / 2, r111 entries 14-21) are moved into the passages just before the room sets its
 * etc models (hook at EtcModelListSet's entry, PAL 0x80106B68), the way the game itself places them. */
static const f32 BOXY[3] = { 0.0f, 0.0f, 286.0f };  /* the ground of each passage (the room's floors) */
void Ch0Ets(u8* list)
{
    int i, b = 0, j = 0, c;
    u16 n;
    if (!on || !pG || STAGE != 1 || ROOM != 0x11 || !list) return;
    n = *(u16*)list;
    for (i = 0; i < n && b < 3; i++) {
        u8* d = list + 0x10 + i * 0x28;
        f32 o;
        if (*(u16*)d != 1 && *(u16*)d != 2) continue;
        c = (int)BLK[b][4];
        o = ((f32)j - (f32)(c - 1) * 0.5f) * (BLK[b][3] / (f32)c);
        *(f32*)(d + 0x10) = 0.0f; *(f32*)(d + 0x14) = BLK[b][2] + 0.3f * (f32)j; *(f32*)(d + 0x18) = 0.0f;
        *(f32*)(d + 0x1C) = BLK[b][0] + Sn(BLK[b][2]) * o;
        *(f32*)(d + 0x20) = BOXY[b];
        *(f32*)(d + 0x24) = BLK[b][1] + Cs(BLK[b][2]) * o;
        if (++j >= c) { j = 0; b++; }
    }
}
static void Restart(void)                            /* caught: the room again from the checkpoint */
{
    hidden = 0; ch0_crouch_force = 0;
    if (!cp) { road_wait = 1; cyc = 0; stage = 0; }
    scene_gate = 0;
    PL_LIFE = PL_LIFE_MAX;
    ready = 0; scene = 0; caught = 0; ch0_padlock = 1; msg = 0;
    ROOM_JUMP(0x111, cp ? &kpos : &apos, cp ? &krot : &arot, 0);
}

#define S_LEN      185                               /* the house scene */

void Ch0Frame(void)
{
    u16 pad, trg;
    if (!on || !pG) { ch0_padlock = 0; ch0_stick = 0; return; }
    pad = barn_pad; trg = pad & ~pad_old; pad_old = pad;
    if (!ready) {                                    /* still loading: keep it black and still */
        ch0_padlock = 1; ch0_stick = 0;
        if (Ashley()) {
            ready = 1; t = 0;
            if (ph == 0) Hud(0); else { ch0_padlock = 0; Hud(1); }
            if (ph == 1 && stage >= 1) Runners(0);
            if (ph == 1 && cp == 1 && !Alive(hman)) hman = HouseGanado(DOOR_IN_X, DOOR_IN_Z - 900.0f, 3.02f);
            if (ph == 1 && key) after_key = 30;
        }
        return;
    }
    if (!Ashley()) return;                           /* menus, death screen... */
    t++;
    if (msg) msg_t++;
    if (msg && msg != 3 && msg_t > 150) msg = 0;
    Areas();
    if (ph == 1 && !caught && !scene && !card) ch0_padlock = 0;
    Guards();
    if (Alive(hman)) {                               /* born without bit 1 (else it stays hidden, barn.c B94) */
        hman_t++;
        if (hman_t == 6) *(u32*)(hman + 0x3C8) |= 1u;
    }
    if (ph == 0) {
        ch0_padlock = 1; ch0_stick = 0;
        if (t >= T_WALK && t < T_STOP) { ch0_stick = 1; ch0_sx = 0; ch0_sy = 56; }     /* four steps */
        IntroCam();
        if (t >= T_STOP) {                           /* the scared clip: in, then a slow fade on its last frame */
            f32 k = Sm((f32)(t - T_STOP) / 14.0f), f = (f32)(t - T_STOP) * (10.0f / 30.0f);
            if (t >= T_SC_END) { k = 1.0f - Sm((f32)(t - T_SC_END) / 30.0f); f = 36.99f; }
            if (f > 36.99f) f = 36.99f;
            ScaredApply(f, k);
        }
        if (t >= T_FREE) { ph = 1; ch0_stick = 0; STOPF &= ~SPF_CAM; card = 1; card_t = 0; }
        return;
    }
    if (ph == 1 && card) {                           /* the level's card: Cross closes it */
        ch0_padlock = 1;
        card_t++;
        if (card == 1 && card_t > 30 && (trg & PAD_A)) { card = 2; card_t = 0; }
        if (card == 2 && card_t > 12) { card = 0; ch0_padlock = 0; Hud(1); }
        return;
    }
    if (ph == 1) {
        if (caught) {                                /* knocked down: fade, text, again */
            cap_t++;
            ch0_padlock = 1;
            if (cap_t == 170) Restart();
            return;
        }
        if (scene_gate) {                            /* the south gate: two of them run in */
            scene_gate++;
            ch0_padlock = 1;
            STOPF |= SPF_CAM;
            {
                f32 k = Sm((f32)scene_gate / 150.0f);
                Cam(-13300.0f - 600.0f * k, 2900.0f + 300.0f * k, 18800.0f + 1500.0f * k, -15200.0f + 1800.0f * k, 3300.0f - 1200.0f * k, 27500.0f - 5000.0f * k, 48.0f);   /* C0-09: the alley climbs to 2.6 m */
            }
            if (scene_gate >= 160) { scene_gate = 0; stage = 1; STOPF &= ~SPF_CAM; ch0_padlock = 0; Hud(1); }
            return;
        }
        Block();
        if (after_key && --after_key == 0) AfterKey();
        if (stage == 0 && !scene && D2(STABLE_X, STABLE_Z) < 2500.0f * 2500.0f) {   /* passing the stable */
            scene_gate = 1; Hud(0);
            Runners(1); Group(2); Group(3);
            return;
        }
        if (pPL[0xFC] == 1 && !scene) { caught = 1; cap_t = 0; msg = 0; hidden = 0; ch0_crouch_force = 0; Hud(0); return; }
        if (scene) {                                 /* the Ganado comes in downstairs */
            scene++;
            ch0_padlock = 1;
            STOPF |= SPF_CAM;
            {   /* C0-07: banging on the door from outside (the camera shakes with each blow), then one comes in */
                f32 sh = 0.0f;
                int b = scene < 30 ? -1 : (scene - 30) % 22, k, in = 0;
                if (scene >= 30 && scene < 96 && b < 7) sh = (f32)(7 - b) * 9.0f * ((b & 1) ? 1.0f : -1.0f);
                if (scene == 100) {                  /* C0-09: one always comes in (C0-08: nobody did) */
                    for (k = 0; k < NG && !in; k++) if (gd[k].role == R_SIEGE && Alive(gd[k].e)) in = k + 1;
                    if (!in) {                       /* none at the door: the nearest one is put there */
                        f32 best = 1e12f, dx, dz;
                        for (k = 0; k < NG; k++) {
                            u8* e = gd[k].e;
                            if (!Alive(e) || e[0xFC] != 1 || k == 0) continue;
                            dx = *(f32*)(e + 0x94) - DOOR_OUT_X; dz = *(f32*)(e + 0x9C) - DOOR_OUT_Z;
                            if (dx * dx + dz * dz < best) { best = dx * dx + dz * dz; in = k + 1; }
                        }
                    }
                    if (in) {
                        u8* e = gd[in - 1].e;
                        *(f32*)(e + 0x94) = *(f32*)(e + 0x110) = DOOR_OUT_X;
                        *(f32*)(e + 0x98) = *(f32*)(e + 0x114) = 0.0f;
                        *(f32*)(e + 0x9C) = *(f32*)(e + 0x118) = DOOR_OUT_Z;
                        *(f32*)(e + 0xA4) = 3.02f;
                        Chase(&gd[in - 1]);
                    } else if (!Alive(hman)) hman = HouseGanado(DOOR_OUT_X, DOOR_OUT_Z, 3.02f);
                }
                Cam(5644.0f + sh, 1500.0f + sh * 0.5f, -9300.0f, DOOR_IN_X, 900.0f, DOOR_IN_Z, 50.0f);
            }
            if (scene >= S_LEN) { scene = 0; STOPF &= ~SPF_CAM; ch0_padlock = 0; Hud(1); stage = 2; AfterKey(); }
            return;
        }
        HideFrame(trg);
        if (hidden) return;
        if (!key) {
            f32 dy = PY() - KY;
            if (D2(KX, KZ) < 1300.0f * 1300.0f && dy > -500.0f && dy < 500.0f && (trg & PAD_A)) {
                key = 1; cp = 1; Msg(2); scene = 1; Hud(0);
                return;
            }
        }
        if (D2(BX, BZ) < 1800.0f * 1800.0f) {
            if (!key) { if (!b_seen) { b_seen = 1; Msg(1); } }
            else if (pPL[0xFC] == 0) { int k; ph = 2; endt = 0; ch0_padlock = 1; Hud(0); Msg(3);
                for (k = 0; k < NG; k++) if (Alive(gd[k].e) && gd[k].e[0xFC] == 1) Hold(&gd[k]);   /* C0-09: everyone stops */
                if (Alive(hman)) { *(u32*)(hman + 0x3C8) &= ~1u; Native(hman); hman[0xFD] = 1; hman[0xFE] = 0; } }
        } else if (D2(BX, BZ) > 4000.0f * 4000.0f) b_seen = 0;
        return;
    }
    if (ph == 2) {
        endt++;
        ch0_padlock = 1;
        if (endt >= 170 && pPL[0xFC] == 0) {     /* C0-09: never while she is being hit (the C0-08 crash) */
            done = 1; on = 0; ch0_padlock = 0; msg = 0; hidden = 0; ch0_crouch_force = 0;
            PL_SELECT(0);
            EMLIST_NO = -1;                          /* r100 reads Leon's list again */
            ROOM_JUMP(0x100, &lpos, &lrot, larg);
        }
    }
}

/* drawing (hud.c) */
static int Ramp(int a, int b, int x) { if (x <= a) return 0; if (x >= b) return 255; return (x - a) * 255 / (b - a); }
int Ch0Black(void)
{
    if (!on) return 0;
    if (!ready) return 255;
    if (ph == 0) return 255 - Ramp(T_FADE_IN, T_LIT, t);
    if (ph == 1 && caught) return Ramp(40, 90, cap_t);
    if (ph == 2) return Ramp(60, 100, endt);
    return 0;
}
/* line k: 0 "Hace 11 horas", 1 Ashley's line, 2 locked (two lines), 3 key prompt, 4 key taken,
 * 5 the door opens, 6 caught, 7 end of Part 1; returns its alpha */
int Ch0Text(int k)
{
    if (!on || !ready) return 0;
    if (ph == 0) {
        if (k == 0) { if (t < T_TXT_FULL) return Ramp(T_TXT_IN, T_TXT_FULL, t); return 255 - Ramp(T_TXT_OUT, T_TXT_GONE, t); }
        if (k == 1) { if (t < T_SAY + 15) return Ramp(T_SAY, T_SAY + 15, t); return 255 - Ramp(T_FREE - 15, T_FREE, t); }
        return 0;
    }
    if (k == 3) {
        f32 dy;
        if (key || scene || caught || ph != 1 || !Ashley()) return 0;
        dy = PY() - KY;
        return D2(KX, KZ) < 1300.0f * 1300.0f && dy > -500.0f && dy < 500.0f ? 255 : 0;
    }
    if (k == 2 && msg == 1) return msg_t < 120 ? Ramp(0, 10, msg_t) : 255 - Ramp(120, 150, msg_t);
    if (k == 4 && msg == 2) return msg_t < 120 ? Ramp(0, 10, msg_t) : 255 - Ramp(120, 150, msg_t);
    if (k == 5 && msg == 3) return 255 - Ramp(50, 70, msg_t);
    if (k == 6 && caught) return Ramp(70, 90, cap_t);
    if (k == 7 && ph == 2) return Ramp(100, 120, endt);
    return 0;
}
int Ch0Coords(int i)                                  /* test: Ashley x, y, z; -999999 = off */
{
    if (!on || !ready || ph != 1 || caught || scene || card || !Ashley()) return -999999;
    return (int)*(f32*)(pPL + 0x94 + 4 * i);
}
