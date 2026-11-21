"""Monta el RE1 REmake completo dentro de RE4 (H15+): todas las salas del REmake de GameCube convertidas
(re1gc/re4/re_rNNN), con sus puertas reales (tabla de puertas de cada .dat: área, destino, llegada y giro).
 - salas de la mansión (REmake st1-st2) -> St1 de RE4; patio, residencia, cuevas y laboratorio (st3-st5) -> St2
 - r120 de RE4 (partida nueva) = puerta automática al vestíbulo
 - ids dentro de la tabla de la fase primero para las salas de paso; las de un solo acceso pueden ir a ids nuevos
uso: montar_remake.py salida_files"""
import json, os, shutil, struct, subprocess, sys
import numpy as np
sys.path.insert(0, '/home/claude/tools'); sys.path.insert(0, '/home/claude/re4src/tools')
import drs, re4inject as RI, uc_ambiente
from hmap import floors, heights
from uc_montar2_mapa import TPL

OUT = sys.argv[1]; ORIG = '/home/claude/disc/ext1/files'; R1 = '/home/claude/re1gc'
for d in ('St1', 'St2', 'Rel', 'etc'): os.makedirs(f'{OUT}/{d}', exist_ok=True)
G = json.load(open(f'{R1}/work/puertas_remake.json'))
ST = {}
for st in range(1, 6):
    for f in sorted(os.listdir(f'{R1}/files/st{st}')):
        if f.endswith('.dat'): ST[f[:4]] = st
listas = {r for r in ST if os.path.exists(f'{R1}/re4/re_{r}/v2') and os.path.exists(f'{R1}/re4/re_{r}/col/sala.sat')}
faltan = sorted(set(ST) - listas)
if faltan: print('sin convertir (fuera del montaje):', ' '.join(faltan))

# ---------------- enlaces válidos: con puerta de vuelta, entre salas convertidas
def enlaces(a):
    out = []
    for d in G[a]:
        b = d['dst']
        if b == a or b not in listas or a not in listas: continue
        if not any(e['dst'] == a for e in G[b]): continue
        out.append(d)
    return out
grado = {r: len({d['dst'] for d in enlaces(r)}) for r in listas}
# componente conectada desde el vestíbulo
INICIO = 'r106'
vistas = {INICIO}; pila = [INICIO]
while pila:
    a = pila.pop()
    for d in enlaces(a):
        if d['dst'] not in vistas: vistas.add(d['dst']); pila.append(d['dst'])
sueltas = sorted(listas - vistas)
if sueltas: print('no se llega desde el vestíbulo:', ' '.join(sueltas))

# ---------------- asignación de huecos
EN_TABLA = {1: [i for i in range(0x20)], 2: [i for i in range(46)]}     # r120 (0x20) queda para la partida nueva
EXTRA = {1: list(range(0x21, 0x60)), 2: list(range(46, 0x80))}
fase = lambda r: 1 if ST[r] <= 2 else 2
HUECO = {}
for f_ in (1, 2):
    rs = sorted([r for r in listas if fase(r) == f_], key=lambda r: (r != INICIO, -grado[r], r))
    libres = list(EN_TABLA[f_]); extra = list(EXTRA[f_])
    if f_ == 1: libres.remove(0x00); HUECO[INICIO] = (1, 0x00); rs.remove(INICIO)
    for r in rs:
        HUECO[r] = (f_, libres.pop(0)) if libres else (f_, extra.pop(0))
nuevas = sorted(r for r, (f_, i) in HUECO.items() if i not in EN_TABLA[f_])
print(f'{len(HUECO)} salas; {len(nuevas)} en ids nuevos (fuera de la tabla de la fase): {" ".join(nuevas)}')

# ---------------- colocación del vestíbulo: r120 (intro original de RE4) salta a r100 en (-109450, -515, 820) mirando a 0
ENT_H = np.array([0.0, 2030.0, 8000.0]); ANG_H = np.pi              # entrada principal del vestíbulo, mirando a la escalera
J = np.array([-109450.0, -515.0, 820.0]); GIRO = -ANG_H
_c, _s = np.cos(GIRO), np.sin(GIRO); RM = np.array([[_c, 0, _s], [0, 1, 0], [-_s, 0, _c]])
def tp(sala, p):        # punto (mm) de la sala -> mundo del juego
    p = np.asarray(p, float)
    return RM @ (p - ENT_H) + J if sala == INICIO else p
def tang(sala, a): return a + GIRO if sala == INICIO else a
def txz(sala, x, z):
    q = tp(sala, (x, 0.0, z)); return float(q[0]), float(q[2])
def ty(sala, y): return float(y + (J[1] - ENT_H[1])) if sala == INICIO else float(y)
def preparar_inicio():
    base = f'{R1}/re4/re_{INICIO}'; dst = f'{R1}/re4/re_{INICIO}_ini'
    if os.path.exists(f'{dst}/hecho'): return dst
    os.makedirs(f'{dst}/col', exist_ok=True)
    col = f'{R1}/salas/{INICIO}/colision.obj'
    esp = ','.join(str(x) for x in list(ENT_H / 1000) + list(J) + [GIRO])
    subprocess.run(['python3', '/home/claude/tools/re4room.py', f'{R1}/salas/{INICIO}/sala.obj', f'{dst}/mod', '--tex-max', '512', f'--colocar={esp}'], check=True, capture_output=True)
    L = []
    for l in open(col):
        if l.startswith('v '):
            v = np.array(l.split()[1:4], float) * 1000; v = tp(INICIO, v) / 1000; L.append(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
        else: L.append(l)
    open(f'{dst}/col/c.obj', 'w').writelines(L)
    subprocess.run(['python3', '/home/claude/tools/obj2sat.py', f'{dst}/col/c.obj', f'{dst}/col'], check=True, capture_output=True)
    open(f'{dst}/hecho', 'w').write('ok'); return dst
DIR_INICIO = preparar_inicio()

# ---------------- puertas
def hit_xz4(p, q):
    x, z = q
    (x0, z0), (x1, z1), (x2, z2), (x3, z3) = p
    if (x3 - x0) * (z - z0) > (z3 - z0) * (x - x0) or (x1 - x0) * (z - z0) < (z1 - z0) * (x - x0): return False
    if (x3 - x2) * (z - z2) < (z3 - z2) * (x - x2) or (x1 - x2) * (z - z2) > (z1 - z2) * (x - x2): return False
    return True
TFL = {}
def hay_suelo(sala, x0, z0, x1, z1, piso):
    if sala not in TFL: TFL[sala] = floors(f'{R1}/re4/re_{sala}/col/colision.obj')
    for x in np.linspace(x0, x1, 7):
        for z in np.linspace(z0, z1, 7):
            h = heights(TFL[sala], x / 1000, z / 1000) * 1000
            if len(h) and np.abs(h - piso).min() < 500: return True
    return False
def area_de(quad, piso, sala=None):
    P = np.array(quad, float).reshape(4, 2); c = P.mean(0)
    # ampliar hasta que el área pise suelo de colisión (si no, no se podría pulsar)
    ext = 300.0
    if sala:
        for e_ in (300.0, 600.0, 1000.0, 1500.0, 2200.0, 3000.0):
            ext = e_; lo = P.min(0) - e_; hi = P.max(0) + e_
            if hay_suelo(sala, lo[0], lo[1], hi[0], hi[1], piso): break
        if ext > 300:
            lo = P.min(0) - ext; hi = P.max(0) + ext
            P = np.array([lo, [hi[0], lo[1]], hi, [lo[0], hi[1]]])
    P = c + (P - c) * (1 + 300.0 / max(np.linalg.norm(P - c, axis=1).max(), 1.0))
    pts = [tuple(map(float, p)) for p in P]
    if not hit_xz4(pts, tuple(c)): pts = pts[::-1]
    if not hit_xz4(pts, tuple(c)):
        # cuadrilátero raro: caja alineada
        x0, z0 = P.min(0); x1, z1 = P.max(0); pts = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
        if not hit_xz4(pts, tuple(c)): pts = pts[::-1]
    if sala == INICIO:
        pts = [txz(sala, x, z) for x, z in pts]
        if not hit_xz4(pts, txz(sala, *c)): pts = pts[::-1]
        piso = ty(sala, piso)
    return dict(floor=float(piso - 400.0), height=3200.0, pts=pts)
def door_rec(no, area, dest, pos, ang):
    rr = bytearray(TPL)
    rr[4], rr[5], rr[6], rr[7] = 1, 1, 0, 0
    struct.pack_into('>3f', rr, 0x08, area['floor'], area['height'], 0.0)
    for k, (x, z) in enumerate(area['pts']): struct.pack_into('>2f', rr, 0x14 + 8 * k, x, z)
    rr[0x36] = no
    struct.pack_into('>4f', rr, 0x5C, *pos, ang)
    rr[0x6C], rr[0x6D], rr[0x6E], rr[0x6F] = dest[0], dest[1], 0, 0
    return bytes(rr)
AEVS = {}; informe_p = []
for a in sorted(HUECO):
    for d in enlaces(a):
        b = d['dst']
        if b not in HUECO: continue
        c = np.array(d['quad'], float).reshape(4, 2).mean(0)
        # altura del suelo junto a esta puerta: la llegada de la puerta de vuelta (b -> a) más cercana
        vuelta = [e for e in G[b] if e['dst'] == a]
        e = min(vuelta, key=lambda e: np.hypot(e['llegada'][0] - c[0], e['llegada'][2] - c[1]))
        piso = e['llegada'][1]
        x, y, z, ang = d['llegada']
        if b not in TFL: TFL[b] = floors(f'{R1}/re4/re_{b}/col/colision.obj')
        h = heights(TFL[b], x / 1000, z / 1000) * 1000
        if not len(h) or np.abs(h - y).min() > 400:
            mejor = None
            for rr in np.arange(200, 3001, 200):
                for t in np.linspace(0, 2 * np.pi, 16, endpoint=False):
                    xx, zz = x + rr * np.sin(t), z + rr * np.cos(t); hh = heights(TFL[b], xx / 1000, zz / 1000) * 1000
                    if len(hh):
                        k_ = int(np.argmin(np.abs(hh - y)))
                        if abs(hh[k_] - y) < 1500: mejor = (xx, float(hh[k_]), zz); break
                if mejor: break
            if mejor: print(f'  llegada {a}->{b} movida a suelo: {np.round(mejor)}'); x, y, z = mejor
        q_ = tp(b, (x, y, z))
        AEVS.setdefault(a, []).append((area_de(d['quad'], piso, a), HUECO[b], (float(q_[0]), float(q_[1]), float(q_[2])), float(tang(b, ang)), f'{a} -> {b}'))
        informe_p.append((a, b))
print('puertas:', len(informe_p))

# ---------------- montaje de cada sala
CAM_VACIO = open('/home/claude/tools/cam_vacio.bin', 'rb').read()
BASE = {1: f'{ORIG}/St1/r10d.das', 2: f'{ORIG}/St2/r22b.das'}
def montar(r):
    f_, i = HUECO[r]; name = f'r{f_}{i:02x}'
    src = f'{ORIG}/St{f_}/{name}.das'
    sig, snd_rec, snd, body, _ = RI.read_das(BASE[2])          # base ligera (r22b: solo escenario) para no gastar memoria
    entries, rel = RI.parse_body(body)
    recs = [door_rec(k, *x[:4]) for k, x in enumerate(AEVS.get(r, []))]
    aev = b'AEV\0' + struct.pack('>HH8x', 0x104, len(recs)) + b''.join(recs)
    base = DIR_INICIO if r == INICIO else f'{R1}/re4/re_{r}'
    new = {'SMD': open(f'{base}/mod/sala.smd', 'rb').read(), 'SMX': open(f'{base}/mod/sala.smx', 'rb').read(),
           'SAT': open(f'{base}/col/sala.sat', 'rb').read(), 'EAT': open(f'{base}/col/sala.eat', 'rb').read(), 'AEV': aev,
           'CAM': CAM_VACIO}
    amb, nl, nluz = uc_ambiente.ambiente('r22b', [], [], horneada=True); new.update(amb)
    done = set(); out = []
    for t, d in entries:
        n = drs.tag_name(t)
        if n in new and n not in done: done.add(n); out.append([t, new[n]])
        elif n in ('FCV', 'SEQ', 'TEX'): out.append([b'x' + t[1:], bytes(32)])
        elif n == 'ITA': out.append([b'x' + t[1:], d])
        else: out.append([t, d])
    for n in new:
        if n not in done: out.append([n.encode() + b'\0', new[n]]); done.add(n)
    nb = RI.pack_body(out, rel); das = RI.write_das(sig, snd_rec, snd, nb)
    open(f'{OUT}/St{f_}/{name}.das', 'wb').write(das)
    return name, len(recs), len(nb), len(das)
import concurrent.futures as cf
informe = []
with cf.ProcessPoolExecutor(max_workers=int(os.environ.get('HILOS', 4))) as ex:
    fut = {ex.submit(montar, r): r for r in sorted(HUECO)}
    for fu in cf.as_completed(fut):
        r = fut[fu]; name, nd, nb, nd_ = fu.result()
        informe.append((r, name, nd, nb, nd_))
        print(f'{name} <- {r}  puertas {nd:2d}  descomprimido {nb/1e6:.2f} MB  fichero {nd_/1e6:.2f} MB', flush=True)

# r120 queda original: película, intro en el coche y salto a r100 (el vestíbulo, colocado para recibirlo)
ENTRADA = tuple(J.tolist())

# ---------------- scripts fuera (Rel) y enemigos fuera (ESL)
for pref, f_ in (('st1', 1), ('st2', 2)):
    lst = sorted(EN_TABLA[f_])
    tmp = f'/tmp/rel_{pref}'; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    for f in os.listdir(f'{ORIG}/Rel'):
        if f.startswith(pref + '_'): shutil.copy(f'{ORIG}/Rel/{f}', tmp)
    rr = subprocess.run(['python3', '/home/claude/tools/relpatch.py', tmp, f'{OUT}/Rel', ','.join('%x' % x for x in lst)], capture_output=True, text=True,
                        env=dict(os.environ, RELPREF=pref))
    print(pref, rr.stdout.strip().splitlines()[-1] if rr.stdout else rr.stderr[-500:])
for k in range(10):
    f = f'{ORIG}/etc/emleon{k:02d}.esl'; d = bytearray(open(f, 'rb').read()); n = 0
    for i in range(len(d) // 0x20):
        e = d[i * 0x20:(i + 1) * 0x20]
        if e[1] and struct.unpack('>H', e[0x18:0x1A])[0] >> 8 in (1, 2): d[i * 0x20 + 1] = 0; n += 1
    open(f'{OUT}/etc/emleon{k:02d}.esl', 'wb').write(d); print(f'emleon{k:02d}.esl: {n} enemigos quitados')
json.dump(dict(HUECO={r: list(v) for r, v in HUECO.items()}, puertas=AEVS and {a: [x[4] for x in v] for a, v in AEVS.items()},
               nuevas=nuevas, informe=informe, entrada=ENTRADA), open(f'{OUT}/../montaje_remake.json', 'w'), indent=1)
open(f'{OUT}/../FIN_MONTAJE', 'w').write('ok')
