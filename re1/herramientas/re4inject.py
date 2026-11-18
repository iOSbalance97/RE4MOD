"""Mete una sala nueva (modelos + colisión) en una sala existente de RE4 GameCube.

Entrada: el rNNN.das original de la sala que se va a sustituir (sacado de la ISO), la carpeta
generada por re4room.py (sala.smd, sala.smx) y la de re4col.py (sala.sat, sala.eat).

Dos modos:
  das     : los modelos van dentro del propio rNNN.das (cabe solo la versión ligera: el juego lee
            el .das entero en un búfer de 0x142800 bytes, ~1,26 MB comprimido).
  bloques : los modelos van en un fichero aparte rNNN_00.dat (sin comprimir, cargado por el
            sistema de bloques del juego) y el .das lleva un SMD de huecos, un BLK con un único
            área que cubre toda la sala, y la colisión.

En los dos se sustituyen SAT, EAT y SMX; el resto de la sala (cámaras, luces, enemigos, puertas,
sonido) se conserva tal cual.

uso: re4inject.py rNNN.das carpeta_modelos carpeta_colision salida_dir [--modo das|bloques]
"""
import argparse
import os
import struct
import sys

sys.path.insert(0, '/home/claude/re4src/tools')
sys.path.insert(0, '/home/claude/re4src/tools/motion')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drs       # noqa: E402
import yz2       # noqa: E402
import yz2enc    # noqa: E402

READ_BUFF = 0x142800


def tag4(s):
    return s.encode('ascii').ljust(4, b'\0')


def pad32(b):
    return bytes(b) + b'\0' * (drs.align(len(b)) - len(b))


def read_das(path):
    d = open(path, 'rb').read()
    sig, recs = drs.read_records(d)
    body_rec, snd_rec = recs
    if yz2.is_yz2(d, drs.TABLE_SIZE):
        body, _, _ = yz2.decode(d, drs.TABLE_SIZE)
        compressed = True
    else:
        body = d[drs.TABLE_SIZE:drs.TABLE_SIZE + body_rec[1]]
        compressed = False
    snd = b'' if snd_rec[0] == drs.EMPTY else d[snd_rec[3]:snd_rec[3] + snd_rec[1]]
    return sig, snd_rec, snd, bytes(body), compressed


def parse_body(body):
    count, rel_offset = struct.unpack_from('>2I', body, 0)
    ofs = struct.unpack_from(f'>{count}I', body, 16)
    tags = [body[16 + 4 * count + 4 * i:][:4] for i in range(count)]
    end_all = rel_offset or len(body)
    entries = []
    for i in range(count):
        end = ofs[i + 1] if i + 1 < count else end_all
        entries.append([tags[i], body[ofs[i]:end]])
    rel = body[rel_offset:] if rel_offset else None
    return entries, rel


def pack_body(entries, rel=None):
    count = len(entries)
    hdr_end = 16 + 8 * count
    off = drs.align(hdr_end); offsets = []
    for _, data in entries:
        offsets.append(off); off += len(pad32(data))
    out = bytearray(struct.pack('>4I', count, off if rel is not None else 0, 0, 0))
    out += struct.pack(f'>{count}I', *offsets)
    for t, _ in entries: out += t
    out += b'\0' * (offsets[0] - len(out))
    for _, data in entries: out += pad32(data)
    if rel is not None: out += rel
    return bytes(out)


def write_das(sig, snd_rec, snd, body):
    packed = yz2enc.compress(body)
    assert yz2enc.verify(packed, body)
    packed = pad32(packed)
    if snd:
        snd_rec = (snd_rec[0], len(snd), 0, drs.TABLE_SIZE + len(packed)) + tuple(snd_rec[4:])
    else:
        snd_rec = (drs.EMPTY, 0, 0, drs.TABLE_SIZE + len(packed), 0, 0, 0, 0)
    return bytes(drs.write_records(sig, [(0, len(packed), 0, drs.TABLE_SIZE, 0, 0, 0, 0), snd_rec]) + packed + snd)


def dummy_smd(n_works):
    """SMD sin modelos: reserva n huecos de objeto (WorkNo 0xFF = no se crea nada)."""
    head = 0x10 + 0x48 * n_works
    tbl = drs.align(head)
    out = bytearray(tbl + 0x20)
    struct.pack_into('>BBHIII', out, 0, 0x20, 0, n_works, tbl, tbl + 4, tbl + 8)
    for i in range(n_works):
        o = 0x10 + 0x48 * i
        struct.pack_into('>9f4BfI', out, o, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0xFF, 0xFF, 0.0, 0)
    return bytes(out)


def blk_one_area(size_mm=200000.0):
    """BLK: 1 bloque, 1 área (prisma XZ enorme), conexión: bloque 0 en MRAM."""
    out = bytearray(0xC0)
    out[0:4] = b'BLK\0'
    struct.pack_into('>HBBHHIII', out, 4, 0x100, 0, 1, 1, 1, 0x20, 0x40, 0x80)
    struct.pack_into('>B3x8b', out, 0x20, 1, *([-1] * 8))
    h = size_mm
    # BlockArea: tag, AREA_HIT_DATA (be_flag 1, tipo XZ4), flags, x35, areaNo, pri
    struct.pack_into('>IBBHfff8f', out, 0x40, 0, 1, 1, 0, -h, 2 * h, 0.0,
                     -h, -h, h, -h, h, h, -h, h)
    struct.pack_into('>BBbB', out, 0x40 + 0x34, 1, 0, 0, 0)
    struct.pack_into('>BB2x8b8b', out, 0x80, 1, 0, *([-1] * 16))
    return bytes(out)


def smd_works(smd):
    return struct.unpack_from('>H', smd, 2)[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('das'); ap.add_argument('modelos'); ap.add_argument('colision'); ap.add_argument('out')
    ap.add_argument('--modo', choices=('das', 'bloques'), default='bloques')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sig, snd_rec, snd, body, was_comp = read_das(a.das)
    entries, rel = parse_body(body)
    print('sala original:', ' '.join(f'{drs.tag_name(t)}({len(d) // 1024}K)' for t, d in entries))
    smd = open(os.path.join(a.modelos, 'sala.smd'), 'rb').read()
    smx = open(os.path.join(a.modelos, 'sala.smx'), 'rb').read()
    sat = open(os.path.join(a.colision, 'sala.sat'), 'rb').read()
    eat = open(os.path.join(a.colision, 'sala.eat'), 'rb').read()
    room = os.path.splitext(os.path.basename(a.das))[0]
    if a.modo == 'bloques':
        new = {'SMD': dummy_smd(smd_works(smd)), 'BLK': blk_one_area()}
        blockfile = pack_body([[tag4('SMD'), smd]])
        open(os.path.join(a.out, f'{room}_00.dat'), 'wb').write(blockfile)
        print(f'{room}_00.dat: {len(blockfile) / 1024:.0f} KB (modelos y texturas, sin comprimir)')
    else:
        new = {'SMD': smd}
    new.update({'SAT': sat, 'EAT': eat})      # SMX y BLK originales se conservan (nuestras piezas no usan SMX)
    done = set()
    out_entries = []
    for t, d in entries:
        name = drs.tag_name(t)
        if name in new and name not in done:
            done.add(name)
            if new[name] is not None:
                out_entries.append([t, new[name]])
            continue
        out_entries.append([t, d])
    for name, d in new.items():
        if name not in done and d is not None:
            out_entries.append([tag4(name), d])
    nb = pack_body(out_entries, rel)
    das = write_das(sig, snd_rec, snd, nb)
    open(os.path.join(a.out, os.path.basename(a.das)), 'wb').write(das)
    packed = len(das) - drs.TABLE_SIZE - len(snd)
    print(f'{os.path.basename(a.das)}: descomprimido {len(nb) / 1024:.0f} KB, comprimido {packed / 1024:.0f} KB, fichero {len(das) / 1024:.0f} KB')
    # las salas originales de St1 llegan a 5.795 KB descomprimidas y 3.242 KB comprimidas (r11b)
    if len(nb) > 5800 * 1024 or packed > 3250 * 1024:
        print('  AVISO: más grande que cualquier sala original del disco; puede no caber en memoria')


if __name__ == '__main__':
    main()
