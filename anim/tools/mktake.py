# Stealth takedown (remake style): Leon grabs a Ganado from behind - left hand over its mouth - and
# drives the knife into the right side of its neck. The Ganado plays the game's own grabbed-from-
# behind death (em10.drs motion 0x2BA + sequence 0x2BB, HUNK's neck-break victim in The
# Mercenaries; arc.py index = game index - 4), which this script also exports as a blob for the mod
# (every Ganado module has the em10 code that plays it, only em10.drs carries the data).
# Leon's side is built here frame by frame against that motion (same skeleton, parts 0-25), with
# two-bone IK for arms and legs, and written in crouch.c's clip format (take_data.h):
#   per frame: local rotation (Euler ZYX, s16 1e-4 rad) of the 29 crouch parts, root height, and
#   Leon's root x/z in the Ganado's start frame (it faces +z, Leon behind it at -z).
import sys, math, struct
import numpy as np
sys.path.insert(0, '/home/claude/re4mod/anim/tools')
from arc import load_arc, entry
from leon import SK, PAR, OFF
from mot import parse, eval_chan, rotm, euler_zyx

OUT = '/home/claude/re4mod/mod/c/take_data.h'
EM10 = '/home/claude/disc/ext1/files/em/em10.drs'
MOT, SEQ = 0x2BA - 4, 0x2BB - 4
BODY = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,113,114,117,118]
N = len(SK)

# ---------------------------------------------------------------- small math
def nrm(v): v = np.asarray(v, float); return v / np.linalg.norm(v)
def Rx(a): c, s = math.cos(a), math.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def Ry(a): c, s = math.cos(a), math.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def Rz(a): c, s = math.cos(a), math.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def frame(a_l, a_w, b_l, b_w):
    """rotation taking local axis a_l to world a_w, and b_l as close as possible to b_w"""
    a_l, a_w = nrm(a_l), nrm(a_w)
    b_l = nrm(np.asarray(b_l, float) - a_l * np.dot(b_l, a_l)); b_w = nrm(np.asarray(b_w, float) - a_w * np.dot(b_w, a_w))
    L = np.stack([a_l, b_l, np.cross(a_l, b_l)], 1); W = np.stack([a_w, b_w, np.cross(a_w, b_w)], 1)
    return W @ L.T
def q_of(R):
    t = R[0,0] + R[1,1] + R[2,2]
    if t > 0:
        s = math.sqrt(t + 1) * 2; return np.array([0.25*s, (R[2,1]-R[1,2])/s, (R[0,2]-R[2,0])/s, (R[1,0]-R[0,1])/s])
    i = int(np.argmax([R[0,0], R[1,1], R[2,2]]))
    if i == 0:
        s = math.sqrt(1 + R[0,0] - R[1,1] - R[2,2]) * 2; return np.array([(R[2,1]-R[1,2])/s, 0.25*s, (R[0,1]+R[1,0])/s, (R[0,2]+R[2,0])/s])
    if i == 1:
        s = math.sqrt(1 + R[1,1] - R[0,0] - R[2,2]) * 2; return np.array([(R[0,2]-R[2,0])/s, (R[0,1]+R[1,0])/s, 0.25*s, (R[1,2]+R[2,1])/s])
    s = math.sqrt(1 + R[2,2] - R[0,0] - R[1,1]) * 2; return np.array([(R[1,0]-R[0,1])/s, (R[0,2]+R[2,0])/s, (R[1,2]+R[2,1])/s, 0.25*s])
def R_of(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
def slerpR(A, B, t):
    qa, qb = q_of(A), q_of(B)
    if np.dot(qa, qb) < 0: qb = -qb
    return R_of(qa * (1 - t) + qb * t)
def rot_between(u, v):
    u = nrm(u); v = nrm(v); c = float(np.dot(u, v)); ax = np.cross(u, v); s_ = np.linalg.norm(ax)
    if s_ < 1e-9: return np.eye(3)
    ax /= s_; K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + K * s_ + K @ K * (1 - c)
def ss(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
def ramp(f, a, b): return ss((f - a) / float(b - a))
def lerp(a, b, t): return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t

def fk(Wrot, root):
    """world rotations (dict, missing parts inherit the parent's) -> world R, P lists"""
    R = [None] * N; P = [None] * N
    for i in range(N):
        p = PAR[i]
        if p == 255: R[i] = Wrot.get(i, np.eye(3)); P[i] = np.asarray(root, float); continue
        R[i] = Wrot.get(i, R[p]); P[i] = P[p] + R[p] @ OFF[i]
    return R, P
def fk_local(L, root):
    R = [None] * N; P = [None] * N
    for i in range(N):
        p = PAR[i]
        if p == 255: R[i] = L.get(i, np.eye(3)); P[i] = np.asarray(root, float); continue
        R[i] = R[p] @ L.get(i, np.eye(3)); P[i] = P[p] + R[p] @ OFF[i]
    return R, P

def two_bone(S, T, la, lb, pole):
    d = T - S; L = np.linalg.norm(d); L = min(L, la + lb - 1.0); u = d / np.linalg.norm(d)
    x = (la * la - lb * lb + L * L) / (2 * L); h = math.sqrt(max(la * la - x * x, 0.0))
    v = pole - u * np.dot(pole, u); v = nrm(v)
    return S + u * x + v * h, S + u * L

# ---------------------------------------------------------------- the Ganado (game motion)
arc = load_arc(EM10)
mot, seq = entry(arc, MOT), entry(arc, SEQ)

# ---- edits to the Ganado's data (B64)
# 1) the neck break twists the head ~80-200 deg (frames 40-84): the head and neck keys are replaced
#    there by a limp head (sags forward, a little to the side), blended in and out.
def patch_rot(m, part, fn):
    m = bytearray(m)
    mf = struct.unpack('>H', m[0:2])[0] & 0x3fff; n = m[2]
    kinds = struct.unpack('>%dH' % n, m[3:3 + 2 * n]); nos = list(m[3 + 2 * n:3 + 3 * n])
    t = (3 + 3 * n + 3) & ~3; t += 4
    offs = struct.unpack('>%dI' % n, m[t:t + 4 * n])
    from mot import KSIZE, key
    for i in range(n):
        if nos[i] != part or (kinds[i] & 0xff) != 2: continue
        fmt = kinds[i] >> 12; p = offs[i]
        assert fmt in (0, 5), fmt
        for ax in range(3):
            k = struct.unpack('>H', m[p:p + 2])[0]
            fr = struct.unpack('>%dH' % k, m[p + 2:p + 2 + 2 * k]); d0 = p + 2 + 2 * k
            old = [key(fmt, bytes(m[d0:]), j) for j in range(k)]
            for j in range(k):
                f = fr[j]
                g = lambda x: fn(ax, x, old, fr)
                v = g(f); sl = g(f + 0.5) - g(f - 0.5)
                tin = sl * (f - fr[j - 1]) if j > 0 else 0.0
                tout = sl * (fr[j + 1] - f) if j + 1 < k else 0.0
                o = d0 + j * KSIZE[fmt]
                if fmt == 0: m[o:o + 12] = struct.pack('>fff', v, tin, tout)
                else:
                    c = lambda x: max(-32767, min(32767, int(round(x * 10000))))
                    m[o:o + 6] = struct.pack('>hhh', c(v), c(tin), c(tout))
            p = d0 + KSIZE[fmt] * k
    return bytes(m)
def herm_old(old, fr, f):
    from mot import sample
    return sample([(fr[j],) + tuple(old[j]) for j in range(len(fr))], f)
def limp(target, axes):
    def fn(ax, f, old, fr):
        o = herm_old(old, fr, f)
        if ax not in axes: return o
        w = ramp(f, 33, 40) * (1 - ramp(f, 84, 94))
        return o * (1 - w) + target[ax] * w
    return fn
mot = patch_rot(mot, 4, limp([0.35, 0.15, -0.15], (0, 1, 2)))
mot = patch_rot(mot, 3, limp([0.0, 0.15, 0.08], (1, 2)))
# 2) the 'neck' event (Free 0x11: death voice, weapon dropped, score) moves from frame 37 to 9, so
#    a pitchfork / axe falls when Leon grabs instead of going through him (B68: 19, the first frame played)
seq = bytearray(seq)
def seq_ent(f): return 4 + 4 * f
assert struct.unpack('>H', seq[seq_ent(37):seq_ent(37) + 2])[0] == 37 << 6 and seq[seq_ent(37) + 3] == 0x11
seq[seq_ent(37) + 3] = 0; seq[seq_ent(19) + 3] |= 0x11     # B68: the motion starts at 18
seq = bytes(seq)
MF, CH = parse(mot)
DISP = [c for c in CH if c['no'] == 0 and c['kind'] == 1][0]
def ganado(f):
    """the Ganado's head / neck frames in the scene (its start frame), plain FK of the rot channels"""
    L = {}; root = np.zeros(3)
    for c in CH:
        if c['no'] >= N: continue
        v = eval_chan(c, f)
        if c['kind'] == 2: L[c['no']] = rotm(v)
        if c['kind'] == 4 and c['no'] == 0: root = np.array(v)
    d = eval_chan(DISP, f)
    off = np.array([d[0], 0, d[2]])
    R, P = fk_local(L, root + off)
    # arms / legs: the motion keys the hand / ankle positions (model space) and IK solves the rest
    ik = {c['no']: np.array(eval_chan(c, f)) for c in CH if c['kind'] == 4 and c['no'] in (10, 16, 20, 24)}
    for s_, m_, e_, pole in ((7, 8, 10, [-1, -1, -0.5]), (13, 14, 16, [1, -1, -0.5]), (18, 19, 20, [0, 0, 1]), (22, 23, 24, [0, 0, 1])):
        if e_ in ik:
            la = np.linalg.norm(OFF[m_]); lb = np.linalg.norm(P[e_] - P[m_])
            K, A = two_bone(P[s_], ik[e_] + off, la, lb, np.array(pole, float))
            P[m_] = K; P[e_] = A
            if m_ == 8: P[9] = A
            if m_ == 14: P[15] = A
    return R, P

# ---------------------------------------------------------------- Leon's crouch idle (start / end pose)
def load_idle():
    src = open('/home/claude/re4mod/mod/c/crouch_data.h').read()
    a = src.index('cr_idle_rot'); b = src.index('{', src.index('= {', a) + 3); e = src.index('}', b)
    vals = [int(x) for x in src[b+1:e].split(',')]
    y0 = int(src[src.index('cr_idle_y'):].split('{')[1].split(',')[0])
    L = {}
    for k, p in enumerate(BODY):
        L[p] = rotm([vals[k*3] * 1e-4, vals[k*3+1] * 1e-4, vals[k*3+2] * 1e-4])
    return L, float(y0)
IDLE_L, IDLE_Y = load_idle()

# ---------------------------------------------------------------- Leon = HUNK's half of the neck break (B68)
# em10.drs also carries the catcher's motion of that pair: game 0x2B9 (arc.py 0x2B5, 77 frames, FK arms,
# IK legs). EmCatchPLSet(em, 0, 2, -75.21, 0, 1076.1) puts the Ganado 1076 in front of HUNK, turned
# away from him (180 deg); from frame ~18 HUNK is at its side holding its head. Leon plays that body
# motion MIRRORED (left <-> right: his right hand - the knife - comes to the front of the throat, the
# left one holds the back of the head) and, instead of the twist, the knife hand draws across the
# throat (frames 33-39). Frames before TK_S0 are not played: the Ganado's motion starts at TK_S0 and
# Leon gets there from his crouch in the first frames.
HUNK = entry(arc, 0x2B9 - 4)
HMF, HCH = parse(HUNK)
_seen = set(); HCH1 = []
for c in HCH:                                   # (it repeats a few channels at the end: not body ones)
    k = (c['no'], c['kind'])
    if k in _seen: continue
    _seen.add(k); HCH1.append(c)
R180 = np.diag([-1.0, 1.0, -1.0]); BASE = np.array([-75.21, 0.0, 1076.1])
MIR = np.diag([-1.0, 1.0, 1.0])
SWAP = {5: 11, 6: 12, 7: 13, 8: 14, 9: 15, 10: 16, 18: 22, 19: 23, 20: 24, 21: 25, 113: 114, 117: 118}
SWAP.update({v: k for k, v in list(SWAP.items())})
TK_S0 = 18                                      # first motion frame played (Ganado held from here)

def hunk(f):
    """HUNK's world rotations / positions at frame f, in the Ganado's start frame, mirrored"""
    f = min(f, HMF)
    L = {}; root = np.array([0, 1050.0, 0]); pos = {}; rot_w = {}; disp = np.zeros(3)
    for c in HCH1:
        v = np.array(eval_chan(c, f)); n = c['no']
        if c['kind'] == 2 and n < N:
            L[n] = rotm(v)
        if c['kind'] == 4:
            if n == 0: root = v
            else: pos[n] = v
        if c['kind'] == 1 and n == 0: disp = v
    off = np.array([disp[0], 0, disp[2]])
    R = [None] * N; P = [None] * N
    for i in range(N):
        p = PAR[i]
        if p == 255: R[i] = np.eye(3); P[i] = root + off; continue
        Li = L.get(i, np.eye(3))
        if i in (20, 24): R[i] = L.get(i, np.eye(3))           # IK effector: model-space rotation
        else: R[i] = R[p] @ Li
        P[i] = P[p] + R[p] @ OFF[i]
    for t in (113, 117, 114, 118):                               # twist bones follow their arm bone
        R[t] = R[{113: 7, 117: 8, 114: 13, 118: 14}[t]]
    # legs: IK to the keyed ankle, knee towards the foot's forward
    for hip, kn, an, toe in ((18, 19, 20, 21), (22, 23, 24, 25)):
        A = pos.get(an, P[an] - off) + off
        fwd = R[an] @ np.array([0, 0, 1.0])
        K, A2 = two_bone(P[hip], A, np.linalg.norm(OFF[kn]), np.linalg.norm(OFF[an]), fwd + np.array([0, 0.2, 0]))
        R[hip] = frame([0, -1, 0], K - P[hip], [0, 0, 1], fwd)
        R[kn] = frame([0, -1, 0], A2 - K, [0, 0, 1], fwd)
        R[toe] = R[an] @ L.get(toe, np.eye(3))
    # HUNK frame -> Ganado start frame (its back to him: 180 deg), then mirrored
    W = {}
    for i in range(N):
        if R[i] is None: continue
        j = SWAP.get(i, i)
        W[j] = MIR @ (R180 @ R[i]) @ MIR
    root_g = MIR @ (R180 @ (P[0] - BASE))
    return W, root_g

# Leon's facing during the take: HUNK's hips, mirrored (about +90 deg: across the Ganado's back)
def _yaw(W): v = W[1] @ np.array([0, 0, 1.0]); return math.atan2(v[0], v[2])
Y0 = float(np.mean([_yaw(hunk(f)[0]) for f in range(TK_S0, 56)]))
RY0 = Ry(Y0)

# ---------------------------------------------------------------- timeline (motion frames, 30 / s)
F_IN = TK_S0 + 9          # crouch -> HUNK's hold
F_SLIT = (33, 41)         # the knife across the throat (B70: longer)
F_STAB = F_SLIT
F_OUT = (42, 50)          # hand away from the throat
F_REL = (52, 62)          # HUNK lets go (hands off the head)
F_HUNK = 56               # last HUNK frame; then Leon settles into the crouch where he is
F_SHEATH = (66, 78)       # down in the crouch: knife to the chest sheath (hidden at 78)
F_END = 92
NF = F_END + 1
KNIFE_K = 0.70
KNIFE = 330.0 * KNIFE_K   # wrist -> blade tip
GD_S0 = ganado(TK_S0)[1][0] * np.array([1, 0, 1])                # Ganado root at the press (x / z)

def arm(Wrot, P_sh, wrist, hand_R, side, pole):
    up, fore = (7, 8) if side < 0 else (13, 14)
    tw_u, tw_f, mid, hand = (113, 117, 9, 10) if side < 0 else (114, 118, 15, 16)
    E, Wp = two_bone(P_sh, wrist, np.linalg.norm(OFF[8]), np.linalg.norm(OFF[9]) + np.linalg.norm(OFF[10]), pole)
    ax = np.array([side, 0, 0.0])
    Ru = frame(ax, E - P_sh, [0, 0, 1], Wp - E)
    Rf = frame(ax, Wp - E, [0, 1, 0], hand_R @ np.array([0, 1, 0]))
    for p in (up, tw_u): Wrot[p] = Ru
    for p in (fore, tw_f, mid): Wrot[p] = Rf
    Wrot[hand] = hand_R
def arm_free(Wrot, P_sh, wrist, hand_fn, side, fd, out=None, w_out=0.0):
    """two-bone arm with the elbow picked round its circle so the forearm points along fd (the
    hand then continues the forearm: hand_fn(forearm dir) -> hand rotation); returns the forearm dir"""
    la = np.linalg.norm(OFF[8]); lb = np.linalg.norm(OFF[9]) + np.linalg.norm(OFF[10])
    axis = nrm(wrist - P_sh); best = None
    ref = nrm(np.cross(axis, [0, 1.0, 0]) if abs(axis[1]) < 0.9 else np.cross(axis, [1.0, 0, 0]))
    for i in range(72):
        a = 2 * math.pi * i / 72
        pole = math.cos(a) * ref + math.sin(a) * np.cross(axis, ref)
        E, Wp = two_bone(P_sh, wrist, la, lb, pole)
        sc = nrm(Wp - E) @ fd - 0.004 * max(0.0, E[1] - P_sh[1] - 120.0)  # not over the shoulder
        if out is not None: sc += w_out * (nrm(E - P_sh) @ out)          # B74: the elbow out, not in
        if best is None or sc > best[0]: best = (sc, pole)
    hand_R = None
    E, Wp = two_bone(P_sh, wrist, la, lb, best[1])
    fdir = nrm(Wp - E)
    hand_R = hand_fn(fdir)
    arm(Wrot, P_sh, wrist, hand_R, side, best[1])
    return fdir
LEAN = 90.0
DY = 0.0                  # auto-fit variants (the neck higher / lower than this Ganado's)
NECK_UP = 0.62            # the throat: 62 % up from the neck base to the head (B72 0.55: a bit low)
R_NECK = 58.0             # neck radius at the throat
INS = 45.0                # how far the tip is in
TH0, TH1 = 15.0, -30.0    # the cut round the front of the neck (B73 +30/-70 folded the arm in)
def knife_hand(d, fingers):
    return frame([0, 0, 1], d, [-1, 0, 0], fingers)

def leon(f):
    fh = min(max(f, TK_S0), F_HUNK)
    W, root = hunk(fh)
    gR, gP = ganado(min(f, 70))
    _, P = fk(W, root)
    # B74: HUNK's body turns away during the cut (the arm ran out of reach): Leon leans in ~9 cm
    w_sh = ramp(f, 28, 35) * (1 - ramp(f, 46, 56))
    if w_sh > 0:
        dv = gP[3] - P[7]; dv[1] = 0.0
        root = root + nrm(dv) * LEAN * w_sh
        _, P = fk(W, root)
    # the knife hand: HUNK's (front of the face) -> across the throat -> away -> down by the side
    # B70: lower and closer in (B69's blade went past the chin, in the air): the throat, 45 mm in
    # front of the neck's middle, just under the jaw
    # B72: the throat from the neck itself (55 % up from the neck base to the head, 60 mm in front of
    # its axis), so the blade follows it; the Ganado is drawn at scale 1 during the kill (stealth.c),
    # earlier builds missed by its random 1.01-1.1 body scale (up to ~140 mm at the neck)
    gP = [None if p is None else p + np.array([0.0, DY, 0.0]) for p in gP]   # DY: the auto-fit variants
    # B73: the tip goes INTO the side of the neck and is dragged round the front of it (a hand and
    # forearm in one line: the blade comes out of the fist at right angles, so it points into the
    # neck, not across it - B72 bent the wrist 100-130 deg to lay it across)
    ax_n = nrm(gP[4] - gP[3])
    fw = np.array([0.0, 0.0, 1.0]); fw = nrm(fw - ax_n * (fw @ ax_n))
    lat = nrm(np.cross(ax_n, fw))
    if lat[0] < 0: lat = -lat                                     # the Ganado's left (+x)
    A = gP[3] + (gP[4] - gP[3]) * NECK_UP                         # the neck's axis at the throat
    t_in = ramp(f, 22, 28)
    t_cut = ramp(f, *F_SLIT)
    t_out = ramp(f, *F_OUT)
    th = math.radians(lerp(TH0, TH1, t_cut))
    u = math.cos(th) * fw + math.sin(th) * lat                    # out of the neck at the blade
    tg = nrm(-math.sin(th) * fw + math.cos(th) * lat)             # round the neck, to its left
    ins = lerp(-40.0, INS, ramp(f, 26, 31))                       # the tip goes in, then stays in
    tip = A + u * (R_NECK - ins) + (u * 90.0 - lat * 80.0 + np.array([0.0, -150.0, 0.0])) * t_out
    b = nrm(-u + np.array([0.0, -0.6, 0.0]) * t_out)              # pulled out: blade down
    wrist = tip - b * KNIFE
    w_ik = t_in * (1 - ramp(f, F_OUT[1], F_REL[1]))
    if w_ik > 0:
        hunk_fd = nrm(P[10] - P[8])
        fd = nrm(lerp(hunk_fd, tg, w_ik))
        wr = lerp(P[10], wrist, w_ik)
        Wk = dict(W)
        def hand_fn(fdir):
            hs = frame([0, 0, 1], b, [-1, 0, 0], fdir)             # blade out of the thumb side, wrist straight
            return slerpR(W[10], hs, w_ik)
        out = P[7] - P[13]; out[1] = 0.0; out = nrm(out)               # Leon's right, outwards
        arm_free(Wk, P[7], wr, hand_fn, -1, fd, out, 0.8 * w_ik)
        W = Wk
    # left hand (mirrored HUNK's right): palm on the back of the head, in line with the forearm
    w_l = ramp(f, TK_S0 + 3, TK_S0 + 9) * (1 - ramp(f, *F_REL))
    if w_l > 0:
        _, P = fk(W, root)
        back = gP[4] + np.array([-20.0, 40.0, -95.0])
        head_c = gP[4] + np.array([0.0, 60.0, 0.0])
        fd = nrm(lerp(nrm(P[16] - P[14]), nrm(back - P[13]), w_l))
        wl = back - fd * 70.0
        for _ in range(3):
            Wk = dict(W)
            def hand_l(fdir):
                hs = frame([1, 0, 0], fdir, [0, -1, 0], head_c - wl)   # palm (-y) on the head
                return slerpR(W[16], hs, w_l)
            fdir = arm_free(Wk, P[13], lerp(P[16], wl, w_l), hand_l, +1, fd)
            wl = back - fdir * 70.0
        W = Wk
    root = root.copy()
    R, P = fk(W, root)
    return W, R, P, root

def locals_of(W):
    R, _ = fk(W, np.zeros(3))
    out = {}
    for p in BODY:
        if PAR[p] == 0: out[p] = RY0.T @ R[p]            # root turned to Leon's facing (ga + Y0)
        else: out[p] = R[PAR[p]].T @ R[p]
    return out

ARM_PARTS = {5,6,7,8,9,10,11,12,13,14,15,16,113,114,117,118}
def build_frames():
    frames = []
    for f in range(NF):
        W, R, P, root = leon(f)
        L = locals_of(W)
        # from the crouch idle (arms first) and, after HUNK, back to it (the sheath on the way)
        a_b = 1.0 - ramp(f, TK_S0, F_IN); a_a = 1.0 - ramp(f, TK_S0, F_IN - 3)
        b = ramp(f, F_HUNK, F_END - 6)
        b_arm = ramp(f, F_OUT[1], F_REL[1] + 4)                            # B72: arms straight to the idle
        root = root.copy(); root[1] = lerp(root[1], IDLE_Y, b)             # height goes with the pose
        for p in BODY:
            k = max(a_a if p in ARM_PARTS else a_b, b, b_arm if p in ARM_PARTS else 0.0)
            if k > 0: L[p] = slerpR(L[p], IDLE_L[p], k)
        # sheath: right hand to the left of the chest, blade down (on top of the idle blend), then back
        w_s = ramp(f, *F_SHEATH) * (1 - ramp(f, F_SHEATH[1] + 2, F_END - 2))
        if w_s > 0:
            R, P = fk_local({**L, 0: RY0}, root)
            Wd = {p: R[p] for p in range(N) if R[p] is not None}
            sheath = P[2] + R[2] @ np.array([70.0, 10.0, 170.0])
            hs = R[2] @ knife_hand(nrm([0.1, -1.0, 0.15]), [1.0, 0.2, 0.3])
            arm(Wd, P[7], lerp(P[10], sheath, w_s), slerpR(R[10], hs, w_s), -1, R[2] @ np.array([-0.3, -1.0, -0.2]))
            for p in (7, 8, 9, 10, 113, 117):
                L[p] = Wd[PAR[p]].T @ Wd[p]
        # feet on the floor: where a toe goes below it (blends between HUNK's legs and the crouch), the leg
        # is solved again with the ankle raised by that much
        R, P = fk_local({**L, 0: RY0}, root)
        Wd = {p: R[p] for p in range(N) if R[p] is not None}; fix = False
        for hip, kn, an, toe in ((18, 19, 20, 21), (22, 23, 24, 25)):
            low = min(P[toe][1], P[an][1] - 85.0)
            if low < 0:
                A = P[an] + np.array([0, -low, 0]); fwd = R[an] @ np.array([0, 0, 1.0])
                K, A2 = two_bone(P[hip], A, np.linalg.norm(OFF[kn]), np.linalg.norm(OFF[an]), fwd + np.array([0, 0.2, 0]))
                Wd[hip] = frame([0, -1, 0], K - P[hip], [0, 0, 1], fwd)
                Wd[kn] = frame([0, -1, 0], A2 - K, [0, 0, 1], fwd); fix = True
        if fix:
            for p in (18, 19, 20, 21, 22, 23, 24, 25):
                L[p] = (RY0.T @ Wd[p]) if PAR[p] == 0 else Wd[PAR[p]].T @ Wd[p]
        frames.append((L, root - GD_S0))
    return frames
frames = build_frames()
# B73 auto-fit: the arms again with the Ganado's neck TK_DV higher / lower (crouch.c blends them
# by the neck height it measures on the real Ganado, stealth.c StealthNeckK)
TK_DV = 70.0
DY = TK_DV; frames_up = build_frames()
DY = -TK_DV; frames_dn = build_frames()
DY = 0.0
V0, V1 = TK_S0, F_REL[1] + 6
def neck_y(f):
    gP = ganado(min(f, 70))[1]
    return gP[3][1] + (gP[4][1] - gP[3][1]) * NECK_UP

def check():
    for f in (TK_S0, 24, 30, 33, 36, 39, 44, 52, 60, 70, 89):
        L, root = frames[f]
        R, P = fk_local({**L, 0: RY0}, root + GD_S0)
        gR, gP = ganado(min(f, 70))
        tip = P[10] + R[10] @ np.array([0, 0, KNIFE])
        mid = P[10] + R[10] @ np.array([0, 0, KNIFE * 0.6])
        print('f%3d root %s  Rhand-head %4.0f Lhand-head %4.0f tip-throat %4.0f blade60-throat %4.0f feet y %3.0f %3.0f' % (
            f, (root).round(), np.linalg.norm(P[10] - gP[4]), np.linalg.norm(P[16] - gP[4]),
            np.linalg.norm(tip - (gP[3] + np.array([0, 0, 45]))), np.linalg.norm(mid - (gP[3] + np.array([0, 0, 45]))), P[21][1], P[25][1]))
check()
print('Y0 %.2f rad' % Y0)

# ---------------------------------------------------------------- render (check)
if '--png' in sys.argv:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    BONES = [(0,1),(1,2),(2,3),(3,4),(2,5),(5,7),(7,8),(8,9),(9,10),(2,11),(11,13),(13,14),(14,15),(15,16),(0,17),(17,18),(18,19),(19,20),(20,21),(17,22),(22,23),(23,24),(24,25)]
    fs = [int(x) for x in sys.argv[sys.argv.index('--png') + 1].split(',')]
    fig, axs = plt.subplots(3, len(fs), figsize=(2.6 * len(fs), 9))
    for j, f in enumerate(fs):
        L, root = frames[f]; R, P = fk_local({**L, 0: RY0}, root + GD_S0)
        gR, gP = ganado(min(f, 70))
        tip = P[10] + R[10] @ np.array([0, 0, KNIFE])
        for r, (a, b, lab) in enumerate(((0, 1, 'detras'), (2, 1, 'lado'), (0, 2, 'arriba'))):
            ax = axs[r][j]
            for u, v in BONES:
                ax.plot([gP[u][a], gP[v][a]], [gP[u][b], gP[v][b]], color='0.6', lw=2)
            for u, v in BONES:
                c = 'r' if v in (7,8,9,10,18,19,20,21) else 'b' if v in (13,14,15,16,22,23,24,25) else 'k'
                ax.plot([P[u][a], P[v][a]], [P[u][b], P[v][b]], c, lw=2)
            ax.plot([P[10][a], tip[a]], [P[10][b], tip[b]], 'g', lw=3)
            ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
            cx = (P[2][a] + gP[2][a]) / 2; ax.set_xlim(cx - 900, cx + 900)
            if b == 1: ax.set_ylim(-50, 1900)
            else: cy = (P[2][b] + gP[2][b]) / 2; ax.set_ylim(cy - 900, cy + 900)
            if r == 0: ax.set_title('f%d' % f, fontsize=9)
    plt.tight_layout(); plt.savefig(sys.argv[sys.argv.index('--png') + 2], dpi=60 if len(fs) > 4 else 150)

# ---------------------------------------------------------------- export
rows = []; ys = []; xz = []
for L, root in frames:
    e = []
    for p in BODY:
        e += [int(round(max(-3.2767, min(3.2767, a)) * 10000)) for a in euler_zyx(L[p])]
    rows.append(e); ys.append(int(round(root[1]))); xz += [int(round(root[0])), int(round(root[2]))]
def blob(name, b):
    b = b + b'\0' * (-len(b) % 4)
    w = struct.unpack('>%dI' % (len(b) // 4), b)
    return 'static const u32 %s[%d] __attribute__((aligned(32))) = {\n' % (name, len(w)) + \
        ',\n'.join(','.join('0x%08X' % x for x in w[i:i+8]) for i in range(0, len(w), 8)) + '};\n'
out = '/* generated by anim/tools/mktake.py - crouch.c defines TK_POSE, stealth.c TK_SCENE */\n'
out += '#define TK_N %d\n#define TK_STAB0 %d\n#define TK_STAB %d\n#define TK_OUT %d\n#define TK_REL %d\n#define TK_SHEATH %d\n#define TK_IN %d\n' % (NF, F_STAB[0], F_STAB[1], F_OUT[0], F_REL[0], F_SHEATH[1], F_IN)
out += '#define TK_KNIFE %.1ff\n#define TK_KNIFE_K %.2ff\n#define TK_S0 %d\n#define TK_YAW %.4ff\n' % (KNIFE, KNIFE_K, TK_S0, Y0)
out += '#define TK_NECK_UP %.2ff\n#define TK_DV %.1ff\n' % (NECK_UP, TK_DV)
out += '#ifdef TK_POSE\n'
out += 'static const s16 tk_rot[TK_N][CR_NPARTS*3] = {\n' + ',\n'.join('{' + ','.join(map(str, e)) + '}' for e in rows) + '};\n'
out += 'static const s16 tk_y[TK_N] = {%s};\n' % ','.join(map(str, ys))
VPARTS = [i for i, p in enumerate(BODY) if p in ARM_PARTS]
def vrows(fr):
    rr = []
    for f in range(V0, V1):
        L, _ = fr[f]; e = []
        for i in VPARTS:
            e += [int(round(max(-3.2767, min(3.2767, a)) * 10000)) for a in euler_zyx(L[BODY[i]])]
        rr.append('{' + ','.join(map(str, e)) + '}')
    return ',\n'.join(rr)
out += '#define TK_V0 %d\n#define TK_VN %d\n#define TK_NV %d\n' % (V0, V1 - V0, len(VPARTS))
out += 'static const s8 tk_vcol[CR_NPARTS] = {%s};\n' % ','.join(str(VPARTS.index(i)) if i in VPARTS else '-1' for i in range(len(BODY)))
out += 'static const s16 tk_rot_up[TK_VN][TK_NV*3] = {\n' + vrows(frames_up) + '};\n'
out += 'static const s16 tk_rot_dn[TK_VN][TK_NV*3] = {\n' + vrows(frames_dn) + '};\n'
out += '#endif\n#ifdef TK_SCENE\n'
out += '/* B73: the throat\'s height on the neck axis (model space, mm) - the auto-fit reference */\n'
out += 'static const s16 tk_neck[TK_N] = {%s};\n' % ','.join(str(int(round(neck_y(f)))) for f in range(NF))
out += '/* Leon\'s root x / z in the Ganado\'s start frame */\n'
out += 'static const s16 tk_xz[TK_N*2] = {%s};\n' % ','.join(map(str, xz))
out += '/* the Ganado: em10.drs motion 0x2BA and its sequence 0x2BB (%d frames) */\n' % MF
out += blob('tk_em_mot', mot) + blob('tk_em_seq', seq)
out += '#endif\n'
open(OUT, 'w').write(out)
print('wrote', OUT, NF, 'frames;', len(mot), '+', len(seq), 'bytes of Ganado motion')
