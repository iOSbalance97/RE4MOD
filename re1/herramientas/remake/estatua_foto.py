"""estatua_foto.py frente.png lado.png espalda.png salida_dir [alto]
Reconstruye una figura a partir de 3 vistas (frente, lado mirando a la izquierda, espalda) por casco visual
(tallado de vóxeles con las siluetas), la malla con marching cubes, la reduce, y la texturiza proyectando las
propias imágenes (frente/espalda/lado según la normal). Añade un mapa entre las manos.
Salida: figura.obj (local: pies en el origen, mirando a +z), figura.png (atlas) en metros."""
import sys, os
import numpy as np, cv2
from PIL import Image
from scipy import ndimage
from skimage import measure
fr, la, es, out = sys.argv[1:5]; ALTO = float(sys.argv[5]) if len(sys.argv) > 5 else 1.15
os.makedirs(out, exist_ok=True)

def cargar(p):
    a = np.asarray(Image.open(p).convert('RGB'), np.float32)
    bg = np.median(np.concatenate([a[:5].reshape(-1, 3), a[-5:].reshape(-1, 3), a[:, :5].reshape(-1, 3), a[:, -5:].reshape(-1, 3)]), 0)
    d = np.abs(a - bg).max(2)
    m = d > 14
    m = ndimage.binary_opening(m, iterations=1); m = ndimage.binary_closing(m, iterations=3)
    lab, n = ndimage.label(m)
    if n > 1:
        tam = ndimage.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(tam)))
    m = ndimage.binary_fill_holes(m)
    rows = np.nonzero(m.any(1))[0]; top, bot = rows[0], rows[-1]
    esc = ALTO / (bot - top)                                  # m por píxel
    # centro: columnas del tronco (entre 30 % y 55 % de la altura)
    r0, r1 = int(top + 0.30 * (bot - top)), int(top + 0.55 * (bot - top))
    cols = np.nonzero(m[r0:r1].any(0))[0]
    cx = float(np.average(np.arange(m.shape[1]), weights=m[r0:r1].sum(0)))
    # rellenar el fondo con el color de la figura más cercano (para que la proyección no coja gris del fondo)
    idx = ndimage.distance_transform_edt(~m, return_distances=False, return_indices=True)
    rel = a[idx[0], idx[1]]
    return dict(a=a, rel=rel, m=m, top=top, bot=bot, esc=esc, cx=cx)
F_, L_, E_ = cargar(fr), cargar(la), cargar(es)
# ---------------- vóxeles
S = 0.007
xs = np.arange(-0.45, 0.45, S); ys = np.arange(0, ALTO + S, S); zs = np.arange(-0.4, 0.4, S)
def px(I, u, y, signo=1):        # coordenada horizontal u (m) y altura y (m) -> (col, fila) de la imagen
    col = I['cx'] + signo * u / I['esc']; row = I['bot'] - y / I['esc']
    return col, row
def dentro(I, u, y, signo=1):
    col, row = px(I, u, y, signo)
    c = np.round(col).astype(int); r = np.round(row).astype(int)
    ok = (c >= 0) & (c < I['m'].shape[1]) & (r >= 0) & (r < I['m'].shape[0])
    out_ = np.zeros(c.shape, bool); out_[ok] = I['m'][r[ok], c[ok]]; return out_
X, Y = np.meshgrid(xs, ys, indexing='ij')
mf = dentro(F_, X, Y, 1) & dentro(E_, X, Y, -1)                   # frente y espalda (espejo)
Zc, Yc = np.meshgrid(zs, ys, indexing='ij')
ml = dentro(L_, Zc, Yc, -1)                                       # lado: mira a la izquierda -> +z hacia la izquierda de la imagen
vol = mf[:, :, None] & ml.T[None, :, :]                           # (x, y, z)
vol = ndimage.binary_opening(vol, iterations=1)
vol = ndimage.gaussian_filter(vol.astype(np.float32), 1.0)
verts, faces, normals, _ = measure.marching_cubes(vol, 0.5, spacing=(S, S, S))
verts = verts + [xs[0], ys[0], zs[0]]
print('casco visual:', len(verts), 'vértices', len(faces), 'triángulos')
# ---------------- reducir
sys.path.insert(0, '/home/claude/tools'); import decimate
obj_ratio = min(1.0, float(os.environ.get('TRI', 9000)) / len(faces))
P, UV0, T = decimate.decimate(verts.astype(np.float64), np.zeros((len(verts), 2)), faces.astype(np.int64), obj_ratio)
print('reducido:', len(T), 'triángulos')
# ---------------- atlas: tres franjas (frente, espalda, lado), cada una el recorte de la figura
W = 1024; FR = W // 3
def franja(I, k):
    rows = np.nonzero(I['m'].any(1))[0]; cols = np.nonzero(I['m'].any(0))[0]
    y0, y1 = rows[0] - 4, rows[-1] + 4; x0, x1 = cols[0] - 4, cols[-1] + 4
    crop = I['rel'][max(0, y0):y1, max(0, x0):x1]
    g = crop @ np.array([0.3, 0.59, 0.11]) / 255
    g = np.clip((g - 0.15) / 0.75, 0, 1) ** 0.9 * 0.92 + 0.06              # mármol: luminancia de la foto
    rgb = np.stack([g, g * 0.985, g * 0.95], -1)
    img = cv2.resize(rgb.astype(np.float32), (FR, W), interpolation=cv2.INTER_AREA)
    return img, (max(0, x0), max(0, y0), x1 - max(0, x0), y1 - max(0, y0), k * FR)
atlas = np.zeros((W, W, 3), np.float32); info = {}
for k, (nm, I) in enumerate((('f', F_), ('e', E_), ('l', L_))):
    img, inf = franja(I, k); atlas[:, k * FR:(k + 1) * FR] = img; info[nm] = (I, inf)
def uv_de(nm, u, y, signo):
    I, (x0, y0, w, h, ox) = info[nm]
    col, row = px(I, u, y, signo)
    return np.stack([(ox + (col - x0) / w * FR) / W, 1 - (row - y0) / h], -1)
Tp = P[T]; n = np.cross(Tp[:, 1] - Tp[:, 0], Tp[:, 2] - Tp[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
vista = np.where(n[:, 2] > np.abs(n[:, 0]) * 0.8, 0, np.where(n[:, 2] < -np.abs(n[:, 0]) * 0.8, 1, 2))
# ---------------- mapa entre las manos: buscar lo más adelantado entre 40 % y 62 % de la altura
sel = (P[:, 1] > 0.40 * ALTO) & (P[:, 1] < 0.62 * ALTO)
zf = P[sel, 2].max() if sel.any() else 0.15; yh = float(np.median(P[sel][P[sel, 2] > zf - 0.06, 1])) if sel.any() else 0.5 * ALTO
mapa_c = np.array([0.0, yh + 0.06, zf - 0.02])
with open(f'{out}/figura.obj', 'w') as fo:
    fo.write('mtllib figura.mtl\nusemtl figura\n')
    for v in P: fo.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
    vt = []
    for i, tri in enumerate(T):
        for j in tri:
            x, y, z = P[j]
            if vista[i] == 0: uv = uv_de('f', x, y, 1)
            elif vista[i] == 1: uv = uv_de('e', x, y, -1)
            else: uv = uv_de('l', z, y, -1)
            vt.append(uv)
    for uv in vt: fo.write(f'vt {uv[0]:.5f} {uv[1]:.5f}\n')
    for i, tri in enumerate(T):
        fo.write(f'f {tri[0]+1}/{3*i+1} {tri[1]+1}/{3*i+2} {tri[2]+1}/{3*i+3}\n')
    # mapa: lámina inclinada, 0.34 x 0.24 m
    nb = len(P) + 1; nt = len(vt) + 1
    ancho, altoM = 0.26, 0.19; inc = np.radians(35)
    esq = [(-ancho / 2, -altoM / 2), (ancho / 2, -altoM / 2), (ancho / 2, altoM / 2), (-ancho / 2, altoM / 2)]
    pts = [mapa_c + [a, b * np.cos(inc), b * np.sin(inc) * -1 + 0.0] for a, b in esq]
    fo.write('usemtl mapa\n')
    for p in pts: fo.write(f'v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n')
    for t in ((0, 0), (1, 0), (1, 1), (0, 1)): fo.write(f'vt {t[0]} {t[1]}\n')
    fo.write(f'f {nb}/{nt} {nb+1}/{nt+1} {nb+2}/{nt+2}\nf {nb}/{nt} {nb+2}/{nt+2} {nb+3}/{nt+3}\n')
    fo.write(f'f {nb}/{nt} {nb+2}/{nt+2} {nb+1}/{nt+1}\nf {nb}/{nt} {nb+3}/{nt+3} {nb+2}/{nt+2}\n')
Image.fromarray((np.clip(atlas, 0, 1) * 255).astype(np.uint8)).save(f'{out}/figura.png')
# mapa: pergamino con el plano de la mansión esbozado (mármol: tono claro)
mp = np.full((256, 256, 3), 0.86, np.float32); rg = np.random.default_rng(3)
mp *= (0.94 + 0.06 * cv2.resize(rg.random((16, 16)), (256, 256)))[..., None]
for (x0, y0, x1, y1) in ((30, 40, 120, 110), (130, 40, 226, 110), (30, 120, 90, 220), (100, 120, 160, 180), (170, 120, 226, 220), (100, 190, 160, 220)):
    cv2.rectangle(mp, (x0, y0), (x1, y1), (0.45, 0.44, 0.42), 2)
cv2.rectangle(mp, (8, 8), (247, 247), (0.5, 0.48, 0.45), 3)
Image.fromarray((mp * 255).astype(np.uint8)).save(f'{out}/mapa.png')
open(f'{out}/figura.mtl', 'w').write('newmtl figura\nmap_Kd figura.png\nnewmtl mapa\nmap_Kd mapa.png\n')
print('ok', out, 'mapa en', mapa_c.round(3))
