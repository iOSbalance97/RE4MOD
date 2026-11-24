"""vistas.py sala.obj salida.jpg 'x,y,z>x,y,z;...' : vistas libres (metros, coordenadas de la sala)"""
import sys, os, subprocess
from PIL import Image
import concurrent.futures as cf
obj, out, spec = sys.argv[1], sys.argv[2], sys.argv[3]
V = [tuple(tuple(float(x) for x in p.split(',')) for p in v.split('>')) for v in spec.split(';')]
def uno(k):
    e, o = V[k]; p = f'/tmp/_vi_{os.getpid()}_{k}.png'
    subprocess.run(['python3', '/home/claude/tools/render.py', obj, p, str(e), str(o), '60', '400', '300'], capture_output=True, env=dict(os.environ, CULL='1'))
    return p
with cf.ProcessPoolExecutor(6) as ex: ps = list(ex.map(uno, range(len(V))))
M = Image.new('RGB', (800, 300 * ((len(ps) + 1) // 2)))
for k, p in enumerate(ps):
    try: M.paste(Image.open(p).convert('RGB'), ((k % 2) * 400, (k // 2) * 300))
    except Exception: pass
M.save(out, quality=82)
