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
# ------------------------------------------------------------------------------- B84: the user's swing
# anim/mixamo/herrero/Heavy_Weapon_Swing.fbx (Mixamo, two hands on a long weapon), retargeted by world
# rotations (both skeletons bind in a T-pose): the fist turned so the beam lies along the weapon's shaft
# (left hand -> right hand), the claw put on the handle by IK, the root kept so the feet stay on the floor.
sys.path.insert(0, '/home/claude/re4mod/anim/tools')
from mix import Fbx
SW_PATH = '/home/claude/re4mod/anim/mixamo/herrero/Heavy_Weapon_Swing.fbx'
SW0, SW1 = 36, 140                                  # the swing inside the clip (30 fps frames)
SW_HIT = (76, 86)                                   # the anvil comes down (clip frames)
SW_FLOOR = 170.0                                    # lowest anvil centre (its half height)
MAPX = {1: 'Spine', 2: 'Spine2', 3: 'Neck', 4: 'Head', 5: 'RightShoulder', 7: 'RightArm', 8: 'RightForeArm',
        9: 'RightForeArm', 10: 'RightHand', 11: 'LeftShoulder', 13: 'LeftArm', 14: 'LeftForeArm', 15: 'LeftForeArm',
        16: 'LeftHand', 17: 'Hips', 18: 'RightUpLeg', 19: 'RightLeg', 20: 'RightFoot', 21: 'RightToeBase',
        22: 'LeftUpLeg', 23: 'LeftLeg', 24: 'LeftFoot', 25: 'LeftToeBase'}
_fb = None; _bind = None
def swing(f):
    global _fb, _bind
    if _fb is None: _fb = Fbx(SW_PATH); _bind = Fbx('/home/claude/re4mod/anim/mixamo/X Bot.fbx').world()
    t = (SW0 + f) / 30.0; Wm = _fb.world(t); W0 = _fb.world(SW0 / 30.0)
    p = Pose()
    for k, n in MAPX.items(): p.W[k] = Wm[n][0] @ _bind[n][0].T
    p.W[6] = p.W[7]; p.W[12] = p.W[13]
    sc = BP[0][1] / _bind['Hips'][1][1]
    d = (Wm['Hips'][1] - _bind['Hips'][1]) * sc
    p.root = BP[0] + np.array([d[0], d[1], d[2]]) - np.array([(W0['Hips'][1] - _bind['Hips'][1])[0] * sc, 0, (W0['Hips'][1] - _bind['Hips'][1])[2] * sc])
    P = fk(p)
    low = min(P[20][1] - BP[20][1], P[24][1] - BP[24][1], P[21][1] - BP[21][1], P[25][1] - BP[25][1])
    p.root[1] -= low                                                     # feet on the floor
    P = fk(p)
    # right fist: beam along the shaft (left hand -> right hand of the clip)
    sh = nrm(Wm['RightHand'][1] - Wm['LeftHand'][1])
    cur = p.W[10] @ np.array([0, 0, -1.0])
    ax = np.cross(cur, sh); s_ = np.linalg.norm(ax); c_ = cur @ sh
    if s_ > 1e-6:
        ax /= s_; a_ = math.atan2(s_, c_); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
        p.W[10] = (np.eye(3) + math.sin(a_) * K + (1 - math.cos(a_)) * K @ K) @ p.W[10]
    P = fk(p)
    grip = P[10] + p.W[10] @ np.array([-GRIP_OFF, 0, 0])
    # our beam is longer than the clip's weapon: where the anvil would go through the floor, the beam is
    # pitched up (about the grip) so the anvil lands on it
    sh_ = p.W[10] @ np.array([0, 0, -1.0]); ymin = (SW_FLOOR - grip[1]) / BEAM
    if sh_[1] < ymin:
        hz = np.array([sh_[0], 0, sh_[2]]); hz = nrm(hz) * math.sqrt(max(1 - ymin * ymin, 0.0)); new = nrm(hz + np.array([0, ymin, 0]))
        ax = np.cross(sh_, new); s_ = np.linalg.norm(ax)
        if s_ > 1e-6:
            ax /= s_; a_ = math.atan2(s_, sh_ @ new); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
            p.W[10] = (np.eye(3) + math.sin(a_) * K + (1 - math.cos(a_)) * K @ K) @ p.W[10]
    P = fk(p)
    grip = P[10] + p.W[10] @ np.array([-GRIP_OFF, 0, 0])                 # bind: the grip is 105 mm along -x from the wrist
    shaft = p.W[10] @ np.array([0, 0, -1.0])
    # claw on the handle, 270 mm behind the grip; its elbow where the clip's is
    target = grip - shaft * 270
    for _ in range(3):
        fl = nrm(target - P[13]); wl = target - fl * 95
        pole = nrm((Wm['LeftForeArm'][1] - (Wm['LeftArm'][1] + Wm['LeftHand'][1]) / 2) + np.array([0, -0.01, 0]))
        hand = aim([1.0, 0, 0], [0, 0, 1.0], fl, -shaft)
        arm(p, P, 1, wl, pole, p.W[16] if False else hand)
    return p


# ---------------------------------------------------------------- B85: the user's creature pack (Mixamo)
PACK = '/home/claude/re4mod/anim/mixamo/herrero/pack/'
_fbs = {}
def mixpose(name, t, travel_z=False):
    """retarget by world rotations; travel_z: the clip's forward travel goes to the root track"""
    global _bind
    if _bind is None: _bind = Fbx('/home/claude/re4mod/anim/mixamo/X Bot.fbx').world()
    if name not in _fbs: _fbs[name] = Fbx(PACK + name + '.fbx')
    fb = _fbs[name]; Wm = fb.world(t); W0 = fb.world(0.0)
    p = Pose()
    for k, n in MAPX.items(): p.W[k] = Wm[n][0] @ _bind[n][0].T
    p.W[6] = p.W[7]; p.W[12] = p.W[13]
    sc = BP[0][1] / _bind['Hips'][1][1]
    d = (Wm['Hips'][1] - W0['Hips'][1]) * sc; h = (W0['Hips'][1] - _bind['Hips'][1]) * sc
    p.root = BP[0] + np.array([d[0], h[1] + d[1], 0.0 if travel_z else d[2]])
    if travel_z: p.travel = np.array([0.0, 0.0, d[2]])
    P = fk(p)
    low = min(P[20][1] - BP[20][1], P[24][1] - BP[24][1], P[21][1] - BP[21][1], P[25][1] - BP[25][1])
    p.root[1] -= low
    return p, Wm
def drag_right(p, swing=0.0):
    """the right arm hangs and drags the anvil on the floor behind (the user likes it): B83's walk arm"""
    P = fk(p)
    wr = P[7] + np.array([-70, -560, 120 + swing])
    fore = nrm(np.array([-0.15, -1.0, 0.25])); grip = wr + fore * GRIP_OFF
    dy = grip[1] - 150; dz = math.sqrt(max(BEAM * BEAM - dy * dy, 1.0)); bdir = nrm([-0.04 * BEAM, -dy, -dz])
    arm(p, P, -1, wr, nrm([0.3, 0, -1.0]), beam_hand(bdir, fore))
WALK_SLOW = 0.55                                     # the clip played at 55 %: heavy (~26 mm per frame)
def walk2(f, n):
    fb_dur = 1.4333
    t = (f / n) * fb_dur
    p, Wm = mixpose('mutant walking', t, travel_z=True)
    ph = 2 * math.pi * f / n
    drag_right(p, 40 * math.sin(ph))
    return p
def idle(f, n):
    p, Wm = mixpose('mutant breathing idle', f / 30.0)
    drag_right(p)
    return p
FLEX0, FLEX1 = 36, 124
def flex(f):
    p, Wm = mixpose('mutant flexing muscles', (FLEX0 + f) / 30.0)
    drag_right(p)                                    # the beam stays in the right hand, the claw flexes
    return p
if __name__ == '__main__':
    WN2 = int(round(43 / WALK_SLOW)); IN = 120
    WP = [walk2(f, WN2) for f in range(WN2 + 1)]; SP = [swing(f) for f in range(SW1 - SW0 + 1)]
    IP = [idle(f, IN) for f in range(IN + 1)]; FP = [flex(f) for f in range(FLEX1 - FLEX0 + 1)]
    wm = build(WP); sm_ = build(SP); im = build(IP); fm = build(FP)
    print('walk', check(wm, WP), len(wm), '| smash', check(sm_, SP), len(sm_), '| idle', len(im), '| flex', len(fm))
    print('walk travel per frame', WP[-1].travel[2] * S / WN2)
    NS = len(SP); h0, h1 = SW_HIT[0] - SW0, SW_HIT[1] - SW0
    ev = {f: (0, 8) for f in range(0, h0 - 8)}              # 8: keep turning to Leon (wind-up)
    ev.update({h0 - 4: (0, 0x20)})                           # 0x20: the swing sound
    # B85: no Free 1 (the game's check sweeps the hidden axe): stealth.c HerreroHit checks the anvil itself
    ss = seq(NS, ev); ws = seq(WN2 + 1, {}); is_ = seq(IN + 1, {}); fs = seq(len(FP), {})
    # the anvil centre in the fist's (part 10) frame, game units (the weapon is rigid on part 10)
    av = (np.array([-GRIP_OFF, 0.0, -BEAM]) + np.array([0, 120.0, 0])) * S
    out = '/* generated by models/herrero/anim/mkanim.py */\n#define HR_WALK_N %d\n#define HR_SMASH_N %d\n' % (WN2, NS - 1)
    out += '#define HR_HIT0 %d\n#define HR_HIT1 %d\n#define HR_ANVIL_X %.1ff\n#define HR_ANVIL_Y %.1ff\n#define HR_ANVIL_Z %.1ff\n' % (h0, h1 + 2, av[0], av[1], av[2])
    # B85: the motions travel inside the Herrero's BIN (game.py appends this pack and puts its offset at
    # BIN+0x5C): the mod's code space in the dol is too small for them
    blobs = [wm, ws, sm_, ss, im, is_, fm, fs]
    pack = bytearray(struct.pack('>8I', *([0] * 8))); pack += b'\0' * ((-len(pack)) % 32); offs = []
    for b_ in blobs:
        offs.append(len(pack)); pack += b_ + b'\0' * ((-len(b_)) % 32)
    pack[:32] = struct.pack('>8I', *offs)
    open('/home/claude/re4mod/mod/data/herrero_anim.bin', 'wb').write(bytes(pack))
    out += '/* motion pack inside the BIN: u32 at BIN+0x5C = pack offset; pack[i] = offset (from the pack) */\n'
    out += '#define HR_WALK 0\n#define HR_SMASH 2\n#define HR_IDLE 4\n#define HR_FLEX 6\n'
    print('pack', len(pack))
    open('/home/claude/re4mod/mod/c/herrero_mot.h', 'w').write(out)
    import pickle; pickle.dump((WP, SP), open('/tmp/hr_poses.pkl', 'wb'))

