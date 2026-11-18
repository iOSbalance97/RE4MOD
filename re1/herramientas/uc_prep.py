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
texdir = {m: src for m in mats}
# objetos colocados (puertas, muebles...) de ucobjs.py, ya en coordenadas del mundo de UC
for ob in (f'/home/claude/uc/objs/{r}/objetos.obj', f'/home/claude/uc/objs/{r}/relleno.obj'):
  if os.path.exists(ob):
      V2, T2, F2_, M2_, G2, mats2 = objload.load(ob)
      F2_ = F2_.copy(); F2_[:, :3] += len(V); F2_[:, 3:] += len(T)
      V = np.concatenate([V, V2]); T = np.concatenate([T, T2]); F = np.concatenate([F, F2_])
      M = np.concatenate([np.asarray(M, dtype=object), np.asarray(M2_, dtype=object)])
      for m, t in mats2.items(): mats[m] = t; texdir[m] = os.path.dirname(ob)
      print(r, 'objetos añadidos:', len(F2_), 'triángulos')
ymax = V[F[:, :3]][:, :, 1].max(1)
# el reflejo del suelo son modelos aparte (rNNN_MirrorModel / _mirror / _Mirror): fuera por nombre, no por altura
import glob, re
partes = sorted(o for o in glob.glob(f'{src}/*.obj') if not o.endswith('/sala.obj'))
espejo = {f'p{k}' for k, o in enumerate(partes) if 'mirror' in os.path.basename(o).lower()}
keep = np.array([re.match(r'(p\d+)m', str(m)) is None or re.match(r'(p\d+)m', str(m)).group(1) not in espejo for m in M])
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
            if not os.path.exists(f'{dst}/{t}'): shutil.copy(f'{texdir[m]}/{t}', f'{dst}/{t}')
print(r, 'triángulos', len(F), '->', len(F2), 'sin los modelos de reflejo', sorted(espejo))
