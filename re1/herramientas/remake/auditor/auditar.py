"""auditar.py sala.obj colision.obj [salida.json]
Busca huecos que dejan ver el fondo: desde puntos pisables (a 1.0, 1.6 y 2.0 m) lanza rayos en todas
direcciones; un rayo que no choca con nada es un hueco. Lo sitúa donde el rayo cruza la colisión
(o, si no la cruza, a 1 m) y agrupa los huecos cercanos."""
import sys, os, json, subprocess, numpy as np
AQ = os.path.dirname(os.path.abspath(__file__))
def load(f):
    V = []; F = []; M = []; cur = None
    for l in open(f):
        if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('usemtl'): cur = l.split()[1]
        elif l.startswith('f '): F.append([int(x.split('/')[0]) - 1 for x in l.split()[1:4]]); M.append(cur)
    V = np.array(V); P = V[np.array(F)]; return P, M
sala, col = sys.argv[1], sys.argv[2]; salida = sys.argv[3] if len(sys.argv) > 3 else '/tmp/auditoria.json'
P, _ = load(sala); C, _ = load(col)
n = np.cross(C[:, 1] - C[:, 0], C[:, 2] - C[:, 0]); A = np.linalg.norm(n, axis=1) / 2; n /= 2 * A[:, None] + 1e-12
suelo = C[(n[:, 1] > 0.45) & (C[:, :, 1].mean(1) < float(os.environ.get('SUELO_YMAX', 99)))]; pared = C[np.abs(n[:, 1]) < 0.35]
# puntos de muestreo cada PASO m en los suelos pisables
PASO = float(os.environ.get('PASO', 0.7)); rng = np.random.default_rng(0); pts = []
for t in suelo:
    a = np.linalg.norm(np.cross(t[1] - t[0], t[2] - t[0])) / 2
    for _ in range(max(1, int(a / PASO ** 2 * 2))): pts.append(rng.dirichlet([1, 1, 1]) @ t)
pts = np.array(pts); sel = []
from scipy.spatial import cKDTree
# distancia a las paredes (muestras de las paredes de colisión)
mw = []
for t in pared:
    a = np.linalg.norm(np.cross(t[1] - t[0], t[2] - t[0])) / 2
    mw.append(rng.dirichlet([1, 1, 1], max(3, int(a / 0.01))) @ t)
mw = np.concatenate(mw) if mw else np.zeros((1, 3)) + 1e9; kw = cKDTree(mw)
for p in pts[rng.permutation(len(pts))]:
    if sel and np.min(np.linalg.norm(np.array(sel) - p, axis=1)) < PASO: continue
    if any(b_[0] <= p[0] <= b_[1] and b_[2] <= p[2] <= b_[3] for b_ in [[float(v) for v in c_.split(',')] for c_ in os.environ.get('EXCLUIR', '').split(';') if c_]): continue
    d, j = kw.query(p + [0, 0.8, 0])
    if d < 0.3: continue
    sel.append(p)
sel = np.array(sel); alturas = [float(x) for x in os.environ.get('ALTURAS', '1.0,1.6,2.0').split(',')]
O = np.concatenate([sel + [0, h, 0] for h in alturas]).astype(np.float32)
# fuera los puntos de vista metidos en la geometría (dentro de una columna, pegados a un mueble)
_dd = np.array([[x, y, z] for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1) if (x, y, z) != (0, 0, 0)], np.float32); _dd /= np.linalg.norm(_dd, axis=1, keepdims=True)
_Or = np.repeat(O, len(_dd), 0); _Dr = np.tile(_dd, (len(O), 1))
P.astype(np.float32).tofile('/tmp/_aud_tris.bin'); _Or.tofile('/tmp/_aud_o0.bin'); _Dr.tofile('/tmp/_aud_d0.bin')
subprocess.run([f'{AQ}/rayos', '/tmp/_aud_tris.bin', '/tmp/_aud_o0.bin', '/tmp/_aud_d0.bin', '/tmp/_aud_t0.bin', 't'], check=True)
_t0 = np.fromfile('/tmp/_aud_t0.bin', np.float32).reshape(len(O), len(_dd)); _t0[_t0 < 0] = 99
O = O[_t0.min(1) > float(os.environ.get('HOLGURA', 0.25))]
# direcciones: esfera de Fibonacci
K = int(os.environ.get('NDIR', 6000)); i = np.arange(K) + 0.5; phi = np.arccos(1 - 2 * i / K); th = np.pi * (1 + 5 ** 0.5) * i
D = np.stack([np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)], 1).astype(np.float32)
D = D[D[:, 1] < 0.85]          # mirando casi al techo no hace falta
P.astype(np.float32).tofile('/tmp/_aud_tris.bin'); O.tofile('/tmp/_aud_o.bin'); D.tofile('/tmp/_aud_d.bin')
subprocess.run([f'{AQ}/rayos', '/tmp/_aud_tris.bin', '/tmp/_aud_o.bin', '/tmp/_aud_d.bin', '/tmp/_aud_out.bin'], check=True)
R = np.fromfile('/tmp/_aud_out.bin', np.uint8).reshape(len(O), len(D))
oi, di = np.nonzero(R)
res = {'origenes': len(O), 'rayos': int(R.size), 'fugas': int(len(oi))}
if len(oi):
    # dónde: primer choque con la colisión (la pared del REmake) o 1 m
    O[oi].astype(np.float32).tofile('/tmp/_aud_o2.bin'); D[di].astype(np.float32).tofile('/tmp/_aud_d2.bin'); C.astype(np.float32).tofile('/tmp/_aud_c.bin')
    subprocess.run([f'{AQ}/rayos', '/tmp/_aud_c.bin', '/tmp/_aud_o2.bin', '/tmp/_aud_d2.bin', '/tmp/_aud_t.bin', 't'], check=True)
    t = np.fromfile('/tmp/_aud_t.bin', np.float32); t[(t < 0) | (t > 30)] = 1.0
    X = O[oi] + D[di] * t[:, None]
    np.savez('/tmp/_aud_fugas.npz', X=X, O=O[oi], D=D[di])
    # agrupar
    from scipy.cluster.hierarchy import fcluster, linkage
    if len(X) > 1:
        sub = np.random.default_rng(1).choice(len(X), min(len(X), 6000), replace=False)
        lab = fcluster(linkage(X[sub], 'single'), 0.25, 'distance')
        grupos = []
        for L in set(lab):
            q = X[sub][lab == L]; o_ = O[oi][sub][lab == L]
            grupos.append({'n': int(len(q)), 'centro': np.round(q.mean(0), 2).tolist(), 'min': np.round(q.min(0), 2).tolist(), 'max': np.round(q.max(0), 2).tolist(), 'desde': np.round(o_[0], 2).tolist()})
        grupos.sort(key=lambda g: -g['n']); res['grupos'] = grupos
json.dump(res, open(salida, 'w'), indent=1)
print(f"{res['origenes']} puntos de vista, {res['rayos']} rayos, {res['fugas']} sin chocar ({100 * res['fugas'] / res['rayos']:.3f} %)")
for g in res.get('grupos', [])[:int(os.environ.get('TOP', 25))]: print(g['n'], g['centro'], g['min'], g['max'], 'visto desde', g['desde'])
