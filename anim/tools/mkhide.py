# C0-19: Ashley climbing into the container, from the game's own partner motion (pl11.drs ARC 0x2C, the hop over
# the rim that she does on the island when Leon tells her to hide) -> mod/c/ch0_hide.h
# The player Ashley (pl01) has the same skeleton (BIN 0 identical), so the FCV is evaluated with the game's
# semantics (render.game_pose: rot channels, root height, IK targets for the hands / feet) and written as
# local rotations of parts 1-25 plus the root offset (height + the clip's root motion), like ch0_scared.h.
import sys, math, numpy as np
sys.path.insert(0, '/home/claude/re4mod/anim/tools'); sys.path.insert(0, '/home/claude/scripts')
import drs, arc, mot
from mot import rotm, euler_zyx, eval_chan
from leon import orient_zx, axis_rot
D, A, N, REL, OFFS, TAGS = drs.arc('/home/claude/disc/ext1/files/em/pl11.drs')
SK = arc.skeleton(drs.ent(A, OFFS, 0))
PAR = [s[1] for s in SK]; OFF = [np.array(s[2:5]) for s in SK]
BINDW = []
for i in range(len(SK)): BINDW.append(OFF[i] if PAR[i] == 255 else BINDW[PAR[i]] + OFF[i])
def ang_up(ch): return np.array({4: (0, 0, 1), 5: (0, 0, -1), 0: (0, 1, 0), 1: (0, -1, 0), 2: (1, 0, 0), 3: (-1, 0, 0)}[ch], float)
def ik_setup(root, eff, ch):
    d = BINDW[eff] - BINDW[root]; ax = ang_up(ch)
    vz = d / np.linalg.norm(d); vy = ax / np.linalg.norm(ax); vx = np.cross(vy, vz); vx /= np.linalg.norm(vx); vy = np.cross(vz, vx); vy /= np.linalg.norm(vy)
    return np.stack([vx, vy, vz], 1).T, vx
def ikcalc(rootR, rootP, effP, la, lb, inv, up):
    d = np.linalg.norm(effP - rootP); a1 = a2 = 0.0
    if d < la + lb:
        c1 = max(-1, min(1, (la * la + d * d - lb * lb) / (2 * la * d))); c2 = max(-1, min(1, (d * d + lb * lb - la * la) / (2 * d * lb)))
        a1 = math.acos(c1); a2 = math.acos(c2)
    axis = rootR @ up; m = orient_zx(effP - rootP, axis) @ inv
    return m @ axis_rot(up, -a1), m @ axis_rot(up, a2)
IKS = ((7, 10, 5, 8), (13, 16, 5, 14), (18, 20, 4, 19), (22, 24, 4, 23))
def pose(vals):
    n = 26; L = [np.eye(3)] * n; pos = [o.copy() for o in OFF[:n]]
    for (no, k), v in vals.items():
        if no >= n: continue
        if k == 'pos': pos[no] = np.array(v)
        else: L[no] = rotm(v)
    R = [None] * n; P = [None] * n
    for i in range(n):
        p = PAR[i]
        if p == 255: R[i] = L[i]; P[i] = pos[i]; continue
        R[i] = R[p] @ L[i]; P[i] = P[p] + R[p] @ OFF[i]
        if i in (10, 16): R[i] = L[i]; P[i] = pos[i]
        if i in (20, 24): R[i] = L[i]; P[i] = pos[i] - L[i] @ OFF[i + 1]
    for root, eff, ch, mid in IKS:
        inv, up = ik_setup(root, eff, ch); la = np.linalg.norm(OFF[mid]); lb = np.linalg.norm(BINDW[eff] - BINDW[mid])
        R[root], R[mid] = ikcalc(R[root], P[root], P[eff], la, lb, inv, up)
    for i in (9, 15): R[i] = R[PAR[i]] @ L[i]
    for i in (21, 25): R[i] = R[PAR[i]] @ L[i]
    return R, P
def clip(w, src=None):
    m = drs.ent(*(src or (A, OFFS)), w - 4); mf, ch = mot.parse(m); rows = []; roots = []
    for f in range(mf):
        vals = {}; mv = np.zeros(3)
        for c in ch:
            v = eval_chan(c, f)
            if c['kind'] == 2: vals[(c['no'], 'rot')] = v
            elif c['kind'] == 4: vals[(c['no'], 'pos')] = v
            elif c['kind'] == 1 and c['no'] == 0: mv = np.array(v)
            elif c['kind'] == 64 and c['no'] == 0: vals[(0, 'rot')] = v; ry = v[1]
        if not any(k == (0, 'rot') for k in vals): ry = 0.0
        R, P = pose(vals)
        e = []
        for p in range(1, 26):
            Lp = R[PAR[p]].T @ R[p]
            e += [int(round(max(-3.2767, min(3.2767, a)) * 10000)) for a in euler_zyx(Lp)]
        rows.append(e); r0 = P[0] + mv; roots.append([int(round(x)) for x in r0] + [int(round(ry * 10000))])
    return mf, rows, roots
def seq(ws, src=None):
    R_, O_ = [], []; base = np.zeros(4)
    for w in ws:
        n, rows, roots = clip(w, src)
        roots = [list(np.array(r) + base) for r in roots]
        R_ += rows; O_ += roots
        last = np.array(roots[-1]); base = np.array([last[0], 0, last[2], 0])
    return R_, [[int(round(x)) for x in r] for r in O_]
rin, oin = seq([0x2C, 0x43]); rout, oout = seq([0x45, 0x2C])
# C0-19: carried off (the Ganado's archive, em17: 0x2A2 the lift onto the shoulder, 0x2A3 held there); her place
# is set by ch0.c from the Ganado (the takeaway offset), so the root keeps only its height and turn
_D7, _A7, _N7, _R7, _O7, _T7 = drs.arc('/home/claude/disc/ext1/files/em/em17.drs')
rkid, okid = seq([0x2A2, 0x2A3], (_A7, _O7)); okid = [[0, r[1], 0, r[3]] for r in okid]
# C0-19: the intro's scared clip (mkscared.py, was in the DOL) moves here too: its rows and its root height
import re
_h = open('/home/claude/re4mod/mod/c/ch0_scared.h').read()
_rows = re.findall(r'\{([-0-9,]+)\}', _h[_h.index('sc_rot'):_h.index('sc_y')])
rsc = [list(map(int, r.split(','))) for r in _rows]
_y = list(map(int, re.search(r'sc_y\[SC_N\] = \{([-0-9,]+)\}', _h).group(1).split(',')))
osc = [[0, int(round(y * 1094.0 / 1140.0)), 0, 0] for y in _y]
assert len(rsc) == len(osc) and all(len(r) == 75 for r in rsc)
rows = rin + rout + rkid + rsc; roots = oin + oout + okid + osc; n = len(rows)
import struct
blob = b''.join(struct.pack('>75h', *e) for e in rows) + b''.join(struct.pack('>4h', *r) for r in roots)
open('/home/claude/re4mod/mod/data/ch0_hide.bin', 'wb').write(blob)   # mkfiles.py puts it after the container
open('/home/claude/re4mod/mod/c/ch0_hide.h', 'w').write('/* generated by anim/tools/mkhide.py: pl11 (the partner): in = ARC 0x2C (the hop into the\n'
    ' * island container) + 0x43 (down inside); out = 0x45 (up) + 0x2C (the hop out). In em12.drs (mkfiles.py, CT_HD):\n'
    ' * s16 rot[HD_N][75] (parts 1-25, zyx euler 1e-4 rad), then s16 root[HD_N][4] (root offset with the root motion, root turn 1e-4 rad). 30 fps */\n'
    '#define HD_N %d\n#define HD_IN %d\n#define HD_OUT %d\n#define HD_KID %d\n#define HD_LIFT 50\n#define HD_SC %d\n#define HD_LEN %d\n' % (n, len(rin), len(rin), len(rin) + len(rout), len(rin) + len(rout) + len(rkid), len(blob)))
print(n, len(rin), len(rkid), 'kid y', okid[0], okid[49], okid[-1], 'in end', oin[-1], 'out start', oout[0], 'out end', oout[-1])
