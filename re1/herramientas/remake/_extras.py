# ---------------- piezas a mano: balaustres bajo pasamanos vacíos y columnas torneadas (config por sala)
import extras as _ex
sys.path.insert(0, '/home/claude/tools'); from hmap import floors as _floors, heights as _heights
_TF = _floors(f'/home/claude/re1gc/salas/{r}/colision.obj')
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
    for base_, h in _ex.balaustres_escalera(Tc, nc, Pr, _hay):
        Vp, Tp, Fp = _ex.torneado(base_, h, _ex.PERFIL_BALAUSTRE, lados=8)
        _anade(Vp, Tp, Fp, mm_r); nb_ += 1
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
    # quitar lo de UC que estorbe (cajas a eliminar)
    for q in cfg.get('quitar', []):
        lo = np.array(q['min']); hi = np.array(q['max'])
        cen_ = V[F[:, :3]].mean(1); fuera = ~np.all((cen_ >= lo) & (cen_ <= hi), 1)
        print(f"  quitados {np.sum(~fuera)} triángulos de UC en {q.get('que', '')}")
        F = F[fuera]; FM = FM[fuera]
if _ext_f:
    V = np.concatenate([V] + _ext_v); VT = np.concatenate([VT] + _ext_t)
    F = np.concatenate([F, np.array(_ext_f)]); FM = np.concatenate([FM, np.array(_ext_m, dtype=object)])
