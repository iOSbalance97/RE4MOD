"""verja_cueva.py : copia la verja del vestíbulo (UC) en las dos puertas de r31a, con el frente a ras de la pared de colisión"""
import numpy as np, shutil, sys
sys.path.insert(0, '/home/claude/tools'); from hmap import floors, heights
src = '/home/claude/re1gc/salas_uc5/r106'; out = '/home/claude/re1gc/modelos/verja'
V = []; VT = []; cur = None; F = []
for l in open(f'{src}/sala.obj'):
    if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('vt '): VT.append([float(x) for x in l.split()[1:3]])
    elif l.startswith('usemtl'): cur = l.split()[1]
    elif l.startswith('f '):
        q = [x.split('/') for x in l.split()[1:4]]; F.append((cur, [int(a[0]) - 1 for a in q], [int(a[1]) - 1 for a in q]))
V = np.array(V); VT = np.array(VT); mt = {}
for l in open(f'{src}/sala.mtl'):
    if l.startswith('newmtl'): m = l.split()[1]
    elif l.startswith('map_Kd'): mt[m] = l.split()[1]
keep = ('wall12', 'light01', 'lantan01', 'rust09', 'Chandelier06', 'light03', 'door09')
sel = [(c, v, t) for c, v, t in F if any(k in c for k in keep) and np.all((V[v].mean(0) > [-0.97, -0.2, -5.1]) & (V[v].mean(0) < [0.97, 2.4, -4.5]))]
P = np.concatenate([V[v] for _, v, _ in sel]); zf = P[:, 2].max(); y0 = P[:, 1].min()
L = lambda p: np.array([p[0] - 0.0, p[1] - y0, p[2] - zf])          # local: frente en z=0, hacia +z
TF = floors('/home/claude/re1gc/salas/r31a/colision.obj')
zz = [z for z in np.arange(0.5, 4.5, 0.02) if len(heights(TF, -14.25, z))]; cz = (min(zz) + max(zz)) / 2; yf = float(heights(TF, -14.25, cz).min())
puertas = {'verja': lambda q: np.array([q[0] - 0.02, q[1] + 10.0, q[2] - 4.85]),               # arriba: pared z=-4.85, mira a +z
           'verja_r315': lambda q: np.array([q[2] - 14.38, q[1] + yf, -q[0] + cz])}          # final del túnel: pared x=-14.38, mira a +x
for nm, tr in puertas.items():
    with open(f'{out}/{nm}.obj', 'w') as f:
        k = 1
        for c, v, t in sel:
            f.write(f'usemtl {c}\n')
            for a in v: f.write('v %.4f %.4f %.4f\n' % tuple(tr(L(V[a]))))
            for a in t: f.write('vt %.4f %.4f\n' % tuple(VT[a]))
            f.write(f'f {k}/{k} {k+1}/{k+1} {k+2}/{k+2}\n'); k += 3
    with open(f'{out}/{nm}.mtl', 'w') as f:
        for c in sorted(set(c for c, _, _ in sel)): f.write(f'newmtl {c}\nmap_Kd {mt[c]}\n'); shutil.copy(f'{src}/{mt[c]}', out)
print('verjas: centro del túnel', round(cz, 2), 'suelo', round(yf, 2), 'fondo', round(P[:, 2].min() - zf, 2))
