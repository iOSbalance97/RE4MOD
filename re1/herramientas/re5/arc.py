"""Extrae un .arc de RE5 PS3 (cabecera SFH + ARC big-endian, datos zlib)."""
import struct, sys, zlib, os
def entradas(path):
    d = open(path, 'rb').read(); b = 0
    if d[1:4] == b'SFH':          # contenedor SFH: bloques de 0x20000 bytes seguidos de 16 bytes de comprobación
        n = struct.unpack('>I', d[8:12])[0]; d = b''.join(d[16 + i * 0x20010:16 + i * 0x20010 + 0x20000] for i in range((n + 0x1FFFF) // 0x20000))[:n]
    assert d[b:b + 4] == b'\0CRA', d[b:b + 4]
    ver, n = struct.unpack('>HH', d[b + 4:b + 8]); out = []
    for i in range(n):
        e = d[b + 8 + i * 0x50:b + 8 + (i + 1) * 0x50]
        name = e[:64].split(b'\0')[0].decode('latin1'); h, cs, ds, off = struct.unpack('>4I', e[64:80])
        data = None
        for o in (off,):
            raw = d[o:o + cs]
            try: data = zlib.decompress(raw); break
            except Exception: pass
        if data is None:
            data = d[b + off:b + off + cs]
            for o in range(off, off + 0x40):
                if d[o:o + 4] in (b'\0XET', b'\0DOM'): data = d[o:o + cs]; break
        out.append((name.replace('\\', '/'), h, data))
    return out
if __name__ == '__main__':
    for name, h, data in entradas(sys.argv[1]):
        p = os.path.join(sys.argv[2], f'{name}.{h:08x}'); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(data)
        print(f'{name} {h:08x} {len(data)}')
