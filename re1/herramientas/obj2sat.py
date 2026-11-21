"""obj2sat.py colision.obj(metros) salida_dir : suelos (ny>0.5; pendiente si ny<0.97) y paredes (|ny|<0.3) -> sala.sat/eat (mm)"""
import sys, os, numpy as np
sys.path.insert(0, '/home/claude/tools'); from re4col import write_sat; from hmap import load
V, F = load(sys.argv[1]); V = V * 1000.0; out = sys.argv[2]; os.makedirs(out, exist_ok=True)
T = V[F]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(n, axis=1); n /= a[:, None] + 1e-9
F = F.copy()
abajo = n[:, 1] < -0.5; F[abajo] = F[abajo][:, [0, 2, 1]]; n[abajo] *= -1          # suelos siempre hacia arriba
K = np.full(len(F), -1); K[n[:, 1] > 0.97] = 0; K[(n[:, 1] > 0.5) & (n[:, 1] <= 0.97)] = 1; K[np.abs(n[:, 1]) < 0.3] = 2
ok = (K >= 0) & (a > 1.0)
sat = write_sat(V, F[ok], K[ok], np.zeros(ok.sum(), int), block_size=2000.0)
open(f'{out}/sala.sat', 'wb').write(sat); open(f'{out}/sala.eat', 'wb').write(sat)
import shutil; shutil.copy(sys.argv[1], f'{out}/colision.obj')
print(f'colisión: {ok.sum()} tri (suelo {(K[ok]==0).sum()}, pendiente {(K[ok]==1).sum()}, pared {(K[ok]==2).sum()}), {len(sat)//1024} KB')
