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

# ---------------------------------------------------------------- timeline (motion frames, 30 / s)
F_IN = 7          # crouch -> grab
F_COCK = (3, 13)  # knife drawn back
F_STAB = (30, 35) # the thrust; hits at 35 (the sequence's 'neck' event is frame 37)
F_OUT = (49, 58)  # knife pulled out
F_REL = (74, 86)  # lets the body go (it falls forward from ~80)
F_END = 100       # back in the crouch idle
NF = F_END + 1
KNIFE = 200.0     # wrist -> blade tip

# Leon root follows the Ganado's neck while he holds it
def neck_track(f):
    R, P = ganado(min(f, F_REL[0]))
    return P[3]
NECK = [neck_track(f) for f in range(NF)]
for it in range(3):     # smooth
    NECK = [NECK[0]] + [(NECK[i-1] + 2 * NECK[i] + NECK[i+1]) / 4 for i in range(1, NF - 1)] + [NECK[-1]]

def leon_root(f):
    n = NECK[f]
    x = n[0] - 70.0
    z = n[2] - 200.0
    y = 1050.0 - 25.0 * math.sin(math.pi * ramp(f, 8, 30))            # settles while pulling
    y = lerp(IDLE_Y, y, ramp(f, 0, F_IN + 2))
    y = lerp(y, IDLE_Y, ramp(f, F_REL[1] - 2, F_END - 2))
    return np.array([x, y, z])

# feet: planted, stepping towards a stance under the root
STANCE = {20: np.array([-125.0, 0, -150.0]), 24: np.array([115.0, 0, 140.0])}
def feet_track():
    _, P0 = fk_local(IDLE_L, [0, IDLE_Y, 0])
    pos = {20: P0[20].copy(), 24: P0[24].copy()}
    for k in pos: pos[k][1] = 0.0
    out = []; step = {20: None, 24: None}; order = [24, 20]
    for f in range(NF):
        r = leon_root(f); fr = {}
        for k in order:
            tgt = np.array([r[0], 0, r[2]]) + STANCE[k]
            if step[k] is None and np.linalg.norm(tgt - pos[k]) > 110 and all(step[j] is None for j in step if j != k):
                step[k] = (f, pos[k].copy(), 7)
            if step[k] is not None:
                f0, p0, nlen = step[k]; t = (f - f0) / nlen
                p = lerp(p0, tgt, ss(t)); lift = 70.0 * math.sin(math.pi * min(1, t))
                fr[k] = p + np.array([0, lift, 0])
                if t >= 1: pos[k] = tgt.copy(); step[k] = None
            else:
                fr[k] = pos[k].copy()
        out.append(fr)
    return out
FEET = feet_track()

LA_ARM = np.linalg.norm(OFF[8]); LB_ARM = np.linalg.norm(OFF[9]) + np.linalg.norm(OFF[10])
LA_LEG = np.linalg.norm(OFF[19]); LB_LEG = np.linalg.norm(OFF[20])

def arm(Wrot, P_sh, wrist, hand_R, side, pole):
    """side -1 right (bone axis -x), +1 left (+x). Sets upper / fore / twist / hand rotations."""
    up, fore = (7, 8) if side < 0 else (13, 14)
    tw_u, tw_f, mid, hand = (113, 117, 9, 10) if side < 0 else (114, 118, 15, 16)
    E, W = two_bone(P_sh, wrist, LA_ARM, LB_ARM, pole)
    ax = np.array([side, 0, 0.0])
    # elbow bend: the forearm folds towards local +z of the upper arm (as the bind's elbow)
    Ru = frame(ax, E - P_sh, [0, 0, 1], W - E)
    Rf = frame(ax, W - E, [0, 1, 0], hand_R @ np.array([0, 1, 0]))
    for p in (6, up, tw_u) if side < 0 else (12, up, tw_u): Wrot[p] = Ru
    for p in (fore, tw_f, mid): Wrot[p] = Rf
    Wrot[hand] = hand_R

def leg(Wrot, P_hip, ankle, side_parts, yaw):
    th, sh, ft, toe = side_parts
    K, A = two_bone(P_hip, ankle, LA_LEG, LB_LEG, Ry(yaw) @ np.array([0, 0.2, 1.0]))
    fwd = Ry(yaw) @ np.array([0, 0, 1.0])
    Wrot[th] = frame([0, -1, 0], K - P_hip, [0, 0, 1], fwd)
    Wrot[sh] = frame([0, -1, 0], A - K, [0, 0, 1], fwd)
    Wrot[ft] = Ry(yaw); Wrot[toe] = Ry(yaw)

def leon(f):
    gR, gP = ganado(min(f, F_REL[1]))
    root = leon_root(f)
    Wrot = {0: np.eye(3)}
    # torso: leans in for the grab, back while pulling, upright when letting go
    lean = lerp(0.30, -0.10, ramp(f, F_IN, 26))
    lean = lerp(lean, 0.05, ramp(f, F_STAB[0] - 3, F_STAB[1]))       # into the thrust
    lean = lerp(lean, 0.10, ramp(f, F_REL[0], F_REL[1]))
    yaw = lerp(0.0, -0.12, ramp(f, F_STAB[0] - 4, F_STAB[1])) * (1 - ramp(f, F_OUT[0], F_REL[1]))
    Rh = Ry(yaw) @ Rx(lean * 0.5)
    Wrot[1] = Rh; Wrot[17] = Ry(yaw * 0.3); Wrot[2] = Rh @ Rx(lean * 0.6)
    _, P = fk(Wrot, root)
    # head looks at the Ganado's neck
    tgt = gP[3] + np.array([0, 40, 0])
    Wrot[4] = frame([0, 0, 1], tgt - P[4], [0, 1, 0], [0, 1, 0])
    Wrot[3] = slerpR(Wrot[2], Wrot[4], 0.5)
    _, P = fk(Wrot, root)
    # left hand over the mouth: palm towards Leon (-z of the head), fingers to the Ganado's right
    gh = gR[4]
    mouth = gP[4] + gh @ np.array([0.0, 5.0, 125.0])
    hand_L = gh @ frame([1, 0, 0], [-1, 0, 0.15], [0, -1, 0], [0, -0.2, -1])
    wrist_L = mouth - hand_L @ np.array([55.0, -15.0, 0.0])
    # right hand: knife back by the shoulder, then into the neck (blade = hand +z, the thumb side)
    def knife_hand(d, fingers):
        return frame([0, 0, 1], d, [-1, 0, 0], fingers)
    neck_c = gP[3] + gR[3] @ np.array([0.0, 25.0, 15.0])
    d_stab = nrm(gR[3] @ np.array([1.0, 0.12, 0.30]))                  # leftwards into the neck
    surf = neck_c - d_stab * 55.0                                        # its right side
    wrist_hit = surf + d_stab * 60.0 - d_stab * KNIFE
    hand_hit = knife_hand(d_stab, [0, -0.3, 1])
    cock = P[2] + Rh @ np.array([-330.0, 160.0, -40.0])
    hand_cock = knife_hand(nrm([0.55, 0.45, 0.70]), [0.2, 0.2, 1])
    rest = P[2] + Rh @ np.array([-260.0, -330.0, 180.0])                 # low guard (start / end)
    hand_rest = knife_hand(nrm([0.6, 0.3, 0.75]), [0.1, -0.5, 1])
    t_c = ramp(f, *F_COCK); t_s = ramp(f, *F_STAB); t_o = ramp(f, *F_OUT)
    # the thrust accelerates (ease-in), small push and twist while it is in
    t_s = min(1.0, max(0.0, (f - F_STAB[0]) / float(F_STAB[1] - F_STAB[0]))) ** 2
    push = 25.0 * math.sin(math.pi * ramp(f, F_STAB[1], F_STAB[1] + 10)) * (1 - t_o)
    wrist_R = lerp(lerp(rest, cock, t_c), wrist_hit + d_stab * push, t_s)
    wrist_R = lerp(wrist_R, lerp(cock, rest, ramp(f, F_OUT[1], F_REL[1])), t_o)
    hR = slerpR(slerpR(hand_rest, hand_cock, t_c), hand_hit @ Rz(0.25 * ramp(f, F_STAB[1], F_STAB[1] + 8)), t_s)
    hR = slerpR(hR, slerpR(hand_cock, hand_rest, ramp(f, F_OUT[1], F_REL[1])), t_o)
    # left arm: reaches round the head, holds, lets go
    reach0 = P[2] + Rh @ np.array([200.0, -150.0, 250.0])
    t_g = ramp(f, 1, F_IN); t_r = ramp(f, *F_REL)
    wL = lerp(lerp(reach0, wrist_L, t_g), P[2] + Rh @ np.array([260.0, -300.0, 160.0]), t_r)
    hL = slerpR(slerpR(frame([1, 0, 0], [0.3, -0.5, 1], [0, -1, 0], [1, -0.3, 0]), hand_L, t_g),
                frame([1, 0, 0], [0.2, -1, 0.3], [0, -1, 0], [1, 0, 0]), t_r)
    arm(Wrot, P[13], wL, hL, +1, np.array([0.8, -1.0, -0.6]))
    arm(Wrot, P[7], wrist_R, hR, -1, np.array([-0.9, -1.0, -0.4]))
    _, P = fk(Wrot, root)
    # legs
    A20 = FEET[f][20] + np.array([0, 91.0, -82.0]); A24 = FEET[f][24] + np.array([0, 91.0, -82.0])
    leg(Wrot, P[18], A20, (18, 19, 20, 21), -0.25)
    leg(Wrot, P[22], A24, (22, 23, 24, 25), 0.15)
    R, P = fk(Wrot, root)
    return R, P, root

def locals_of(R):
    return {p: (R[PAR[p]].T @ R[p] if PAR[p] != 0 else R[p]) for p in BODY}

frames = []
_, IDLE_P = fk_local(IDLE_L, [0, IDLE_Y, 0])
for f in range(NF):
    R, P, root = leon(f)
    L = locals_of(R)
    # blend from / back to the crouch idle (local rotations)
    a = 1.0 - ramp(f, 0, F_IN); b = ramp(f, F_REL[1], F_END)
    k = max(a, b)
    if k > 0: L = {p: slerpR(L[p], IDLE_L[p], k) for p in BODY}
    frames.append((L, root))

def check():
    """distances that matter, printed for the record"""
    for f in (0, 8, 20, 30, 35, 40, 60, 76, 90, 100):
        L, root = frames[f]
        R, P = fk_local({**L, 0: np.eye(3)}, root)
        gR, gP = ganado(min(f, F_REL[1]))
        tip = P[10] + R[10] @ np.array([0, 0, KNIFE])
        print('f%3d heads %4.0f root %s  Lhand-mouth %4.0f  tip-neck %4.0f  Lchest-Gneck z %4.0f  feet y %3.0f %3.0f' % (
            f, np.linalg.norm(P[4] - gP[4]), root.round(), np.linalg.norm(P[16] - (gP[4] + gR[4] @ np.array([0, 5, 125]))),
            np.linalg.norm(tip - gP[3]), gP[3][2] - P[2][2], P[21][1], P[25][1]))
check()

# ---------------------------------------------------------------- render (check)
if '--png' in sys.argv:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    BONES = [(0,1),(1,2),(2,3),(3,4),(2,5),(5,7),(7,8),(8,9),(9,10),(2,11),(11,13),(13,14),(14,15),(15,16),(0,17),(17,18),(18,19),(19,20),(20,21),(17,22),(22,23),(23,24),(24,25)]
    fs = [int(x) for x in sys.argv[sys.argv.index('--png') + 1].split(',')]
    fig, axs = plt.subplots(3, len(fs), figsize=(2.6 * len(fs), 9))
    for j, f in enumerate(fs):
        L, root = frames[f]; R, P = fk_local({**L, 0: np.eye(3)}, root)
        gR, gP = ganado(f)
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
out += '#define TK_N %d\n#define TK_STAB0 %d\n#define TK_STAB %d\n#define TK_OUT %d\n#define TK_REL %d\n' % (NF, F_STAB[0], F_STAB[1], F_OUT[0], F_REL[0])
out += '#define TK_KNIFE %.1ff\n' % KNIFE
out += '#ifdef TK_POSE\n'
out += 'static const s16 tk_rot[TK_N][CR_NPARTS*3] = {\n' + ',\n'.join('{' + ','.join(map(str, e)) + '}' for e in rows) + '};\n'
out += 'static const s16 tk_y[TK_N] = {%s};\n' % ','.join(map(str, ys))
out += '#endif\n#ifdef TK_SCENE\n'
out += '/* Leon\'s root x / z in the Ganado\'s start frame */\n'
out += 'static const s16 tk_xz[TK_N*2] = {%s};\n' % ','.join(map(str, xz))
out += '/* the Ganado: em10.drs motion 0x2BA and its sequence 0x2BB (%d frames) */\n' % MF
out += blob('tk_em_mot', mot) + blob('tk_em_seq', seq)
out += '#endif\n'
open(OUT, 'w').write(out)
print('wrote', OUT, NF, 'frames;', len(mot), '+', len(seq), 'bytes of Ganado motion')
