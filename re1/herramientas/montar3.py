"""Monta el mapa completo (H12): salas UC de la mansión (uc_montar2) + salas generadas + salas UC de fuera,
con todas las puertas de mundo.py, el ambiente (oscuridad, linterna, fuego), los scripts vaciados y sin enemigos.
uso: montar3.py salida_files   (escribe St1/, St2/, Rel/, etc/ bajo salida_files)"""
import json, os, shutil, struct, subprocess, sys
import numpy as np
sys.path.insert(0, '/home/claude/tools'); sys.path.insert(0, '/home/claude/re4src/tools')
import drs, re4inject as RI, uc_ambiente, mundo
from hmap import floors, heights

OUT = sys.argv[1]; ORIG = '/home/claude/disc/ext1/files'
for d in ('St1', 'St2', 'Rel', 'etc'): os.makedirs(f'{OUT}/{d}', exist_ok=True)
# 1) mansión de UC con sus puertas de siempre
r = subprocess.run(['python3', '/home/claude/tools/uc_montar2.py', '/home/claude/uc/re4/conexiones2.json', f'{ORIG}/St1', f'{OUT}/St1'], capture_output=True, text=True)
if r.returncode: print(r.stdout[-2000:], r.stderr[-3000:]); raise SystemExit(1)
print('\n'.join(l for l in r.stdout.splitlines() if 'MAYORES' in l or '¡' in l))
import uc_montar2_mapa as UM
MAPA = UM.MAPA

def hit_xz4(p, q):
    x, z = q
    (x0, z0), (x1, z1), (x2, z2), (x3, z3) = p
    if (x3 - x0) * (z - z0) > (z3 - z0) * (x - x0) or (x1 - x0) * (z - z0) < (z1 - z0) * (x - x0): return False
    if (x3 - x2) * (z - z2) < (z3 - z2) * (x - x2) or (x1 - x2) * (z - z2) > (z1 - z2) * (x - x2): return False
    return True
def caja(c, u, n, ancho, fondo0, fondo1):
    """área XZ4 delante de una puerta: centro c (x,z), u a lo largo de la pared, n hacia dentro"""
    c = np.asarray(c, float); u = np.asarray(u, float); n = np.asarray(n, float)
    pts = [c + u * ancho / 2 + n * fondo0, c - u * ancho / 2 + n * fondo0, c - u * ancho / 2 + n * fondo1, c + u * ancho / 2 + n * fondo1]
    pts = [tuple(map(float, p)) for p in pts]; m = tuple(map(float, c + n * (fondo0 + fondo1) / 2))
    if not hit_xz4(pts, m): pts = pts[::-1]
    assert hit_xz4(pts, m)
    return pts

# 2) puntos de puerta
EP = {}
def ep(key, slots, centro, n, ancho, y, fondo=1500.0):
    """fondo: hasta dónde hay suelo delante de la puerta (mm); el área y la llegada se ajustan si hay poco"""
    n = np.asarray(n, float); n /= np.linalg.norm(n); u = np.array([-n[1], n[0]])
    c = np.asarray(centro, float)
    f1 = 1100.0 if fondo >= 1500.0 else max(500.0, fondo - 450.0); dl = 1500.0 if fondo >= 1500.0 else fondo - 150.0
    EP[key] = dict(slots=slots, area=dict(floor=float(y - 300.0), height=2600.0, pts=caja(c, u, n, ancho + 300.0, 50.0, f1)),
                   pos=(float(c[0] + n[0] * dl), float(y), float(c[1] + n[1] * dl)), ang=float(np.arctan2(n[0], n[1])))
def fondo_suelo(rr, c, n, y):
    Tc = floors(f'{mundo.dir_sala(rr)}/col/colision.obj'); n = np.asarray(n, float) / np.linalg.norm(n); f = 0.0
    for d in np.arange(300.0, 1501.0, 100.0):              # el mayor fondo con suelo (el umbral puede no tenerlo)
        q = (np.asarray(c, float) + n * d) / 1000.0; h = heights(Tc, q[0], q[1]) * 1000.0
        if len(h) and np.abs(h - y).min() < 400: f = d
    return f if f > 0 else 1500.0
libres = json.load(open('/home/claude/uc/puertas_libres.json'))
def huecos_uc(rr): return [(1, s & 0xFF) for s in sorted(MAPA[rr], reverse=True)]     # r102: primero r113 (el vestíbulo normal)
def lado_con_suelo(rr, c, n, y):
    Tc = floors(f'{mundo.dir_sala(rr)}/col/colision.obj'); n = np.asarray(n, float) / np.linalg.norm(n); ok = []
    for s in (1, -1):
        q = (np.asarray(c, float) + s * n * 1500.0) / 1000.0; h = heights(Tc, q[0], q[1]) * 1000.0
        ok.append(len(h) > 0 and np.abs(h - y).min() < 400)
    return n if ok[0] or not ok[1] else -n
for rr, L in libres.items():
    for i, d in enumerate([d for d in L if not d['conectada']]):
        c = (d['centro'][0], d['centro'][2])
        nn = lado_con_suelo(rr, c, d['normal'], d['centro'][1])
        ep(f'm:{rr}:{i}', huecos_uc(rr), c, nn, d['ancho'], d['centro'][1], fondo_suelo(rr, c, nn, d['centro'][1]))
for k, v in mundo.VIRTUALES.items():
    ep(f'v:{k}', huecos_uc(v['sala']), (v['centro'][0], v['centro'][2]), v['normal'], v['ancho'], v['centro'][1])
for sname in [s for s in mundo.HUECO if not mundo.es_malla(s)]:
    meta = json.load(open(f'/home/claude/gen/{sname}/meta.json'))
    for d in meta['puertas']:
        ep(f'g:{sname}:{d["id"]}', [mundo.HUECO[sname]], (d['centro'][0] * 1000, d['centro'][2] * 1000), d['normal'], d['ancho'] * 1000, d['centro'][1] * 1000)
import pisable
for rr, pts in mundo.AREAS.items():
    P = pisable.Pisable(f'{mundo.dir_sala(rr)}/col/colision.obj'); comp = int(np.argmax(P.tam))
    for k, (x, z) in pts.items():
        p, v, dist = P.ajustar(x, z, comp)
        if dist > 2.0: print(f'  aviso: puerta {rr}:{k} movida {dist:.1f} m para quedar en la zona pisable principal')
        c = p[[0, 2]] - v * 0.6
        ep(f'a:{rr}:{k}', [mundo.HUECO[rr]], c * 1000, v, 1400.0, p[1] * 1000)
        q, _, _ = P.ajustar(*(p[[0, 2]] + v * 0.9), comp, margen=0.4)           # llegada: dentro del mismo componente
        EP[f'a:{rr}:{k}']['pos'] = (float(q[0] * 1000), float(q[1] * 1000), float(q[2] * 1000))
# 3) registros AEV por hueco
TPL = UM.TPL
CAM_VACIO = open('/home/claude/tools/cam_vacio.bin', 'rb').read()   # 'EMPT': sin zonas de cámara (cámara libre de RE4)
def door_rec(no, area, dest, pos, ang):
    rr = bytearray(TPL)
    rr[4], rr[5], rr[6], rr[7] = 1, 1, 0, 0
    struct.pack_into('>3f', rr, 0x08, area['floor'], area['height'], 0.0)
    for k, (x, z) in enumerate(area['pts']): struct.pack_into('>2f', rr, 0x14 + 8 * k, x, z)
    rr[0x36] = no
    struct.pack_into('>4f', rr, 0x5C, *pos, ang)
    rr[0x6C], rr[0x6D], rr[0x6E], rr[0x6F] = dest[0], dest[1], 0, 0
    return bytes(rr)
AEVS = {}
usados = set()
for a, b in mundo.ENLACES:
    for x, y in ((a, b), (b, a)):
        assert x in EP and y in EP, (x, y); usados.add(x)
        for s in EP[x]['slots']:
            AEVS.setdefault(s, []).append((EP[x]['area'], EP[y]['slots'][0], EP[y]['pos'], EP[y]['ang'], f'{x} -> {y}'))
sin_usar = sorted(set(EP) - usados)
print('puntos de puerta:', len(EP), '| sin enlazar:', ' '.join(sin_usar))

def leer(st, rid):
    return RI.read_das(f'{ORIG}/St{st}/r{st}{rid:02x}.das')
def montar_nueva(st, rid, base, llamas, lamparas, HORN=False):
    name = f'r{st}{rid:02x}'
    sig, snd_rec, snd, body, _ = leer(st, rid)
    entries, rel = RI.parse_body(body)
    recs = [door_rec(i, *x[:4]) for i, x in enumerate(AEVS.get((st, rid), []))]
    aev = b'AEV\0' + struct.pack('>HH8x', 0x104, len(recs)) + b''.join(recs)
    new = {'SMD': open(f'{base}/mod/sala.smd', 'rb').read(), 'SMX': open(f'{base}/mod/sala.smx', 'rb').read(),
           'SAT': open(f'{base}/col/sala.sat', 'rb').read(), 'EAT': open(f'{base}/col/sala.eat', 'rb').read(), 'AEV': aev,
           'CAM': CAM_VACIO}
    amb, nl, nluz = uc_ambiente.ambiente(name, llamas, lamparas, horneada=HORN); new.update(amb)
    done = set(); out = []
    for t, d in entries:
        n = drs.tag_name(t)
        if n in new and n not in done: done.add(n); out.append([t, new[n]])
        elif n in ('FCV', 'SEQ'): out.append([b'x' + t[1:], bytes(32)])
        elif n == 'ITA': out.append([b'x' + t[1:], d])
        else: out.append([t, d])
    for n in new:
        if n not in done: out.append([n.encode() + b'\0', new[n]]); done.add(n)
    nb = RI.pack_body(out, rel); das = RI.write_das(sig, snd_rec, snd, nb)
    open(f'{OUT}/St{st}/{name}.das', 'wb').write(das)
    return name, len(recs), nl, nluz, len(nb), len(body)

informe = []
for sname, (st, rid) in mundo.HUECO.items():
    if mundo.es_malla(sname):
        base = mundo.dir_sala(sname)
        lamparas = [] if mundo.HORNEADA(sname) else [(p[0], p[1] + 2400.0, p[2]) for k, p in ((k, EP[k]['pos']) for k in EP if k.startswith(f'a:{sname}:'))]
        llamas = []
    else:
        base = f'/home/claude/gen/{sname}'; meta = json.load(open(f'{base}/meta.json'))
        llamas, lamparas = meta['llamas'], meta['lamparas']
    name, nd, nl, nluz, nb, ob = montar_nueva(st, rid, base, llamas, lamparas, mundo.HORNEADA(sname))
    informe.append((name, sname, nd, nl, nluz, nb, ob))
    print(f'{name} <- {sname:13s} puertas {nd:2d} llamas {nl:2d} luces {nluz:2d}  {nb/1e6:.2f} MB (original {ob/1e6:.2f}){"  ¡MAYOR!" if nb > ob else ""}')
# r120 (partida nueva): sus animaciones de textura (TEX, opcional) fuera para que no crezca por el AEV nuevo
p = f'{OUT}/St1/r120.das'; sig, snd_rec, snd, body, _ = RI.read_das(p); entries, rel = RI.parse_body(body)
entries = [[b'x' + t[1:], bytes(32)] if drs.tag_name(t) in ('FCV', 'SEQ', 'ITA', 'TEX') else [t, CAM_VACIO if drs.tag_name(t) == 'CAM' else d] for t, d in entries]
nb = RI.pack_body(entries, rel); open(p, 'wb').write(RI.write_das(sig, snd_rec, snd, nb))
print(f'r120: {len(nb)} bytes (original {len(leer(1, 0x20)[3])})')
# 4) puertas nuevas en las salas UC de la mansión (añadidas al AEV que ya escribió uc_montar2)
for rr, ids in MAPA.items():
    for s in ids:
        extra = AEVS.get((1, s & 0xFF), [])
        p = f'{OUT}/St1/r{s:03x}.das'
        sig, snd_rec, snd, body, _ = RI.read_das(p); entries, rel = RI.parse_body(body)
        out = []
        for t, d in entries:
            if drs.tag_name(t) == 'CAM': d = CAM_VACIO
            if drs.tag_name(t) == 'AEV' and extra:
                n0 = struct.unpack('>H', d[6:8])[0]
                recs = [door_rec(n0 + i, *x[:4]) for i, x in enumerate(extra)]
                d = d[:4] + struct.pack('>HH8x', 0x104, n0 + len(recs)) + d[0x10:0x10 + n0 * 0x9C] + b''.join(recs)
                print(f'r{s:03x} ({rr}): +{len(recs)} puertas: ' + '; '.join(x[4] for x in extra))
            out.append([t, d])
        nb = RI.pack_body(out, rel); open(p, 'wb').write(RI.write_das(sig, snd_rec, snd, nb))
        ob = len(leer(1, s & 0xFF)[3])
        if len(nb) > ob: print(f'   ¡r{s:03x} mayor que la original!')
# 5) scripts de sala fuera (Rel) y enemigos fuera (ESL)
st1 = sorted({s & 0xFF for v in MAPA.values() for s in v} | {0x20} | {rid for st, rid in mundo.HUECO.values() if st == 1})
st2 = sorted({rid for st, rid in mundo.HUECO.values() if st == 2})
for pref, lst in (('st1', st1), ('st2', st2)):
    tmp = f'/tmp/rel_{pref}'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for f in os.listdir(f'{ORIG}/Rel'):
        if f.startswith(pref + '_'): shutil.copy(f'{ORIG}/Rel/{f}', tmp)
    r = subprocess.run(['python3', '/home/claude/tools/relpatch.py', tmp, f'{OUT}/Rel', ','.join('%x' % x for x in lst)], capture_output=True, text=True,
                       env=dict(os.environ, RELPREF=pref))
    print(pref, r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-500:])
salas_esl = {0x100 | x for x in st1} | {0x200 | x for x in st2}
for k in range(10):
    f = f'{ORIG}/etc/emleon{k:02d}.esl'; d = bytearray(open(f, 'rb').read()); n = 0
    for i in range(len(d) // 0x20):
        e = d[i * 0x20:(i + 1) * 0x20]
        if e[1] and struct.unpack('>H', e[0x18:0x1A])[0] in salas_esl: d[i * 0x20 + 1] = 0; n += 1
    open(f'{OUT}/etc/emleon{k:02d}.esl', 'wb').write(d); print(f'emleon{k:02d}.esl: {n} enemigos quitados')
json.dump(dict(EP={k: dict(slots=v['slots'], pos=v['pos'], ang=v['ang']) for k, v in EP.items()}, informe=informe, sin_usar=sin_usar),
          open(f'{OUT}/../montaje_H12.json', 'w'), indent=1)
