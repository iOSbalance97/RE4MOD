"""MAPA de uc_montar2 (salas UC de la mansión -> huecos de St1) y plantilla de puerta de botón (puerta 25 de r101)."""
import sys
sys.path.insert(0, '/home/claude/tools'); sys.path.insert(0, '/home/claude/re4src/tools')
import drs, re4inject as RI
MAPA = {'r102': [0x103, 0x113], 'r101': [0x102], 'r100': [0x104], 'r103': [0x112], 'r104': [0x106], 'r105': [0x107],
        'r106': [0x108], 'r107': [0x109], 'r108': [0x10a], 'r109': [0x10b], 'r111': [0x10c], 'r112': [0x10d],
        'r113': [0x10e], 'r114': [0x10f], 'r115': [0x105]}
def _plantilla():
    sig, sr, snd, body, c = RI.read_das('/home/claude/disc/ext1/files/St1/r101.das')
    e, _ = RI.parse_body(body)
    aev = [d for t, d in e if drs.tag_name(t) == 'AEV'][0]
    r = bytearray(aev[0x10 + 25 * 0x9C:0x10 + 26 * 0x9C])
    assert r[0x35] == 1 and r[0x38] == 0x8 and r[5] == 1 and r[0x6D] == 0x02
    return r
TPL = _plantilla()
