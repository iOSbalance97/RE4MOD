"""Relleno de huecos en texturas con patrón repetido (baldosas, damero, parqué): busca la red de periodicidad
por autocorrelación de la parte vista y copia en los huecos lo que hay a un periodo de distancia."""
import numpy as np
def red(img, vale, maxp=160):
    from scipy.ndimage import gaussian_filter
    g = img.mean(2).astype(np.float64); m = vale.astype(np.float64)
    g = g - gaussian_filter(g, 10)                      # paso alto: solo el dibujo, no los degradados de luz
    if g[vale].std() < 7: return None
    g = g * m
    H, W = g.shape; Hp, Wp = 2 * H, 2 * W
    F = np.fft.rfft2(g, (Hp, Wp)); Fm = np.fft.rfft2(m, (Hp, Wp))
    ac = np.fft.irfft2(F * np.conj(F), (Hp, Wp)); cnt = np.fft.irfft2(Fm * np.conj(Fm), (Hp, Wp))
    var = ac[0, 0] / max(cnt[0, 0], 1)
    acn = np.where(cnt > 0.25 * cnt[0, 0], ac / np.maximum(cnt, 1) / max(var, 1e-6), -1)
    A = np.roll(np.roll(acn, maxp + 1, 0), maxp + 1, 1)[:2 * maxp + 3, :2 * maxp + 3]   # centro en (maxp+1, maxp+1)
    c0 = maxp + 1
    yy, xx = np.mgrid[:A.shape[0], :A.shape[1]]; rr = np.hypot(yy - c0, xx - c0)
    r0 = 3
    for rad in range(2, maxp):
        if A[(rr >= rad) & (rr < rad + 1)].mean() < 0.25: r0 = rad; break
    from scipy.ndimage import maximum_filter
    pico = (A == maximum_filter(A, 5)) & (rr > r0 + 1)
    cand = sorted([(A[y, x], x - c0, y - c0) for y, x in zip(*np.nonzero(pico)) if (x - c0 > 0 or (x == c0 and y > c0))], reverse=True)
    cand.sort(reverse=True)
    if not cand or cand[0][0] < 0.35: return None
    v1 = np.array(cand[0][1:]); 
    for s, dx, dy in cand[1:]:
        v2 = np.array([dx, dy])
        if s < 0.3: break
        if abs(v1[0] * v2[1] - v1[1] * v2[0]) > 0.4 * np.linalg.norm(v1) * np.linalg.norm(v2): return v1, v2, cand[0][0]
    return v1, None, cand[0][0]
def red_ventanas(img, vale, lado=200):
    H, W = vale.shape; mejor = None
    for y in range(0, max(1, H - lado + 1), lado // 3):
        for x in range(0, max(1, W - lado + 1), lado // 3):
            v = vale[y:y + lado, x:x + lado]
            if v.mean() < 0.6: continue
            r = red(img[y:y + lado, x:x + lado], v, maxp=lado // 3)
            if r and (mejor is None or r[2] > mejor[2]): mejor = r
    return mejor
def rellenar(img, vale, iters=60):
    r = red_ventanas(img, vale)
    if r is None: return img, vale, None
    v1, v2, s = r
    img = img.copy(); vale = vale.copy(); H, W = vale.shape
    vecs = [v1, -v1] + ([v2, -v2, v1 + v2, -v1 - v2, v1 - v2, v2 - v1] if v2 is not None else [])
    for _ in range(iters):
        hu = ~vale
        if not hu.any(): break
        cambio = False
        for v in vecs:
            ys, xs = np.nonzero(~vale)
            sy, sx = ys + v[1], xs + v[0]
            ok = (sy >= 0) & (sy < H) & (sx >= 0) & (sx < W)
            ys, xs, sy, sx = ys[ok], xs[ok], sy[ok], sx[ok]
            k = vale[sy, sx]
            if k.any():
                img[ys[k], xs[k]] = img[sy[k], sx[k]]; vale[ys[k], xs[k]] = True; cambio = True
        if not cambio: break
    return img, vale, (v1, v2, s)
def baldosa(img, vale, v1, v2):
    """Celda media (mediana) del patrón y su valor para cada píxel."""
    H, W = vale.shape
    M = np.array([[v1[0], v2[0]], [v1[1], v2[1]]], float); Mi = np.linalg.inv(M)
    yy, xx = np.mgrid[:H, :W]
    ab = np.einsum('ij,jhw->ihw', Mi, np.stack([xx, yy]).astype(float))
    fa, fb = ab[0] % 1, ab[1] % 1
    na, nb = max(4, int(np.linalg.norm(v1))), max(4, int(np.linalg.norm(v2)))
    ia = (fa * na).astype(int) % na; ib = (fb * nb).astype(int) % nb
    idx = ia * nb + ib
    out = np.zeros((na * nb, img.shape[2]), np.float32)
    vi = idx[vale]; vals = img[vale].astype(np.float32)
    orden = np.argsort(vi, kind='stable'); vi = vi[orden]; vals = vals[orden]
    cortes = np.searchsorted(vi, np.arange(na * nb + 1))
    lleno = np.zeros(na * nb, bool)
    for k in range(na * nb):
        a, b = cortes[k], cortes[k + 1]
        if b > a: out[k] = np.median(vals[a:b], 0); lleno[k] = True
    if not lleno.all() and lleno.any():
        out[~lleno] = out[lleno].mean(0)
    # celda real más típica y nítida (la mediana sale borrosa si la red no es exacta)
    ca, cb = np.floor(ab[0]).astype(int), np.floor(ab[1]).astype(int)
    inst = (ca - ca.min()) * (cb.max() - cb.min() + 1) + (cb - cb.min())
    nbins = na * nb; clave = inst[vale] * nbins + idx[vale]
    lum = img[vale].astype(np.float64) @ np.array([0.3, 0.59, 0.11])
    cnt = np.bincount(clave, minlength=(inst.max() + 1) * nbins).reshape(-1, nbins)
    sm = np.bincount(clave, lum, minlength=(inst.max() + 1) * nbins).reshape(-1, nbins)
    completas = np.nonzero((cnt > 0).mean(1) > 0.97)[0]
    if len(completas):
        ref = out @ np.array([0.3, 0.59, 0.11], np.float32); ref = ref - ref.mean()
        mejor = None
        for c in completas:
            v = sm[c] / np.maximum(cnt[c], 1); v = v - v.mean()
            sc = (v * ref).sum() / (np.linalg.norm(v) * np.linalg.norm(ref) + 1e-9) + 0.002 * v.std()
            if mejor is None or sc > mejor[0]: mejor = (sc, c)
        c = mejor[1]
        sel = (inst == c) & vale
        cel = np.zeros((nbins, img.shape[2]), np.float32); n_ = np.zeros(nbins)
        np.add.at(cel, idx[sel], img[sel].astype(np.float32)); np.add.at(n_, idx[sel], 1)
        okb = n_ > 0; cel[okb] /= n_[okb][:, None]; cel[~okb] = out[~okb]
        out = cel
    return out[idx], lleno.mean()
def _corr(g, m, dx, dy):
    H, W = g.shape
    if abs(dy) >= H - 8 or abs(dx) >= W - 8: return -1
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    a = g[ys, xs]; b = g[yd, xd]; w = m[ys, xs] * m[yd, xd]
    n = w.sum()
    if n < 500: return -1
    return (a * b * w).sum() / np.sqrt((a * a * w).sum() * (b * b * w).sum() + 1e-9)
def afinar(img, vale, v, k=2):
    from scipy.ndimage import gaussian_filter
    g = img.mean(2).astype(float); g = g - gaussian_filter(g, 10); m = vale.astype(float)
    c = np.round(np.asarray(v) * k).astype(int); mejor = (-2, c)
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            s = _corr(g, m, c[0] + dx, c[1] + dy)
            if s > mejor[0]: mejor = (s, c + [dx, dy])
    return mejor[1] / k, mejor[0]
def rellenar_baldosa(img, vale):
    r = red_ventanas(img, vale)
    if r is None or r[1] is None: return img, vale, None
    v1, v2, s = r
    v1, s1 = afinar(img, vale, v1); v2, s2 = afinar(img, vale, v2)
    if min(s1, s2) < 0.15: return img, vale, None
    T_, cob = baldosa(img, vale, v1, v2)
    img = img.astype(np.float32).copy()
    lum = lambda a: a @ np.array([0.3, 0.59, 0.11], np.float32)
    # luz local: relación entre lo visto y la baldosa, suavizada
    from scipy.ndimage import gaussian_filter
    rel = np.where(vale, (lum(img) + 4) / (lum(T_) + 4), 0); w = gaussian_filter(vale.astype(float), 25)
    luz = np.where(w > 0.02, gaussian_filter(rel, 25) / np.maximum(w, 1e-3), 1.0)
    luz = np.clip(np.where(w > 0.02, luz, np.median(rel[vale]) if vale.any() else 1), 0.4, 1.8)
    sint = T_ * luz[..., None]
    raro = vale & (np.abs(lum(img) - lum(sint)) > 70)          # muebles proyectados sobre el suelo
    usar = ~vale | raro
    img[usar] = sint[usar]
    return img.clip(0, 255).astype(np.uint8), np.ones_like(vale), (v1, v2, s, cob, raro.mean())
def periodo_ejes(img, vale, dmin=10, dmax=130):
    from scipy.ndimage import gaussian_filter
    g = img.mean(2).astype(float); g = g - gaussian_filter(g, 10); m = vale.astype(float)
    res = []
    for eje in (0, 1):
        c = [(_corr(g, m, d, 0) if eje == 0 else _corr(g, m, 0, d), d) for d in range(dmin, dmax)]
        # primer pico alto (evita múltiplos)
        best = max(c)[0]
        for k in range(1, len(c) - 1):
            if c[k][0] >= c[k - 1][0] and c[k][0] >= c[k + 1][0] and c[k][0] > 0.8 * best:
                res.append(c[k]); break
        else: res.append(max(c))
    return res
def rellenar_recorte(img, vale, calidad=None):
    (sx, px), (sy, py) = periodo_ejes(img, vale)
    if min(sx, sy) < 0.2: return img, vale, None
    nx = max(1, round(160 / px)); ny = max(1, round(160 / py)); w, h = nx * px, ny * py
    H, W = vale.shape
    from scipy.ndimage import uniform_filter, gaussian_filter
    cob = uniform_filter(vale.astype(float), (h, w), mode='constant')
    g = img.mean(2).astype(float); det = uniform_filter(np.abs(g - gaussian_filter(g, 3)), (h, w), mode='constant')
    lf = gaussian_filter(g, 10); lfs = np.sqrt(np.maximum(uniform_filter(lf * lf, (h, w), mode='constant') - uniform_filter(lf, (h, w), mode='constant') ** 2, 0))
    D = np.zeros_like(g)
    D[:, :-px] += np.abs(g[:, :-px] - g[:, px:]); D[:-py] += np.abs(g[:-py] - g[py:])
    rep = uniform_filter(D, (h, w), mode='constant')            # lo que no se repite (muebles, manchas) puntúa mal
    if calidad is not None:
        q = uniform_filter(np.minimum(calidad, 1.5), (h, w), mode='constant')
        qv = np.where(cob > 0.995, q, -1)
        buenos = qv >= 0.6 * qv.max()
        mu = uniform_filter(g, (h, w), mode='constant') + 5
        buenos &= mu >= 0.9 * np.median(g[vale])
        puntua = np.where(buenos, -(lfs + rep) / mu + 0.3 * det / mu, -1e9)
    else:
        puntua = np.where(cob > 0.995, det - 0.8 * lfs - 1.2 * rep, -1e9)
    cy, cx = np.unravel_index(np.argmax(puntua), puntua.shape)
    if puntua[cy, cx] < -1e8: return img, vale, None
    y0, x0 = cy - h // 2, cx - w // 2
    if y0 < 0 or x0 < 0 or y0 + h > H or x0 + w > W: return img, vale, None
    tile = img[y0:y0 + h, x0:x0 + w].astype(np.float32)
    yy, xx = np.mgrid[:H, :W]
    T_ = tile[(yy - y0) % h, (xx - x0) % w]
    img = img.astype(np.float32).copy()
    lum = lambda a: a @ np.array([0.3, 0.59, 0.11], np.float32)
    rel = np.where(vale, (gaussian_filter(lum(img), 12) + 4) / (gaussian_filter(lum(T_), 12) + 4), 0)
    wv = gaussian_filter(vale.astype(float), 30)
    luz = np.where(wv > 0.02, gaussian_filter(rel, 30) / np.maximum(wv, 1e-3), np.median(rel[vale]))
    sint = T_ * np.clip(luz, 0.4, 1.8)[..., None]
    raro = vale & (np.abs(gaussian_filter(lum(img), 2) - gaussian_filter(lum(sint), 2)) > 45)
    usar = ~vale | raro
    img[usar] = sint[usar]
    return img.clip(0, 255).astype(np.uint8), np.ones_like(vale), ((px, 0), (0, py), min(sx, sy), w, raro.mean())
