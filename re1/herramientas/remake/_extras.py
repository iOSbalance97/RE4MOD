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
    for base_, h in ([] if os.environ.get('BARANDILLA_RAMPAS') else _ex.balaustres_escalera(Tc, nc, Pr, _hay)):
        Vp, Tp, Fp = _ex.torneado(base_, h, _ex.PERFIL_BALAUSTRE, lados=8)
        _anade(Vp, Tp, Fp, mm_r); nb_ += 1; _bases1.append(base_)
# segunda pasada: balaustres justo debajo de cualquier pasamanos que no tenga nada debajo (ni tarjetas con alfa)
if _mr and not os.environ.get('BARANDILLA_RAMPAS'):
    _okt = np.array([not _re2.search(r'handrail|tesuri', str(mats.get(m_) or m_), _re2.I) for m_ in _SMa])
    _S3 = S[_okt]; _T3 = cKDTree(_S3[:, [0, 2]])
    def _hay_todo(x, y0, y1, z, rad=0.09):
        for j in _T3.query_ball_point([x, z], rad):
            if y0 <= _S3[j, 1] <= y1: return True
        return False
    _ya = [b_ for b_, _ in []]
    _puestos = cKDTree(np.array([[0, 1e6, 0]]))
    _celdas = {}
    for p in Pr:
        k = (int(np.floor(p[0] / 0.17)), int(np.floor(p[2] / 0.17)))
        if k not in _celdas or p[1] < _celdas[k][1]: _celdas[k] = p
    _nuevos = []
    for k, p in _celdas.items():
        x, z = (k[0] + 0.5) * 0.17, (k[1] + 0.5) * 0.17
        ytop = p[1] - 0.04
        cand = []
        for rr_ in (0.0, 0.18, 0.35):
            for t_ in (np.linspace(0, 2 * np.pi, 8, endpoint=False) if rr_ else [0.0]):
                h = _heights(_TF, x + rr_ * np.cos(t_), z + rr_ * np.sin(t_)); h = h[(h < ytop - 0.45) & (h > ytop - 1.35)]
                if len(h): cand.append(float(h.max()))
            if cand: break
        if not cand: continue
        yb = max(cand); hh = ytop - yb
        if any(np.hypot(x - q[0], z - q[2]) < 0.13 and abs(yb - q[1]) < 0.6 for q in _bases1): continue
        if _hay_todo(x, yb + 0.2 * hh, yb + 0.8 * hh, z): continue
        if any(np.hypot(x - q[0], z - q[2]) < 0.15 and abs(yb - q[1]) < 0.5 for q, _ in _nuevos): continue
        _nuevos.append(((x, yb, z), hh))
    for base_, h in _nuevos:
        Vp, Tp, Fp = _ex.torneado(base_, h, _ex.PERFIL_BALAUSTRE, lados=8)
        _anade(Vp, Tp, Fp, mm_r)
    print(f'balaustres bajo pasamanos vacíos: {len(_nuevos)}')
# escaleras: la escalera de UC no sigue a la del REmake -> barandilla propia en los bordes de las rampas
if os.environ.get('BARANDILLA_RAMPAS') and _mr:
    _wall = np.nonzero(np.abs(nc[:, 1]) < 0.3)[0]
    _Wp = []
    for i in _wall:
        w = np.random.default_rng(i).dirichlet([1, 1, 1], 12); _Wp.append(w @ Tc[i])
    _Wt = cKDTree(np.concatenate(_Wp)) if _Wp else None
    def _es_pared(x, y, z): return _Wt is not None and len(_Wt.query_ball_point([x, y, z], 0.2)) > 0
    _vig, _bal, _pos = _ex.barandilla_rampas(Tc, nc, _es_pared, alturas=lambda x, z: _heights(_TF, x, z))
    # quitar el pasamanos/balaustres de UC sobre o junto a las rampas
    _ramp = (nc[:, 1] > 0.45) & (nc[:, 1] < 0.97)
    _Rp = np.concatenate([np.random.default_rng(i).dirichlet([1, 1, 1], 20) @ Tc[i] for i in np.nonzero(_ramp)[0]])
    _Rt = cKDTree(_Rp[:, [0, 2]])
    _cen2 = V[F[:, :3]].mean(1); _rm = np.zeros(len(F), bool)
    for i in np.nonzero(np.array([bool(_re2.search(r'handrail|tesuri', str(mats.get(m_) or m_), _re2.I)) for m_ in FM]))[0]:
        x, y, z = _cen2[i]
        for j in _Rt.query_ball_point([x, z], 1.5):
            if -0.3 < y - _Rp[j, 1] < 1.6: _rm[i] = True; break
    F = F[~_rm]; FM = FM[~_rm]
    _mm_v = next((m_ for m_, t_ in mats.items() if t_ and 'wood04' in t_), mm_r)
    for a_, b_ in _vig:
        Vp, Tp, Fp = _ex.viga(a_, b_); _anade(Vp, Tp, Fp, _mm_v)
    for base_, h in _bal:
        Vp, Tp, Fp = _ex.torneado(base_, h, _ex.PERFIL_BALAUSTRE_LIGERO, lados=4); _anade(Vp, Tp, Fp, _mm_v)
    for p_ in _pos:
        Vp, Tp, Fp = _ex.torneado(p_, 1.12, _ex.PERFIL_COLUMNA, escala_r=0.075, lados=6); _anade(Vp, Tp, Fp, _mm_v)
    print(f'escaleras: quitados {_rm.sum()} triángulos de UC; puestos {len(_vig)} tramos, {len(_bal)} balaustres, {len(_pos)} postes')
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
    for es in cfg.get('estatuas', []):
        mm = next((m_ for m_, t_ in mats.items() if t_ == es['textura']), None)
        if not mm and os.path.exists(os.path.join(base, es['textura'])): mm = es['textura'][:-4]; mats[mm] = es['textura']
        if not mm: print('  textura de estatua no encontrada', es['textura']); continue
        Vp, Tp, Fp = _ex.estatua((es['x'], es['y0'], es['z']), es.get('alto', 1.15), es.get('giro', 0.0))
        _anade(Vp, Tp, Fp, mm); print('  estatua añadida en', es['x'], es['z'])
    # quitar lo de UC que estorbe (cajas a eliminar)
    for q in cfg.get('quitar', []):
        lo = np.array(q['min']); hi = np.array(q['max'])
        cen_ = V[F[:, :3]].mean(1); fuera = ~np.all((cen_ >= lo) & (cen_ <= hi), 1)
        if q.get('mat'): fuera |= np.array([not _re2.search(q['mat'], str(mats.get(m_) or m_), _re2.I) for m_ in FM])
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
