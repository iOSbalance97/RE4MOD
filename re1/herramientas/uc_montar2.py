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
import uc_ambiente
LUCES = json.load(open('/home/claude/uc/luces.json'))
CONX, SRC, DST = sys.argv[1:4]
MAPA = {'r102': [0x103, 0x113], 'r101': [0x102], 'r100': [0x104], 'r103': [0x112], 'r104': [0x106], 'r105': [0x107],
        'r106': [0x108], 'r107': [0x109], 'r108': [0x10a], 'r109': [0x10b], 'r111': [0x10c], 'r112': [0x10d],
        'r113': [0x10e], 'r114': [0x10f], 'r115': [0x105]}
DESTINO = {k: v[-1] for k, v in MAPA.items()}
PUEBLO = {0x103: 0x101, 0x113: 0x111}                       # puerta principal del vestíbulo: vuelta al pueblo
PUEBLO_POS = (39371.68359375, 3201.473388671875, -26666.533203125, -1.503808856010437)
ANULAR = {'ITA'}                                              # objetos recogibles y sueltos (se renombran)
VACIAR = {'FCV', 'SEQ'}                                              # cinemáticas: solo las usa el código de la sala
# H07-H09 anulaban también CAM/EAR/SAR/ESE/FSE/EFF/ETM/BIN/TPL: pantalla gris. Se vuelve a lo de H06 (se conservan).

def plantilla():
    sig, sr, snd, body, c = RI.read_das(f'{SRC}/r101.das')
    e, _ = RI.parse_body(body)
    aev = [d for t, d in e if drs.tag_name(t) == 'AEV'][0]
    r = bytearray(aev[0x10 + 25 * 0x9C:0x10 + 26 * 0x9C])
    assert r[0x35] == 1 and r[0x38] == 0x8 and r[5] == 1 and r[0x6D] == 0x02
    return r
TPL = plantilla()

ENTRADA = (-47609.0, 12.0, 7084.0, 1.889)        # donde deja la puerta norte del pueblo, dentro del vestíbulo

def hit_xz4(p, q):
    x, z = q
    (x0, z0), (x1, z1), (x2, z2), (x3, z3) = p
    if (x3 - x0) * (z - z0) > (z3 - z0) * (x - x0) or (x1 - x0) * (z - z0) < (z1 - z0) * (x - x0): return False
    if (x3 - x2) * (z - z2) < (z3 - z2) * (x - x2) or (x1 - x2) * (z - z2) > (z1 - z2) * (x - x2): return False
    return True

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
grandes = []
for uc, ids in MAPA.items():
    for rid in ids:
        recs = []; name = f'r{rid:03x}'
        for q in conx:
            for me, other, area, lleg in ((q['a'], q['b'], 'area_a', 'llegada_b'), (q['b'], q['a'], 'area_b', 'llegada_a')):
                if me != uc: continue
                if other == 'PUEBLO':
                    recs.append(door_rec(len(recs), q[area], PUEBLO[rid], PUEBLO_POS[:3], PUEBLO_POS[3])); dest = PUEBLO[rid]
                else:
                    L = q[lleg]; recs.append(door_rec(len(recs), q[area], DESTINO[other], L['pos'], L['ang'])); dest = DESTINO[other]
                resumen.append((f'r{rid:03x}', uc, other, f'r{dest:03x}'))
        if uc == 'r102':
            # rescate: al cargar una partida guardada en la granja (r103/r113 originales) se aparece fuera del vestíbulo;
            # cuatro franjas alrededor de él (todo lo de fuera) llevan con el botón a la entrada del vestíbulo
            X0, X1, Z0, Z1 = -51450.0, -30930.0, -4950.0, 14910.0
            for xa, xb, za, zb in ((-120000, X0, -100000, 80000), (X1, 60000, -100000, 80000), (X0, X1, -100000, Z0), (X0, X1, Z1, 80000)):
                pts = [(xa, za), (xb, za), (xb, zb), (xa, zb)]
                if not hit_xz4(pts, ((xa + xb) / 2, (za + zb) / 2)): pts = pts[::-1]
                assert hit_xz4(pts, ((xa + xb) / 2, (za + zb) / 2))
                recs.append(door_rec(len(recs), dict(floor=-3000.0, height=12000.0, pts=pts), rid, ENTRADA[:3], ENTRADA[3]))
                resumen.append((name, uc, 'FUERA (rescate)', name))
            assert not any(hit_xz4(p_, ENTRADA[0::2][:2]) for p_ in [])
        aev = b'AEV\0' + struct.pack('>HH8x', 0x104, len(recs)) + b''.join(recs)
        sig, snd_rec, snd, body, _ = RI.read_das(f'{SRC}/{name}.das')
        entries, rel = RI.parse_body(body)
        base = f'/home/claude/uc/re4/{uc}'
        new = {'SMD': open(f'{base}/mod/sala.smd', 'rb').read(), 'SMX': open(f'{base}/mod/sala.smx', 'rb').read(),
               'SAT': open(f'{base}/col/sala.sat', 'rb').read(), 'EAT': open(f'{base}/col/sala.eat', 'rb').read(), 'AEV': aev}
        amb, n_llamas, n_luces = uc_ambiente.ambiente(name, LUCES[uc]['llamas'], LUCES[uc]['lamparas'])
        new.update(amb)
        done = set(); out = []; anul = []
        for t, d in entries:
            n = drs.tag_name(t)
            if n in new and n not in done: done.add(n); out.append([t, new[n]])
            elif n in VACIAR: out.append([b'x' + t[1:], bytes(32)]); anul.append(n)
            elif n in ANULAR: out.append([b'x' + t[1:], d]); anul.append(n)
            else: out.append([t, d])
        for n in ('EAR', 'ETS', 'ETM'):                      # la sala original puede no tenerlas: se añaden
            if n not in done: out.append([n.encode() + b'\0', new[n]]); done.add(n)
        assert done == set(new), (name, set(new) - done)
        nb = RI.pack_body(out, rel)
        das = RI.write_das(sig, snd_rec, snd, nb)
        open(f'{DST}/{name}.das', 'wb').write(das)
        print(f'{name} <- UC {uc}: {n_llamas} llamas, {n_luces} luces, {len(recs)} puertas, descomprimido {len(nb)/1e6:.2f} MB, fichero {len(das)/1e6:.2f} MB, '
              f'anulados {len(anul)} ({",".join(sorted(set(anul)))})')
        if len(nb) > len(body): print(f'   ¡{name} MAYOR que la original ({len(body)/1e6:.2f} MB)!'); grandes.append(uc)
# r120: primera sala de una partida nueva -> puerta automática (trg 2, como la puerta 2 del pueblo) que cubre
# toda la sala y lleva a la entrada del vestíbulo (r103). Sus scripts se vacían en los Rel (relpatch) y sus
# enemigos en el ESL.
def puerta_auto():
    sig, sr, snd, body, c = RI.read_das(f'{SRC}/r101.das')
    e, _ = RI.parse_body(body)
    aev = [d for t, d in e if drs.tag_name(t) == 'AEV'][0]
    r = bytearray(aev[0x10 + 2 * 0x9C:0x10 + 3 * 0x9C]); assert r[0x38] == 2
    r[4], r[5] = 1, 1
    struct.pack_into('>3f', r, 0x08, -100000.0, 200000.0, 0.0)
    for k, (x, z) in enumerate(((-900000, -900000), (900000, -900000), (900000, 900000), (-900000, 900000))):
        struct.pack_into('>2f', r, 0x14 + 8 * k, x, z)
    pts = [struct.unpack('>2f', r[0x14 + 8 * k:0x1C + 8 * k]) for k in range(4)]
    if not hit_xz4(pts, (0.0, 0.0)):
        for k, (x, z) in enumerate(pts[::-1]): struct.pack_into('>2f', r, 0x14 + 8 * k, x, z)
    assert hit_xz4([struct.unpack('>2f', r[0x14 + 8 * k:0x1C + 8 * k]) for k in range(4)], (0.0, 0.0))
    r[0x36] = 0
    r[0x38] = 1                                   # trg 1: salta mientras Leon está dentro (sin pulsar nada)
    struct.pack_into('>4f', r, 0x5C, *ENTRADA)
    r[0x6C], r[0x6D], r[0x6E], r[0x6F] = 1, 0x03, 0, 0
    return b'AEV\0' + struct.pack('>HH8x', 0x104, 1) + bytes(r)
sig, snd_rec, snd, body, _ = RI.read_das(f'{SRC}/r120.das')
entries, rel = RI.parse_body(body)
out = [[t, d] for t, d in entries if drs.tag_name(t) != 'AEV'] + [[b'AEV\0', puerta_auto()]]
nb = RI.pack_body(out, rel); das = RI.write_das(sig, snd_rec, snd, nb)
open(f'{DST}/r120.das', 'wb').write(das)
print(f'r120 (partida nueva): puerta automática al vestíbulo, descomprimido {len(nb)/1e6:.2f} MB (original {len(body)/1e6:.2f})')
for x in resumen: print('  %s (%s) -> %s = %s' % x)
print('MAYORES QUE LA ORIGINAL:', sorted(set(grandes)))
