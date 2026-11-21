"""Ambiente de la mansión para una sala de RE4: oscuridad, linterna, fuego.
Devuelve entradas nuevas para el .das (LIT, EAR, ETS, ETM) a partir del LIT original de la sala.
- LIT: todos los cortes iguales (la sala elige corte por zonas): ambiente casi negro, niebla negra; luces:
  las de Leon de la sala original (ParentType 1) más tenues; linterna = foco (tipo 3) pegado a Leon (padre 1, nº 0)
  a la altura del pecho mirando hacia delante; una luz naranja con parpadeo (tipo 2, id 1) pegada a cada antorcha
  (ParentType 3 = objeto etc de la sala); luz cálida suave en cada lámpara.
- ETM/ETS: antorcha TAIMATU01 (etc 0x14) con el modelo colapsado (solo se ve la llama) en cada punta de vela.
- EAR: 32 áreas de efectos (nº 0..31) que lo cubren todo, para que ningún efecto quede oculto."""
import glob, struct
import numpy as np

SCAN = '/home/claude/scan'
MAX_LLAMAS, MAX_LAMPARAS = 16, 10

def lit_parse(d):
    cn, ver, mx = struct.unpack('>HBB', d[:4]); offs = struct.unpack(f'>{cn}I', d[4:4 + 4 * cn]); cuts = []
    for o in offs:
        env = d[o:o + 0x104]; n = struct.unpack('>I', env[4:8])[0]
        cuts.append((env, [d[o + 0x104 + i * 0x12C:o + 0x104 + (i + 1) * 0x12C] for i in range(n)]))
    return cn, ver, mx, cuts

def _plantilla_antorcha():
    d = open(sorted(glob.glob(f'{SCAN}/r11b/*_LIT.bin'))[0], 'rb').read()
    for l in lit_parse(d)[3][0][1]:
        if l[0x1C] == 3 and l[1] == 2 and l[2] == 1: return bytearray(l)
    raise SystemExit('sin plantilla de luz de antorcha')
ANT = _plantilla_antorcha()

def reparto(P, n):
    """hasta n puntos repartidos (muestreo del punto más lejano)"""
    P = np.asarray(P, float)
    if len(P) <= n: return P
    sel = [0]; d = np.linalg.norm(P - P[0], axis=1)
    while len(sel) < n:
        i = int(np.argmax(d)); sel.append(i); d = np.minimum(d, np.linalg.norm(P - P[i], axis=1))
    return P[sel]

def luz(base, tipo, id_, mask, pos, radio, col, inten, padre, no, flick=0):
    l = bytearray(base)
    l[0], l[1], l[2], l[3] = 7, tipo, id_, mask
    struct.pack_into('>3ff', l, 0x04, *pos, radio)
    l[0x14:0x18] = bytes(col)
    struct.pack_into('>f', l, 0x18, inten)
    l[0x1C] = padre
    struct.pack_into('>I', l, 0x20, no)
    if id_ == 1:
        l[0x6C:0x70] = bytes(col); l[0x70] = flick & 0xFF
    return bytes(l)

def ambiente(rid_orig, llamas, lamparas, horneada=False):
    """rid_orig: nombre de la sala original de RE4 (rNNN) cuyo LIT sirve de base"""
    lits = sorted(glob.glob(f'{SCAN}/{rid_orig}/*_LIT.bin'))
    d = open(lits[0], 'rb').read()
    cn, ver, mx, cuts = lit_parse(d)
    env = bytearray(cuts[0][0])
    env[0:4] = bytes((0x1A, 0x18, 0x1A, 0x80))                     # ambiente del escenario: oscuro, pero se intuye la sala
    struct.pack_into('>2f', env, 0x0C, 4000.0, 30000.0)              # niebla: de 4 a 30 m
    env[0x14:0x18] = bytes((0, 0, 0, 0x80))                          # niebla negra
    env[0xFC:0x100] = bytes((0x30, 0x2C, 0x2C, 0x80))               # ambiente de personajes (se ve a Leon)
    if horneada:                                                     # texturas con la luz ya pintada (fondos del REmake): que se vean tal cual
        env[0:4] = bytes((0x80, 0x80, 0x80, 0x80)); struct.pack_into('>2f', env, 0x0C, 8000.0, 40000.0); llamas = []
    luces = []
    # luces de Leon de la sala original, más tenues
    leon = [l for l in cuts[0][1] if l[0x1C] == 1 and struct.unpack('>I', l[0x20:0x24])[0] == 0]
    for l in leon[:3]:
        l = bytearray(l); struct.pack_into('>f', l, 0x18, struct.unpack('>f', l[0x18:0x1C])[0] * 0.5); luces.append(bytes(l))
    # linterna: foco pegado a Leon (parte 0), delante del pecho, mirando al frente y un poco hacia abajo
    base = leon[0] if leon else ANT
    lin = bytearray(luz(base, 3, 0, 0x57, (0.0, 1250.0, 250.0), 16000.0, (0xFF, 0xF2, 0xD8, 0x80), 1.6, 1, 0))
    n_ = np.array([0.0, -0.12, 1.0]); n_ /= np.linalg.norm(n_)
    struct.pack_into('>3fff', lin, 0x2C, *n_, 28.0, 2500.0)          # normal, ángulo del cono (grados), borde
    luces.append(bytes(lin))
    # fuego: antorchas invisibles en las puntas de las velas + su luz
    L = reparto(llamas, MAX_LLAMAS) if len(llamas) else np.zeros((0, 3))
    ets = bytearray(struct.pack('>H', len(L)) + bytes(14))
    for i, p in enumerate(L):
        e = bytearray(0x28)
        struct.pack_into('>HH3f3f3f', e, 0, 0x14, i, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, p[0], p[1] - 300.0, p[2])
        ets += e
    # luz del fuego: una por grupo de llamas (una araña o un candelabro = una luz), alcance corto
    usadas = []
    for i, p in enumerate(L):
        if any(np.linalg.norm(np.subtract(p, L[j])) < 1500.0 for j in usadas): continue
        usadas.append(i)
        n_g = sum(1 for q in L if np.linalg.norm(np.subtract(p, q)) < 1500.0)
        luces.append(luz(ANT, 2, 1, 0x57, (0.0, 300.0, 0.0), 3200.0 + 300.0 * min(n_g, 4), (0xE0, 0x98, 0x58, 0x80), 0.55 + 0.05 * min(n_g, 4), 3, i, flick=0x10))
    for p in reparto(lamparas, MAX_LAMPARAS) if len(lamparas) else []:
        luces.append(luz(ANT, 2, 1, 0x57, tuple(p), 3500.0, (0xD0, 0xB8, 0x90, 0x80), 0.5, 0, 0, flick=0x04))
    luces = luces[:32]
    struct.pack_into('>I', env, 4, len(luces))
    corte = bytes(env) + b''.join(luces)
    hdr = struct.pack('>HBB', cn, ver, len(luces))
    o0 = 4 + 4 * cn
    lit = hdr + b''.join(struct.pack('>I', o0 + i * len(corte)) for i in range(cn)) + corte * cn
    # áreas de efectos: 32 que cubren todo
    ear = bytearray(struct.pack('>II8x', 32, 0))
    for i in range(32):
        e = bytearray(0x98)
        e[0], e[1], e[2] = i, 1, i
        e[4], e[5] = 1, 1
        struct.pack_into('>3f', e, 0x08, -100000.0, 200000.0, 0.0)
        for k, (x, z) in enumerate(((-600000, -600000), (-600000, 600000), (600000, 600000), (600000, -600000))):
            struct.pack_into('>2f', e, 0x14 + 8 * k, x, z)
        struct.pack_into('>I', e, 0x34, 1)
        ear += e
    # ETM con la antorcha invisible
    # entradas copiadas del ETM de r10c con su cabecera (tamaño, tipo...); el modelo, colapsado
    etm = bytearray(struct.pack('>I', 3) + bytes(0x1C))
    for name in ('et1400.bin', 'et1400.tpl', 'et14.eff'):
        raw = bytearray(open(f'/home/claude/fuego/raw_{name}', 'rb').read())
        if name == 'et1400.bin':
            inv = open('/home/claude/fuego/et1400_invisible.bin', 'rb').read(); assert len(inv) <= len(raw) - 0x40
            raw[0x40:0x40 + len(inv)] = inv
        etm += raw
    return dict(LIT=bytes(lit), EAR=bytes(ear), ETS=bytes(ets), ETM=bytes(etm)), len(L), len(luces)

if __name__ == '__main__':
    import json, sys
    lu = json.load(open('/home/claude/uc/luces.json'))
    e, nl, nluz = ambiente('r103', lu['r102']['llamas'], lu['r102']['lamparas'])
    print({k: len(v) for k, v in e.items()}, 'llamas', nl, 'luces', nluz)
    cn, ver, mx, cuts = lit_parse(e['LIT']); print('releído: cortes', cn, 'versión', ver, 'luces', len(cuts[0][1]))
