"""ver_uc.py uc_sala.obj alin.json st rNNN salida.jpg [camaras]: UC alineado renderizado desde las cámaras del REmake, junto al fondo."""
import sys, json, os, subprocess, numpy as np
sys.path.insert(0, '/home/claude/re1gc/work'); import remake
from PIL import Image
ucobj, alj, st, r, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
A = json.load(open(alj)); R = np.array(A['R']); s = A['s']; t = np.array(A['t'])
base = os.path.dirname(ucobj); tmp = f'{base}/_alin.obj'
with open(tmp, 'w') as f:
    for l in open(ucobj):
        if l.startswith('# envolvente'): break
        if l.startswith('v '):
            v = np.array(l.split()[1:4], float) @ R.T * s + t; f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
        else: f.write(l)
cams = [c for c in remake.camaras(st, r) if c['img'] is not None]
sel = [int(x) for x in sys.argv[6].split(',')] if len(sys.argv) > 6 else list(range(0, len(cams), max(1, len(cams) // 4)))[:4]
M = Image.new('RGB', (2 * 384, 336 * len(sel)))
for k, ci in enumerate(sel):
    c = cams[ci]; e = tuple(np.array(c['ojo']) / 1000); o = tuple(np.array(c['obj']) / 1000)
    fov = float(c['fov']); fov = np.degrees(fov) if fov < 3.2 else fov
    p = f'/tmp/_vu_{k}.png'
    env = dict(os.environ, CULL='1')
    subprocess.run(['python3', '/home/claude/tools/render.py', tmp, p, str(e), str(o), str(fov), '384', '336'], capture_output=True, env=env)
    M.paste(c['img'].resize((384, 336)), (0, k * 336))
    try: M.paste(Image.open(p).convert('RGB'), (384, k * 336))
    except Exception as ex: print(ex)
M.save(out, quality=80); print('fov ejemplo', cams[sel[0]]['fov'])
