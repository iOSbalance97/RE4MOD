"""ver_sala.py sala.obj st rNNN salida.jpg cams : la sala (en coordenadas del REmake) desde las cámaras del REmake, junto al fondo."""
import sys, os, subprocess, numpy as np
sys.path.insert(0, '/home/claude/re1gc/work'); import remake
from PIL import Image
obj, st, r, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
cams = [c for c in remake.camaras(st, r) if c['img'] is not None]
sel = [int(x) for x in sys.argv[5].split(',')]
import concurrent.futures as cf
def uno(k):
    c = cams[sel[k]]; e = tuple(np.array(c['ojo']) / 1000); o = tuple(np.array(c['obj']) / 1000)
    p = f'/tmp/_vs_{os.getpid()}_{k}.png'
    subprocess.run(['python3', '/home/claude/tools/render.py', obj, p, str(e), str(o), str(float(c['fov'])), '384', '336'], capture_output=True, env=dict(os.environ, CULL=os.environ.get('CULL', '1')))
    return k, p
M = Image.new('RGB', (2 * 384, 336 * len(sel)))
with cf.ProcessPoolExecutor(6) as ex:
    for k, p in ex.map(uno, range(len(sel))):
        M.paste(cams[sel[k]]['img'].resize((384, 336)), (0, k * 336))
        try: M.paste(Image.open(p).convert('RGB'), (384, k * 336))
        except Exception as e: print(e)
M.save(out, quality=82)
