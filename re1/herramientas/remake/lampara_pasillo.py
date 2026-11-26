"""lampara_pasillo.py rNNN : copia una lámpara de pared del comedor (con su brazo) a las fuentes de luz de la sala, girada hacia su pared"""
import sys, json, shutil, numpy as np
sys.path.insert(0, '/home/claude/tools'); from hmap import floors, heights
r = sys.argv[1]; out = f'/home/claude/re1gc/modelos/lamparas_{r}'; import os; os.makedirs(out, exist_ok=True)
src = '/home/claude/re1gc/salas_uc5/r105'
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
# lámpara junto a la pared z = -3.7 en x ~ 1.4 (brazo hacia -z)
C = np.array([1.4, 2.1, -3.2])
sel = [(c, v, t) for c, v, t in F if ('dentou1b' in c or 'syokudai' in c) and np.all(np.abs(V[v].mean(0) - C) < [0.35, 0.6, 0.6])]
P = np.concatenate([V[v] for _, v, _ in sel]); zw = -3.69          # plano de la pared
ctr = np.array([(P[:, 0].min() + P[:, 0].max()) / 2, P[:, 1].min(), zw])
print('lámpara:', len(sel), 'triángulos, alto', round(P[:, 1].max() - P[:, 1].min(), 2), 'saliente', round(P[:, 2].max() - zw, 2))
col = f'/home/claude/re1gc/salas/{r}/colision.obj'
Vc = []; Fc = []
for l in open(col):
    if l.startswith('v '): Vc.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('f '): Fc.append([int(x.split('/')[0]) - 1 for x in l.split()[1:4]])
Vc = np.array(Vc); Tc = Vc[np.array(Fc)]; nc = np.cross(Tc[:, 1] - Tc[:, 0], Tc[:, 2] - Tc[:, 0]); nc /= np.linalg.norm(nc, axis=1, keepdims=True) + 1e-12
TF = floors(col)
fu = json.load(open(sys.argv[2]))['fuentes']
with open(f'{out}/lamparas.obj', 'w') as f:
    k = 1; nl = 0
    for p in fu:
        p = np.array(p); best = None
        for t3, nn in zip(Tc, nc):
            if abs(nn[1]) > 0.3 or not (t3[:, 1].min() - 0.5 < p[1] < t3[:, 1].max() + 0.5): continue
            nh = np.array([nn[0], 0, nn[2]]); nh /= np.linalg.norm(nh); dd = abs((p - t3[0]) @ nh)
            tg = np.cross([0, 1, 0], nh); pr = (t3 - t3[0]) @ tg; s_ = (p - t3[0]) @ tg
            if pr.min() - 0.1 <= s_ <= pr.max() + 0.1 and (best is None or dd < best[0]): best = (dd, t3, nh)
        if best is None or best[0] > 1.2: continue
        _, t3, nh = best; q = p - nh * ((p - t3[0]) @ nh)          # punto en la pared
        hs = heights(TF, *(q + nh * 0.4)[[0, 2]]); hs2 = heights(TF, *(q - nh * 0.4)[[0, 2]])
        if not len(hs) and len(hs2): nh = -nh; hs = hs2
        if not len(hs): continue
        yf = float(hs[hs < p[1]].max()) if np.any(hs < p[1]) else float(hs.min())
        # local: x lateral, y alto, z saliente (+z sale de la pared) -> mundo
        tg = np.cross([0, 1, 0], nh)
        def W(v): l_ = v - ctr; return q * [1, 0, 1] + [0, yf + 1.75, 0] + tg * l_[0] + np.array([0, l_[1], 0]) + nh * l_[2] * 0.5
        for c, v, t in sel:
            f.write(f'usemtl {c}\n')
            for a in v: f.write('v %.4f %.4f %.4f\n' % tuple(W(V[a])))
            for a in t: f.write('vt %.4f %.4f\n' % tuple(VT[a]))
            f.write(f'f {k}/{k} {k+1}/{k+1} {k+2}/{k+2}\n'); k += 3
        nl += 1
with open(f'{out}/lamparas.mtl', 'w') as f:
    for c in sorted(set(c for c, _, _ in sel)): f.write(f'newmtl {c}\nmap_Kd {mt[c]}\n'); shutil.copy(f'{src}/{mt[c]}', out)
print('lámparas puestas:', nl)
