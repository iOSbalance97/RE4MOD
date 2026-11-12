"""El Carnicero's motions (game format): a fast run on all fours (bounding gallop, the claw and the sickle
hand on the floor) and a leaping claw swipe. Same skeleton numbering as the Ganado (parts 0-25); the rig is
models/carnicero (/home/claude/carnicero_lp/rig.py), the writer/IK helpers are El Herrero's mkanim.py.
Output: mod/data/carnicero_anim.bin (pack of offsets: [0] run mot, [1] run seq, [2] swipe mot, [3] swipe seq)
and mod/c/carnicero_mot.h (frame counts)."""
import sys, math, struct, importlib.util, numpy as np
sys.path.insert(0, '/home/claude/carnicero_lp')
import rig                                          # the Carnicero's rig takes the name 'rig' first
sys.argv = [sys.argv[0]]
spec = importlib.util.spec_from_file_location('mk', '/home/claude/re4mod/models/herrero/anim/mkanim.py')
mk = importlib.util.module_from_spec(spec); spec.loader.exec_module(mk)
assert mk.rig is rig
from_ = mk
Pose, fk, two_bone, aim, rx, ry, rz, nrm, sm, lerp, D = mk.Pose, mk.fk, mk.two_bone, mk.aim, mk.rx, mk.ry, mk.rz, mk.nrm, mk.sm, mk.lerp, mk.D
BP = mk.BP; L_TH, L_SH = mk.L_TH, mk.L_SH
LA_R = (np.linalg.norm(BP[8] - BP[7]), np.linalg.norm(BP[10] - BP[8]))
LA_L = (np.linalg.norm(BP[14] - BP[13]), np.linalg.norm(BP[16] - BP[14]))
def leg(p, P, side, foot, pole, foot_R=None): mk.leg(p, P, side, foot, pole, foot_R)
def arm(p, P, side, wrist, pole, hand_R):
    c, u, f, m, hnd = (5, 7, 8, 9, 10) if side < 0 else (11, 13, 14, 15, 16)
    la, lb = LA_R if side < 0 else LA_L
    sh = P[u]; el, wr = two_bone(sh, wrist, la, lb, pole)
    X = np.array([side * 1.0, 0, 0])
    p.W[u] = aim(X, [0, 0, 1], el - sh, -pole); p.W[u - 1] = p.W[u]
    p.W[f] = aim(X, [0, 0, 1], wr - el, -pole); p.W[m] = p.W[f]
    p.W[hnd] = hand_R
def spine(p, pitch, yaw, roll, head_pitch):
    p.W[1] = ry(yaw * 0.4) @ rx(pitch * 0.6) @ rz(roll * 0.5)
    p.W[2] = ry(yaw) @ rx(pitch) @ rz(roll)
    p.W[3] = p.W[2] @ rx(-pitch * 0.5 + head_pitch * 0.4); p.W[4] = p.W[2] @ rx(-pitch * 0.8 + head_pitch)
    p.W[5] = p.W[2]; p.W[11] = p.W[2]
# ------------------------------------------------------------------------------------- run on all fours
RN = 20; SPEED = 150.0                     # mm per frame (4.5 m/s at 30 fps); one bound every 20 frames
def run4(f):
    p = Pose(); u0 = (f % RN) / RN; ph = 2 * math.pi * u0
    p.travel = np.array([0, 0, SPEED * f])
    bounce = 55 * math.sin(ph * 2 + 0.6)                         # up while airborne, down on the landings
    p.root = BP[0] + np.array([0, -360 + bounce, 0])
    pitch = D(94) + D(6) * math.sin(ph + 1.2)                    # back nearly level, rocking with the bound
    spine(p, pitch, D(3) * math.sin(ph), -D(3) * math.sin(ph), head_pitch=D(-80))
    p.W[0] = rx(D(4) * math.sin(ph)); p.W[17] = rx(D(10) * math.sin(ph + 0.3))
    P = fk(p)
    stride = SPEED * RN                                          # 3 m per bound
    def foot_at(u, z0, reach, lift, duty):
        """stance (0..duty): from +reach/2 to -reach/2 under the body; swing: back to the front in an arc"""
        if u < duty: return z0 + reach / 2 - reach * (u / duty), 0.0, 0.0
        v = (u - duty) / (1 - duty); return z0 - reach / 2 + reach * sm(v), lift * math.sin(math.pi * v), v
    DUTY = 0.24; reach = SPEED * RN * DUTY                       # ground contact: the foot stays put while the body passes
    for side, off in ((1, 0.0), (-1, 0.07)):                     # hind legs, nearly together
        u = (u0 + off) % 1.0
        z, y, v = foot_at(u, P[0][2] - 120, reach, 230, DUTY)
        foot = np.array([side * (BP[22][0] + 30), y, z])
        leg(p, P, side, foot, nrm([side * 0.3, 0.2, 1.0]), rx(D(-35) * math.sin(math.pi * v)))
    P = fk(p)
    for side, off in ((1, 0.5), (-1, 0.58)):                     # the arms half a cycle later
        u = (u0 + off) % 1.0
        sh = P[13] if side > 0 else P[7]
        z, y, v = foot_at(u, sh[2] + 160, reach, 260, DUTY)
        if side > 0:                                             # the claw: talons on the floor
            wr = np.array([sh[0] + 70, 230 + y, z])
            hand = aim([1.0, 0, 0], [0, -1.0, 0], nrm([0.1, -0.35, 1.0]), [0.0, -1.0, 0.2])
            arm(p, P, 1, wr, nrm([0.6, 0.1, -1.0]), hand)
        else:                                                    # the sickle hand on its knuckles, blade up
            wr = np.array([sh[0] - 50, 90 + y, z])
            hand = aim([-1.0, 0, 0], [0, 0, 1.0], nrm([0, 0.25, 1.0]), [0, 1.0, -0.3])     # handle up, the blade arcing ahead
            arm(p, P, -1, wr, nrm([-0.6, 0.1, -1.0]), hand)
    return p
# ------------------------------------------------------------------------------------- leaping swipe
SN = 40; S_HIT = (17, 24)
def swipe(f):
    """from the run: gathers (0-8), springs up and forward (8-16), the claw rakes from high right to low left
    (16-24), lands crouched (24-32), stays low, ready to run again (32-40)"""
    p = Pose(); t = f
    g = sm(t / 8.0) * (1 - sm((t - 8) / 6.0)); up = sm((t - 8) / 8.0) * (1 - sm((t - 26) / 8.0))
    sw = sm((t - 15) / 9.0); land = sm((t - 24) / 8.0)
    leap = 700 * sm((t - 8) / 16.0)
    p.travel = np.array([0, 0, leap])
    pitch = lerp(D(78), D(28), up) + D(10) * g + D(30) * land * (1 - sm((t - 32) / 8.0)) * 0.5
    yaw = D(-25) * up * (1 - sw) + D(30) * sw * (1 - land)
    p.root = BP[0] + np.array([0, -310 - 80 * g + 260 * up - 120 * land * (1 - sm((t - 34) / 6.0)), 0])
    spine(p, pitch, yaw, D(-8) * sw, head_pitch=lerp(D(-62), D(-20), up))
    P = fk(p)
    for side in (1, -1):
        z = 120 - 250 * up + 200 * land
        leg(p, P, side, np.array([side * (BP[22][0] + 60), 0.0, P[0][2] - 100 + z * 0.5]), nrm([side * 0.4, 0.2, 1.0]))
    P = fk(p)
    # the claw: up and out to the right -> raked down across to the left, in front
    sh = P[13]
    w0 = sh + np.array([60, -500, 200]); w1 = sh + np.array([-250, 380, 260]); w2 = sh + np.array([-650, -420, 560])
    wr = lerp(lerp(w0, w1, up * (1 - sw)), w2, sw); wr = lerp(wr, sh + np.array([60, -480, 260]), land)
    hd = nrm(lerp(nrm([0.2, 0.8, 0.4]), nrm([-0.8, -0.6, 0.4]), sw))
    arm(p, P, 1, wr, nrm([0.7, -0.2, -0.6]), aim([1.0, 0, 0], [0, -1.0, 0], hd, [0, 0, 1.0]))
    # the sickle arm cocked back, for balance
    shr = P[7]
    wrr = lerp(shr + np.array([-120, -480, 150]), shr + np.array([-300, 120, -250]), up)
    arm(p, P, -1, wrr, nrm([-0.6, -0.3, -0.8]), aim([-1.0, 0, 0], [0, 0, 1.0], nrm(wrr - shr), [0, 1.0, 0]))
    return p
if __name__ == '__main__':
    RP = [run4(f) for f in range(RN + 1)]; SP = [swipe(f) for f in range(SN + 1)]
    rm = mk.build(RP); sm_ = mk.build(SP)
    print('run', len(rm), mk.check(rm, RP)[1], 'swipe', len(sm_), mk.check(sm_, SP)[1])
    steps = {}
    for k_, se in ((24, 3), (20, 4)):                           # footfalls (Se 3/4: the Ganado's running steps)
        y = [fk(p)[k_][1] for p in RP]; lo = min(y)
        for f in range(1, len(y)):
            if y[f] < lo + 10 and y[f - 1] >= lo + 10: steps[f] = (se, 0)
    rs = mk.seq(RN + 1, steps)
    ss = mk.seq(SN + 1, {**{f: (0, 8) for f in range(0, S_HIT[0] - 6)}, S_HIT[0] - 3: (0, 0x20)})
    pack = bytearray(32); offs = []
    for b_ in (rm, rs, sm_, ss):
        offs.append(len(pack)); pack += b_ + b'\0' * ((-len(b_)) % 32)
    pack[:16] = struct.pack('>4I', *offs)
    open('/home/claude/re4mod/mod/data/carnicero_anim.bin', 'wb').write(bytes(pack))
    open('/home/claude/re4mod/mod/c/carnicero_mot.h', 'w').write('/* mkcarn.py */\n#define CR_RUN 0\n#define CR_SWIPE 2\n#define CR_RUN_N %d\n#define CR_SWIPE_N %d\n#define CR_HIT0 %d\n#define CR_HIT1 %d\n#define CR_SPEED %.1ff\n' % (RN + 1, SN + 1, S_HIT[0], S_HIT[1], SPEED * 0.95))
    print('pack', len(pack), 'steps', steps)
