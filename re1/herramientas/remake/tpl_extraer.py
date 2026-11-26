"""tpl_extraer.py destino sala.das [...] : extrae las texturas (TPL) de salas de RE4 a PNG"""
import sys, os, struct
import numpy as np
from PIL import Image
for p in ('/home/claude/re1gc/work', '/home/claude/tools'): sys.path.insert(0, p)
import re4inject as RI, drs, mdl0
dst = sys.argv[1]; os.makedirs(dst, exist_ok=True); n = 0
for f in sys.argv[2:]:
    sala = os.path.basename(f)[:4]
    try: sig, sr, snd, body, _ = RI.read_das(f); e, rel = RI.parse_body(body)
    except Exception as ex: print('no se pudo leer', f, ex); continue
    B = bytes(body); pos = 0; k_ = 0
    while True:
        pos = B.find(b'\x00\x20\xaf\x30', pos)
        if pos < 0: break
        d = B[pos:]; pos += 4; k_ += 1
        try: num, tab = struct.unpack_from('>II', d, 4)
        except Exception: continue
        if not (0 < num < 300 and 8 <= tab < 64): continue
        for i in range(num):
            ih, ph = struct.unpack_from('>II', d, tab + 8 * i)
            h, w, fmt, off = struct.unpack_from('>HHII', d, ih)
            try:
                img = mdl0.decode_tex(fmt, w, h, d[off:])
                a = np.asarray(img) if not isinstance(img, np.ndarray) else img
                Image.fromarray(a.astype(np.uint8)).save(f'{dst}/{sala}_{k_:02d}_{i:03d}.png'); n += 1
            except Exception as ex: pass
print('texturas extraídas:', n)
