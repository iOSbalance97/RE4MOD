"""ver.py sala.obj auditoria.json salida.jpg [n]: vista de cada grupo de huecos (en rojo lo que deja ver el fondo)"""
import sys, json, subprocess, numpy as np
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor
sala, aj, out = sys.argv[1:4]; N = int(sys.argv[4]) if len(sys.argv) > 4 else 8
G = json.load(open(aj)).get('grupos', [])[:N]
def uno(k):
    g = G[k]; o = np.array(g['desde']); c = np.array(g['centro']); d = c - o; o2 = c - d / np.linalg.norm(d) * min(np.linalg.norm(d), 2.5)
    p = f'/tmp/_ver_{k}.png'
    subprocess.run(['python3', '/home/claude/tools/render.py', sala, p, '%f,%f,%f' % tuple(o2), '%f,%f,%f' % tuple(c), '70', '320', '240'], capture_output=True)
    im = np.asarray(Image.open(p).convert('RGB')).astype(int).copy(); bg = np.abs(im - 38).sum(2) < 4; im[bg] = [255, 0, 0]
    im = Image.fromarray(im.astype(np.uint8)); ImageDraw.Draw(im).text((4, 4), f"{k}: {g['centro']}", fill=(255, 255, 0)); return im
with ThreadPoolExecutor(2) as ex: ims = list(ex.map(uno, range(len(G))))
M = Image.new('RGB', (640, 240 * ((len(ims) + 1) // 2)))
for k, im in enumerate(ims): M.paste(im, ((k % 2) * 320, (k // 2) * 240))
M.save(out, quality=85)
