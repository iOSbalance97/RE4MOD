"""Comprobaciones de H12 sobre los .das montados: tamaños, puertas (destino existe, llegada sobre suelo pisable y fuera
de las áreas de puerta del destino), conexión de todo el mapa desde el vestíbulo, ambiente coherente."""
import glob, json, os, struct, sys
from collections import deque
import numpy as np
sys.path.insert(0, '/home/claude/tools'); sys.path.insert(0, '/home/claude/re4src/tools')
import drs, re4inject as RI, mundo, uc_ambiente
from uc_montar2_mapa import MAPA
from hmap import floors, heights
B = sys.argv[1]; ORIG = '/home/claude/disc/ext1/files'
col = {}
for rr, ids in MAPA.items():
    for s in ids: col[(1, s & 0xFF)] = ('obj', f'/home/claude/uc/re4/{rr}/col/colision.obj', rr)
for n, (st, rid) in mundo.HUECO.items():
    col[(st, rid)] = ('obj', f'{mundo.dir_sala(n)}/col/colision.obj', n) if mundo.es_malla(n) else ('npz', f'/home/claude/gen/{n}/col.npz', n)
col[(1, 0x01)] = None; col[(1, 0x11)] = None          # pueblo (sin tocar)
cache = {}
def suelos(k):
    if k not in cache:
        t, p, n = col[k]
        if t == 'obj': T = floors(p)
        else:
            z = np.load(p); T = z['T'][z['K'] < 2] / 1000.0
        cache[k] = T
    return cache[k]
def hit_xz4(p, q):
    x, z = q
    (x0, z0), (x1, z1), (x2, z2), (x3, z3) = p
    if (x3 - x0) * (z - z0) > (z3 - z0) * (x - x0) or (x1 - x0) * (z - z0) < (z1 - z0) * (x - x0): return False
    if (x3 - x2) * (z - z2) < (z3 - z2) * (x - x2) or (x1 - x2) * (z - z2) > (z1 - z2) * (x - x2): return False
    return True
salas = {}; problemas = []
for st in (1, 2):
    for p in sorted(glob.glob(f'{B}/St{st}/r*.das')):
        rid = int(os.path.basename(p)[2:4], 16)
        sig, sr, snd, body, c = RI.read_das(p); e, _ = RI.parse_body(body)
        ob = len(RI.read_das(f'{ORIG}/St{st}/{os.path.basename(p)}')[3])
        if len(body) > ob: problemas.append(f'{os.path.basename(p)} mayor que la original ({len(body)} > {ob})')
        tags = {}
        for t, d in e: tags.setdefault(drs.tag_name(t), d)
        aev = tags.get('AEV'); recs = []
        if aev:
            n = struct.unpack('>H', aev[6:8])[0]
            for k in range(n):
                r = aev[0x10 + k * 0x9C:0x10 + (k + 1) * 0x9C]
                pts = [struct.unpack('>2f', r[0x14 + 8 * j:0x1C + 8 * j]) for j in range(4)]
                pos = struct.unpack('>4f', r[0x5C:0x6C]); recs.append(dict(pts=pts, pos=pos, dest=(r[0x6C], r[0x6D]), trg=r[0x38], floor=struct.unpack('>f', r[8:12])[0]))
        # ambiente
        if 'LIT' in tags and 'ETS' in tags:
            cn, ver, mx, cuts = uc_ambiente.lit_parse(tags['LIT']); nets = struct.unpack('>H', tags['ETS'][:2])[0]
            tor = sum(1 for l in cuts[0][1] if l[0x1C] == 3)
            if tor > nets or (nets and not tor): problemas.append(f'{os.path.basename(p)}: {tor} luces de antorcha y {nets} antorchas')
        salas[(st, rid)] = recs
print('salas montadas:', len(salas))
# puertas
G = {}
for k, recs in salas.items():
    for r in recs:
        if r['trg'] != 8: continue
        d = r['dest']
        G.setdefault(k, set()).add(d)
        if d not in salas and d not in ((1, 0x01), (1, 0x11)):
            problemas.append(f'r{k[0]}{k[1]:02x}: puerta a r{d[0]}{d[1]:02x}, que no se ha montado'); continue
        if col.get(d) is None: continue
        x, y, z, a = r['pos']
        h = heights(suelos(d), x / 1000, z / 1000) * 1000
        if not len(h) or np.abs(h - y).min() > 400:
            problemas.append(f'r{k[0]}{k[1]:02x} -> r{d[0]}{d[1]:02x}: llegada ({x:.0f},{y:.0f},{z:.0f}) sin suelo debajo (alturas {np.round(h).tolist()[:4]})')
        for r2 in salas.get(d, []):
            if r2['trg'] == 8 and hit_xz4(r2['pts'], (x, z)) and abs(r2['floor'] + 300 - y) < 1500:
                problemas.append(f'r{k[0]}{k[1]:02x} -> r{d[0]}{d[1]:02x}: llegada dentro de un área de puerta del destino')
# conexión desde el vestíbulo
inicio = (1, 0x03); vis = {inicio}; q = deque([inicio])
while q:
    u = q.popleft()
    for v in G.get(u, ()):
        if v not in vis: vis.add(v); q.append(v)
falta = sorted(set(salas) - vis - {(1, 0x20)})
print('alcanzables desde el vestíbulo:', len(vis), '| sin llegar:', ' '.join(f'r{s}{r:02x}' for s, r in falta) or 'ninguna')
# ida y vuelta
for u, vs in G.items():
    for v in vs:
        if v in salas and u not in G.get(v, ()) and v not in ((1, 0x01), (1, 0x11)): problemas.append(f'r{u[0]}{u[1]:02x} -> r{v[0]}{v[1]:02x} sin vuelta')
print('PROBLEMAS', len(problemas)); print('\n'.join(problemas[:60]))
