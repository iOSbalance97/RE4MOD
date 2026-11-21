"""Biblioteca de materiales para rellenar superficies: texturas de las salas de UC clasificadas por uso
(suelo / pared / techo) según la normal de las caras que las llevan, con su tamaño real de repetición
(metros por repetición) y su color medio. Salida: biblioteca/<clase>/NNN.png + indice.json
uso: biblioteca.py"""
import glob, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude/tools')
import objload
OUT = '/home/claude/re1gc/biblioteca'
for c in ('suelo', 'pared', 'techo'): os.makedirs(f'{OUT}/{c}', exist_ok=True)
acum = {}
for obj in sorted(glob.glob('/home/claude/uc/m/r1*/sala.obj')):
    base = os.path.dirname(obj)
    # solo la parte original (antes de la envolvente)
    txt = open(obj).read().split('# envolvente')[0]
    tmp = '/tmp/_bib.obj'; open(tmp, 'w').write(txt)
    os.system(f'cp -f {base}/*.mtl /tmp/ 2>/dev/null')
    try:
        V, T, F, M, G, mats = objload.load(tmp)
    except Exception as e:
        print('salto', obj, e); continue
    if not len(F): continue
    P = V[F[:, :3]]; n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); a = np.linalg.norm(n, axis=1) / 2
    n = n / (2 * a[:, None] + 1e-12)
    UV = T[F[:, 3:]]; d1 = UV[:, 1] - UV[:, 0]; d2 = UV[:, 2] - UV[:, 0]; ua = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2
    cls = np.where(n[:, 1] > 0.8, 0, np.where(n[:, 1] < -0.8, 2, np.where(np.abs(n[:, 1]) < 0.3, 1, -1)))
    for m in set(M):
        tex = mats.get(m)
        if not tex: continue
        s = M == m
        for c in (0, 1, 2):
            k = s & (cls == c)
            A = a[k].sum()
            if A < 1.0: continue
            mpr = np.sqrt(A / max(ua[k].sum(), 1e-9))      # metros por repetición completa de la textura
            key = (os.path.join(base, tex), c)
            e = acum.setdefault(key, [0.0, []]); e[0] += A; e[1].append(mpr)
idx = []
nombres = ('suelo', 'pared', 'techo')
for (path, c), (A, mprs) in sorted(acum.items(), key=lambda x: -x[1][0]):
    try:
        im = Image.open(path).convert('RGBA')
    except Exception: continue
    if min(im.size) < 64: continue
    arr = np.asarray(im, float)
    if (arr[..., 3] < 200).mean() > 0.02: continue                  # con transparencias: no sirve de relleno
    mpr = float(np.median(mprs))
    if not 0.2 < mpr < 8: continue
    rgb = arr[..., :3]
    # variación de detalle (descarta texturas planas o degradados sin detalle)
    g = rgb.mean(2); det = float(np.abs(np.diff(g, axis=0)).mean() + np.abs(np.diff(g, axis=1)).mean())
    i = len(idx); dst = f'{OUT}/{nombres[c]}/{i:03d}.png'
    im.convert('RGB').save(dst)
    idx.append(dict(id=i, clase=nombres[c], png=dst, origen=path, area=round(A, 1), m_rep=round(mpr, 2),
                    color=[round(float(x), 1) for x in rgb.reshape(-1, 3).mean(0)], detalle=round(det, 2), tam=im.size))
json.dump(idx, open(f'{OUT}/indice.json', 'w'), indent=1)
for c in nombres: print(c, sum(1 for e in idx if e['clase'] == c))
