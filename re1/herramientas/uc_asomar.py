"""Lo que se ve por cada puerta: a la sala A se le añade la geometría de la sala vecina B que queda al otro lado del
umbral (radio 5 m, de 0,5 m por debajo del suelo a 4 m por encima), como en UC donde por la puerta se ve la sala de al lado.
Entrada /home/claude/uc/m/rNNN/sala.obj (metros, mundo de UC) -> salida /home/claude/uc/m2/rNNN/sala.obj
uso: uc_asomar.py conexiones2.json"""
import json, os, shutil, sys
import numpy as np
sys.path.insert(0, '/home/claude/tools')
import objload, re4room
COL = "19.4,0,15.0,-47609,12,7084,-1.253"
RADIO, BAJO, ALTO, MARGEN = 5.0, 0.5, 4.0, 0.2
conx = json.load(open(sys.argv[1]))
salas = sorted({q['a'] for q in conx} | {q['b'] for q in conx} - {'PUEBLO'})
geo = {r: objload.load(f'/home/claude/uc/m/{r}/sala.obj') for r in salas}
plc = {r: re4room.place(geo[r][0], COL, 1000.0) for r in salas}
extra = {r: [] for r in salas}
for q in conx:
    if q['b'] == 'PUEBLO': continue
    t = np.array(q['umbral']); u = np.array(q['u'])
    for A, B, sg, y in ((q['a'], q['b'], 1, q['ya']), (q['b'], q['a'], -1, q['yb'])):
        V, T, F, M, G, mats = geo[B]; P = plc[B]
        cen = P[F[:, :3]].mean(1)
        d = np.hypot(cen[:, 0] - t[0], cen[:, 2] - t[2])
        lado = (cen[:, [0, 2]] - t[[0, 2]]) @ (u * sg)
        sel = (d < RADIO) & (lado > -MARGEN) & (cen[:, 1] > y - BAJO) & (cen[:, 1] < y + ALTO)
        extra[A].append((B, np.where(sel)[0]))
for A in salas:
    V, T, F, M, G, mats = geo[A]
    src = f'/home/claude/uc/m/{A}'; dst = f'/home/claude/uc/m2/{A}'
    os.makedirs(dst, exist_ok=True)
    Vs, Ts, Fs, Ms = [V], [T], [F], [list(M)]; mt = dict(mats); tdir = {m: src for m in mats}; nv, nt = len(V), len(T)
    añadidos = []
    for B, idx in extra[A]:
        if not len(idx): continue
        VB, TB, FB, MB, GB, matsB = geo[B]
        f = FB[idx].copy(); f[:, :3] += nv; f[:, 3:] += nt
        Vs.append(VB); Ts.append(TB); Fs.append(f); Ms.append([f'{B}_{MB[i]}' for i in idx])
        for m, tx in matsB.items(): mt[f'{B}_{m}'] = tx; tdir[f'{B}_{m}'] = f'/home/claude/uc/m/{B}'
        nv += len(VB); nt += len(TB); añadidos.append(f'{B}:{len(idx)}')
    V2 = np.concatenate(Vs); T2 = np.concatenate(Ts); F2 = np.concatenate(Fs); M2 = sum(Ms, [])
    used = np.unique(F2[:, :3]); ut = np.unique(F2[:, 3:])
    rv = np.zeros(len(V2), int); rv[used] = np.arange(1, len(used) + 1); rt = np.zeros(len(T2), int); rt[ut] = np.arange(1, len(ut) + 1)
    with open(f'{dst}/sala.obj', 'w') as f:
        f.write('mtllib sala.mtl\n')
        f.writelines(f'v {x:.4f} {y:.4f} {z:.4f}\n' for x, y, z in V2[used])
        f.writelines(f'vt {a:.5f} {b:.5f}\n' for a, b in T2[ut])
        cur = None
        for fc, m in zip(F2, M2):
            if m != cur: f.write(f'usemtl {m}\n'); cur = m
            f.write(f'f {rv[fc[0]]}/{rt[fc[3]]} {rv[fc[1]]}/{rt[fc[4]]} {rv[fc[2]]}/{rt[fc[5]]}\n')
    with open(f'{dst}/sala.mtl', 'w') as f:
        for m in dict.fromkeys(M2):
            tx = mt.get(m); f.write(f'newmtl {m}\nKd 1 1 1\n' + (f'map_Kd {tx}\n' if tx else ''))
            if tx and not os.path.exists(f'{dst}/{tx}'): shutil.copy(f'{tdir[m]}/{tx}', f'{dst}/{tx}')
    print(A, 'propios', len(F), 'vecinos', ' '.join(añadidos))
