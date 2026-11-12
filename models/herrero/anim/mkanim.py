"""El Herrero's own motions (game format) + sequences: a heavy walk that drags the anvil, and an overhead
smash. Skeleton = models/herrero rig (game parts 0-25, bind T-pose, identity rotations); the game model is
the rig x0.95 (game.py S), so positions are scaled on export. Output: mod/c/herrero_mot.h"""
import sys, math, struct, numpy as np
sys.path.insert(0, '/home/claude/brute_lp'); sys.path.insert(0, '/home/claude/re4mod/anim/tools')
import rig
from mot import parse, eval_chan, rotm, euler_zyx
S = 0.95
B = {k: (p, np.array(v, float)) for k, (p, v) in rig.B.items()}
ORDER = rig.ORDER
def nrm(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
def lerp(a, b, t): return a + (b - a) * t
def sm(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def aim(d0, u0, d, u):
    """world rotation taking bind direction d0 to d, and bind side vector u0 as close as possible to u"""
    d0, d = nrm(d0), nrm(d)
    u0 = nrm(np.asarray(u0, float) - d0 * (d0 @ u0)); u = nrm(np.asarray(u, float) - d * (d @ u))
    A = np.stack([d0, u0, np.cross(d0, u0)], 1); C = np.stack([d, u, np.cross(d, u)], 1)
    return C @ A.T
def rx(a): c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def ry(a): c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
D = math.radians
def two_bone(Sp, T, la, lb, pole):
    d = T - Sp; L = min(np.linalg.norm(d), la + lb - 1.0); u = nrm(d)
    x = (la * la - lb * lb + L * L) / (2 * L); h = math.sqrt(max(la * la - x * x, 0.0))
    v = nrm(pole - u * (pole @ u)); return Sp + u * x + v * h, Sp + u * L
BP = {k: B[k][1] for k in B}
L_TH = np.linalg.norm(BP[19] - BP[18]); L_SH = np.linalg.norm(BP[20] - BP[19])
L_UA = np.linalg.norm(BP[8] - BP[7]); L_FA = np.linalg.norm(BP[10] - BP[8])
HIP0 = BP[0][1]
GRIP_OFF = 105.0                                  # the fist grips 105 mm past the wrist (model.py GRIP)
BEAM = (1180.0 - 190.0)                           # grip -> anvil centre along the beam (model.py)
class Pose:
    def __init__(s): s.W = {k: np.eye(3) for k in B}; s.root = BP[0].copy(); s.travel = np.zeros(3)
def fk(p):
    P = {}
    for k in ORDER:
        par, pos = B[k]
        P[k] = p.root.copy() if par < 0 else P[par] + p.W[par] @ (pos - B[par][1])
    return P
def spine(p, pitch, yaw, roll, head_pitch=0.0):
    R0 = ry(yaw * 0.4) @ rx(pitch * 0.55) @ rz(roll * 0.5)
    p.W[1] = R0; p.W[2] = ry(yaw) @ rx(pitch) @ rz(roll)
    p.W[3] = p.W[2] @ rx(-pitch * 0.55 + head_pitch * 0.5); p.W[4] = p.W[2] @ rx(-pitch * 0.85 + head_pitch)
    p.W[5] = p.W[2]; p.W[11] = p.W[2]
def leg(p, P, side, foot, pole_fw, foot_R=None):
    h, k_, a, t = (18, 19, 20, 21) if side < 0 else (22, 23, 24, 25)
    hip = P[h]; ank = foot + np.array([0, BP[a][1], 0])
    knee, ank = two_bone(hip, ank, L_TH, L_SH, pole_fw)
    fw = np.array([0, 0, 1.0])
    p.W[h] = aim(BP[k_] - BP[h], fw, knee - hip, pole_fw)
    p.W[k_] = aim(BP[a] - BP[k_], fw, ank - knee, pole_fw)
    p.W[a] = foot_R if foot_R is not None else np.eye(3); p.W[t] = p.W[a]
def arm(p, P, side, wrist, pole, hand_R):
    c, u, f, m, hnd = (5, 7, 8, 9, 10) if side < 0 else (11, 13, 14, 15, 16)
    sh = P[u]; el, wr = two_bone(sh, wrist, L_UA, L_FA, pole)
    X = np.array([side * 1.0, 0, 0])
    p.W[u] = aim(X, [0, 0, 1], el - sh, -pole); p.W[u - 1] = p.W[u]
    p.W[f] = aim(X, [0, 0, 1], wr - el, -pole); p.W[m] = p.W[f]
    p.W[hnd] = hand_R
def beam_hand(beam_dir, fore_dir, side=-1):
    """the right fist: its bind beam axis (-z) along beam_dir, the bind forearm axis (-x) along fore_dir"""
    return aim([0, 0, -1.0], [side * 1.0, 0, 0], beam_dir, fore_dir)
def wrist_for_grip(grip, fore_dir): return grip - nrm(fore_dir) * GRIP_OFF
# ------------------------------------------------------------------------------------------- walk
WN = 64; STEP = 0.6
def walk(f, speed=17.0):
    p = Pose(); ph = 2 * math.pi * f / WN
    p.travel = np.array([0, 0, speed * f])
    sway = 42 * math.sin(ph); bob = -30 - 22 * math.cos(2 * ph)
    p.root = BP[0] + np.array([sway, bob, 0])
    spine(p, D(16) + D(2.5) * math.cos(2 * ph), D(7) * math.sin(ph), -D(4) * math.sin(ph), head_pitch=D(-6))
    p.W[0] = np.eye(3); p.W[17] = ry(-D(6) * math.sin(ph)) @ rz(D(3) * math.sin(ph))
    P = fk(p)
    Lst = speed * STEP * WN
    for side, off in ((1, 0.0), (-1, 0.5)):
        u = (f / WN + off) % 1.0
        x = side * (BP[22][0] + 40)
        if u < STEP: z = Lst / 2 - Lst * (u / STEP); y = 0.0; pitch = 0.0
        else:
            v = (u - STEP) / (1 - STEP); z = -Lst / 2 + Lst * sm(v); y = 150 * math.sin(math.pi * v); pitch = D(-25) * math.sin(math.pi * v)
        foot = np.array([x - sway * 0.0, y, z + 40]) + np.array([0, 0, 0])
        foot = foot + np.array([0, 0, 0])
        leg(p, P, side, np.array([foot[0], foot[1], foot[2]]), nrm([side * 0.25, 0, 1]), rx(pitch))
    P = fk(p)
    # right arm: hangs a little forward, the beam trails back and down, the anvil dragging on the floor
    wr = P[7] + np.array([-70, -560, 120 + 30 * math.sin(ph)])
    fore = nrm(np.array([-0.15, -1.0, 0.25]))
    grip = wr + fore * GRIP_OFF
    back = nrm(np.array([-0.05, -(grip[1] - 140) / BEAM, -1.0])); back = nrm(back * np.array([1, 1, 1]))
    dy = grip[1] - 150; dz = math.sqrt(max(BEAM * BEAM - dy * dy, 1.0)); bdir = nrm([-0.04 * BEAM, -dy, -dz])
    arm(p, P, -1, wr, nrm([0.3, 0, -1.0]), beam_hand(bdir, fore))
    # left arm (the claw): swings against the left leg, elbow bent, claw open in front
    sw = -D(22) * math.sin(ph)
    wl = P[13] + np.array([90, -520, 140]) + np.array([0, 30 * math.cos(ph), 0]) + 260 * np.array([0, 0, math.sin(sw)])
    fl = nrm(wl - P[13])
    arm(p, P, 1, wl, nrm([-0.2, 0, -1.0]), aim([1.0, 0, 0], [0, -1.0, 0], nrm(fl + np.array([0, 0, 0.6])), [-0.3, -0.4, 0.8]))
    return p
# ------------------------------------------------------------------------------------------- smash
SN = 84
F_UP, F_HIT, F_HOLD, F_END = 24, 33, 52, 83
def smash(f):
    p = Pose()
    def key(t):
        """t: 0 idle -> 1 wound up -> 2 impact"""
        return t
    a = sm(f / F_UP); b = sm((f - F_UP) / (F_HIT - F_UP)) if f > F_UP else 0.0
    c = sm((f - F_HOLD) / (F_END - F_HOLD)) if f > F_HOLD else 0.0
    w = a * (1 - b)                                             # wind-up weight
    h = b * (1 - c)                                             # impact weight
    # body
    lunge = 260 * sm((f - F_UP + 4) / (F_HIT - F_UP + 4)) if f > F_UP - 4 else 0.0
    p.travel = np.array([0, 0, lunge])
    drop = -40 * w - 150 * h
    p.root = BP[0] + np.array([-30 * w + 20 * h, drop - 25, 60 * w - 60 * h])
    pitch = D(14) - D(14) * w + D(42) * h; yaw = -D(32) * w + D(14) * h; roll = D(6) * w - D(4) * h
    spine(p, pitch, yaw, roll, head_pitch=D(-14) * h + D(-6))
    p.W[17] = ry(-D(12) * w + D(8) * h)
    P = fk(p)
    # legs: wide stance, left foot forward; the right one slides forward with the lunge
    lf = np.array([BP[22][0] + 70, 0, 260]) - np.array([0, 0, lunge]) * 0.0
    rf = np.array([-BP[18][0] - 60, 0, -150 + 0.0 * lunge])
    leg(p, P, 1, lf - np.array([0, 0, lunge]) + np.array([0, 0, lunge]), nrm([0.3, 0, 1]))
    leg(p, P, -1, rf, nrm([-0.3, 0, 1]))
    P = fk(p)
    # right arm + the anvil: idle (dragging) -> raised over the right shoulder -> slammed down in front
    fore0 = nrm([-0.15, -1.0, 0.25]); wr0 = P[7] + np.array([-70, -560, 120])
    g0 = wr0 + fore0 * GRIP_OFF; dy = g0[1] - 150; bdir0 = nrm([-0.04 * BEAM, -dy, -math.sqrt(max(BEAM ** 2 - dy * dy, 1))])
    wr1 = P[7] + np.array([60, 330, -120]); fore1 = nrm([0.35, 0.75, 0.25]); bdir1 = nrm([0.25, 0.55, -0.8])
    anvil2 = np.array([-60, 170, 1450]); fore2 = nrm([0.1, -0.35, 1.0])
    g2 = anvil2 - nrm(anvil2 - (P[7] + np.array([0, -250, 500]))) * BEAM; bdir2 = nrm(anvil2 - g2); wr2 = g2 - fore2 * GRIP_OFF
    wr = wr0 * (1 - a) + wr1 * a; fore = nrm(fore0 * (1 - a) + fore1 * a); bdir = nrm(bdir0 * (1 - a) + bdir1 * a)
    wr = wr * (1 - b) + wr2 * b; fore = nrm(fore * (1 - b) + fore2 * b); bdir = nrm(bdir * (1 - b) + bdir2 * b)
    wr = wr * (1 - c) + wr0 * c; fore = nrm(fore * (1 - c) + fore0 * c); bdir = nrm(bdir * (1 - c) + bdir0 * c)
    arm(p, P, -1, wr, nrm([0.2, -0.3 * w, -1.0]), beam_hand(bdir, fore))
    # left claw: reaches forward on the wind-up (aiming), braces down on the impact
    wl0 = P[13] + np.array([90, -520, 140]); wl1 = P[13] + np.array([-120, -120, 520]); wl2 = P[13] + np.array([60, -480, 330])
    wl = wl0 * (1 - a) + wl1 * a; wl = wl * (1 - b) + wl2 * b; wl = wl * (1 - c) + wl0 * c
    fl = nrm(wl - P[13])
    arm(p, P, 1, wl, nrm([-0.2, 0, -1.0]), aim([1.0, 0, 0], [0, -1.0, 0], nrm(fl + np.array([0, 0, 0.6])), [-0.3, -0.4, 0.8]))
    return p
# ------------------------------------------------------------------------------------------- export
CH = [(0, 1), (0, 4)] + [(k, 2) for k in (1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25)]
def local(p, k):
    par = B[k][0]; return (p.W[par].T @ p.W[k]) if par >= 0 else p.W[k]
def reduce(v, tol):
    n = len(v); d = np.gradient(v) if n > 1 else np.zeros(n); keys = [0]; s = 0
    while s < n - 1:
        e = s + 1
        while e + 1 < n:
            L = e + 1 - s; ok = True
            for f in range(s + 1, e + 1):
                t = (f - s) / L; t2 = t * t; t3 = t2 * t; h01 = -2 * t3 + 3 * t2; h11 = t3 - t2; h10 = h11 - t2 + t; h00 = 1 - h01
                if abs(v[s] * h00 + v[e + 1] * h01 + d[s] * L * h10 + d[e + 1] * L * h11 - v[f]) > tol: ok = False; break
            if not ok: break
            e += 1
        keys.append(e); s = e
    return [(k, float(v[k]), float(d[k] * ((k - keys[j - 1]) if j else 0)), float(d[k] * ((keys[j + 1] - k) if j + 1 < len(keys) else 0))) for j, k in enumerate(keys)]
def build(poses):
    N = len(poses); kinds = []; nos = []; blobs = []
    for no, kind in CH:
        if kind == 1: arr = np.array([p.travel * S for p in poses])
        elif kind == 4: arr = np.array([p.root * S for p in poses])
        else: arr = np.unwrap(np.array([euler_zyx(local(p, no)) for p in poses]), axis=0)
        kinds.append(kind); nos.append(no); b = b''
        for ax in range(3):
            ks = reduce(arr[:, ax], 0.5 if kind != 2 else 0.002)
            b += struct.pack('>H', len(ks)) + b''.join(struct.pack('>H', k[0]) for k in ks) + b''.join(struct.pack('>fff', *k[1:]) for k in ks)
        blobs.append(b)
    n = len(CH); hdr = struct.pack('>HB', N - 1, n) + b''.join(struct.pack('>H', x) for x in kinds) + bytes(nos)
    hdr += b'\0' * ((-len(hdr)) % 4); base = len(hdr) + 4 + 4 * n; offs = []; data = b''; q = base
    for b in blobs: offs.append(q); data += b; q += len(b)
    out = hdr + struct.pack('>I', (base + len(data) + 31) & ~31) + b''.join(struct.pack('>I', o) for o in offs) + data
    return out + b'\0' * ((-len(out)) % 32)
def seq(N, events):
    """events: frame -> (se, free). Free persists until changed (one entry per frame, like the game's)"""
    out = struct.pack('>HH', N, 0); fr = 0
    for f in range(N):
        se, free = events.get(f, (0, events.get('default', (0, 0))[1]))
        out += struct.pack('>HBB', f << 6, se, free)
    return out + b'\0' * ((-len(out)) % 32)
def check(blob, poses):
    mf, ch = parse(blob); err = 0
    for c, (no, kind) in zip(ch, CH):
        for f in range(0, len(poses), 3):
            v = np.array(eval_chan(c, f))
            w_ = poses[f].travel * S if kind == 1 else (poses[f].root * S if kind == 4 else euler_zyx(local(poses[f], no)))
            dd = np.abs(((v - w_ + np.pi) % (2 * np.pi)) - np.pi) if kind == 2 else np.abs(v - w_)
            err = max(err, dd.max() / (0.001 if kind == 2 else 1))
    return mf, err
def blobc(name, b):
    b = b + b'\0' * (-len(b) % 4); w = struct.unpack('>%dI' % (len(b) // 4), b)
    return 'static const u32 %s[%d] __attribute__((aligned(32))) = {\n' % (name, len(w)) + ',\n'.join(','.join('0x%08X' % x for x in w[i:i + 8]) for i in range(0, len(w), 8)) + '};\n'
if __name__ == '__main__':
    WP = [walk(f) for f in range(WN + 1)]; SP = [smash(f) for f in range(SN)]
    wm = build(WP); sm_ = build(SP)
    print('walk', check(wm, WP), len(wm), '| smash', check(sm_, SP), len(sm_))
    ev = {f: (0, 8) for f in range(0, 20)}                  # 8: keep turning to Leon (wind-up)
    ev.update({F_UP: (0, 0x20)})                             # 0x20: the swing sound
    ev.update({f: (0, 1) for f in range(F_HIT - 5, F_HIT + 2)})   # 1: the attack check (the game's own)
    ss = seq(SN, ev); ws = seq(WN + 1, {})
    out = '/* generated by models/herrero/anim/mkanim.py */\n#define HR_WALK_N %d\n#define HR_SMASH_N %d\n' % (WN, SN)
    out += blobc('hr_walk_mot', wm) + blobc('hr_walk_seq', ws) + blobc('hr_smash_mot', sm_) + blobc('hr_smash_seq', ss)
    open('/home/claude/re4mod/mod/c/herrero_mot.h', 'w').write(out)
    import pickle; pickle.dump((WP, SP), open('/tmp/hr_poses.pkl', 'wb'))
