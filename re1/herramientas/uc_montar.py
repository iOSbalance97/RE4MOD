"""Monta las salas de UC en St1 de RE4 con puertas entre ellas.
- modelos/colisión: /home/claude/uc/re4/rNNN/{mod,col}
- puertas: conexiones.json (uc_conexiones.py)
- AEV nuevo por sala: solo nuestras puertas (registro de puerta copiado de r101.das, puerta 2 del pueblo)
uso: uc_montar.py conexiones.json St1_original salida_St1"""
import json, os, struct, sys
import numpy as np
sys.path.insert(0, '/home/claude/tools'); sys.path.insert(0, '/home/claude/re4src/tools'); sys.argv += []
import drs, re4inject as RI
CONX, SRC, DST = sys.argv[1:4]
# sala de UC -> salas de RE4 (St1). El vestíbulo va en r103 y r113 (las dos versiones a las que lleva la puerta norte del pueblo)
MAPA = {'r102': [0x103, 0x113], 'r101': [0x102], 'r100': [0x104], 'r103': [0x105], 'r104': [0x106], 'r105': [0x107],
        'r106': [0x108], 'r107': [0x109], 'r108': [0x10a], 'r109': [0x10b], 'r111': [0x10c], 'r112': [0x10d],
        'r113': [0x10e], 'r114': [0x10f], 'r115': [0x112]}
DESTINO = {k: v[-1] for k, v in MAPA.items()}          # al volver al vestíbulo se entra en r113

def plantilla():
    sig, sr, snd, body, c = RI.read_das(f'{SRC}/r101.das')
    e, _ = RI.parse_body(body)
    aev = [d for t, d in e if drs.tag_name(t) == 'AEV'][0]
    return bytearray(aev[0x10 + 2 * 0x9C:0x10 + 3 * 0x9C])     # puerta 2: pueblo -> granja

RADIO = 700.0
TPL = plantilla()
assert TPL[0x35] == 1 and TPL[0x6D] == 0x03

def door_rec(no, trig, dest_room, pos, ang):
    r = bytearray(TPL)
    # AREA_HIT_DATA en 0x04: be_flag, tipo (1 = XZ4, 2 = cilindro), pad; cuerpo desde 0x08
    r[4], r[5], r[6], r[7] = 1, 2, 0, 0
    struct.pack_into('>5f', r, 0x08, trig[1] - 300.0, 2600.0, RADIO, trig[0], trig[2])   # suelo, alto, radio, x, z
    r[0x1C:0x34] = bytes(0x18)                                                         # pad[6]
    r[0x36] = no
    struct.pack_into('>4f', r, 0x5C, *pos, ang)
    r[0x6C], r[0x6D], r[0x6E], r[0x6F] = 1, dest_room & 0xFF, 0, 0
    return bytes(r)

conx = json.load(open(CONX))
# llegadas: lejos de TODOS los disparadores de la sala de destino (las puertas saltan solas al pisarlas)
import pickle
fl = pickle.load(open('/tmp/fl.pkl', 'rb'))
LIBRE = 1.3                                            # m entre la llegada y cualquier disparador de esa sala
for c in conx:
    for me, m in ((c['a'], c['A']), (c['b'], c['B'])):
        trigs = np.array([q['trig'] for cc in conx for mm, q in ((cc['a'], cc['A']), (cc['b'], cc['B'])) if mm == me]) / 1000
        P = fl[me]; cen = np.array(c['centro']) / 1000; old = np.array(m['llegada']) / 1000
        dt = np.min(np.hypot(P[:, None, 0] - trigs[None, :, 0], P[:, None, 2] - trigs[None, :, 2]), 1)
        dd = np.hypot(P[:, 0] - cen[0], P[:, 2] - cen[2])
        for dy, rmax in ((0.6, 3.5), (1.5, 5.0), (2.5, 6.0)):          # escaleras: se admite subir algo
            ok = (dt > LIBRE) & (np.abs(P[:, 1] - cen[1]) < dy) & (dd < rmax)
            if ok.any(): break
        assert ok.any(), (me, c['a'], c['b'])
        j = np.where(ok)[0][np.argmin(np.abs(dd[ok] - 1.5) + 0.5 * np.hypot(*(P[ok] - old)[:, [0, 2]].T))]
        q = P[j]; v = q - cen
        m['llegada'] = [float(x * 1000) for x in q]; m['ang'] = float(np.arctan2(v[0], v[2]))
os.makedirs(DST, exist_ok=True)
resumen = []
for uc, ids in MAPA.items():
    recs = []
    for c in conx:
        for me, other, mine, theirs in ((c['a'], c['b'], c['A'], c['B']), (c['b'], c['a'], c['B'], c['A'])):
            if me != uc: continue
            recs.append(door_rec(len(recs), mine['trig'], DESTINO[other], theirs['llegada'], theirs['ang']))
            resumen.append((uc, other, DESTINO[other]))
    aev = b'AEV\0' + struct.pack('>HH8x', 0x104, len(recs)) + b''.join(recs)
    for rid in ids:
        name = f'r{rid:03x}'
        sig, snd_rec, snd, body, _ = RI.read_das(f'{SRC}/{name}.das')
        entries, rel = RI.parse_body(body)
        base = f'/home/claude/uc/re4/{uc}'
        new = {'SMD': open(f'{base}/mod/sala.smd', 'rb').read(), 'SMX': open(f'{base}/mod/sala.smx', 'rb').read(),
               'SAT': open(f'{base}/col/sala.sat', 'rb').read(), 'EAT': open(f'{base}/col/sala.eat', 'rb').read(), 'AEV': aev}
        done = set(); out = []
        for t, d in entries:
            n = drs.tag_name(t)
            if n in new and n not in done: done.add(n); out.append([t, new[n]])
            else: out.append([t, d])
        assert done == set(new), (name, done)
        nb = RI.pack_body(out, rel)
        das = RI.write_das(sig, snd_rec, snd, nb)
        open(f'{DST}/{name}.das', 'wb').write(das)
        orig = os.path.getsize(f'{SRC}/{name}.das')
        print(f'{name} <- UC {uc}: {len(recs)} puertas, descomprimido {len(nb)//1024} KB, fichero {len(das)//1024} KB (original {orig//1024} KB)')
        assert len(nb) <= 5800 * 1024, 'sala demasiado grande'
for uc in MAPA:
    trigs = [np.array(m['trig']) for c in conx for me, m in ((c['a'], c['A']), (c['b'], c['B'])) if me == uc]
    arr = [np.array(m['llegada']) for c in conx for me, m in ((c['a'], c['A']), (c['b'], c['B'])) if me == uc]
    dmin = min(np.hypot(*(a_ - t)[[0, 2]]) for a_ in arr for t in trigs)
    print(f'  {uc}: llegada más cercana a un disparador {dmin/1000:.2f} m')
    assert dmin > RADIO + 500, uc
for uc, o, d in resumen: print(f'  {uc} -> {o} (r{d:03x})')
