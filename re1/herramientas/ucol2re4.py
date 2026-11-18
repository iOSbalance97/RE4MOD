"""Colisión de UC (rNNN_chit.col) -> SAT/EAT de RE4 con la misma colocación que los modelos.
chit = colisión de personajes de UC: suelos, escaleras como rampas y paredes, ya simplificada.
Clasificación por normal: suelo ny>0.97, pendiente 0.5..0.97, pared |ny|<=0.5; techos (ny<-0.5) fuera.
uso: ucol2re4.py rNNN salida --colocar hx,hy,hz,x,y,z,giro"""
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ucol, re4room
from re4col import write_sat

ap = argparse.ArgumentParser(); ap.add_argument('sala'); ap.add_argument('out'); ap.add_argument('--colocar', required=True)
ap.add_argument('--tipo', default='chit')
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
V, N, A = ucol.load(f'/home/claude/uc/r/{a.sala}/{a.sala}_{a.tipo}.col')
P = re4room.place((V * 0.1).reshape(-1, 3), a.colocar, 1000.0) * 1000.0          # mm de RE4
Nr = re4room.place(N, '0,0,0,0,0,0,' + a.colocar.split(',')[-1], 1000.0)        # solo giro
# soldar vértices (1 mm)
key = np.round(P).astype(np.int64)
_, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
SV = P[first]; T = inv.reshape(-1, 3)
ny = Nr[:, 1]
keep = (ny >= 0.5) | (np.abs(ny) <= 0.2)          # paredes casi verticales; lo inclinado intermedio y los techos fuera
# fuera degenerados
ar = np.linalg.norm(np.cross(SV[T[:, 1]] - SV[T[:, 0]], SV[T[:, 2]] - SV[T[:, 0]]), axis=1)
keep &= ar > 1.0
# orientación: que el orden de vértices dé la normal de UC
c = np.cross(SV[T[:, 1]] - SV[T[:, 0]], SV[T[:, 2]] - SV[T[:, 0]])
flip = (c * Nr).sum(1) < 0
T[flip] = T[flip][:, [0, 2, 1]]
T = T[keep]; ny = ny[keep]
K = np.where(ny > 0.97, 0, np.where(ny >= 0.5, 1, 2))
sat = write_sat(SV, T, K, np.zeros(len(T), int), block_size=2000.0)
open(f'{a.out}/sala.sat', 'wb').write(sat); open(f'{a.out}/sala.eat', 'wb').write(sat)
with open(f'{a.out}/colision.obj', 'w') as f:
    f.writelines(f'v {x/1000} {y/1000} {z/1000}\n' for x, y, z in SV)
    for t, k in zip(T, K):
        f.write(f'g {"suelo" if k == 0 else "pendiente" if k == 1 else "pared"}\nf {t[0]+1} {t[1]+1} {t[2]+1}\n')
print(f'{a.sala}: SAT {len(T)} polígonos (suelo {(K==0).sum()}, pendiente {(K==1).sum()}, pared {(K==2).sum()}), {len(sat)//1024} KB, '
      f'giradas {int(flip.sum())}')
