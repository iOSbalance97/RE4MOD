"""Sala de UC (OBJ en unidades de UC) -> OBJ en metros, sin la geometría reflejada bajo el suelo.
UC: 1 unidad = 10 cm (puerta = 22 u de alto, 10 de ancho). uso: uc_prep.py rNNN"""
import os, shutil, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import objload
r = sys.argv[1]
src = f'/home/claude/uc/obj/{r}'; dst = f'/home/claude/uc/m/{r}'
os.makedirs(dst, exist_ok=True)
V, T, F, M, G, mats = objload.load(f'{src}/sala.obj')
ymax = V[F[:, :3]][:, :, 1].max(1)
keep = V[F[:, :3]][:, :, 1].min(1) > -1.0   # el reflejo es una copia invertida bajo y=0: fuera todo lo que baja del suelo
F2, M2 = F[keep], M[keep]
with open(f'{dst}/sala.obj', 'w') as f:
    f.write('mtllib sala.mtl\n')
    used = np.unique(F2[:, :3]); ut = np.unique(F2[:, 3:])
    rv = {v: i + 1 for i, v in enumerate(used)}; rt = {v: i + 1 for i, v in enumerate(ut)}
    f.writelines(f'v {x*0.1:.4f} {y*0.1:.4f} {z*0.1:.4f}\n' for x, y, z in V[used])
    f.writelines(f'vt {u:.5f} {v:.5f}\n' for u, v in T[ut])
    cur = None
    for t, m in zip(F2, M2):
        if m != cur: f.write(f'usemtl {m}\n'); cur = m
        f.write(f'f {rv[t[0]]}/{rt[t[3]]} {rv[t[1]]}/{rt[t[4]]} {rv[t[2]]}/{rt[t[5]]}\n')
with open(f'{dst}/sala.mtl', 'w') as f:
    for m, t in mats.items():
        f.write(f'newmtl {m}\nKd 1 1 1\n')
        if t:
            f.write(f'map_Kd {t}\n')
            if not os.path.exists(f'{dst}/{t}'): shutil.copy(f'{src}/{t}', f'{dst}/{t}')
print(r, 'triángulos', len(F), '->', len(F2), 'sin reflejo')
