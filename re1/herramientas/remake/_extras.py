# ---------------- piezas a mano: balaustres bajo pasamanos vacíos y columnas torneadas (config por sala)
import extras as _ex
sys.path.insert(0, '/home/claude/tools'); from hmap import floors as _floors, heights as _heights
_TF = _floors(f'/home/claude/re1gc/salas/{r}/colision_fusion.obj' if os.path.exists(f'/home/claude/re1gc/salas/{r}/colision_fusion.obj') else f'/home/claude/re1gc/salas/{r}/colision.obj')
import re as _re2
_SMa = np.array(SM, dtype=object)
_excl = {mm for mm in set(FM) if _re2.search(r'handrail|tesuri', str(mats.get(mm) or ''), _re2.I)}
def _tiene_alfa(mm):
    tn = mats.get(mm)
    if not tn: return False
    try: return (np.asarray(Image.open(os.path.join(base, tn)).convert('RGBA'))[..., 3] < 128).mean() > 0.05
    except Exception: return False
_excl |= {mm for mm in set(FM) if _tiene_alfa(mm)}
_Sok = np.array([m_ not in _excl for m_ in _SMa])
_S2 = S[_Sok]
_Sxz = cKDTree(_S2[:, [0, 2]])
def _alt(x, z, ymax):
    h = _heights(_TF, x, z); h = h[h <= ymax] if len(h) else h
    return float(h.max()) if len(h) else None
def _hay(x, y0, y1, z):
    for j in _Sxz.query_ball_point([x, z], 0.07):
        if y0 <= _S2[j, 1] <= y1: return True
    return False
_ext_v = []; _ext_t = []; _ext_f = []; _ext_m = []
def _anade(Vp, Tp, Fp, mm):
    b0 = len(V) + sum(len(a) for a in _ext_v); bt = len(VT) + sum(len(a) for a in _ext_t)
    _ext_v.append(Vp); _ext_t.append(Tp)
    for f in Fp: _ext_f.append([b0 + f[0], b0 + f[1], b0 + f[2], bt + f[0], bt + f[1], bt + f[2]]); _ext_m.append(mm)
_mr = [mm for mm in set(FM) if _re2.search(r'handrail|tesuri', str(mats.get(mm) or ''), _re2.I)]
nb_ = 0
if _mr:
    selr = np.nonzero(np.isin(FM, _mr))[0]
    Pr = V[F[selr, :3]].reshape(-1, 3)
    mm_r = max(_mr, key=lambda m_: (FM == m_).sum())
    _bases1 = []
    _Tall = cKDTree(S[:, [0, 2]])
    def _hay_all(x, y0, y1, z):
        return any(y0 <= S[j, 1] <= y1 for j in _Tall.query_ball_point([x, z], 0.14))
    _alf1 = np.array([_tiene_alfa(m_) for m_ in _SMa]); _Sa1 = S[_alf1]; _Ta1 = cKDTree(_Sa1[:, [0, 2]]) if len(_Sa1) else None
    def _lamina_cerca(x, y0, y1, z):
        return _Ta1 is not None and any(y0 <= _Sa1[j, 1] <= y1 for j in _Ta1.query_ball_point([x, z], 0.3))
    for base_, h in ([] if (os.environ.get('BARANDILLA_RAMPAS') or os.environ.get('BALAUSTRES_TOTAL')) else [bh for bh in _ex.balaustres_escalera(Tc, nc, Pr, _hay_all)
                                                                     if not _lamina_cerca(bh[0][0], bh[0][1] + 0.2 * bh[1], bh[0][1] + 0.8 * bh[1], bh[0][2])]):
        Vp, Tp, Fp = _ex.torneado(base_, h, _ex.PERFIL_BALAUSTRE_LIGERO, escala_r=0.7, lados=6)
        _anade(Vp, Tp, Fp, mm_r); nb_ += 1; _bases1.append(base_)
# segunda pasada: balaustres justo debajo de cualquier pasamanos que no tenga nada debajo (ni tarjetas con alfa)
if _mr and not os.environ.get('BARANDILLA_RAMPAS') and not os.environ.get('BALAUSTRES_TOTAL'):
    _S3 = S; _T3 = cKDTree(_S3[:, [0, 2]])                       # todo cuenta, también las láminas de balaustres de UC
    def _hay_todo(x, y0, y1, z, rad=0.14):
        for j in _T3.query_ball_point([x, z], rad):
            if y0 <= _S3[j, 1] <= y1: return True
        return False
    _ya = [b_ for b_, _ in []]
    _puestos = cKDTree(np.array([[0, 1e6, 0]]))
    _celdas = {}
    # puntos de toda la superficie del pasamanos (las vigas largas solo tienen vértices en los extremos)
    _Pr_s = [Pr]
    for i_ in np.nonzero(np.isin(FM, _mr))[0]:
        t3 = V[F[i_, :3]]; L_ = np.linalg.norm(t3 - np.roll(t3, 1, 0), axis=1).max()
        k_ = int(min(60, max(3, L_ / 0.05)))
        _Pr_s.append(np.random.default_rng(i_).dirichlet([1, 1, 1], k_) @ t3)
    for p in np.concatenate(_Pr_s):
        k = (int(np.floor(p[0] / 0.17)), int(np.floor(p[2] / 0.17)))
        if k not in _celdas or p[1] < _celdas[k][1]: _celdas[k] = p
    _nuevos = []; _por = {'sin suelo': 0, 'ya hay': 0, 'cerca de otro': 0}
    for k, p in _celdas.items():
        x, z = (k[0] + 0.5) * 0.17, (k[1] + 0.5) * 0.17
        ytop = p[1] - 0.04
        cand = []
        for rr_ in (0.0, 0.18, 0.35, 0.5, 0.65):
            for t_ in (np.linspace(0, 2 * np.pi, 8, endpoint=False) if rr_ else [0.0]):
                h = _heights(_TF, x + rr_ * np.cos(t_), z + rr_ * np.sin(t_)); h = h[(h < ytop - 0.45) & (h > ytop - 1.35)]
                if len(h): cand.append(float(h.max()))
            if cand: break
        if not cand: _por['sin suelo'] += 1; continue
        yb = max(cand); hh = ytop - yb
        if any(np.hypot(x - q[0], z - q[2]) < 0.13 and abs(yb - q[1]) < 0.6 for q in _bases1): continue
        if _hay_todo(x, yb + 0.35 * hh, yb + 0.8 * hh, z): _por['ya hay'] += 1; continue
        if any(np.hypot(x - q[0], z - q[2]) < 0.15 and abs(yb - q[1]) < 0.5 for q, _ in _nuevos): _por['cerca de otro'] += 1; continue
        _nuevos.append(((x, yb, z), hh))
    # control de fila doble: distancia de cada balaustre nuevo a la lámina de UC más cercana (a media altura)
    _alf = np.array([_tiene_alfa(m_) for m_ in _SMa]); _Sa = S[_alf]
    if len(_Sa) and _nuevos:
        _Ta = cKDTree(_Sa[:, [0, 2]]); _dd = []
        for (x_, yb_, z_), hh_ in _nuevos:
            ii = [j for j in _Ta.query_ball_point([x_, z_], 0.6) if yb_ + 0.2 * hh_ <= _Sa[j, 1] <= yb_ + 0.8 * hh_]
            _dd.append(min(np.hypot(_Sa[ii, 0] - x_, _Sa[ii, 2] - z_)) if ii else 9)
        _dd = np.array(_dd); print(f'  distancia a lámina de UC: <0.3 m: {(_dd < 0.3).sum()}, 0.3-0.6: {((_dd >= 0.3) & (_dd < 0.6)).sum()}, sin lámina cerca: {(_dd >= 0.6).sum()}')
        _nuevos = [n_ for n_, d_ in zip(_nuevos, _dd) if d_ >= 0.3]     # nada de segunda fila junto a una lámina
    for base_, h in _nuevos:
        Vp, Tp, Fp = _ex.torneado(base_, h, _ex.PERFIL_BALAUSTRE_LIGERO, escala_r=0.7, lados=6)
        _anade(Vp, Tp, Fp, mm_r)
    print(f'balaustres bajo pasamanos vacíos: {len(_nuevos)} (celdas {len(_celdas)}, descartes {_por})')
# barandilla por lógica: en los bordes del suelo pisable con caída real, sin pared, sin suelo al lado a la misma altura
# y sin barandilla de UC ya puesta. Nunca en mitad del paso.
if os.environ.get('BARANDILLA_CAIDAS'):
    _wall = np.nonzero(np.abs(nc[:, 1]) < 0.3)[0]
    _Wt = cKDTree(np.concatenate([np.random.default_rng(i).dirichlet([1, 1, 1], 12) @ Tc[i] for i in _wall])) if len(_wall) else None
    def _es_pared(x, y, z): return _Wt is not None and len(_Wt.query_ball_point([x, y, z], 0.18)) > 0
    _mrl = np.array([bool(_re2.search(r'handrail|tesuri', str(mats.get(m_) or m_), _re2.I)) for m_ in _SMa])
    _noalfa = np.array([not _tiene_alfa(m_) for m_ in _SMa]); _Sna = S[_noalfa]
    _Ht = cKDTree(_Sna[:, [0, 2]])
    def _ya_hay(x, y, z):          # algo macizo (no tarjetas con transparencia, que el juego no pinta bien) a la altura de los balaustres
        for j in _Ht.query_ball_point([x, z], 0.22):
            if y + 0.25 <= _Sna[j, 1] <= y + 0.8: return True
        return False
    _piso = np.nonzero(nc[:, 1] > 0.45)[0]; _pts = []
    for i in _piso:
        _tt = Tc[i]; cen = _tt.mean(0)
        for a_, b_ in ((_tt[0], _tt[1]), (_tt[1], _tt[2]), (_tt[2], _tt[0])):
            L = np.linalg.norm((b_ - a_)[[0, 2]])
            if L < 0.15: continue
            m = (a_ + b_) / 2; fuera = m - cen; fuera[1] = 0; fuera /= np.linalg.norm(fuera) + 1e-9
            d = (b_ - a_) / L
            perp = np.array([-d[2], 0, d[0]]);  perp = perp if perp @ fuera > 0 else -perp
            for s_ in np.arange(0.1, L, 0.2):
                p = a_ + (b_ - a_) * (s_ / L) + [0, 0, 0]
                p = p - perp * 0.05
                q = p + perp * 0.18; hs = _heights(_TF, q[0], q[2])
                if len(hs) and np.abs(hs - p[1]).min() < 0.35: continue          # suelo al otro lado: no es borde
                if not len(hs) or hs.max() > p[1] - 0.8: continue                    # sin caída real
                if _es_pared(*(p + perp * 0.1 + [0, 0.6, 0])): continue
                if _ya_hay(*p): continue
                _pts.append((tuple(np.round(p, 3)), tuple(perp)))
    # quitar repetidos y unir en tramos
    _u = []
    for p, n_ in _pts:
        if not any(np.hypot(p[0] - q[0], p[2] - q[2]) < 0.12 and abs(p[1] - q[1]) < 0.3 for q, _ in _u): _u.append((p, n_))
    _mm_v = next((m_ for m_, t_ in mats.items() if t_ and 'wood04' in t_), mm_r if _mr else None)
    nb2 = 0; nv = 0
    if _mm_v and _u:
        P_ = np.array([p for p, _ in _u]); arb = cKDTree(P_)
        for k, p in enumerate(P_):
            Vp, Tp, Fp = _ex.torneado(tuple(p), 0.93, _ex.PERFIL_BALAUSTRE_LIGERO, lados=4); _anade(Vp, Tp, Fp, _mm_v); nb2 += 1
            for j in arb.query_ball_point(p, 0.3):
                if j > k and abs(P_[j][1] - p[1]) < 0.5:
                    Vp, Tp, Fp = _ex.viga(P_[k] + [0, 0.95, 0], P_[j] + [0, 0.95, 0]); _anade(Vp, Tp, Fp, _mm_v); nv += 1
    print(f'barandilla por caída: {nb2} balaustres, {nv} tramos de pasamanos')
print(f'balaustres añadidos: {nb_}')
_cfg = f'/home/claude/re1gc/work/extras_{r}.json'
if os.path.exists(_cfg):
    cfg = json.load(open(_cfg))
    for col in cfg.get('columnas', []):
        mm = next((m_ for m_, t_ in mats.items() if t_ == col['textura']), None)
        if not mm: print('  textura de columna no encontrada', col['textura']); continue
        y0 = _alt(col['x'], col['z'], col['y1']) if col.get('y0') is None else col['y0']
        if y0 is None: continue
        Vp, Tp, Fp = _ex.torneado((col['x'], y0, col['z']), col['y1'] - y0, _ex.PERFIL_COLUMNA, escala_r=col['r'], lados=14, uv_vueltas=1, uv_alto=1.5)
        _anade(Vp, Tp, Fp, mm)
    print(f"columnas añadidas: {len(cfg.get('columnas', []))}")
    for cp_ in cfg.get('copiar', []):          # copiar una pieza de UC (puerta, lámpara, mueble) a otros sitios, girada
        lo_ = np.array(cp_['min']); hi_ = np.array(cp_['max']); cen_ = V[F[:, :3]].mean(1)
        sel_ = np.all((cen_ >= lo_) & (cen_ <= hi_), 1)
        if cp_.get('mat'): sel_ &= np.array([bool(_re2.search(cp_['mat'], str(mats.get(m_) or m_), _re2.I)) for m_ in FM])
        Fs_ = F[sel_]; Ms_ = FM[sel_]
        if not len(Fs_): print('  copiar: nada en', cp_.get('que')); continue
        P0 = V[Fs_[:, :3]].reshape(-1, 3); U0 = VT[Fs_[:, 3:]].reshape(-1, 2)
        org = np.array(cp_['origen'], float); th0 = np.arctan2(*cp_.get('frente', [0, 1]))          # frente de la pieza (x, z)
        for d_ in cp_['destinos']:
            th = np.arctan2(d_['frente'][0], d_['frente'][1]) - th0; c, s_ = np.cos(th), np.sin(th)
            L_ = P0 - org; Pn = np.stack([c * L_[:, 0] + s_ * L_[:, 2], L_[:, 1], -s_ * L_[:, 0] + c * L_[:, 2]], 1) + np.array(d_['punto'], float)
            for k_, m_ in enumerate(Ms_):
                _anade(Pn[3 * k_:3 * k_ + 3], U0[3 * k_:3 * k_ + 3], np.array([[0, 1, 2]]), m_)
        print(f"  copiado {cp_.get('que')}: {len(Fs_)} triángulos x {len(cp_['destinos'])}")
    for zs_ in cfg.get('suelo_junto_pared', []):          # tira de suelo pegada a las paredes altas: tapa la rendija entre el suelo de UC y la pared
        _cf = f'/home/claude/re1gc/salas/{r}/colision.obj'; _Vc = []; _Fc = []
        for l_ in open(_cf):
            if l_.startswith('v '): _Vc.append([float(x) for x in l_.split()[1:4]])
            elif l_.startswith('f '): _Fc.append([int(x.split('/')[0]) - 1 for x in l_.split()[1:4]])
        _Tc = np.array(_Vc)[np.array(_Fc)]; _nc = np.cross(_Tc[:, 1] - _Tc[:, 0], _Tc[:, 2] - _Tc[:, 0]); _nc /= np.linalg.norm(_nc, axis=1, keepdims=True) + 1e-12
        _cu = V[F[:, :3]]; _nu = np.cross(_cu[:, 1] - _cu[:, 0], _cu[:, 2] - _cu[:, 0]); _nu /= np.linalg.norm(_nu, axis=1, keepdims=True) + 1e-12
        _hz = np.abs(_nu[:, 1]) > 0.9; _ch = _cu[_hz].mean(1); _mh = FM[_hz]; _kh = cKDTree(_ch)
        nst = 0
        for t3, nn in zip(_Tc, _nc):
            if abs(nn[1]) > 0.3 or np.ptp(t3[:, 1]) < zs_.get('alto_min', 2.0): continue
            ya_ = t3[:, 1].min()
            if not (zs_['y0'] <= ya_ <= zs_['y1']): continue
            nh = np.array([nn[0], 0, nn[2]]) / (np.hypot(nn[0], nn[2]) + 1e-12)
            c_ = t3.mean(0); hs1 = _heights(_TF, *(c_ + nh * 0.3)[[0, 2]]); hs2 = _heights(_TF, *(c_ - nh * 0.3)[[0, 2]])
            ok1 = len(hs1) and np.abs(hs1 - ya_).min() < 0.15; ok2 = len(hs2) and np.abs(hs2 - ya_).min() < 0.15
            if ok1 == ok2: continue
            if not ok1: nh = -nh
            h_ = np.array([-nh[2], 0, nh[0]]); pr = t3 @ h_; A_ = t3[pr.argmin()] * [1, 0, 1] + [0, ya_ + 0.006, 0]; B_ = t3[pr.argmax()] * [1, 0, 1] + [0, ya_ + 0.006, 0]
            if np.linalg.norm(B_ - A_) < 0.05: continue
            d_, j_ = _kh.query(((A_ + B_) / 2 + nh * 0.6) * [1, 1, 1], k=8); cand = [_mh[k] for k, dd in zip(j_, d_) if abs(_ch[k][1] - ya_) < 0.3]
            if not cand: continue
            from collections import Counter as _Cn
            mm_ = _Cn(cand).most_common(1)[0][0]; W_ = zs_.get('ancho', 0.4)
            q = np.array([A_ - nh * 0.03, B_ - nh * 0.03, B_ + nh * W_, A_ + nh * W_])
            _anade(q, q[:, [0, 2]] / 1.2, np.array([[0, 1, 2], [0, 2, 3]]), mm_); nst += 1
            if zs_.get('rodapie'):          # rodapié: tapa la rendija vertical entre la pared y el suelo
                mr_ = next((m_ for m_ in set(FM) if _re2.search(zs_['rodapie'], str(mats.get(m_) or m_))), None)
                if mr_ is not None:
                    a2 = A_ + nh * 0.02; b2 = B_ + nh * 0.02; L2 = np.linalg.norm(B_ - A_)
                    q = np.array([a2 - [0, 0.08, 0], b2 - [0, 0.08, 0], b2 + [0, zs_.get('alto_rodapie', 0.28), 0], a2 + [0, zs_.get('alto_rodapie', 0.28), 0]])
                    _anade(q, np.array([[0, 0], [L2 / 0.6, 0], [L2 / 0.6, 0.5], [0, 0.5]]), np.array([[0, 1, 2], [0, 2, 3]]), mr_)
        print(f'  tiras de suelo junto a la pared: {nst}')
    for sb_ in cfg.get('suelo_bajo', []):          # suelo de respaldo un poco por debajo del pisable (ensanchado): lo que asome por las rendijas es alfombra, no el vacío
        from scipy import ndimage as _nd2
        mb_ = next((m_ for m_ in set(FM) if _re2.search(sb_['mat'], str(mats.get(m_) or m_))), None)
        G2 = 0.1; nsb = 0
        for cj in sb_['cajas']:
            xs2 = np.arange(cj[0], cj[1], G2); zs2 = np.arange(cj[2], cj[3], G2); Mk2 = np.zeros((len(xs2), len(zs2)), bool)
            for ii, x_ in enumerate(xs2):
                for jj, z_ in enumerate(zs2):
                    h_ = _heights(_TF, x_ + G2 / 2, z_ + G2 / 2); Mk2[ii, jj] = len(h_) > 0 and np.abs(h_ - sb_['y']).min() < sb_.get('tol', 0.15)
            Mk2 = _nd2.binary_dilation(Mk2, iterations=int(sb_.get('dilatar', 0.4) / G2))
            yb_ = sb_['y'] - sb_.get('bajo', 0.03)
            for ii in range(len(xs2)):
                jj = 0
                while jj < len(zs2):
                    if Mk2[ii, jj]:
                        j0 = jj
                        while jj < len(zs2) and Mk2[ii, jj]: jj += 1
                        q = np.array([[xs2[ii], yb_, zs2[j0]], [xs2[ii] + G2, yb_, zs2[j0]], [xs2[ii] + G2, yb_, zs2[jj - 1] + G2], [xs2[ii], yb_, zs2[jj - 1] + G2]])
                        _anade(q, q[:, [0, 2]] / 1.2, np.array([[0, 1, 2], [0, 2, 3]]), mb_); nsb += 1
                    else: jj += 1
        print(f'  suelo de respaldo: {nsb} tiras')
    for es_ in cfg.get('escaleras', []):          # tramo de escalera que UC no tiene (solo dejaba ver el techo de abajo como franjas)
        mh_ = next((m_ for m_ in set(FM) if _re2.search(es_['huella'], str(mats.get(m_) or m_))), None)
        mt_ = next((m_ for m_ in set(FM) if _re2.search(es_['tabica'], str(mats.get(m_) or m_))), None) or mh_
        x0, x1, z0, z1, y0, y1 = es_['x0'], es_['x1'], es_['z0'], es_['z1'], es_['y0'], es_['y1']
        N = max(2, int(round((y1 - y0) / 0.17))); ru = (z1 - z0) / N; ri = (y1 - y0) / N; E_ = 0.6
        for k in range(N):
            za, zb = z0 + k * ru, z0 + (k + 1) * ru; yt = y0 + (k + 1) * ri; yb_ = y0 + k * ri
            q = np.array([[x0, yt, za], [x1, yt, za], [x1, yt, zb], [x0, yt, zb]])
            _anade(q, q[:, [0, 2]] / E_, np.array([[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]]), mh_)
            q = np.array([[x0, yb_ - 0.02, za], [x1, yb_ - 0.02, za], [x1, yt, za], [x0, yt, za]])
            _anade(q, q[:, [0, 1]] / E_, np.array([[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]]), mt_)
            for xx in (x0, x1):
                q = np.array([[xx, y0 - 0.3, za], [xx, y0 - 0.3, zb], [xx, yt, zb], [xx, yt, za]])
                _anade(q, q[:, [2, 1]] / E_, np.array([[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]]), mt_)
        print(f"  escalera añadida: {N} peldaños en x {x0}..{x1}")
    for br_ in cfg.get('brazos', []):           # lámparas de pared que UC dejó flotando: brazo de metal hasta la pared
        import scipy.sparse as _sp
        from scipy.sparse.csgraph import connected_components as _cc
        sel_ = np.nonzero(np.array([bool(_re2.search(br_['mat'], str(m_) + ' ' + str(mats.get(m_) or ''))) for m_ in FM]))[0]
        if not len(sel_): print('  brazos: material no encontrado', br_['mat']); continue
        mm_b = next((m_ for m_ in set(FM) if _re2.search(br_['metal'], str(m_) + ' ' + str(mats.get(m_) or ''))), FM[sel_[0]])
        Fs_ = F[sel_, :3]; _, inv_ = np.unique(np.round(V[Fs_.ravel()] * 100).astype(np.int64), axis=0, return_inverse=True); inv_ = inv_.reshape(-1, 3)
        nvv = inv_.max() + 1; A_ = _sp.coo_matrix((np.ones(len(inv_) * 2), (np.r_[inv_[:, 0], inv_[:, 1]], np.r_[inv_[:, 1], inv_[:, 2]])), shape=(nvv, nvv))
        ncc, lab_ = _cc(A_, directed=False); labf = lab_[inv_[:, 0]]
        _ok = np.array([not _re2.search(br_['mat'] + '|' + br_.get('ignorar', '^$'), str(m_) + ' ' + str(mats.get(m_) or '')) for m_ in _SMa])
        _Sb = S[_ok]; _Tb = cKDTree(_Sb[:, [0, 2]]); hechos = 0
        # agrupar piezas cercanas (una lámpara puede ser varias piezas sueltas)
        cents = [V[Fs_[labf == c]].reshape(-1, 3) for c in range(ncc)]
        grupos = []
        for P_ in cents:
            c_ = P_.mean(0)
            for g in grupos:
                if np.hypot(*(g['c'][[0, 2]] - c_[[0, 2]])) < br_.get('agrupar', 0.35) and abs(g['c'][1] - c_[1]) < 0.6: g['P'] = np.r_[g['P'], P_]; g['c'] = g['P'].mean(0); break
            else: grupos.append(dict(P=P_, c=c_))
        for g in grupos:
            P_ = g['P']; lo_ = P_.min(0); hi_ = P_.max(0); cx, cz = (lo_[0] + hi_[0]) / 2, (lo_[2] + hi_[2]) / 2
            yb = hi_[1] - br_.get('baja', 0.0); ya = yb + br_.get('sube', 0.12)
            r_ = max(hi_[0] - lo_[0], hi_[2] - lo_[2]) / 2
            mejor = None
            for j in _Tb.query_ball_point([cx, cz], r_ + br_.get('alcance', 0.8)):
                q = _Sb[j]
                if not (ya - 0.25 <= q[1] <= ya + 0.25): continue
                dd = np.hypot(q[0] - cx, q[2] - cz)
                if dd < r_ * 0.6: continue
                if mejor is None or dd < mejor[0]: mejor = (dd, q)
            if mejor is None: continue
            w = np.array([mejor[1][0], ya, mejor[1][2]]); arr = np.array([cx, ya, cz]); dirw = (w - arr) / (np.linalg.norm(w - arr) + 1e-9)
            w = w + dirw * 0.03
            Vp, Tp, Fp = _ex.tubo(arr + [0, 0.0, 0], w, br_.get('r', 0.022), br_.get('r', 0.022) * 1.3, lados=8); _anade(Vp, Tp, Fp, mm_b)
            Vp, Tp, Fp = _ex.tubo(np.array([cx, yb - 0.02, cz]), arr + [0, 0.02, 0], br_.get('r', 0.022) * 0.9, br_.get('r', 0.022), lados=8); _anade(Vp, Tp, Fp, mm_b)
            Vp, Tp, Fp = _ex.tubo(w - dirw * 0.035, w + dirw * 0.01, 0.06, 0.07, lados=10); _anade(Vp, Tp, Fp, mm_b)          # roseta en la pared
            hechos += 1
        print(f"  brazos de {br_['mat']}: {hechos} de {len(grupos)} lámparas")
    for aj in cfg.get('ajustar', []):          # encajar una pieza en una caja (p. ej. una hoja de puerta en su marco)
        lo = np.array(aj['min']); hi = np.array(aj['max']); dlo = np.array(aj['a_min']); dhi = np.array(aj['a_max'])
        cen_ = V[F[:, :3]].mean(1)
        sel_ = np.all((cen_ >= lo) & (cen_ <= hi), 1) & np.array([bool(_re2.search(aj['mat'], str(mats.get(m_) or m_), _re2.I)) for m_ in FM])
        idx_ = np.unique(F[sel_, :3]); P_ = V[idx_]; plo = P_.min(0); phi = P_.max(0)
        V = V.copy(); V[idx_] = dlo + (P_ - plo) / np.maximum(phi - plo, 1e-6) * (dhi - dlo)
        print(f"  ajustada {aj.get('que', '')}: {sel_.sum()} triángulos")
    for rx_ in cfg.get('cerrar', []):          # telas abiertas (UC solo modeló la cara que ve su cámara): envolvente convexa por pieza
        from scipy.spatial import ConvexHull
        import scipy.sparse as _sp
        from scipy.sparse.csgraph import connected_components as _cc
        sel_ = np.nonzero(np.array([bool(_re2.search(rx_, str(mats.get(m_) or m_), _re2.I)) for m_ in FM]))[0]
        if not len(sel_): continue
        Fs_ = F[sel_, :3]; _, inv_ = np.unique(np.round(V[Fs_.ravel()] * 200).astype(np.int64), axis=0, return_inverse=True); inv_ = inv_.reshape(-1, 3)
        nvv = inv_.max() + 1; A_ = _sp.coo_matrix((np.ones(len(inv_) * 2), (np.r_[inv_[:, 0], inv_[:, 1]], np.r_[inv_[:, 1], inv_[:, 2]])), shape=(nvv, nvv))
        ncc_, lab_ = _cc(A_, directed=False); tl_ = lab_[inv_[:, 0]]
        quitar_ = np.zeros(len(F), bool); hechas = 0
        for k_ in range(ncc_):
            tt_ = sel_[tl_ == k_]
            if len(tt_) < 6: continue
            pts_ = V[F[tt_, :3].ravel()]
            if np.ptp(pts_, 0).min() < 0.05: continue
            try: H_ = ConvexHull(pts_)
            except Exception: continue
            hv = pts_[H_.vertices].copy(); mp_ = {v: i for i, v in enumerate(H_.vertices)}
            # que no atraviese paredes: rayo desde el centro de la tela a cada vértice contra las paredes de la colisión
            _cw2 = np.nonzero(np.abs(nc[:, 1]) < 0.35)[0]; c0_ = pts_.mean(0)
            Wt_ = Tc[_cw2]; Wt_ = Wt_[np.linalg.norm(Wt_.mean(1) - c0_, axis=1) < 4]
            if len(Wt_):
                e1 = Wt_[:, 1] - Wt_[:, 0]; e2 = Wt_[:, 2] - Wt_[:, 0]
                for iv in range(len(hv)):
                    dvec = hv[iv] - c0_; pv = np.cross(dvec, e2); det = (e1 * pv).sum(1); ok_ = np.abs(det) > 1e-9
                    inv = np.where(ok_, 1 / np.where(ok_, det, 1), 0); tv = c0_ - Wt_[:, 0]
                    u_ = (tv * pv).sum(1) * inv; qv = np.cross(tv, e1); v_ = (dvec[None] * qv).sum(1) * inv; t_ = (e2 * qv).sum(1) * inv
                    hit = ok_ & (u_ >= 0) & (v_ >= 0) & (u_ + v_ <= 1) & (t_ > 0) & (t_ < 1)
                    if hit.any(): hv[iv] = c0_ + dvec * max(0.0, t_[hit].min() - 0.04 / (np.linalg.norm(dvec) + 1e-9))
            tris = np.array([[mp_[a_] for a_ in sx] for sx in H_.simplices])
            # orientar hacia fuera
            cc_ = hv.mean(0); n_ = np.cross(hv[tris[:, 1]] - hv[tris[:, 0]], hv[tris[:, 2]] - hv[tris[:, 0]])
            flip = ((hv[tris].mean(1) - cc_) * n_).sum(1) < 0; tris[flip] = tris[flip][:, ::-1]
            Vt_ = hv[tris.ravel()]; nn2 = np.repeat(np.cross(Vt_[1::3] - Vt_[0::3], Vt_[2::3] - Vt_[0::3]), 3, 0)
            ax_ = np.abs(nn2).argmax(1)
            uvt = np.where(ax_[:, None] == 1, Vt_[:, [0, 2]], np.where(ax_[:, None] == 0, Vt_[:, [2, 1]], Vt_[:, [0, 1]])) / 1.2
            _anade(Vt_, uvt, np.arange(len(Vt_)).reshape(-1, 3), FM[tt_[0]]); quitar_[tt_] = True; hechas += 1
        F = F[~quitar_]; FM = FM[~quitar_]
        print(f'  telas cerradas ({rx_}): {hechas}')
    for rc in cfg.get('reconstruir', []):
        lo = np.array(rc['min']); hi = np.array(rc['max']); E_ = rc.get('escala', 1.5)
        cen_ = V[F[:, :3]].mean(1); dentro_ = np.all((cen_ >= lo) & (cen_ <= hi), 1)
        if rc.get('conservar'): dentro_ &= np.array([not _re2.search(rc['conservar'], str(mats.get(m_) or m_), _re2.I) for m_ in FM])
        F = F[~dentro_]; FM = FM[~dentro_]
        def _mk(tex):
            mk = tex[:-4]; mats[mk] = tex; return mk
        def _quad(p0, p1, y0, y1, tex, ulen, ajustar_v=False):
            q = np.array([[p0[0], y0, p0[1]], [p1[0], y0, p1[1]], [p1[0], y1, p1[1]], [p0[0], y1, p0[1]]])
            uv = np.array([[0, y0], [ulen, y0], [ulen, y1], [0, y1]]) / E_
            if ajustar_v: uv = np.array([[0, 0], [ulen / E_, 0], [ulen / E_, 1], [0, 1]])          # la textura entera en la altura de la banda
            _anade(q, uv, np.array([[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]]), _mk(tex))     # dos caras
        ns_ = np.zeros(3, int)
        # zona pisable en rejilla (con margen), agujeros interiores (objetos) rellenos -> solo el contorno exterior lleva pared
        from scipy import ndimage as _nd
        from skimage import measure as _ms
        G_ = 0.05; mg = 0.6; xs_ = np.arange(lo[0] - mg, hi[0] + mg, G_); zs_ = np.arange(lo[2] - mg, hi[2] + mg, G_)
        Mk = np.zeros((len(xs_), len(zs_)), bool)
        for ii, x_ in enumerate(xs_):
            for jj, z_ in enumerate(zs_):
                h_ = _heights(_TF, x_, z_); Mk[ii, jj] = len(h_) > 0 and np.abs(h_ - rc['y_suelo']).min() < rc.get('tol_suelo', 0.3)
        Mk = _nd.binary_fill_holes(_nd.binary_closing(Mk, iterations=2))
        _mp = rc.get('margen_pared', -0.02)
        dentro_box = lambda x_, z_: lo[0] - _mp < x_ < hi[0] + _mp and lo[2] - _mp < z_ < hi[2] + _mp
        y0 = rc['y_suelo']; zh = y0 + rc.get('zocalo_h', 0.9)
        if rc.get('solo_paredes_colision'):          # solo donde la colisión tiene pared (no en la boca de una escalera o un paso)
            _cf = f'/home/claude/re1gc/salas/{r}/colision.obj'; _Vc = []; _Fc = []
            for l_ in open(_cf):
                if l_.startswith('v '): _Vc.append([float(x) for x in l_.split()[1:4]])
                elif l_.startswith('f '): _Fc.append([int(x.split('/')[0]) - 1 for x in l_.split()[1:4]])
            _Tc = np.array(_Vc)[np.array(_Fc)]; _nc = np.cross(_Tc[:, 1] - _Tc[:, 0], _Tc[:, 2] - _Tc[:, 0]); _nc /= np.linalg.norm(_nc, axis=1, keepdims=True) + 1e-12
            _Tc = _Tc[(np.abs(_nc[:, 1]) < 0.3) & (_Tc[:, :, 1].max(1) > y0 + 0.5) & (_Tc[:, :, 1].min(1) < y0 + 0.5)]
            _Pc = np.concatenate([np.random.default_rng(0).dirichlet([1, 1, 1], 40) @ t_ for t_ in _Tc]) if len(_Tc) else np.zeros((1, 3)) + 1e9
            _Kc = cKDTree(_Pc[:, [0, 2]])
        _cornisa = rc.get('cornisa_h', 0.0)
        for cont in _ms.find_contours(np.pad(Mk.astype(float), 1), 0.5):
            cont = _ms.approximate_polygon(cont - 1, tolerance=1.2)
            pts = np.stack([xs_[0] + cont[:, 0] * G_, zs_[0] + cont[:, 1] * G_], 1)
            for p0, p1 in zip(pts[:-1], pts[1:]):
                m_ = (p0 + p1) / 2; L_ = np.linalg.norm(p1 - p0)
                if L_ < 0.04 or not dentro_box(*m_): continue
                if rc.get('solo_paredes_colision') and not _Kc.query_ball_point(m_, 0.3): continue
                _quad(p0, p1, y0, zh, rc['zocalo'], L_, rc.get('zocalo_entero', False)); _quad(p0, p1, zh, zh + 0.08, rc.get('moldura', rc['zocalo']), L_)
                _quad(p0, p1, zh + 0.08, rc['y_techo'] - _cornisa, rc['pared'], L_)
                if _cornisa: _quad(p0, p1, rc['y_techo'] - _cornisa, rc['y_techo'], rc.get('moldura', rc['zocalo']), L_)
                ns_[2] += 1
        # suelo y techo: filas de la silueta dentro de la caja
        for ii, x_ in enumerate(xs_):
            _mt = max(_mp, 0.0)
            if not (lo[0] - _mt <= x_ < hi[0] + _mt): continue
            jj = 0
            while jj < len(zs_):
                if Mk[ii, jj] and lo[2] - _mt <= zs_[jj] < hi[2] + _mt:
                    j0 = jj
                    while jj < len(zs_) and Mk[ii, jj] and zs_[jj] < hi[2] + _mt: jj += 1
                    za, zb = zs_[j0], zs_[jj - 1] + G_; xa, xb = x_, x_ + G_
                    for yy, tex, inv in ((y0, rc['suelo'], False), (rc['y_techo'], rc['techo'], True)):
                        q = np.array([[xa, yy, za], [xb, yy, za], [xb, yy, zb], [xa, yy, zb]])
                        _anade(q, q[:, [0, 2]] / E_, np.array([[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]]), _mk(tex))
                    ns_[0] += 1
                else: jj += 1
        print(f"  reconstruido {rc.get('que', '')}: quitados {dentro_.sum()} de UC; suelo {ns_[0]}, techo {ns_[1]}, paredes {ns_[2]}")
    for rz in cfg.get('retexturizar', []):
        lo = np.array(rz['min']); hi = np.array(rz['max'])
        P3_ = V[F[:, :3]]; cen_ = P3_.mean(1); dentro_ = np.all((cen_ >= lo) & (cen_ <= hi), 1)
        nn_ = np.cross(P3_[:, 1] - P3_[:, 0], P3_[:, 2] - P3_[:, 0]); nn_ /= np.linalg.norm(nn_, axis=1, keepdims=True) + 1e-12
        if rz.get('excluir'): dentro_ &= np.array([not _re2.search(rz['excluir'], str(mats.get(m_) or m_), _re2.I) for m_ in FM])
        idx_ = np.nonzero(dentro_)[0]
        def _mk(tex):
            mk = tex[:-4]; mats[mk] = tex; return mk
        nV_ = []; nT_ = []; nF_ = []; nM_ = []
        for i in idx_:
            t3 = P3_[i]; n_ = nn_[i]; yc = cen_[i, 1]
            if any(np.all((cen_[i] >= np.array(d_['min'])) & (cen_[i] <= np.array(d_['max']))) and abs(n_[d_['eje']]) > 0.8 for d_ in rz.get('descartar', [])): continue
            if n_[1] > 0.7 and yc < rz['y_suelo'] + 0.3: tex = rz['suelo']
            elif n_[1] < -0.7 and yc > rz['y_techo'] - 0.5: tex = rz['techo']
            elif abs(n_[1]) > 0.7: tex = rz.get('moldura', rz['pared'])          # repisas y cornisas: madera, nunca la tela girada
            elif yc < rz['y_suelo'] + rz.get('zocalo', 0.25): tex = rz.get('moldura', rz['pared'])
            elif yc > rz['y_techo'] - rz.get('cornisa', 0.25): tex = rz.get('moldura', rz['pared'])
            else: tex = rz['pared']
            a_ = np.abs(n_).argmax(); uv = t3[:, [k for k in range(3) if k != a_]] / rz.get('escala', 1.2)
            if a_ != 1: uv = t3[:, [2 if a_ == 0 else 0, 1]] / rz.get('escala', 1.2)
            _anade(t3.copy(), uv, np.array([[0, 1, 2]]), _mk(tex))
        keep_ = np.ones(len(F), bool); keep_[idx_] = False; F = F[keep_]; FM = FM[keep_]
        if rz.get('techo_colision'):
            nt_ = 0
            for t3 in Tc[nc[:, 1] > 0.7]:
                c_ = t3.mean(0)
                if np.all((c_ >= lo) & (c_ <= hi)):
                    q3 = t3.copy(); q3[:, 1] = rz['y_techo']; q3 = q3[::-1]
                    _anade(q3, q3[:, [0, 2]] / rz.get('escala', 1.2), np.array([[0, 1, 2]]), _mk(rz['techo'])); nt_ += 1
            if rz.get('paredes_colision'):          # paredes desde el contorno pisable, un poco por detrás: tapan los huecos de UC
                from scipy import ndimage as _nd
                from skimage import measure as _ms
                G_ = 0.05; mg = 0.6; xs_ = np.arange(lo[0] - mg, hi[0] + mg, G_); zs_ = np.arange(lo[2] - mg, hi[2] + mg, G_)
                Mk = np.zeros((len(xs_), len(zs_)), bool)
                for ii, x_ in enumerate(xs_):
                    for jj, z_ in enumerate(zs_):
                        h_ = _heights(_TF, x_, z_); Mk[ii, jj] = len(h_) > 0 and np.abs(h_ - rz['y_suelo']).min() < 0.3
                Mk = _nd.binary_fill_holes(_nd.binary_closing(Mk, iterations=2)); Mk = _nd.binary_dilation(Mk, iterations=1)
                npw = 0; E_ = rz.get('escala', 1.2)
                for cont in _ms.find_contours(np.pad(Mk.astype(float), 1), 0.5):
                    cont = _ms.approximate_polygon(cont - 1, tolerance=1.2)
                    pts = np.stack([xs_[0] + cont[:, 0] * G_, zs_[0] + cont[:, 1] * G_], 1)
                    for p0, p1 in zip(pts[:-1], pts[1:]):
                        m_ = (p0 + p1) / 2; L_ = np.linalg.norm(p1 - p0)
                        if L_ < 0.04 or not (lo[0] - 0.1 < m_[0] < hi[0] + 0.1 and lo[2] - 0.1 < m_[1] < hi[2] + 0.1): continue
                        for (ya_, yb_, tx_) in ((rz['y_suelo'], rz['y_suelo'] + rz.get('zocalo', 0.25), rz.get('moldura', rz['pared'])), (rz['y_suelo'] + rz.get('zocalo', 0.25), rz['y_techo'], rz['pared'])):
                            q = np.array([[p0[0], ya_, p0[1]], [p1[0], ya_, p1[1]], [p1[0], yb_, p1[1]], [p0[0], yb_, p0[1]]])
                            uv = np.array([[0, ya_], [L_, ya_], [L_, yb_], [0, yb_]]) / E_
                            _anade(q, uv, np.array([[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]]), _mk(tx_))
                        npw += 1
                print(f'  paredes de respaldo: {npw}')
            if rz.get('techo_caja'):
                q3 = np.array([[lo[0], rz['y_techo'], lo[2]], [hi[0], rz['y_techo'], lo[2]], [hi[0], rz['y_techo'], hi[2]], [lo[0], rz['y_techo'], hi[2]]])
                _anade(q3, q3[:, [0, 2]] / rz.get('escala', 1.2), np.array([[0, 1, 2], [0, 2, 3], [0, 2, 1], [0, 3, 2]]), _mk(rz['techo'])); nt_ += 4
            print(f'  techo añadido: {nt_} triángulos')
        print(f"  retexturizado {rz.get('que', '')}: {len(idx_)} triángulos")
    for md in cfg.get('modelos', []):          # modelo .obj propio (p. ej. estatua hecha desde fotos), con sus texturas ya en la carpeta de la sala
        Vm_ = []; VTm_ = []; Fm_ = []; Mm_ = []; cur_ = None
        for l_ in open(md['obj']):
            if l_.startswith('v '): Vm_.append([float(x) for x in l_.split()[1:4]])
            elif l_.startswith('vt '): VTm_.append([float(x) for x in l_.split()[1:3]])
            elif l_.startswith('usemtl'): cur_ = l_.split()[1]
            elif l_.startswith('f '):
                q_ = [x.split('/') for x in l_.split()[1:4]]; Fm_.append([int(a_[0]) - 1 for a_ in q_] + [int(a_[1]) - 1 for a_ in q_]); Mm_.append(cur_)
        Vm_ = np.array(Vm_) * md.get('escala', 1.0); VTm_ = np.array(VTm_); Fm_ = np.array(Fm_)
        g_ = md.get('giro', 0.0); c_, s_ = np.cos(g_), np.sin(g_)
        Vm_ = Vm_ @ np.array([[c_, 0, -s_], [0, 1, 0], [s_, 0, c_]]) + [md['x'], md['y0'], md['z']]
        for mat_, tex_ in md['texturas'].items():
            sel_ = np.array([m_ == mat_ for m_ in Mm_])
            if not sel_.any(): continue
            mk_ = tex_[:-4]; mats[mk_] = tex_
            # cada triángulo con sus propios vértices de UV
            Fs_ = Fm_[sel_]; Vv_ = Vm_[Fs_[:, :3].ravel()]; Tt_ = VTm_[Fs_[:, 3:].ravel()]
            _anade(Vv_, Tt_, np.arange(len(Vv_)).reshape(-1, 3), mk_)
        print(f"  modelo {os.path.basename(md['obj'])} añadido en", md['x'], md['z'])
    for es in cfg.get('estatuas', []):
        mm = next((m_ for m_, t_ in mats.items() if t_ == es['textura']), None)
        if not mm and os.path.exists(os.path.join(base, es['textura'])): mm = es['textura'][:-4]; mats[mm] = es['textura']
        if not mm: print('  textura de estatua no encontrada', es['textura']); continue
        Vp, Tp, Fp = (_ex.estatua_busto if es.get('tipo') == 'busto' else _ex.estatua)((es['x'], es['y0'], es['z']), es.get('alto', 1.15), es.get('giro', 0.0))
        if es.get('sombreado'):
            # sombreado horneado: 4 tonos según la luz de los focos (de arriba y de frente)
            g_ = es.get('giro', 0.0); ld = np.array([0.35 * np.cos(g_) + 0.55 * np.sin(g_), 1.0, -0.35 * np.sin(g_) + 0.55 * np.cos(g_)]); ld /= np.linalg.norm(ld)
            nn_ = np.cross(Vp[Fp[:, 1]] - Vp[Fp[:, 0]], Vp[Fp[:, 2]] - Vp[Fp[:, 0]]); nn_ /= np.linalg.norm(nn_, axis=1, keepdims=True) + 1e-12
            cen_ = Vp[Fp].mean(1); cen0 = Vp.mean(0)
            nn_ *= np.sign(((cen_ - cen0) * nn_).sum(1, keepdims=True) + 1e-9)          # normales hacia fuera
            k_ = np.clip(3 - np.floor((nn_ @ ld + 0.2) / 1.2 * 4), 0, 3).astype(int)
            for kk in range(4):
                sel_ = k_ == kk
                if not sel_.any(): continue
                tx_ = es['sombreado'].format(kk); mk = tx_[:-4]; mats[mk] = tx_
                _anade(Vp, Tp, Fp[sel_], mk)
        else: _anade(Vp, Tp, Fp, mm)
        print('  estatua añadida en', es['x'], es['z'])
    # quitar lo de UC que estorbe (cajas a eliminar)
    for q in cfg.get('quitar', []):
        lo = np.array(q['min']); hi = np.array(q['max'])
        cen_ = V[F[:, :3]].mean(1); fuera = ~np.all((cen_ >= lo) & (cen_ <= hi), 1)
        if q.get('mat'): fuera |= np.array([not _re2.search(q['mat'], str(mats.get(m_) or m_), _re2.I) for m_ in FM])
        if q.get('eje') is not None:
            P3q = V[F[:, :3]]; nq = np.cross(P3q[:, 1] - P3q[:, 0], P3q[:, 2] - P3q[:, 0]); nq /= np.linalg.norm(nq, axis=1, keepdims=True) + 1e-12
            fuera |= np.abs(nq[:, q['eje']]) < 0.8
        print(f"  quitados {np.sum(~fuera)} triángulos de UC en {q.get('que', '')}")
        F = F[fuera]; FM = FM[fuera]

# pasamanos de UC que cruzan por mitad de un suelo pisable del REmake (UC tiene hueco de escalera donde el REmake tiene rellano)
_mrail = np.array([bool(_re2.search(r'handrail|tesuri', str(mats.get(m_) or m_), _re2.I)) for m_ in FM])
if _mrail.any():
    _cen = V[F[:, :3]].mean(1); _quita = np.zeros(len(F), bool)
    def _suelo_bajo(x, z, y):
        h = _heights(_TF, x, z); h = h[(h < y - 0.25) & (h > y - 1.5)]
        return float(h.max()) if len(h) else None
    _dirs = [(np.cos(t) * rr, np.sin(t) * rr) for rr in (0.0, 0.35, 0.7) for t in np.linspace(0, 2 * np.pi, 8, endpoint=False)]
    for i in np.nonzero(_mrail)[0]:
        x, y, z = _cen[i]
        vals = [_suelo_bajo(x + dx, z + dz, y) for dx, dz in _dirs]
        hay = [v for v in vals if v is not None]
        if not hay:
            # barra en el aire solo si todo el triángulo queda alto: ningún suelo cercano a menos de 0,6 m de su punto más bajo
            ymin = V[F[i, :3], 1].min(); cerca_ = []
            for dx, dz in _dirs:
                hh_ = _heights(_TF, x + dx, z + dz); hh_ = hh_[hh_ <= ymin + 0.05]
                if len(hh_): cerca_.append(ymin - hh_.max())
            if not cerca_ or min(cerca_) > 0.6: _quita[i] = True
            continue
        h0 = vals[0]
        if h0 is not None and all(v is not None and abs(v - h0) < 0.08 for v in vals[:17]): _quita[i] = True   # en mitad de un suelo
        # tumbado sobre un suelo plano: todo el triángulo a menos de 55 cm del suelo que tiene debajo
        hh_ = _heights(_TF, x, z); ymin_ = V[F[i, :3], 1].min(); ymax_ = V[F[i, :3], 1].max(); hh_ = hh_[hh_ <= ymin_ + 0.05]
        if len(hh_) and ymax_ - hh_.max() < 0.55:
            ok_ = [_heights(_TF, x + dx, z + dz) for dx, dz in ((0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3))]
            if all(len(o_) and np.abs(o_ - hh_.max()).min() < 0.05 for o_ in ok_): _quita[i] = True
    print(f'pasamanos sobre suelo pisable quitados: {_quita.sum()} triángulos')
    F = F[~_quita]; FM = FM[~_quita]
# paredes de UC en mitad del paso del REmake (UC tiene otro trazado): suelo pisable a la misma altura a los dos lados
if os.environ.get('QUITAR_PAREDES_PASO'):
    _P3 = V[F[:, :3]]; _nn = np.cross(_P3[:, 1] - _P3[:, 0], _P3[:, 2] - _P3[:, 0]); _aa = np.linalg.norm(_nn, axis=1); _nn /= _aa[:, None] + 1e-12
    _vert = np.nonzero((np.abs(_nn[:, 1]) < 0.3) & (_aa > 1e-6))[0]; _qp = np.zeros(len(F), bool)
    _cw = np.nonzero(np.abs(nc[:, 1]) < 0.3)[0]
    _CWt = cKDTree(np.concatenate([np.random.default_rng(i).dirichlet([1, 1, 1], 30) @ Tc[i] for i in _cw])[:, [0, 2]]) if len(_cw) else None
    for i in _vert:
        c_ = _P3[i].mean(0); h_ = _heights(_TF, c_[0], c_[2]); h_ = h_[h_ <= c_[1] + 0.05]
        if not len(h_): continue
        y0_ = h_.max()
        if c_[1] - y0_ > 2.4 or _P3[i][:, 1].min() - y0_ > 0.4: continue
        if _CWt is not None and _CWt.query_ball_point(c_[[0, 2]], 0.4): continue      # el REmake tiene pared ahí: se queda
        dd = _nn[i].copy(); dd[1] = 0; dd /= np.linalg.norm(dd) + 1e-9
        ok_ = True
        for sgn in (1, -1):
            for off in (0.3, 0.6):
                q_ = c_ + dd * sgn * off; hh_ = _heights(_TF, q_[0], q_[2])
                if not len(hh_) or np.abs(hh_ - y0_).min() > 0.05: ok_ = False; break
            if not ok_: break
        _qp[i] = ok_
    print(f'paredes de UC en mitad del paso quitadas: {_qp.sum()} triángulos')
    F = F[~_qp]; FM = FM[~_qp]
# barandillas en zonas marcadas a mano (config 'barandillas_zonas': [xmin, xmax, zmin, zmax]): en cada borde con caída o hueco
if os.path.exists(f'/home/claude/re1gc/work/extras_{r}.json') and json.load(open(f'/home/claude/re1gc/work/extras_{r}.json')).get('barandillas_zonas'):
    _zonas = json.load(open(f'/home/claude/re1gc/work/extras_{r}.json'))['barandillas_zonas']
    _wall2 = np.nonzero(np.abs(nc[:, 1]) < 0.3)[0]
    _W2 = cKDTree(np.concatenate([np.random.default_rng(i).dirichlet([1, 1, 1], 12) @ Tc[i] for i in _wall2])) if len(_wall2) else None
    _G = 0.1; _pz = []
    def _hmax(x, z):
        h = _heights(_TF, x, z); return float(h.max()) if len(h) else None
    for x0, x1, z0, z1 in _zonas:
        for x in np.arange(x0, x1 + 1e-6, _G):
            for z in np.arange(z0, z1 + 1e-6, _G):
                h = _hmax(x, z)
                if h is None: continue
                for dx, dz in ((_G, 0), (-_G, 0), (0, _G), (0, -_G)):
                    h2 = _hmax(x + dx, z + dz)
                    if h2 is None or h - h2 > 0.6:
                        p = (x + dx * 0.4, h, z + dz * 0.4)
                        if _W2 is not None and _W2.query_ball_point([p[0], h + 0.6, p[2]], 0.15): continue
                        _pz.append(p)
    _u2 = []
    for p in _pz:
        if not any(np.hypot(p[0] - q[0], p[2] - q[2]) < 0.17 and abs(p[1] - q[1]) < 0.4 for q in _u2): _u2.append(p)
    _mmv2 = next((m_ for m_, t_ in mats.items() if t_ and 'handrail01' in t_), None) or next((m_ for m_, t_ in mats.items() if t_ and 'wood04' in t_), None)
    nv2 = 0
    if _u2 and _mmv2:
        P2_ = np.array(_u2); arb2 = cKDTree(P2_)
        for k, p in enumerate(P2_):
            Vp, Tp, Fp = _ex.torneado(tuple(p), 0.93, _ex.PERFIL_BALAUSTRE_LIGERO, lados=6); _anade(Vp, Tp, Fp, _mmv2)
            for j in arb2.query_ball_point(p, 0.27):
                if j > k and abs(P2_[j][1] - p[1]) < 0.35:
                    Vp, Tp, Fp = _ex.viga(P2_[k] + [0, 0.95, 0], P2_[j] + [0, 0.95, 0], ancho=0.1, alto=0.08); _anade(Vp, Tp, Fp, _mmv2); nv2 += 1
    print(f'barandillas en zonas marcadas: {len(_u2)} balaustres, {nv2} tramos')
# ---------------- barandilla completa: fuera las láminas de balaustres con transparencia (en el juego solo se ven
# desde algunos lados) y balaustres reales a paso regular bajo cada pasamanos macizo de UC, siguiendo su inclinación
if os.environ.get('BALAUSTRES_TOTAL'):
    _rx = r'handrail|tesuri|rail|saku|rankan'
    _lam = np.array([bool(_re2.search(_rx, str(mats.get(m_) or m_), _re2.I)) and _tiene_alfa(m_) for m_ in FM])
    _rx_vig = os.environ.get('MATS_PASAMANOS', r'handrail|wood16')
    _mac = np.array([bool(_re2.search(_rx_vig, str(mats.get(m_) or m_), _re2.I)) and not _tiene_alfa(m_) for m_ in FM])
    print(f'láminas de balaustres quitadas: {_lam.sum()} triángulos')
    from collections import Counter as _Cn
    print('  pasamanos macizos por material:', _Cn(str(mats.get(m_) or m_) for m_ in FM[_mac]).most_common(6))
    # muestras del pasamanos macizo
    _Pm = []
    for i_ in np.nonzero(_mac)[0]:
        t3 = V[F[i_, :3]]; a_ = np.linalg.norm(np.cross(t3[1] - t3[0], t3[2] - t3[0])) / 2
        _Pm.append(np.random.default_rng(i_).dirichlet([1, 1, 1], int(np.clip(a_ / 0.0015, 2, 80))) @ t3)
    F = F[~_lam]; FM = FM[~_lam]
    _Pm = np.concatenate(_Pm) if _Pm else np.zeros((0, 3))
    # lo macizo que no sea pasamanos ni lámina (para no meter balaustres dentro de paneles, paredes, postes)
    _sol = np.array([not _tiene_alfa(m_) and not _re2.search(r'wood16' + ('|' + os.environ['NO_MACIZO'] if os.environ.get('NO_MACIZO') else ''), str(mats.get(m_) or m_), _re2.I) for m_ in _SMa]); _Ss = S[_sol]; _Ts = cKDTree(_Ss[:, [0, 2]])
    def _suelo_cerca(x, z, ytop):
        best = None
        for rr_ in (0.0, 0.15, 0.3, 0.45):
            for t_ in (np.linspace(0, 2 * np.pi, 8, endpoint=False) if rr_ else [0.0]):
                h = _heights(_TF, x + rr_ * np.cos(t_), z + rr_ * np.sin(t_)); h = h[(h < ytop - 0.45) & (h > ytop - 1.3)]
                if len(h) and (best is None or h.max() > best): best = float(h.max())
            if best is not None: return best
        return None
    _pan = []
    for i_ in np.nonzero(np.array([bool(_re2.search(r'handrail01', str(mats.get(m_) or m_), _re2.I)) for m_ in FM]))[0]:
        t3 = V[F[i_, :3]]; a_ = np.linalg.norm(np.cross(t3[1] - t3[0], t3[2] - t3[0])) / 2
        _pan.append(np.random.default_rng(i_ + 7).dirichlet([1, 1, 1], int(np.clip(a_ / 0.0008, 3, 400))) @ t3)
    _pan = np.concatenate(_pan) if _pan else np.zeros((0, 3)); _Tp = cKDTree(_pan[:, [0, 2]]) if len(_pan) else None
    def _macizo_debajo(x, y0, y1, z):
        if sum(1 for j in _Ts.query_ball_point([x, z], 0.2) if y0 <= _Ss[j, 1] <= y1) >= 3: return True   # panel tallado, poste o pared
        if _Tp is not None:                                  # panel tallado de pasamanos (barandilla ya dibujada)
            ii = _Tp.query_ball_point([x, z], 0.2)
            if sum(1 for j in ii if y0 <= _pan[j, 1] <= y1) >= 3: return True
        return False
    # el pasamanos: la parte alta de las muestras macizas (vigas), agrupada en tramos rectos
    _grid = {}
    for p in _Pm:
        k = (int(np.floor(p[0] / 0.06)), int(np.floor(p[2] / 0.06)))
        if k not in _grid or p[1] > _grid[k][1]: _grid[k] = p
    _top = np.array(list(_grid.values())) if _grid else np.zeros((0, 3))
    _bal = []; _mot = dict(celdas=len(_top), sin_suelo=0, altura=0, macizo=0, repetido=0)
    _arb_b = None; _dbg = []
    for p in sorted(_top, key=lambda q: (q[0], q[2])):
        ytop = p[1] - 0.045
        yb = _suelo_cerca(p[0], p[2], ytop)
        if yb is None: _mot['sin_suelo'] += 1; _dbg.append((list(map(float, p)), 'sin_suelo')); continue
        h = ytop - yb
        if h < 0.45 or h > 1.25: _mot['altura'] += 1; _dbg.append((list(map(float, p)), 'altura')); continue
        if _macizo_debajo(p[0], yb + 0.25 * h, yb + 0.75 * h, p[2]): _mot['macizo'] += 1; _dbg.append((list(map(float, p)), 'macizo')); continue
        if any(np.hypot(p[0] - q[0], p[2] - q[2]) < 0.14 and abs(yb - q[1]) < 0.45 for q, _ in _bal): _mot['repetido'] += 1; continue
        _bal.append(((p[0], yb, p[2]), h))
    for zb in cfg_zonas_sin if 'cfg_zonas_sin' in dir() else []: pass
    _sin = json.load(open(f'/home/claude/re1gc/work/extras_{r}.json')).get('sin_balaustres', []) if os.path.exists(f'/home/claude/re1gc/work/extras_{r}.json') else []
    _antes = len(_bal)
    _bal = [(b_, h_) for b_, h_ in _bal if not any(z_[0] <= b_[0] <= z_[1] and z_[2] <= b_[2] <= z_[3] and b_[1] >= z_[4] and (len(z_) < 6 or b_[1] <= z_[5]) for z_ in _sin)]
    print(f'  zonas con barandilla tallada (sin balaustres nuevos): quitados {_antes - len(_bal)}')
    _mm_b = next((m_ for m_ in set(FM) if 'handrail01' in str(mats.get(m_) or m_)), None) or mm_r
    # pasamanos horizontales que se quedan cortos antes de la pared: alargarlos hasta ella con sus balaustres
    if os.environ.get('PASAMANOS_A_PARED') and len(_top):
        _tt = cKDTree(_top[:, [0, 2]]); _ends = []
        for i_, p in enumerate(_top):
            nb = [j for j in _tt.query_ball_point(p[[0, 2]], 0.35) if j != i_]
            if len(nb) < 3 or np.abs(_top[nb, 1] - p[1]).max() > 0.08: continue          # solo tramos horizontales
            if p[1] < max(_top[j, 1] for j in nb) - 0.03: continue                           # la viga alta
            d_ = _top[nb][:, [0, 2]] - p[[0, 2]]; m_ = d_.mean(0)
            if np.linalg.norm(m_) > 0.12: _ends.append((p, -m_ / np.linalg.norm(m_)))
        _Sw = _Ss[(_Ss[:, 1] > 0)]; _Tw = cKDTree(_Sw[:, [0, 2]]); _hechos = []; _ext_n = 0
        for p, dv in _ends:
            if any(np.hypot(*(p[[0, 2]] - q)) < 0.4 for q in _hechos): continue
            # dirección recta del eje (x o z) si está cerca
            if abs(dv[0]) > 0.9: dv = np.array([np.sign(dv[0]), 0.0])
            elif abs(dv[1]) > 0.9: dv = np.array([0.0, np.sign(dv[1])])
            else: continue
            ytop = p[1] - 0.045; hit = None
            for s_ in np.arange(0.04, 0.62, 0.02):
                q = p[[0, 2]] + dv * s_
                if sum(1 for j in _Tw.query_ball_point(q, 0.05) if ytop - 0.9 <= _Sw[j, 1] <= ytop + 0.05) >= 2: hit = s_; break
            if hit is None or hit < 0.08: continue
            yb = _suelo_cerca(p[0], p[2], ytop)
            if yb is None: continue
            _hechos.append(p[[0, 2]])
            a3 = np.array([p[0], ytop + 0.02, p[2]]); b3 = np.array([p[0] + dv[0] * (hit + 0.02), ytop + 0.02, p[2] + dv[1] * (hit + 0.02)])
            Vp, Tp, Fp = _ex.viga(a3, b3, ancho=0.1, alto=0.08); _anade(Vp, Tp, Fp, _mm_b)
            Vp, Tp, Fp = _ex.viga(a3 * [1, 0, 1] + [0, yb + 0.06, 0], b3 * [1, 0, 1] + [0, yb + 0.06, 0], ancho=0.12, alto=0.1); _anade(Vp, Tp, Fp, _mm_b)
            for s_ in np.arange(0.12, hit - 0.03, 0.14):
                _bal.append(((p[0] + dv[0] * s_, yb, p[2] + dv[1] * s_), ytop - yb))
            _ext_n += 1
            print(f'  pasamanos alargado hasta la pared en {np.round(p, 2)} hacia {dv}: {hit:.2f} m')
        print(f'  pasamanos alargados: {_ext_n}')
    _ycopia = float(os.environ.get('BALAUSTRE_UC_Y', 99))
    if os.environ.get('BALAUSTRE_UC'):
        # plantilla: un balaustre torneado de la escalera central de UC (madera 16), enderezado (la escalera tiene pendiente)
        bx0, bx1, bz0, bz1, pend = [float(v) for v in os.environ['BALAUSTRE_UC'].split(',')]
        _mw = np.array([bool(_re2.search('wood16', str(mats.get(m_) or m_))) for m_ in FM])
        _cw = V[F[:, :3]].mean(1); _sw = _mw & (_cw[:, 0] > bx0) & (_cw[:, 0] < bx1) & (_cw[:, 2] > bz0) & (_cw[:, 2] < bz1)
        _Ft = F[_sw]; _mmt = FM[_sw][0]
        _Pt = V[_Ft[:, :3]].reshape(-1, 3).copy(); _Ut = VT[_Ft[:, 3:]].reshape(-1, 2)
        _ax = np.array([(_Pt[:, 0].min() + _Pt[:, 0].max()) / 2, 0, (_Pt[:, 2].min() + _Pt[:, 2].max()) / 2])
        _Pt[:, 1] -= pend * (_Pt[:, 2] - _ax[2])
        _Pt -= [_ax[0], _Pt[:, 1].min(), _ax[2]]; _Ht = _Pt[:, 1].max()
        print(f'  plantilla de balaustre de UC: {len(_Ft)} triángulos, alto {_Ht:.2f} m')
        # esquinero (poste cuadrado con remate) de la barandilla de abajo
        _Fe = _Pe = _Ue = None
        if os.environ.get('ESQUINERO_UC'):
            ex0, ex1, ez0, ez1 = [float(v) for v in os.environ['ESQUINERO_UC'].split(',')]
            _me = np.array([bool(_re2.search('wood24', str(mats.get(m_) or m_))) for m_ in FM])
            _se = _me & (_cw[:, 0] > ex0) & (_cw[:, 0] < ex1) & (_cw[:, 2] > ez0) & (_cw[:, 2] < ez1) & (_cw[:, 1] < 3.3)
            _Fe = F[_se]; _mme = FM[_se][0]; _Pe = V[_Fe[:, :3]].reshape(-1, 3).copy(); _Ue = VT[_Fe[:, 3:]].reshape(-1, 2)
            _axe = np.array([(_Pe[:, 0].min() + _Pe[:, 0].max()) / 2, _Pe[:, 1].min(), (_Pe[:, 2].min() + _Pe[:, 2].max()) / 2]); _Pe -= _axe; _He = _Pe[:, 1].max()
            print(f'  plantilla de esquinero de UC: {len(_Fe)} triángulos, alto {_He:.2f} m')
        def _rot(P, tx, tz):
            th = np.arctan2(tx, tz); c, s_ = np.cos(th), np.sin(th)
            return np.stack([c * P[:, 0] + s_ * P[:, 2], P[:, 1], -s_ * P[:, 0] + c * P[:, 2]], 1)
        # balaustres originales de UC (no duplicar encima)
        _orig = []
        if True:
            _cw16 = _cw[_mw]; _ko = cKDTree(_cw16[:, [0, 2]]) if len(_cw16) else None
        _arr = [(b_, h_) for b_, h_ in _bal if b_[1] >= _ycopia]; _bal = []          # los finos de antes ya no se ponen en ningún sitio
        P_ = np.array([[b_[0], b_[1], b_[2], h_] for b_, h_ in _arr]) if _arr else np.zeros((0, 4))
        usado = np.zeros(len(P_), bool); ncop = 0; nesq = 0; PASO = float(os.environ.get('PASO_BALAUSTRE', 0.188))
        _tb = cKDTree(P_[:, [0, 2]]) if len(P_) else None
        _puestos = []; _postes = []
        while len(P_) and not usado.all():
            i0 = int(np.nonzero(~usado)[0][0]); cad = [i0]; usado[i0] = True
            for _dir in (0, 1):
                while True:
                    j = cad[-1] if _dir == 0 else cad[0]
                    cand = [k for k in _tb.query_ball_point(P_[j, [0, 2]], 0.32) if not usado[k] and abs(P_[k, 1] - P_[j, 1]) < 0.3]
                    if not cand: break
                    k = min(cand, key=lambda k: np.hypot(*(P_[k, [0, 2]] - P_[j, [0, 2]]))); usado[k] = True
                    if _dir == 0: cad.append(k)
                    else: cad.insert(0, k)
            Q = P_[cad]
            if len(Q) < 3: continue
            # suavizar el trazado (media móvil) y repartir por longitud
            Qs = Q.copy()
            for c_ in (0, 2): Qs[:, c_] = np.convolve(np.pad(Q[:, c_], 2, mode='edge'), np.ones(5) / 5, mode='valid')
            L_ = np.r_[0, np.cumsum(np.hypot(*(np.diff(Qs[:, [0, 2]], axis=0)).T))]
            if L_[-1] < 0.3: continue
            # altura: recta ajustada (tramo recto o inclinado), sin saltos
            A_ = np.polyfit(L_, Qs[:, 1], 1); hh_ = float(np.median(Qs[:, 3]))
            if abs(A_[0]) < 0.06: A_ = np.array([0.0, float(np.median(Qs[:, 1]))])
            ybf = lambda t_: float(np.polyval(A_, t_))
            def pos(t_): return np.interp(t_, L_, Qs[:, 0]), np.interp(t_, L_, Qs[:, 2])
            def tang(t_):
                a0 = pos(max(0, t_ - 0.2)); a1 = pos(min(L_[-1], t_ + 0.2)); d_ = np.array(a1) - np.array(a0); return d_ / (np.linalg.norm(d_) + 1e-9)
            # esquinas: extremos y cambios de dirección
            ts = [0.0, L_[-1]]
            for t_ in np.arange(0.3, L_[-1] - 0.3, 0.05):
                if abs(tang(t_ - 0.25) @ tang(t_ + 0.25)) < 0.8 and all(abs(t_ - u_) > 0.5 for u_ in ts): ts.append(t_)
            ts = sorted(ts)
            if _Fe is not None:
                for t_ in ts:
                    x_, z_ = pos(t_)
                    if any(np.hypot(x_ - a_, z_ - c_) < 0.3 for a_, c_ in _postes): continue
                    _postes.append((x_, z_)); tg_ = tang(t_)
                    Pp = _rot(_Pe * [1, (hh_ + 0.17) / _He, 1], tg_[0], tg_[1]) + [x_, ybf(t_), z_]
                    _anade(Pp, _Ue, np.arange(len(Pp)).reshape(-1, 3), _mme); nesq += 1
            # balaustres entre esquinas a paso regular
            for a_, b_ in zip(ts[:-1], ts[1:]):
                n_ = max(1, int(round((b_ - a_) / PASO)))
                for t_ in np.linspace(a_, b_, n_ + 1)[1:-1]:
                    x_, z_ = pos(t_)
                    if any(np.hypot(x_ - a2, z_ - c2) < 0.16 for a2, c2 in _puestos): continue
                    if _ko is not None and _ko.query_ball_point([x_, z_], 0.12) and abs(ybf(t_) - _cw16[_ko.query([x_, z_])[1], 1]) < 1.2: continue
                    _puestos.append((x_, z_)); tg_ = tang(t_)
                    Pp = _rot(_Pt * [1, hh_ / _Ht, 1], tg_[0], tg_[1]) + [x_, ybf(t_), z_]
                    _anade(Pp, _Ut, np.arange(len(Pp)).reshape(-1, 3), _mmt); ncop += 1
        print(f'  esquineros: {nesq}')
        print(f'  balaustres de UC copiados: {ncop}')
    for base_, h in _bal:
        Vp, Tp, Fp = _ex.torneado(base_, h, _ex.PERFIL_BALAUSTRE_LIGERO, escala_r=0.65, lados=6)
        _anade(Vp, Tp, Fp, _mm_b)
    print(f'balaustres bajo los pasamanos: {len(_bal)} {_mot}')
    json.dump(dict(desc=_dbg, bal=[list(map(float, b_)) + [float(h_)] for b_, h_ in _bal]), open(f'/tmp/bal_dbg_{r}.json', 'w'))
# ---------------- meter en la malla todas las piezas añadidas (siempre al final)
if _ext_f:
    V = np.concatenate([V] + _ext_v); VT = np.concatenate([VT] + _ext_t)
    F = np.concatenate([F, np.array(_ext_f)]); FM = np.concatenate([FM, np.array(_ext_m, dtype=object)])
