"""Añade a la biblioteca de materiales las texturas de la mansión Spencer de RE5 (Lost in Nightmares),
clasificadas por su nombre (yuka = suelo, tenjou = techo, wall/kabe/panel = pared)."""
import glob, json, os, re
import numpy as np
from PIL import Image
OUT = '/home/claude/re1gc/biblioteca'; idx = json.load(open(f'{OUT}/indice.json'))
idx = [e for e in idx if not e['origen'].startswith('re5:')]
REGLAS = [('suelo', r'yuka|floor|_fl0|jutang'), ('techo', r'tenj|tenjo|ceil'),
          ('pared', r'wall|kabe|panel|wallpaper|hasira|woodpanel|turo_wall|kaidan')]
n0 = len(idx)
for p in sorted(glob.glob('/home/claude/re5x/tex_s70*/*.png')):
    nm = os.path.basename(p).lower()
    if re.search(r'_nm|_mm|_lm|_cm|nomip', nm): continue
    cl = next((c for c, rx in REGLAS if re.search(rx, nm)), None)
    if not cl: continue
    im = Image.open(p).convert('RGB')
    if min(im.size) < 256: continue
    a = np.asarray(im.resize((64, 64), Image.BOX), float)
    blk = a.reshape(4, 16, 4, 16, 3).mean((1, 3)); unif = float(blk.std((0, 1)).mean())
    g = a.mean(2); interior = np.abs(np.diff(g, axis=1)).mean() + 1e-6
    cost = float((np.abs(g[:, 0] - g[:, -1]).mean() + np.abs(g[0] - g[-1]).mean()) / 2 / interior)
    i = len(idx); dst = f'{OUT}/{cl}/re5_{i:03d}.png'
    im.resize((512, 512), Image.LANCZOS).save(dst)
    gg = np.asarray(im.convert('L'), float)
    det = float(np.abs(np.diff(gg, axis=0)).mean() + np.abs(np.diff(gg, axis=1)).mean())
    idx.append(dict(id=i, clase=cl, png=dst, origen='re5:' + nm, area=600.0, m_rep=2.0,
                    color=[round(float(x), 1) for x in a.reshape(-1, 3).mean(0)], detalle=round(det, 2), tam=im.size,
                    uniforme=round(unif, 1), costura=round(cost, 2), repite=unif < 16 and cost < 3.5))
json.dump(idx, open(f'{OUT}/indice.json', 'w'), indent=1)
nuevos = idx[n0:]
for c in ('suelo', 'pared', 'techo'): print(c, sum(1 for e in nuevos if e['clase'] == c), 'repiten', sum(1 for e in nuevos if e['clase'] == c and e['repite']))
