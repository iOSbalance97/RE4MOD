"""eat_columnas.py coldir 'x0,x1,z0,z1,y0,y1;...' : reescribe sala.eat (colisión de cámara) = colisión + cajas
(columnas de roca), para que la cámara no se meta dentro de ellas. sala.sat no se toca."""
import sys, numpy as np
sys.path.insert(0, '/home/claude/tools'); from re4col import write_sat; from hmap import load
d = sys.argv[1]; V, F = load(f'{d}/colision.obj'); V = list(V); F = list(F)
for c in sys.argv[2].split(';'):
    x0, x1, z0, z1, y0, y1 = map(float, c.split(','))
    P = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    for k in range(4):
        (ax, az), (bx, bz) = P[k], P[(k + 1) % 4]; b = len(V)
        V += [np.array(v) for v in ((ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az))]
        F += [np.array([b, b + 1, b + 2]), np.array([b, b + 2, b + 3]), np.array([b, b + 2, b + 1]), np.array([b, b + 3, b + 2])]
V = np.array(V) * 1000.0; F = np.array(F)
T = V[F]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(n, axis=1); n /= a[:, None] + 1e-9
abajo = n[:, 1] < -0.5; F[abajo] = F[abajo][:, [0, 2, 1]]; n[abajo] *= -1
K = np.full(len(F), -1); K[n[:, 1] > 0.97] = 0; K[(n[:, 1] > 0.5) & (n[:, 1] <= 0.97)] = 1; K[np.abs(n[:, 1]) < 0.3] = 2
ok = (K >= 0) & (a > 1.0)
_b = write_sat(V, F[ok], K[ok], np.zeros(ok.sum(), int), block_size=2000.0); open(f'{d}/sala.eat', 'wb').write(_b); open(f'{d}/sala.sat', 'wb').write(_b)
print('eat con columnas:', ok.sum(), 'tri')
