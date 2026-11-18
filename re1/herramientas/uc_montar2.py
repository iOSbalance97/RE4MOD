"""Monta las salas de UC en St1 de RE4 (H07+).
- modelo /home/claude/uc/re4/rNNN/mod (re4room desde uc/m2: sala + objetos + lo que se ve por las puertas)
- colisión /home/claude/uc/re4/rNNN/col (ucol2re4: colisión de personajes de UC)
- AEV nuevo: solo puertas de botón (plantilla: puerta 25 de r101, trg 0x8, área XZ4) desde conexiones2.json
- datos del RE4 original que ya no se usan se anulan (etiqueta renombrada, el juego no los encuentra y sigue):
  ITA objetos recogibles, ETS/ETM objetos sueltos (barriles...), ESE sonidos, EAR/SAR áreas de efecto/luz, CAM cámaras,
  FSE suelos, EFF efectos, FCV/SEQ/BIN/TPL datos de cinemáticas (solo los usaba el código de la sala, ya vaciado)
uso: uc_montar2.py conexiones2.json St1_original salida_St1"""
import json, os, struct, sys
import numpy as np
sys.path.insert(0, '/home/claude/tools'); sys.path.insert(0, '/home/claude/re4src/tools')
import drs, re4inject as RI
CONX, SRC, DST = sys.argv[1:4]
MAPA = {'r102': [0x103, 0x113], 'r101': [0x102], 'r100': [0x104], 'r103': [0x105], 'r104': [0x106], 'r105': [0x107],
        'r106': [0x108], 'r107': [0x109], 'r108': [0x10a], 'r109': [0x10b], 'r111': [0x10c], 'r112': [0x10d],
        'r113': [0x10e], 'r114': [0x10f], 'r115': [0x112]}
DESTINO = {k: v[-1] for k, v in MAPA.items()}
PUEBLO = {0x103: 0x101, 0x113: 0x111}                       # puerta principal del vestíbulo: vuelta al pueblo
PUEBLO_POS = (39371.68359375, 3201.473388671875, -26666.533203125, -1.503808856010437)
ANULAR = {'ITA', 'ETS', 'ESE', 'EAR', 'SAR', 'CAM', 'FSE'}           # se renombran (datos intactos, son pequeños)
VACIAR = {'EFF', 'ETM', 'FCV', 'SEQ', 'BIN', 'TPL'}                  # se renombran y se dejan en 32 bytes

def plantilla():
    sig, sr, snd, body, c = RI.read_das(f'{SRC}/r101.das')
    e, _ = RI.parse_body(body)
    aev = [d for t, d in e if drs.tag_name(t) == 'AEV'][0]
    r = bytearray(aev[0x10 + 25 * 0x9C:0x10 + 26 * 0x9C])
    assert r[0x35] == 1 and r[0x38] == 0x8 and r[5] == 1 and r[0x6D] == 0x02
    return r
TPL = plantilla()

def door_rec(no, area, dest_room, pos, ang):
    r = bytearray(TPL)
    r[4], r[5], r[6], r[7] = 1, 1, 0, 0                               # AREA_HIT_DATA: en uso, XZ4
    struct.pack_into('>3f', r, 0x08, area['floor'], area['height'], 0.0)
    for k, (x, z) in enumerate(area['pts']): struct.pack_into('>2f', r, 0x14 + 8 * k, x, z)
    r[0x36] = no
    struct.pack_into('>4f', r, 0x5C, *pos, ang)
    r[0x6C], r[0x6D], r[0x6E], r[0x6F] = 1, dest_room & 0xFF, 0, 0
    return bytes(r)

conx = json.load(open(CONX))
os.makedirs(DST, exist_ok=True)
resumen = []
for uc, ids in MAPA.items():
    for rid in ids:
        recs = []
        for q in conx:
            for me, other, area, lleg in ((q['a'], q['b'], 'area_a', 'llegada_b'), (q['b'], q['a'], 'area_b', 'llegada_a')):
                if me != uc: continue
                if other == 'PUEBLO':
                    recs.append(door_rec(len(recs), q[area], PUEBLO[rid], PUEBLO_POS[:3], PUEBLO_POS[3])); dest = PUEBLO[rid]
                else:
                    L = q[lleg]; recs.append(door_rec(len(recs), q[area], DESTINO[other], L['pos'], L['ang'])); dest = DESTINO[other]
                resumen.append((f'r{rid:03x}', uc, other, f'r{dest:03x}'))
        aev = b'AEV\0' + struct.pack('>HH8x', 0x104, len(recs)) + b''.join(recs)
        name = f'r{rid:03x}'
        sig, snd_rec, snd, body, _ = RI.read_das(f'{SRC}/{name}.das')
        entries, rel = RI.parse_body(body)
        base = f'/home/claude/uc/re4/{uc}'
        new = {'SMD': open(f'{base}/mod/sala.smd', 'rb').read(), 'SMX': open(f'{base}/mod/sala.smx', 'rb').read(),
               'SAT': open(f'{base}/col/sala.sat', 'rb').read(), 'EAT': open(f'{base}/col/sala.eat', 'rb').read(), 'AEV': aev}
        done = set(); out = []; anul = []
        for t, d in entries:
            n = drs.tag_name(t)
            if n in new and n not in done: done.add(n); out.append([t, new[n]])
            elif n in VACIAR: out.append([b'x' + t[1:], bytes(32)]); anul.append(n)
            elif n in ANULAR: out.append([b'x' + t[1:], d]); anul.append(n)
            else: out.append([t, d])
        assert done == set(new), (name, done)
        nb = RI.pack_body(out, rel)
        das = RI.write_das(sig, snd_rec, snd, nb)
        open(f'{DST}/{name}.das', 'wb').write(das)
        print(f'{name} <- UC {uc}: {len(recs)} puertas, descomprimido {len(nb)/1e6:.2f} MB, fichero {len(das)/1e6:.2f} MB, '
              f'anulados {len(anul)} ({",".join(sorted(set(anul)))})')
        assert len(nb) <= 5_300_000, 'sala demasiado grande'
for x in resumen: print('  %s (%s) -> %s = %s' % x)
