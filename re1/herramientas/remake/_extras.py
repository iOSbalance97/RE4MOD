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
    for base_, h in ([] if os.environ.get('BARANDILLA_RAMPAS') else [bh for bh in _ex.balaustres_escalera(Tc, nc, Pr, _hay_all)
                                                                     if not _lamina_cerca(bh[0][0], bh[0][1] + 0.2 * bh[1], bh[0][1] + 0.8 * bh[1], bh[0][2])]):
        Vp, Tp, Fp = _ex.torneado(base_, h, _ex.PERFIL_BALAUSTRE_LIGERO, escala_r=0.7, lados=6)
        _anade(Vp, Tp, Fp, mm_r); nb_ += 1; _bases1.append(base_)
# segunda pasada: balaustres justo debajo de cualquier pasamanos que no tenga nada debajo (ni tarjetas con alfa)
if _mr and not os.environ.get('BARANDILLA_RAMPAS'):
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
            if n_[1] > 0.7: tex = rz['suelo']
            elif n_[1] < -0.7: tex = rz['techo']
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
if _ext_f:
    V = np.concatenate([V] + _ext_v); VT = np.concatenate([VT] + _ext_t)
    F = np.concatenate([F, np.array(_ext_f)]); FM = np.concatenate([FM, np.array(_ext_m, dtype=object)])

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
