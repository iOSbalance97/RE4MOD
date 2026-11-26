"""fbx_estatua.py modelo.fbx salida_dir [alto] : figura del FBX con piel (skinning), brazos doblados sujetando un mapa,
convertida en estatua de mármol (sombreado horneado en tonos por normal). Salida: figura.obj + texturas, local (pies en 0, mira a +z)."""
import sys, os, re
import numpy as np
sys.path.insert(0, '/home/claude/re1gc/work'); import fbxbin
ruta, out = sys.argv[1], sys.argv[2]; ALTO = float(sys.argv[3]) if len(sys.argv) > 3 else 1.15
os.makedirs(out, exist_ok=True)
R = fbxbin.leer(ruta); O = R.hijo('Objects')
obj = {}; nom = {}
for n in O.hijos:
    obj[n.props[0]] = n; nom[n.props[0]] = n.props[1].split('\x00')[0] if isinstance(n.props[1], str) else ''
hijos = {}; padre = {}
for c in R.hijo('Connections').hijos:
    if c.props[0] in ('OO', 'OP'): hijos.setdefault(c.props[2], []).append(c.props[1]); padre.setdefault(c.props[1], []).append(c.props[2])
OMIT = re.compile(os.environ.get('OMITIR', r'Eyelash|Eyebrow|Basemesh_Mat\.002|Mouth|EyeShell|Teeth'), re.I)
def mat4(a): return np.array(a, float).reshape(4, 4).T          # FBX guarda por columnas
mallas = []
for gid, g in obj.items():
    if g.nombre != 'Geometry' or g.props[2] != 'Mesh': continue
    if OMIT.search(nom[gid]): continue
    V = g.hijo('Vertices').props[0].reshape(-1, 3).astype(float)
    pvi = g.hijo('PolygonVertexIndex').props[0].astype(np.int64)
    # triangular polígonos
    tris = []; poly = []
    for k, i in enumerate(pvi):
        if i < 0: poly.append((~i, k)); tris += [(poly[0], poly[j], poly[j + 1]) for j in range(1, len(poly) - 1)]; poly = []
        else: poly.append((i, k))
    T = np.array([[a[0], b[0], c[0]] for a, b, c in tris]); TK = np.array([[a[1], b[1], c[1]] for a, b, c in tris])
    # piel: clusters
    pes = np.zeros((len(V), 0)); bones = []
    W = []
    for d in hijos.get(gid, []):
        if obj.get(d) is not None and obj[d].nombre == 'Deformer' and obj[d].props[2] == 'Skin':
            for cl in hijos.get(d, []):
                cn = obj.get(cl)
                if cn is None or cn.props[2] != 'Cluster' or cn.hijo('Indexes') is None: continue
                bone = [b for b in hijos.get(cl, []) if obj.get(b) is not None and obj[b].nombre == 'Model']
                W.append((nom[bone[0]] if bone else '?', cn.hijo('Indexes').props[0], cn.hijo('Weights').props[0],
                          mat4(cn.hijo('Transform').props[0]), mat4(cn.hijo('TransformLink').props[0])))
    mallas.append(dict(nombre=nom[gid], V=V, T=T, W=W))
    print(nom[gid], len(V), 'vértices', len(T), 'triángulos', len(W), 'huesos')
np.save(f'{out}/_mallas.npy', np.array(mallas, dtype=object), allow_pickle=True)

# ---------------- postura: brazos doblados sujetando el mapa delante del pecho
C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)           # Z arriba -> Y arriba (frente -Y -> +Z)
def link(nombre):
    for m in mallas:
        for w in m['W']:
            if w[0] == nombre: return w[4]
def pos(*nombres):
    for nombre in nombres:
        L = link(nombre)
        if L is not None: return C @ L[:3, 3]
def rot_a(u, t):
    u = u / np.linalg.norm(u); t = t / np.linalg.norm(t); ax = np.cross(u, t); s = np.linalg.norm(ax); c = u @ t
    if s < 1e-8: return np.eye(3)
    ax /= s; K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + s * K + (1 - c) * K @ K
def slerp_m(Rm, f):           # fracción de una rotación (por ángulo-eje)
    ang = np.arccos(np.clip((np.trace(Rm) - 1) / 2, -1, 1))
    if ang < 1e-6: return np.eye(3)
    ax = np.array([Rm[2, 1] - Rm[1, 2], Rm[0, 2] - Rm[2, 0], Rm[1, 0] - Rm[0, 1]]) / (2 * np.sin(ang))
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); a = ang * f
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
POSE = {}
for lado, sx in (('L', 1), ('R', -1)):
    sh = pos(f'{lado}_Arm_Upper_Twist_0'); el = pos(f'{lado}_Arm_Lower_Twist_0'); wr = pos(f'{lado}_Arm_Hand', f'{lado}_Hand_Palm', f'{lado}_Hand_MiddleF_1')
    if sh is None or el is None or wr is None: print('sin brazo', lado); continue
    sgn = np.sign(sh[0]) or sx
    Rs = rot_a(el - sh, np.array([sgn * 0.18, -1.0, 0.30]))                          # brazo: abajo, algo adelante
    el2 = sh + Rs @ (el - sh); wr1 = sh + Rs @ (wr - sh)
    Re = rot_a(wr1 - el2, np.array([-sgn * 0.30, 0.30, 1.0]))                        # antebrazo: hacia delante y adentro
    POSE[lado] = (sh, Rs, el2, Re)
def M_hueso(nombre):
    m = re.match(r'([LR])_(.*)', nombre)
    if not m or m.group(1) not in POSE: return None
    lado, resto = m.groups(); sh, Rs, el2, Re = POSE[lado]
    if re.match(r'Arm_Lower|Arm_Hand|Hand_', resto): return ('low', sh, Rs, el2, Re, 1.0)
    if re.match(r'Arm_Upper|Elbow', resto): return ('up', sh, Rs, None, None, 1.0)
    if re.match(r'Delt_|Armpit|ClothPit|Lat_A|Trap_A', resto): return ('up', sh, slerp_m(Rs, 0.5), None, None, 0.5)
    return None
def aplicar(p, info):
    kind, sh, Rs, el2, Re, f = info
    q = sh + Rs @ (p - sh)
    if kind == 'low': q = el2 + Re @ (q - el2)
    return q
partes = []
for m in mallas:
    Vb = m['V']; n = len(Vb); acc = np.zeros((n, 3)); wsum = np.zeros(n)
    Wl = m['W']
    P0 = Vb.copy()                                                                # los vértices ya están en Y arriba
    if not Wl: P = P0
    else:
        for (bn, idx, w, Tm, TL) in Wl:
            info = M_hueso(bn); pw = P0[idx]
            q = pw if info is None else np.array([aplicar(p, info) for p in pw])
            acc[idx] += q * w[:, None]; wsum[idx] += w
        P = np.where(wsum[:, None] > 1e-6, acc / np.maximum(wsum, 1e-9)[:, None], P0)
    partes.append((m['nombre'], P, m['T']))
allP = np.concatenate([p for _, p, _ in partes]); y0 = allP[:, 1].min(); h = allP[:, 1].max() - y0
cx, cz = np.median(allP[:, 0]), np.median(allP[:, 2]); esc = ALTO / h
print(f'altura del modelo {h:.3f} -> escala {esc:.4f}')
# ---------------- reducir (el pelo es muy denso) y escribir con mármol en tonos por normal
sys.path.insert(0, '/home/claude/tools'); import decimate
OBJ = {'Hair': 2500, 'Cloth': 4200, 'Pill': 600, 'Basemesh': 1800, 'Hand': 1600, 'Face': 2600, 'Eyeball': 150}
ld = np.array([0.35, 1.0, 0.65]); ld /= np.linalg.norm(ld)
Vs = []; Fs = []; Ks = []; b0 = 0
for ip_, (nm_, Praw, T) in enumerate(partes):
    P = (Praw - [cx, y0, cz]) * esc
    obj_n = next((v for k, v in OBJ.items() if k in nm_), 1500)
    if 'Hair' in nm_:
        if any('Hair' in q[0] for q in partes[:ip_]): continue   # una sola masa para todo el pelo
        from scipy import ndimage as _nd
        from skimage import measure as _ms
        Hp = np.concatenate([(pp - [cx, y0, cz]) * esc for nn_, pp, _ in partes if 'Hair' in nn_])
        S_ = 0.006; lo = Hp.min(0) - 0.03; dims = np.ceil((Hp.max(0) + 0.03 - lo) / S_).astype(int) + 1
        G_ = np.zeros(dims, bool); G_[tuple(((Hp - lo) / S_).astype(int).T)] = True
        G_ = _nd.binary_dilation(G_, iterations=2); G_ = _nd.binary_fill_holes(G_); G_ = _nd.binary_erosion(G_, iterations=1)
        vv, ff, _, _ = _ms.marching_cubes(_nd.gaussian_filter(G_.astype(np.float32), 1.2), 0.5, spacing=(S_, S_, S_))
        P = vv + lo; T = ff.astype(np.int64)
    used = np.unique(T); remap = -np.ones(len(P), int); remap[used] = np.arange(len(used)); P = P[used]; T = remap[T]
    if len(T) > obj_n:
        try: P, _, T = decimate.decimate(P, np.zeros((len(P), 2)), T, obj_n / len(T))
        except Exception as ex: print('decimado falló', nm_, ex)
    nn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12
    k = np.clip(np.floor((1 - (nn @ ld + 1) / 2) * 5), 0, 4).astype(int)            # 5 tonos: luz de arriba-delante
    Vs.append(P); Fs.append(T + b0); Ks.append(k); b0 += len(P); print(f'  {nm_}: {len(T)} triángulos')
V = np.concatenate(Vs); F = np.concatenate(Fs); K = np.concatenate(Ks)
# mapa entre las manos
hands = [V[np.abs(V[:, 0] - s * 0.1).argmin()] for s in (1, -1)]
manos = []
for lado in POSE:
    sh, Rs, el2, Re = POSE[lado]; wr = pos(f'{lado}_Arm_Hand', f'{lado}_Hand_Palm', f'{lado}_Hand_MiddleF_1'); w2 = el2 + Re @ ((sh + Rs @ (wr - sh)) - el2)
    manos.append((w2 - [cx, y0, cz]) * esc)
mc = np.mean(manos, 0) + [0, 0.03, 0.04] if manos else np.array([0, 0.6 * ALTO, 0.2]); mc[0] = 0.0
print('manos en', np.round(manos, 3), 'mapa en', mc.round(3))
import cv2
from PIL import Image
rg = np.random.default_rng(7); N = 512
def ruido(s_): a = rg.random((N // s_ + 2, N // s_ + 2)); return cv2.resize(a, (N, N), interpolation=cv2.INTER_CUBIC)
nz = ruido(128) * 0.5 + ruido(32) * 0.3 + ruido(8) * 0.2; yy, xx = np.mgrid[0:N, 0:N] / N
vena = np.clip(1 - np.abs(np.sin((xx * 3 + yy * 1.5 + nz * 2.2) * np.pi * 2)), 0, 1) ** 10
L = np.clip(0.78 + 0.07 * (ruido(16) - 0.5) - 0.20 * vena, 0, 1)
sucio = cv2.GaussianBlur(ruido(4), (0, 0), 6); L = L * (0.9 + 0.1 * sucio)
TON = [1.0, 0.80, 0.62, 0.47, 0.34]
for k, f in enumerate(TON):
    Image.fromarray((np.clip(np.stack([L * 0.90, L * 0.88, L * 0.85], -1) * f, 0, 1) * 255).astype(np.uint8)).save(f'{out}/marmol_t{k}.png')
with open(f'{out}/figura.obj', 'w') as fo:
    fo.write('mtllib figura.mtl\n')
    for v in V: fo.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    nt = 1
    for k in range(5):
        sel = np.nonzero(K == k)[0]
        if not len(sel): continue
        fo.write(f'usemtl marmol_t{k}\n')
        for i in sel:
            tri = F[i]; Pt = V[tri]; nn = np.cross(Pt[1] - Pt[0], Pt[2] - Pt[0]); a = np.abs(nn).argmax()
            uv = Pt[:, [ax for ax in range(3) if ax != a]] / 0.45
            for u in uv: fo.write(f'vt {u[0]:.4f} {u[1]:.4f}\n')
            fo.write(f'f {tri[0]+1}/{nt} {tri[1]+1}/{nt+1} {tri[2]+1}/{nt+2}\n'); nt += 3
    # mapa: tablilla con grosor, inclinada hacia arriba-delante
    nb = len(V) + 1; a_, b_, g_ = 0.27, 0.20, 0.035; inc = np.radians(40)
    ex = np.array([1.0, 0, 0]); ey = np.array([0, np.cos(inc), -np.sin(inc)]); ez = np.cross(ex, ey)
    cs = [mc + ex * sx * a_ / 2 + ey * sy * b_ / 2 + ez * sz * g_ / 2 for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    fo.write('usemtl marmol_t1\n')
    for p in cs: fo.write(f'v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n')
    for t in ((0, 0), (1, 0), (1, 1), (0, 1)): fo.write(f'vt {t[0]*0.6} {t[1]*0.45}\n')
    caras = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for q in caras:
        a0, a1, a2, a3 = [nb + i for i in q]
        fo.write(f'f {a0}/{nt} {a1}/{nt+1} {a2}/{nt+2}\nf {a0}/{nt} {a2}/{nt+2} {a3}/{nt+3}\n')
        fo.write(f'f {a0}/{nt} {a2}/{nt+2} {a1}/{nt+1}\nf {a0}/{nt} {a3}/{nt+3} {a2}/{nt+2}\n')
open(f'{out}/figura.mtl', 'w').write(''.join(f'newmtl marmol_t{k}\nmap_Kd marmol_t{k}.png\n' for k in range(5)))
print('ok', len(F), 'triángulos')
