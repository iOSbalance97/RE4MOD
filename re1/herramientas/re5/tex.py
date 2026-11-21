"""Textura .tex de RE5 PS3 (v0x66, big-endian) -> PNG (DXT1/DXT3/DXT5 vía DDS de PIL)."""
import struct, sys, io, os, glob
from PIL import Image
def leer(path):
    d = open(path, 'rb').read()
    if d[:4] != b'\0XET': return None
    mips, faces, w, h = d[8], d[9], struct.unpack('>H', d[10:12])[0], struct.unpack('>H', d[12:14])[0]
    fcc = d[16:20][::-1]
    off0 = struct.unpack('>I', d[0x24:0x28])[0] if mips > 0 else 0x28
    if fcc not in (b'DXT1', b'DXT3', b'DXT5'): return ('fmt', fcc)
    bs = 8 if fcc == b'DXT1' else 16
    n = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * bs
    data = d[off0:off0 + n]
    if len(data) < n: return ('corto', len(data), n)
    hdr = struct.pack('<4sIIIIIII44x', b'DDS ', 124, 0x1007 | 0x80000, h, w, n, 0, 1) + struct.pack('<II4sIIIII', 32, 4, fcc, 0, 0, 0, 0, 0) + struct.pack('<IIIII', 0x1000, 0, 0, 0, 0)
    im = Image.open(io.BytesIO(hdr + data)); im.load()
    return im
if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True); ok = mal = 0
    for p in glob.glob(f'{src}/**/*_BM.241f5deb', recursive=True) + glob.glob(f'{src}/**/*BM.241f5deb', recursive=True):
        try: im = leer(p)
        except Exception as e: im = ('err', str(e)[:60])
        if isinstance(im, Image.Image):
            nm = os.path.basename(p).split('.')[0]
            im.save(f'{out}/{nm}.png'); ok += 1
        else: mal += 1
    print('ok', ok, 'mal', mal)
