"""Conexiones entre salas de UC colocadas en coordenadas de RE4 -> puertas AEV.
Las parejas de salas conectadas se dan a mano (sacadas del mapa y del contacto entre suelos);
el sitio exacto de cada puerta se calcula: hoja de puerta detectada si la hay, si no la zona donde los
suelos de las dos salas se tocan. Llegada: suelo de la sala destino a ~1,2 m de la puerta, mirando hacia dentro.
uso: uc_conexiones.py colocar puertas.json salida.json"""
import json, pickle, sys
import numpy as np
from scipy.spatial import cKDTree
COLOCAR, PJSON, OUT = sys.argv[1:4]
PARES = [('r102', 'r101'), ('r102', 'r103'), ('r102', 'r111'), ('r101', 'r100'), ('r100', 'r111'),
         ('r103', 'r104'), ('r104', 'r105'), ('r105', 'r106'), ('r106', 'r107'), ('r107', 'r108'),
         ('r108', 'r109'), ('r111', 'r112'), ('r112', 'r113'), ('r113', 'r114'), ('r114', 'r115')]
fl = pickle.load(open('/tmp/fl.pkl', 'rb'))
hojas = json.load(open(PJSON))
tr = {r: cKDTree(P[:, [0, 2]]) for r, P in fl.items()}
out = []
for A, B in PARES:
    pa, pb = fl[A], fl[B]
    h = [q for q in hojas if {q['a'], q['b']} == {A, B}]
    if h:
        c = np.array(h[0]['centro']) / 1000; how = 'hoja'
    else:
        d, j = cKDTree(pb).query(pa)
        ok = np.abs(pa[:, 1] - pb[j, 1]) < 0.5
        g = d[ok].min(); sel = np.where(ok & (d < g + 0.2))[0]
        mids = (pa[sel] + pb[j[sel]]) / 2
        t = cKDTree(mids[:, [0, 2]]); best = None; left = set(range(len(mids)))
        while left:
            s = next(iter(left)); grp = set(t.query_ball_point(mids[s, [0, 2]], 1.0)) & left
            # crecer el grupo
            fr = list(grp)
            while fr:
                q = fr.pop()
                for k in t.query_ball_point(mids[q, [0, 2]], 0.4):
                    if k in left and k not in grp: grp.add(k); fr.append(k)
            left -= grp
            if best is None or len(grp) > len(best): best = grp
        c = mids[list(best)].mean(0); how = f'contacto {g:.2f} m ({len(best)} pts)'
    def lado(R, O):
        P = fl[R]; dd = np.hypot(P[:, 0] - c[0], P[:, 2] - c[2])
        m = np.abs(P[:, 1] - c[1]) < 0.6
        dO = tr[O].query(P[:, [0, 2]])[0]                       # cuánto se aleja de la otra sala
        # llegada: ~1,2 m de la puerta, dentro de R (lejos del suelo de O)
        sc = np.where(m, np.abs(dd - 1.2) - 0.8 * np.minimum(dO, 1.0), 1e9)
        j = int(np.argmin(sc)); p = P[j]
        v = p - c; ang = float(np.arctan2(v[0], v[2]))
        # disparador: punto de R más cercano a la puerta
        k = int(np.argmin(np.where(m, dd, 1e9))); trg = P[k]
        return dict(llegada=[float(x * 1000) for x in p], ang=ang, trig=[float(x * 1000) for x in trg],
                    dist_trig=float(dd[k]), dist_lleg=float(dd[j]), fuera=float(dO[j]))
    la, lb = lado(A, B), lado(B, A)
    out.append(dict(a=A, b=B, centro=[float(x * 1000) for x in c], como=how, A=la, B=lb))
    print(f'{A}<->{B} {np.round(c, 2)} [{how}] trig {la["dist_trig"]:.2f}/{lb["dist_trig"]:.2f} m, '
          f'llegada {la["dist_lleg"]:.2f}/{lb["dist_lleg"]:.2f} m (separada {la["fuera"]:.2f}/{lb["fuera"]:.2f} m de la otra sala)')
json.dump(out, open(OUT, 'w'), indent=1)
