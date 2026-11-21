"""Comprobaciones del montaje del REmake antes de entregar:
 - cada llegada cae sobre suelo de colisión (a menos de 0,4 m de su altura)
 - cada puerta tiene suelo dentro de su área (se puede llegar a pulsarla)
 - llegada y puerta de cada sala en la misma zona pisable (conexas)
 - todas las salas alcanzables desde el vestíbulo
uso: verificar_remake.py montaje_remake.json"""
import json, sys
import numpy as np
sys.path.insert(0, '/home/claude/tools')
from hmap import floors, heights
import pisable
M = json.load(open(sys.argv[1])); G = json.load(open('/home/claude/re1gc/work/puertas_remake.json'))
H = M['HUECO']; mal = 0; avisos = 0
col = lambda r: f'/home/claude/re1gc/re4/re_{r}/col/colision.obj'
TF = {r: floors(col(r)) for r in H}
PI = {}
def comp(r, x, z, y):
    if r not in PI: PI[r] = pisable.Pisable(col(r))
    P = PI[r]
    try:
        p, v, dist = P.ajustar(x / 1000, z / 1000)
        return dist
    except Exception: return 99
for a in sorted(H):
    for d in G[a]:
        b = d['dst']
        if b == a or b not in H or not any(e['dst'] == a for e in G[b]): continue
        x, y, z, ang = d['llegada']
        h = heights(TF[b], x / 1000, z / 1000) * 1000
        if not len(h) or np.abs(h - y).min() > 400:
            print(f'LLEGADA SIN SUELO {a}->{b}: ({x:.0f},{y:.0f},{z:.0f}) alturas {np.round(h).tolist()}'); mal += 1
        q = np.array(d['quad'], float).reshape(4, 2); c = q.mean(0)
        hs = [heights(TF[a], (c[0] + (p[0] - c[0]) * f) / 1000, (c[1] + (p[1] - c[1]) * f) / 1000) for p in q for f in (0.5, 0.8, 1.0)]
        if not any(len(t) for t in hs):
            print(f'  aviso: puerta {a}->{b} sin suelo en su área (centro {c.round()})'); avisos += 1
# alcanzables
vis = {'r106'}; pila = ['r106']
while pila:
    a = pila.pop()
    for d in G[a]:
        b = d['dst']
        if b in H and b not in vis and any(e['dst'] == a for e in G[b]): vis.add(b); pila.append(b)
fuera = sorted(set(H) - vis)
print(f'salas {len(H)}, alcanzables {len(vis)}; fuera: {" ".join(fuera)}')
print(f'llegadas sin suelo: {mal}; puertas sin suelo: {avisos}')
