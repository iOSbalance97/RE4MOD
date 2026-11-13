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
 *   first and then back toward the start (not past her) once she is round the south side.
 * C0-10 (user): the game's own texts in the game's own message window (door B's "Está cerrada y no se abre..."
 *   and "Has usado la Llave de la insignia." from r101; Ashley's line in the game's letters); the key is the
 *   game's own item (0x3B, the Insignia Key r101 asks for) lying on the bed, picked up the game's way; every
 *   item of the rooms (Leon's ammo, money, herbs...) is gone; the house scene opens the door (cEmDoor::setOpen)
 *   and the Ganado walks in; door B with the key leads on to the road to the church (r112, the farm at night)
 *   and its far end (the way down to the cemetery, r118) ends Part 1. */
#include "game.h"
#include "ch0_msg.h"
#include "ch0_key.h"

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
static int key, b_seen, caught, cap_t, cp;      /* cp: checkpoint 0 start, 1 the bed */
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
enum { R_NONE, R_GROUP, R_RUN, R_SIEGE, R_LADDER, R_PAT, R_RING, R_DOOR = 9, R_UP = 10 };
/* C0-14: the house's stairs (SAT ramp y 0 -> 3200): foot, top */
static const f32 UPW[2][2] = { { 3600.0f, -10300.0f }, { 3600.0f, -15100.0f } };
#define HOUSE_X 3000.0f                              /* the key house, roughly its middle */
#define HOUSE_Z (-11000.0f)
typedef struct { u8* e; u8 st, role, leg, vis, pat, pad[3]; f32 base, meter, ax, az, bx, bz, tx, tz; int tm, lost; } Guard;
static int scene_gate, after_key;                    /* C0-07: the south gate scene (frames); split after a restart */
static int cyc;                                      /* C0-06: road / watch cycle */
static int cyc2;                                     /* C0-10b: north-east / square cycle */
int ch0_got;                                         /* item.c: the key has been taken */
static int stage;                                    /* C0-07: 0 start, 1 the gate scene done (grouped), 2 the key */
static Guard gd[12];
static int hidden, hide_no, card, card_t, road_wait;
static int scene_n, watch_on, rw, kwait;
static int scene_x, x_done, grab;                    /* C0-14: out of the house scene; a chaser at arm's length */
static u8 ins[3];                                    /* C0-14: the three who come in (gd index + 1) */
static u8* hdoor;
static int keep_open;                   /* C0-12: the north crossing scene */

#define BX 19713.0f                                  /* door B */
#define BZ 2003.0f
#define KX 2329.0f                                   /* the bed */
#define KY 3199.0f
#define KZ (-9063.0f)
#define DOOR_OUT_X 7169.0f                           /* house C's door, outside / inside (user's video) */
#define DOOR_OUT_Z (-5545.0f)
#define DOOR_IN_X 7309.0f
#define DOOR_IN_Z (-6724.0f)
#define HDOOR_X 6540.0f                              /* house C's door model (ETS 2, et03: the hinge) */
#define HDOOR_Z (-6422.0f)
#define KEY_ID 0x3B                                  /* the Insignia Key (r101's iron door to the farm) */
static const f32 KEYP[3] = { 2400.0f, 3965.0f, -8450.0f };   /* on the bed (its top, EAT: y 3900-3950) */
static Vec fpos = { -19691.0f, 0.0f, -19088.0f }, frot = { 0.0f, 0.988f, 0.0f };
#define EX (-4050.0f)                                /* r112's way down to the cemetery (r118): the end */
#define EZ 51612.0f
static int talk_t;                                   /* the message on screen: frames left */
static int door_in;                                  /* C0-10: gd index + 1 of the one who comes in */
static u32 talk_attr;

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
    on = 1; ph = 0; t = 0; ready = 0; endt = 0; key = 0; b_seen = 0; cp = 0; caught = 0; scene = 0; door_in = 0; talk_t = 0; ch0_got = 0; cyc2 = 0; scene_n = 0; watch_on = 0; scene_x = 0; x_done = 0; grab = 0; keep_open = 0;
}

/* the guards (user's map, snapped to the ground, 0.9 m clear of walls): pos (mm), facing (s16, pi/0x4000), type
 * C0-07: the two of the south alley are gone from the start: they come in by the south gate later. */
static const s16 GU[][5] = {
    { -27951, 0,   9471,   8407,  0 },   /* 0 road, just past the start */
    { -15500, 0,  -8800, -8192,  3 },   /* 1 the watch: C0-12 born in the north crossing's scene (Spawn) */
    {  10400, 0,   -800,  8192, 12 },   /* 2, 3 C0-12: the square pair, patrolling from the start */
    {  11200, 897,  8400,  1500,  0 },
    {  22500, 2025, -21800, 12308,  3 },   /* 4 C0-10b: out of the house, the north-east road (patrol) */
    {  15561, 978, -19534,  -6931,  1 },
};
#define NGU (int)(sizeof(GU) / sizeof(GU[0]))
#define G_RUN0 NGU                       /* the two who run in by the south gate (EmSetEvent) */
#define NG (NGU + 2)
#define G_WATCH 1
#define CYC 600
static const f32 ROAD_W[2] = { -27951.0f, 9471.0f }, ROAD_E[2] = { -22081.0f, 9007.0f };
/* the crossing: (-14239, 7377); the watch looks at it at 0.160 rad, away = -2.98 */
static const f32 BV[NGU][2] = { { 0, 0 }, { 0, 0 }, { 0, 1250 }, { 0, 1250 }, { 0, 0 }, { 0, 0 } };
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
static const f32 LADDER[2] = { -5600.0f, -17300.0f };   /* C0-10b: the key house's ladder (ETS 5, id 6) */
/* C0-10b: patrols (user): waypoints; end 0 / end n-1 by the cycles. The watch: north (away) / south (looking at
 * the crossing), in step with the road guard as before; the north-east one: the gate / almost the square; the
 * square pair after the stable: west / east. The north-east one and the pair are away at the same time (the
 * first half of cyc2): the way from B to the house is clear then. */
typedef struct { f32 x[4], z[4]; int n, loop, hold; f32 fa, fb; } Pat;
static const Pat PATS[4] = {
    /* 1 the watch (C0-12, user): a T behind the north houses: the junction, west along the back, the junction,
       south to the square; it stops and looks round at the two ends (hold bits) */
    { { -13200.0f, -21000.0f, -13200.0f, -13200.0f }, { -8000.0f, -9000.0f, -8000.0f, 1000.0f }, 4, 1, 0xA, 0.0f, 0.0f },
    { { 22500.0f, 15800.0f, 14600.0f }, { -21800.0f, -13500.0f, -10500.0f }, 3, 0, 0, 2.36f, -0.5f },   /* 2 NE */
    /* 3, 4 the square pair (C0-12): the square / back east where they were; the south one round the walls */
    { { -3200.0f, 10400.0f }, { -1600.0f, -800.0f }, 2, 0, 0, -1.571f, 1.571f },
    { { -3200.0f, 8000.0f, 10800.0f, 11200.0f }, { 6400.0f, 2000.0f, 4000.0f, 8400.0f }, 4, 0, 0, -1.571f, 0.3f },
};
#define CYC2 1200                                                   /* foot of the ladder up */

/* hook at EmSetFromList's entry: r111's list -> our guards */
void Ch0EmList(void)
{
    int i, k = 0;
    if (!on || !pG || STAGE != 1) return;
    if (ROOM == 0x12) {                              /* C0-10: the road to the church, empty for now */
        for (i = 0; i < 256; i++) {
            u8* e = EMLIST(i);
            if (*(u16*)(e + 0x18) == 0x112) { e[0] = 0; e[1] = 0; }
        }
        ngidx = 0; hman = 0;
        memclr_asm(gd, sizeof(gd));
        return;
    }
    if (ROOM != 0x11) return;
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
        *(u32*)(e + 4) = 0x04000000u;                /* C0-12: torch (0x04000000 -> Wep 6); 0x20000 was dynamite */
        *(u16*)(e + 8) = 1000;
        *(s16*)(e + 0x0C) = GU[k][0] / 10; *(s16*)(e + 0x0E) = GU[k][1] / 10; *(s16*)(e + 0x10) = GU[k][2] / 10;
        *(s16*)(e + 0x14) = GU[k][3];
        if (k == G_WATCH) e[0] = 0;                  /* C0-12: the watch comes in its own scene (Spawn) */
        *(u16*)(e + 0x18) = 0x111;
        *(s16*)(e + 0x1A) = 10;
        gidx[ngidx++] = (u8)i;
        k++;
    }
    hman = 0;
    memclr_asm(gd, sizeof(gd));
}

static int Ashley(void) { return pPL && PLTYPE == 1 && STAGE == 1 && (ROOM == 0x11 || ROOM == 0x12); }
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
    *(u32*)(rrec + 4) = 0x04000000u;
    *(u16*)(rrec + 8) = 1000;
    *(s16*)(rrec + 0x0C) = (s16)(x / 10.0f); *(s16*)(rrec + 0x0E) = (s16)(y / 10.0f); *(s16*)(rrec + 0x10) = (s16)(z / 10.0f);
    *(s16*)(rrec + 0x14) = (s16)(ang * 16384.0f / 3.14159265f);
    *(u16*)(rrec + 0x18) = 0x111; *(s16*)(rrec + 0x1A) = 10;
    e = EM_SET_EVENT(rrec);
    return Alive(e) ? e : 0;
}

/* C0-10b: line of sight through the effect collision (walls, fences...): cSatMgr::hitCheck on EatMgr (PAL
 * 0x800B7FE0 / 0x8027DE48), the game's own sight check (em36: 0 = nothing in between). Eyes at 1.5 m, Ashley's
 * chest at 1.2 m standing, 0.7 m crouched. */
#define EATMGR   ((void*)0x8027DE48)
#define HITCHECK ((int (*)(void*, Vec*, Vec*, Vec*, Vec*, int, int))0x800B7FE0)
static int Los(u8* e, int crouched)
{
    Vec a, b, c;
    a.x = *(f32*)(e + 0x94); a.y = *(f32*)(e + 0x98) + 1500.0f; a.z = *(f32*)(e + 0x9C);
    b.x = PX(); b.y = PY() + (crouched ? 700.0f : 1200.0f); b.z = PZ();
    return HITCHECK(EATMGR, &a, &b, &c, 0, 0, 0) == 0;
}
static void Steer(u8* e, f32 tx, f32 tz)              /* C0-12: walking straight at its target (no feints) */
{
    f32 dx = tx - *(f32*)(e + 0x94), dz = tz - *(f32*)(e + 0x9C);
    if (dx * dx + dz * dz > 300.0f * 300.0f) Turn(e, Atan2f(dx, dz), 0.12f);
}
static int PatNear(const Pat* p, f32 x, f32 z)
{
    int i, b = 0;
    f32 bd = 1e18f;
    for (i = 0; i < p->n; i++) {
        f32 dd = (p->x[i] - x) * (p->x[i] - x) + (p->z[i] - z) * (p->z[i] - z);
        if (dd < bd) { bd = dd; b = i; }
    }
    return b;
}
static void Patrol(int k, int pat)                   /* guard k walks patrol `pat` (1-4) */
{
    Guard* g = &gd[k];
    g->pat = (u8)pat; g->role = R_PAT;
    if (g->e) g->leg = (u8)PatNear(&PATS[pat - 1], *(f32*)(g->e + 0x94), *(f32*)(g->e + 0x9C));
}
static int PatSide(int pat)                          /* 1: toward the last waypoint */
{
    if (pat == 1) return (road_wait || (cyc % CYC) < CYC / 2) ? 1 : 0;
    return (cyc2 % CYC2) >= CYC2 / 2;
}

static void Guards(void)
{
    int k, alarm = -1, crouched = CrouchActive(), running = pPL[0xFC] == 0 && pPL[0xFD] == 3, inh = InHouse();
    f32 rv = running ? 13000.0f : crouched ? 7000.0f : 11000.0f;
    if (!road_wait && ph == 1 && !card) cyc++;
    if (ph == 1 && !card) cyc2++;
    for (k = 0; k < NG; k++) {
        Guard* g = &gd[k];
        int listed = k < ngidx && k != G_WATCH;      /* C0-12: the watch is spawned, like the runners */
        u8* e = listed ? EmFind(gidx[k]) : (Alive(g->e) ? g->e : 0);
        f32 ex, ez, dx, dz, d, fw, ang, hx;
        if (k >= ngidx && k < G_RUN0) continue;
        if (listed && e != g->e) {                /* new room / new work: start guarding */
            g->e = e; g->meter = 0.0f; g->leg = 0; g->lost = 0; g->role = R_NONE;
            if (!e) continue;
            g->base = *(f32*)(e + 0xA4);
            g->ax = *(f32*)(e + 0x94); g->az = *(f32*)(e + 0x9C);          /* home */
            g->bx = BV[k][0]; g->bz = BV[k][1];
            g->pat = 0;
            if (k == 2 || k == 3) { g->bx = g->bz = 0.0f; Hold(g); Patrol(k, k == 2 ? 3 : 4); }
            else if (k == 4) { Hold(g); Patrol(k, 2); }
            else Hold(g);
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
            if (g->lost > 120) {                     /* back home / to its patrol */
                g->meter = 0.6f;
                if (g->pat) { Hold(g); Patrol(k, g->pat); }
                else { g->leg = 2; Walk(g, g->ax, g->az); }
            }
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
                Steer(e, tx, tz);
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
        } else if (g->role == R_UP) {                /* C0-14: up the house's stairs, then after her */
            f32 tx = UPW[g->leg][0], tz = UPW[g->leg][1];
            if (g->st != G_WALK || g->tx != tx || g->tz != tz) Walk(g, tx, tz);
            *(s32*)(e + 0x3E4) = 300;
            if (e[0xFD] != 0x14) { e[0xFD] = 0x14; e[0xFE] = 0; e[0xFF] = 0; }
            *(f32*)(e + 0x92C) = tx; *(f32*)(e + 0x934) = tz;
            Steer(e, tx, tz);
            if ((ex - tx) * (ex - tx) + (ez - tz) * (ez - tz) < 600.0f * 600.0f) { if (g->leg < 1) g->leg++; else Chase(g); }
            else if (g->tm > 600) Chase(g);
            continue;
        } else if (g->role == R_PAT) {               /* C0-10b: patrols, in step; C0-12: loops */
            const Pat* p = &PATS[g->pat - 1];
            int side = PatSide(g->pat), tgt = side ? p->n - 1 : 0;
            f32 tx = p->x[g->leg], tz = p->z[g->leg];
            if ((ex - tx) * (ex - tx) + (ez - tz) * (ez - tz) < 500.0f * 500.0f) {
                if (p->loop) {
                    if (((p->hold >> g->leg) & 1) && !(g->st == G_HOLD && g->tm > (g->leg == 1 ? 420 : 150))) {   /* C0-14: long at the far end */
                        if (g->st != G_HOLD) { Hold(g); g->base = *(f32*)(e + 0xA4); }
                        if (e[0xFD] != 1) { e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0; }
                        g->tm++;
                        if (e[0xFE] == 1) Turn(e, g->base + 1.3f * Sn((f32)g->tm * 0.045f), 0.05f);
                    } else { g->leg = (u8)((g->leg + 1) % p->n); Walk(g, p->x[g->leg], p->z[g->leg]); }
                } else if (g->leg != tgt) { g->leg += tgt > g->leg ? 1 : -1; Walk(g, p->x[g->leg], p->z[g->leg]); }
                else {
                    if (g->st != G_HOLD) Hold(g);
                    if (e[0xFD] != 1) { e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0; }
                    g->tm++;
                    if (e[0xFE] == 1) Turn(e, (side ? p->fb : p->fa) + 0.4f * Sn((f32)g->tm * 0.02f + (f32)k), 0.04f);
                }
            } else {
                if (g->st != G_WALK || g->tx != tx || g->tz != tz) Walk(g, tx, tz);
                *(s32*)(e + 0x3E4) = 300;
                if (e[0xFD] != 0x14) { e[0xFD] = 0x14; e[0xFE] = 0; e[0xFF] = 0; }
                *(f32*)(e + 0x92C) = tx; *(f32*)(e + 0x934) = tz;
                Steer(e, tx, tz);
                if (g->pat == 1) *(f32*)(e + 0x298) = 0.65f;   /* C0-14: the watch walks slower (Motion.Seq_speed) */
                if (++g->tm > 1500) Hold(g);
            }
        } else if (g->st == G_HOLD) {
            if (e[0xFD] != 1) { e[0xFD] = 1; e[0xFE] = 0; e[0xFF] = 0; }
            g->tm++;
            if (g->role == R_SIEGE) {                /* at the house: faces it, restless */
                if (e[0xFE] == 1) Turn(e, 3.14159265f + 0.35f * Sn((f32)g->tm * 0.09f + (f32)k), 0.08f);
            } else if (g->role == R_RING) {          /* C0-12: round the house after the key, watching it */
                if (e[0xFE] == 1) Turn(e, Atan2f(HOUSE_X - ex, HOUSE_Z - ez) + 0.6f * Sn((f32)g->tm * 0.03f + (f32)k), 0.05f);
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
            Steer(e, tx, tz);
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
        if (!hidden && ph == 1 && !scene && !scene_n && !card && g->role != R_SIEGE && g->role != R_RUN) {
            f32 dy = PY() - *(f32*)(e + 0x98), rate = 0.0f, r = rv;
            if (dy < 0.0f) dy = -dy;
            if (g->role == R_GROUP) r = crouched ? 0.0f : running ? 24000.0f : 20000.0f;   /* crouched: unseen */
            if (dy < 2500.0f) {
                fw = (d > 1.0f) ? (dx * Sn(*(f32*)(e + 0xA4)) + dz * Cs(*(f32*)(e + 0xA4))) / d : 1.0f;
                if (d < r + 1000.0f || d < 2500.0f) { if (((t + k) % 6) == 0) g->vis = (u8)Los(e, crouched); }
                else g->vis = 0;
                if (fw > 0.5f && d < r && g->vis) rate = 0.012f + 0.05f * (1.0f - d / r);
                if (d < (g->role == R_GROUP ? 1500.0f : 1800.0f) && g->vis) rate += crouched ? 0.03f : 0.08f;
                if (running && d < 6000.0f) rate += 0.05f;
            }
            if (rate > 0.0f) g->meter += rate; else { g->meter -= 0.006f; if (g->meter < 0.0f) g->meter = 0.0f; }
            if (g->meter >= 1.0f) alarm = k;
        } else { g->meter -= 0.006f; if (g->meter < 0.0f) g->meter = 0.0f; }
        if (g->role == R_RING && g->meter < 0.5f) g->meter = 0.5f;   /* C0-13: on the alert after the key */
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
    if (!on || !ready || ph != 1 || scene || scene_gate || scene_n || caught || card || k >= NG) return 0;
    g = &gd[k];
    if (!Alive(g->e) || g->e[0xFC] != 1) return 0;
    *x = *(f32*)(g->e + 0x94); *y = *(f32*)(g->e + 0x98) + 2050.0f; *z = *(f32*)(g->e + 0x9C);
    if (g->st == G_CHASE) return 100;
    if (g->meter < 0.03f) return 0;
    return (int)(g->meter * 99.0f) + 1;
}
static const f32 HIDE[][3] = {                       /* hiding places: x, z, radius */
    /* C0-12: where the user stood in his captures (the containers go there; barrels until then) */
    { -24287.0f, 399.0f, 1500.0f },                  /* the alley to the square's entrance */
    { -22855.0f, -5531.0f, 1500.0f },                /* the north crossing's corner */
    { -5140.0f, 14167.0f, 1500.0f },                 /* in the stable */
    { 13000.0f, 10500.0f, 1500.0f },                 /* C0-13: in the south alley (user) */
    { 28580.0f, -2130.0f, 1500.0f },                 /* between the tower and the door */
};
/* the room's barrels (ETS id 17 x4, id 30 x1) moved to the new hiding places */
static const f32 BARREL[5][3] = { { -24287.0f, 0.0f, 399.0f }, { -22855.0f, 0.0f, -5531.0f },
    { -5140.0f, 0.0f, 14167.0f }, { 13000.0f, 854.0f, 10500.0f }, { 28580.0f, 1138.0f, -2130.0f } };
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
    ch0_padlock = 2;                                 /* still, crouched, the camera free (C0-12); Cross: out */
    if (trg & PAD_A) { hidden = 0; ch0_crouch_force = 0; ch0_padlock = 0; }
}
int Ch0Card(void) { if (!on || !card) return 0; return card == 1 ? (card_t < 12 ? card_t * 255 / 12 : 255) : 255 - card_t * 255 / 12; }
int Ch0Hide(void)
{
    if (!on || !ready || ph != 1 || scene || scene_n || scene_gate || caught || card) return 0;
    if (key && D2(BX, BZ) < 2500.0f * 2500.0f) return 3;     /* C0-12: door B: Cross to open */
    return hidden ? 2 : (HideSpot() >= 0 ? 1 : 0);
}

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
void CrouchOff(void);
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
/* C0-12 (user): after the key the one who came in goes after her; the others ring the house's front and east
 * side to press her, watching it (no chase on sight of the house alone); north and west stay free: the window
 * to the roof and the other ladder are the way out. The patrols go on. */
static const f32 RING[8][2] = { { 7169.0f, -4800.0f }, { 8700.0f, -5000.0f }, { 6300.0f, -4300.0f },
                                { 9800.0f, -8500.0f }, { 9800.0f, -12500.0f }, { 5000.0f, -3800.0f },
                                { 10500.0f, -6500.0f }, { 3500.0f, -4000.0f } };
static void AfterKey(void)                           /* C0-13: every Ganado on the map comes, on the alert */
{
    int k, n = 0;
    for (k = 0; k < NG; k++) {
        Guard* g = &gd[k];
        if (!Alive(g->e) || k == ins[0] - 1 || k == ins[1] - 1 || k == ins[2] - 1) continue;
        g->role = R_RING; g->pat = 0; g->ax = RING[n % 8][0]; g->az = RING[n % 8][1]; g->bx = g->bz = 0.0f; n++;
        g->meter = 0.6f;
        Walk(g, g->ax, g->az);
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
    for (i = 0, c = 0; i < n && c < 5; i++) {
        u8* d = list + 0x10 + i * 0x28;
        if (*(u16*)d != 17 && *(u16*)d != 30) continue;
        *(f32*)(d + 0x1C) = BARREL[c][0]; *(f32*)(d + 0x20) = BARREL[c][1]; *(f32*)(d + 0x24) = BARREL[c][2];
        c++;
    }
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
/* C0-10: the rooms' items (ITA records, 0x9C bytes) just before the game reads them (hook at SceAtInit's entry,
 * PAL 0x8014E434): all off (Leon's ammo, money, herbs, the shotgun...), and in r111 one of them becomes the key
 * on the bed. No taken flag (item_flg / auto_item_flg 0): nothing of Leon's game is touched. */
/* C0-10b: the key's pick-up model is only in r105's pack: mkfiles.py puts a copy at the end of em12.drs; it is
 * read here (blocking, while the room is set up, into the room's heap like the room's own pack) and registered
 * in the item model table (g_pItemModelSys: work[id] = { bin, tpl }) before the items are made. */
#define DVD_OBJ  ((void*)0x8027EFF8)
#define FST_PTR  (*(u8**)0x80000038)
#define ITM_SYS  (*(u8**)0x802B83D4)                 /* g_pItemModelSys (r13 0x802BEA20 - 26188); C0-12: was wrong */
int  DvdFileExistCheck(void* dvd, const char* name, u32* len);
void* mem_alloc(u32 size, const char* file, int line, int flag, int heap);
#define DVD_READ_PRIO ((int (*)(void*, void*, s32, s32, s32))0x80075BE8)
static u32 km_fi[0x10] __attribute__((aligned(8)));
static void KeyModel(void)
{
    u32 len = 0, i;
    int entry;
    u8 *fe, *buf, *sys = ITM_SYS;
    if ((u32)sys < 0x80000000u || (u32)sys >= 0x81800000u || *(u32*)(sys + KEY_ID * 8)) return;
    entry = DvdFileExistCheck(DVD_OBJ, "em/em12.drs", &len);
    if (entry < 0 || len < KM_OFS + KM_LEN || !FST_PTR) return;
    fe = FST_PTR + entry * 12;
    buf = mem_alloc(KM_LEN + 0x40, 0, 0, 0, 13);
    if (!buf) return;
    buf = (u8*)(((u32)buf + 0x1F) & ~0x1Fu);
    for (i = 0; i < 0x10; i++) km_fi[i] = 0;
    km_fi[0x30 / 4] = *(u32*)(fe + 4) + KM_OFS;
    km_fi[0x34 / 4] = KM_LEN;
    for (i = 0; i < KM_LEN + 0x20; i += 0x20) __asm__ volatile("dcbi 0,%0" :: "r"(buf + i));
    if (DVD_READ_PRIO(km_fi, buf, KM_LEN, 0, 2) < (s32)KM_LEN) return;
    *(u8**)(sys + KEY_ID * 8) = buf;
    *(u8**)(sys + KEY_ID * 8 + 4) = buf + KM_TPL;
}
void Ch0Ita(u8* aev, u8* ita)
{
    int i, n;
    (void)aev;
    if (!on || !pG || STAGE != 1 || !ita || (ROOM != 0x11 && ROOM != 0x12)) return;
    if (ita[0] != 'I' || ita[1] != 'T' || ita[2] != 'A') return;
    n = *(u16*)(ita + 6);
    for (i = 0; i < n; i++) ita[0x10 + i * 0x9C + 0x34] = 0;
    if (ROOM != 0x11 || key) return;
    KeyModel();
    for (i = 0; i < n; i++) {
        u8* w = ita + 0x10 + i * 0x9C;
        if (*(u16*)(w + 0x78) != 0x57) continue;    /* r111's treasure up on a roof: now the key */
        *(f32*)(w + 0x5C) = KEYP[0]; *(f32*)(w + 0x60) = KEYP[1]; *(f32*)(w + 0x64) = KEYP[2];
        *(u32*)(w + 0x68) = 0;
        *(f32*)(w + 0x6C) = *(f32*)(w + 0x70) = *(f32*)(w + 0x74) = 0.0f;
        *(u16*)(w + 0x78) = KEY_ID; *(u16*)(w + 0x7A) = 0; *(u16*)(w + 0x7C) = 1; *(u16*)(w + 0x7E) = 0;
        w[0x80] = 1; w[0x81] = 0; w[0x82] = 0; w[0x83] = 0; w[0x84] = 0; w[0x85] = 0;
        *(s16*)(w + 0x86) = -1;
        *(f32*)(w + 0x88) = 800.0f;
        *(f32*)(w + 0x8C) = *(f32*)(w + 0x90) = *(f32*)(w + 0x94) = 0.0f;
        w[0x46] = 0; w[0x47] = 0; w[0x52] = 0;
        w[0x34] = 3;
        break;
    }
}
typedef struct { u16 id, num; u8 flags, type; u16 lv, bullet; s8 x, y, orient; u8 board; } Item;
static Item* KeyItem(void)                           /* the key in Ashley's case, or 0 */
{
    Item* it = *(Item**)((u8*)ItemMgr + 0x14);
    int i, n = *(s32*)((u8*)ItemMgr + 0x1C);
    u8 ch = *((u8*)ItemMgr + 0x13);
    if ((u32)it < 0x80000000u || (u32)it >= 0x81800000u || n > 256) return 0;
    (void)ch;
    for (i = 0; i < n; i++, it++) if ((it->flags & 1) && it->id == KEY_ID) return it;   /* C0-10b: any owner */
    return 0;
}
/* the game's own message window, without stopping the game: 0x1002 the game's text look (SceMesSet),
 * 0x10 the game goes on, 0x80000 each line centred, 0x01000000 it stays (we take it away), 0x02000000 no
 * waiting for a button */
#define TALK_WK 2
static void Say(const u16* txt, int frames)
{
    u8* m = cMes + 4 + 236 * TALK_WK;
    talk_attr = 0x1002 | 0x10 | 0x80000 | 0x01000000 | 0x02000000;
    MesSet(cMes, 0x15, 0x64, 282, talk_attr, TALK_WK, 0, 4);
    *(const u16**)(m + 0x98) = txt;
    talk_t = frames;
}
static void SayTick(void)
{
    if (talk_t <= 0) return;
    if (--talk_t > 0) return;
    if (*(u32*)(cMes + 4 + 236 * TALK_WK + 0x80) == talk_attr) MesDelete(cMes, TALK_WK);
}
static u8* HouseDoor(void)                           /* house C's door (cEmDoor, id 0x41) */
{
    u32 n = *(u32*)((u8*)EMMGR + 4), i, sz = *(u32*)((u8*)EMMGR + 8);
    u8* base = *(u8**)EMMGR;
    if ((u32)base < 0x80000000u || (u32)base >= 0x81800000u || n > 1024 || sz < 0xC00 || sz > 0x40000) return 0;
    for (i = 0; i < n; i++) {
        u8* e = base + i * sz;
        f32 dx, dz;
        if (!(*(u32*)e & 1) || e[0x100] != 0x41) continue;
        dx = *(f32*)(e + 0x94) - HDOOR_X; dz = *(f32*)(e + 0x9C) - HDOOR_Z;
        if (dx * dx + dz * dz < 800.0f * 800.0f) return e;
    }
    return 0;
}
#define DOOR_OPEN ((void (*)(u8*, Vec*, int, int, int))0x800DE5A0)   /* cEmDoor::setOpen (PAL) */
static void WalkE(u8* e, f32 x, f32 z)               /* GuardWalk for a work outside gd[] */
{
    e[0xFD] = 0x14; e[0xFE] = 0; e[0xFF] = 0;
    *(f32*)(e + 0x92C) = x; *(f32*)(e + 0x930) = *(f32*)(e + 0x98); *(f32*)(e + 0x934) = z;
    *(s32*)(e + 0x3E4) = 300;
}
static void Restart(void)                            /* caught: the room again from the checkpoint */
{
    hidden = 0; ch0_crouch_force = 0;
    if (!cp) { road_wait = 1; cyc = 0; stage = 0; ch0_got = 0; watch_on = 0; }
    scene_n = 0; scene_x = 0; grab = 0; keep_open = 0; x_done = 0;
    scene_gate = 0;
    PL_LIFE = PL_LIFE_MAX;
    ready = 0; scene = 0; caught = 0; ch0_padlock = 1;
    ROOM_JUMP(0x111, cp ? &kpos : &apos, cp ? &krot : &arot, 0);
}

#define S_LEN      250                               /* the house scene */
#define S_OPEN     104                               /* C0-10: the door opens */

/* C0-12 (user): the north crossing. Ashley comes up the alley; at the crossing a Ganado comes slowly out from
 * behind the north houses looking about; she runs back down the alley (the camera behind her) and crouches at
 * its corner; the camera turns to him searching; he turns and starts his patrol (a T: west along the back of
 * the houses, south to the square). So the way is the one down to the square. */
static const f32 NRW[2][2] = { { -26000.0f, -2250.0f }, { -25250.0f, -1500.0f } };   /* walls kept 0.45 m off */
#define N_TRIG_X  (-26987.0f)                        /* C0-13: the crossing before the alley (user's capture) */
#define N_TRIG_Z  (-3615.0f)
#define N_SPAWN_X (-18500.0f)
#define N_SPAWN_Z (-9200.0f)
#define N_STOP_X  (-22000.0f)
#define N_STOP_Z  (-8500.0f)
#define N_CAM_X   (-23800.0f)                        /* C0-15 (video): west of his stop, sees his way east */
#define N_CAM_Z   (-7500.0f)
static f32 ncam[6];
static int nt, nph;                                  /* the scene's own clock and step */
int ch0_btn;                                         /* pad.c: buttons held for her in a scene */
static void WatchSpawn(f32 x, f32 z, f32 ang)
{
    Guard* g = &gd[G_WATCH];
    memclr_asm(g, sizeof(*g));
    g->e = Spawn(x, 0.0f, z, ang, 3);
    if (!g->e) return;
    g->ax = x; g->az = z; g->base = ang;
    Hold(g);
}
static void CamTo(f32 fx, f32 fy, f32 fz, f32 tx, f32 ty, f32 tz, f32 k)   /* eased camera */
{
    ncam[0] += (fx - ncam[0]) * k; ncam[1] += (fy - ncam[1]) * k; ncam[2] += (fz - ncam[2]) * k;
    ncam[3] += (tx - ncam[3]) * k; ncam[4] += (ty - ncam[4]) * k; ncam[5] += (tz - ncam[5]) * k;
    Cam(ncam[0], ncam[1], ncam[2], ncam[3], ncam[4], ncam[5], 50.0f);
}
/* C0-13 (user): the scene starts at the crossing before the alley (so it is always seen): he comes out from
 * behind the houses (the camera over her shoulder), stops and looks round (a pause to see him); she runs to the
 * alley's corner and crouches (the camera behind her); then the camera goes up to a point that sees the alley
 * top and follows him while he turns and goes off on his round. */
static int NorthScene(void)                          /* 1 while it runs */
{
    Guard* w = &gd[G_WATCH];
    u8* e = Alive(w->e) ? w->e : 0;
    f32 gx = e ? *(f32*)(e + 0x94) : N_STOP_X, gz = e ? *(f32*)(e + 0x9C) : N_STOP_Z;
    if (!scene_n) {
        if (stage || watch_on || D2(N_TRIG_X, N_TRIG_Z) > 1800.0f * 1800.0f || pPL[0xFC] != 0) return 0;
        scene_n = 1; rw = 0; nt = 0; nph = 0; watch_on = 1; Hud(0);
        WatchSpawn(N_SPAWN_X, N_SPAWN_Z, -1.571f);
        *(f32*)(pPL + 0xA4) = Atan2f(N_STOP_X - PX(), N_STOP_Z - PZ());   /* she looks up the alley */
        ncam[0] = PX(); ncam[1] = PY() + 1700.0f; ncam[2] = PZ() + 900.0f;
        ncam[3] = N_STOP_X; ncam[4] = 1200.0f; ncam[5] = N_STOP_Z;
        return 1;
    }
    scene_n++; nt++;
    ch0_padlock = 1; ch0_stick = 0; ch0_btn = 0;
    STOPF |= SPF_CAM;
    if (nph == 0) {                                  /* he comes out, slowly; over her shoulder */
        if (nt == 8 && e) { w->ax = N_STOP_X; w->az = N_STOP_Z; Walk(w, N_STOP_X, N_STOP_Z); }
        { f32 dx = gx - PX(), dz = gz - PZ(), dd = Sq(dx * dx + dz * dz) + 1.0f;   /* C0-14: nearer, over her shoulder */
          dx /= dd; dz /= dd;
          CamTo(PX() - dx * 1000.0f - dz * 350.0f, PY() + 1750.0f, PZ() - dz * 1000.0f + dx * 350.0f, gx, 1200.0f, gz, 0.06f); }
        if (nt > 20 && (!e || w->st == G_HOLD || nt > 200)) { nph = 1; nt = 0; }
    } else if (nph == 1) {                           /* the pause: he looks round */
        if (e && e[0xFE] == 1) Turn(e, -1.571f + 1.2f * Sn((f32)nt * 0.06f), 0.06f);
        { f32 dx = gx - PX(), dz = gz - PZ(), dd = Sq(dx * dx + dz * dz) + 1.0f;
          dx /= dd; dz /= dd;
          CamTo(PX() - dx * 900.0f - dz * 400.0f, PY() + 1650.0f, PZ() - dz * 900.0f + dx * 400.0f, gx, 1300.0f, gz, 0.05f); }
        if (nt >= 80) { nph = 2; nt = 0; }
    } else if (nph == 2) {                           /* she runs to the corner, the camera behind her */
        f32 dx = NRW[rw][0] - PX(), dz = NRW[rw][1] - PZ(), d = Sq(dx * dx + dz * dz);
        if (d < 450.0f || nt > 150) {
            if (++rw >= 2 || nt > 150) { nph = 3; nt = 0; ch0_crouch_force = 1; *(f32*)(pPL + 0xA4) = Atan2f(gx - PX(), gz - PZ()); }
        } else {
            dx /= d; dz /= d;
            *(f32*)(pPL + 0xA4) = Atan2f(dx, dz);    /* tank controls: face the way, stick up, run held */
            ch0_stick = 1; ch0_sx = 0; ch0_sy = 127; ch0_btn = PAD_B;
            CamTo(PX() - dx * 2600.0f, PY() + 1700.0f, PZ() - dz * 2600.0f, PX() + dx * 3000.0f, PY() + 900.0f, PZ() + dz * 3000.0f, 0.12f);
        }
    } else {                                         /* she is down: up to the alley's view, on him */
        CamTo(N_CAM_X, 2000.0f, N_CAM_Z, gx, 1200.0f, gz, nt < 40 ? 0.05f : 0.08f);
        if (nt == 30 && e) { Patrol(G_WATCH, 1); w->leg = 0; }   /* he turns and goes on his round */
        if (nt >= 150) {
            scene_n = 0; STOPF &= ~SPF_CAM; ch0_padlock = 0; ch0_stick = 0; ch0_btn = 0; ch0_crouch_force = 0; Hud(1);
            if (e && w->role != R_PAT) Patrol(G_WATCH, 1);
        }
    }
    return 1;
}

/* C0-14 (user): once she is out of the house with the key (window, ladder or door) they "find" her: her
 * scared clip from the start, the camera in front of her, "Ya viene. Debo darme prisa." and they all come. */
static int OutScene(void)
{
    int k;
    if (!scene_x) {
        if (stage < 2 || x_done || scene || InHouse() || pPL[0xFC] != 0) return 0;
        scene_x = 1; x_done = 1; Hud(0); CrouchOff(); ch0_crouch_force = 0;
        ncam[0] = PX(); ncam[1] = PY() + 1500.0f; ncam[2] = PZ();
        ncam[3] = PX(); ncam[4] = PY() + 1100.0f; ncam[5] = PZ();
        return 1;
    }
    scene_x++;
    ch0_padlock = 1; ch0_stick = 0; ch0_btn = 0;
    STOPF |= SPF_CAM;
    {
        f32 a = *(f32*)(pPL + 0xA4), f = (f32)scene_x * (10.0f / 30.0f), kk = Sm((f32)scene_x / 14.0f);
        if (f > 36.99f) { f = 36.99f; kk = 1.0f - Sm((f32)(scene_x - 111) / 30.0f); }
        ScaredApply(f, kk);
        CamTo(PX() + Sn(a) * 2300.0f, PY() + 1500.0f, PZ() + Cs(a) * 2300.0f, PX(), PY() + 1100.0f, PZ(), 0.1f);
    }
    if (scene_x == 25) Say(MSG_HURRY, 90);
    if (scene_x >= 140) {
        scene_x = 0; STOPF &= ~SPF_CAM; ch0_padlock = 0; Hud(1);
        for (k = 0; k < NG; k++) if (Alive(gd[k].e) && gd[k].st != G_CHASE) Chase(&gd[k]);
    }
    return 1;
}

static void Leave(void)                              /* C0-10: door B with the key: on to the road to the church */
{
    int k;
    Item* it = KeyItem();
    if (it) { it->num = 0; it->flags &= ~1; }       /* used, as the game does with a key */
    for (k = 0; k < NG; k++) if (Alive(gd[k].e) && gd[k].e[0xFC] == 1) Hold(&gd[k]);
    if (Alive(hman)) { *(u32*)(hman + 0x3C8) &= ~1u; Native(hman); hman[0xFD] = 1; hman[0xFE] = 0; }
    Say(MSG_USED, 100);
    ph = 4; endt = 0; ch0_padlock = 1; Hud(0);
}

void Ch0Frame(void)
{
    u16 pad, trg;
    if (!on || !pG) { ch0_padlock = 0; ch0_stick = 0; return; }
    pad = barn_pad; trg = pad & ~pad_old; pad_old = pad;
    SayTick();
    if (!ready) {                                    /* still loading: keep it black and still */
        ch0_padlock = 1; ch0_stick = 0;
        if (Ashley() && (ph != 3 || ROOM == 0x12)) {
            ready = 1; t = 0;
            if (ph == 0) Hud(0); else { ch0_padlock = 0; Hud(1); }
            if (ph == 1 && stage >= 1) Runners(0);
            if (ph == 1 && watch_on && !Alive(gd[G_WATCH].e)) { WatchSpawn(PATS[0].x[0], PATS[0].z[0], -1.571f); Patrol(G_WATCH, 1); }
            if (ph == 1 && cp == 1 && !Alive(hman)) hman = HouseGanado(DOOR_IN_X, DOOR_IN_Z - 900.0f, 3.02f);
            if (ph == 1 && key) after_key = 30;
        }
        return;
    }
    if (!Ashley()) return;                           /* menus, death screen... */
    t++;
    Areas();
    if (ph == 3) {                                   /* C0-10: r112, the road to the church */
        if (ROOM != 0x12) return;
        if (D2(EX, EZ) < 2500.0f * 2500.0f && pPL[0xFC] == 0) { ph = 2; endt = 0; ch0_padlock = 1; Hud(0); }
        return;
    }
    if (ph == 4) {                                   /* door B: the message, black, r112 */
        endt++;
        ch0_padlock = 1;
        if (endt >= 75 && pPL[0xFC] == 0) { ph = 3; ready = 0; ROOM_JUMP(0x112, &fpos, &frot, 0); }
        return;
    }
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
        if (t == T_SAY) Say(MSG_ASHLEY, T_FREE - 15 - T_SAY);   /* C0-10: in the game's own letters */
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
            if (cap_t == 200) Restart();      /* C0-15: grabbed, carried off two steps, then the screen */
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
        if (!scene && NorthScene()) return;
        if (stage == 0 && !scene && D2(STABLE_X, STABLE_Z) < 2500.0f * 2500.0f) {   /* passing the stable */
            scene_gate = 1; Hud(0);
            Runners(1); Patrol(2, 3); Patrol(3, 4);
            return;
        }
        if (keep_open && Alive(hdoor) && keep_open++ < 600) *(s32*)(hdoor + 0x7E0) = 0x96;   /* C0-14: it stays open */
        if ((pPL[0xFC] == 1 || grab) && !scene && !scene_x) {
            caught = 1; cap_t = 0; hidden = 0; ch0_crouch_force = 0; grab = 0; Hud(0);   /* C0-15: the game's own grab plays */
            return;
        }
        if (OutScene()) return;
        if (scene) {                                 /* the Ganado comes in downstairs */
            u8* d = HouseDoor();
            f32 sh = 0.0f;
            int b = scene < 30 ? -1 : (scene - 30) % 22, k, in = 0;
            if ((STOPF & 0x10000000u) || (*(u32*)(pG + 0x501C) & 0x10000000u)) { ch0_padlock = 0; return; }   /* C0-13: a game screen is up: wait, never lock it */
            scene++;
            ch0_padlock = 1;
            STOPF |= SPF_CAM;
            /* C0-07: banging on the door from outside (the camera shakes with each blow); C0-10: the door
               rattles with them, then it is opened (the game's own door, no sound) and one walks in */
            if (scene >= 30 && scene < 96 && b < 7) sh = (f32)(7 - b) * 9.0f * ((b & 1) ? 1.0f : -1.0f);
            if (d && scene < S_OPEN) *(f32*)(d + 0xA4) = *(f32*)(d + 0x778) + sh * 0.0012f;
            if (scene == S_OPEN - 8) {               /* C0-14 (user): the three nearest to Ashley come in */
                int j;
                ins[0] = ins[1] = ins[2] = 0;
                for (j = 0; j < 3; j++) {
                    f32 best = 1e12f, dx, dz;
                    in = 0;
                    for (k = 0; k < NG; k++) {
                        u8* e = gd[k].e;
                        if (!Alive(e) || (e[0xFC] != 1 && gd[k].st != G_CHASE) || k + 1 == ins[0] || k + 1 == ins[1]) continue;
                        dx = *(f32*)(e + 0x94) - PX(); dz = *(f32*)(e + 0x9C) - PZ();
                        if (dx * dx + dz * dz < best) { best = dx * dx + dz * dz; in = k + 1; }
                    }
                    ins[j] = (u8)in;
                    if (in) {
                        Guard* g = &gd[in - 1];
                        u8* e = g->e;
                        f32 ox = j == 0 ? 0.0f : j == 1 ? -650.0f : 650.0f, oz = (f32)j * 700.0f;
                        *(f32*)(e + 0x94) = *(f32*)(e + 0x110) = DOOR_OUT_X + ox;
                        *(f32*)(e + 0x98) = *(f32*)(e + 0x114) = 0.0f;
                        *(f32*)(e + 0x9C) = *(f32*)(e + 0x118) = DOOR_OUT_Z + oz;
                        *(f32*)(e + 0xA4) = 3.02f;
                        g->role = R_DOOR; g->ax = DOOR_IN_X - 1200.0f + 1700.0f * (f32)(j & 1); g->az = DOOR_IN_Z - 1800.0f - 900.0f * (f32)(j == 2);
                        g->leg = 0; g->meter = 0.6f;
                        Hold(g);
                    }
                }
                door_in = ins[0];
                if (!ins[0] && !Alive(hman)) hman = HouseGanado(DOOR_OUT_X, DOOR_OUT_Z, 3.02f);
            }
            if (scene == S_OPEN && d) {
                Vec p;
                p.x = DOOR_OUT_X; p.y = 0.0f; p.z = DOOR_OUT_Z;
                *(f32*)(d + 0xA4) = *(f32*)(d + 0x778);
                DOOR_OPEN(d, &p, 0, 1, 0);
                hdoor = d; keep_open = 1;
            }
            if (scene == S_OPEN + 10) {
                if (ins[0]) Walk(&gd[ins[0] - 1], gd[ins[0] - 1].ax, gd[ins[0] - 1].az);
                else if (Alive(hman)) WalkE(hman, DOOR_IN_X, DOOR_IN_Z - 1500.0f);
            }
            if (scene == S_OPEN + 35 && ins[1]) { gd[ins[1] - 1].role = R_UP; gd[ins[1] - 1].leg = 0; }   /* this one goes up */
            if (scene == S_OPEN + 60 && ins[2]) Walk(&gd[ins[2] - 1], gd[ins[2] - 1].ax, gd[ins[2] - 1].az);
            Cam(5644.0f + sh, 1500.0f + sh * 0.5f, -9300.0f, DOOR_IN_X, 900.0f, DOOR_IN_Z, 50.0f);
            if (scene >= S_LEN) {
                scene = 0; STOPF &= ~SPF_CAM; ch0_padlock = 0; Hud(1); stage = 2;
                if (door_in && Alive(gd[door_in - 1].e)) gd[door_in - 1].meter = 0.6f;   /* C0-13: he searches downstairs */
                AfterKey();
            }
            return;
        }
        HideFrame(trg);
        if (hidden) return;
        if (!key && (ch0_got || KeyItem())) {      /* C0-10: picked up the game's way (its own screen) */
            /* C0-13: only once its screen is closed (the scene's pad lock kept it open) */
            if (pPL[0xFC] == 0 && !(STOPF & 0x10000000u) && !(*(u32*)(pG + 0x501C) & 0x10000000u)) kwait++;
            else kwait = 0;
            if (kwait < 15) return;
            key = 1; cp = 1; scene = 1; door_in = 0; kwait = 0; Hud(0);
            return;
        }
        if (D2(BX, BZ) < 2500.0f * 2500.0f) {
            if (!key) { if (!b_seen || ((trg & PAD_A) && talk_t <= 0)) { b_seen = 1; Say(MSG_LOCKED, 150); } }
            else if (D2(BX, BZ) < 2500.0f * 2500.0f && pPL[0xFC] == 0 && (trg & PAD_A)) { Leave(); return; }   /* C0-12: by hand */
        } else {
            if (b_seen && !key && talk_t > 1 && D2(BX, BZ) > 3000.0f * 3000.0f) { talk_t = 1; SayTick(); }   /* C0-10b: gone when she walks off */
            if (D2(BX, BZ) > 4000.0f * 4000.0f) b_seen = 0;
        }
        return;
    }
    if (ph == 2) {
        endt++;
        ch0_padlock = 1;
        if (endt >= 170 && pPL[0xFC] == 0) {     /* C0-09: never while she is being hit (the C0-08 crash) */
            done = 1; on = 0; ch0_padlock = 0; hidden = 0; ch0_crouch_force = 0;
            if (talk_t > 0) { talk_t = 1; SayTick(); }
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
    if (ph == 1 && caught) return Ramp(80, 115, cap_t);
    if (ph == 2) return Ramp(60, 100, endt);
    if (ph == 4) return Ramp(25, 70, endt);                  /* C0-10: door B -> r112 */
    if (ph == 3) return 255 - Ramp(0, 40, t);
    return 0;
}
/* line k: 0 "Hace 11 horas", 1 Ashley's line, 2 locked (two lines), 3 key prompt, 4 key taken,
 * 5 the door opens, 6 caught, 7 end of Part 1; returns its alpha */
int Ch0Text(int k)
{
    if (!on || !ready) return 0;
    if (ph == 0) {
        if (k == 0) { if (t < T_TXT_FULL) return Ramp(T_TXT_IN, T_TXT_FULL, t); return 255 - Ramp(T_TXT_OUT, T_TXT_GONE, t); }
        return 0;
    }
    if (k == 6 && caught) return Ramp(110, 130, cap_t);
    if (k == 7 && ph == 2) return Ramp(100, 120, endt);
    return 0;
}
int Ch0Coords(int i)                                  /* test: Ashley x, y, z; -999999 = off */
{
    if (!on || !ready || (ph != 1 && ph != 3) || caught || scene || card || !Ashley()) return -999999;
    return (int)*(f32*)(pPL + 0x94 + 4 * i);
}

/* C0-15: the crash when a Ganado grabs playable Ashley (C0-13: write to 0x1C0, PC 0x801925A8): the grab turns on
 * IK for a part whose chain (the next two parts in the list) Ashley's model does not have. Hook at
 * InverseKinematics' entry (PAL 0x80192084): such a part is marked "skip" (IK flag 0x80) before it runs. */
void Ch0Ik(u8* m)
{
    u8* p;
    int n = 0;
    if (!m || (u32)m < 0x80000000u || (u32)m >= 0x81800000u) return;
    for (p = *(u8**)(m + 0xF4); p && (u32)p >= 0x80000000u && (u32)p < 0x81800000u && n < 96; p = *(u8**)(p + 0xF4), n++) {
        u32 f = *(u32*)(p + 0x1C0);
        u8* j;
        if (!(f & 4) || (f & 0x80)) continue;
        j = *(u8**)(p + 0xF4);
        if (!j || (u32)j < 0x80000000u || !*(u8**)(j + 0xF4)) *(u32*)(p + 0x1C0) = f | 0x80;
    }
}
