"""Objetos de una sala de UC (Data/bg/rNNNbgobj.arc) -> OBJ en coordenadas del mundo de UC.
model.brres trae el modelo rNNN_obj cuyos huesos son las colocaciones (matriz de mundo en +0x70); cada hueso
'rNNN_tipo[_NN]' usa el modelo 'rNNN_tipo' (en model.brres o en rNNN_tipo.brres / rNNN_tipo_M.brres).
Los vértices de los objetos están en espacio de modelo: mundo = colocación · v.
uso: ucobjs.py rNNN   -> /home/claude/uc/objs/rNNN/objetos.obj (+ .mtl y texturas)"""
import glob, os, re, subprocess, sys
import numpy as np
sys.path.insert(0, '/home/claude/tools')
import brres, mdl0, ucbones, objload

r = sys.argv[1]
arc = f'/home/claude/uc/ext/Data/bg/{r}bgobj.arc'
src = f'/home/claude/uc/bgo/{r}'; out = f'/home/claude/uc/objs/{r}'
os.makedirs(src, exist_ok=True); os.makedirs(out, exist_ok=True)
subprocess.run(['python3', '/home/claude/tools/u8.py', arc, src], check=True, capture_output=True)
d = open(f'{src}/model.brres', 'rb').read()
models = dict(brres.tree(d)['3DModels(NW4R)'])
place = ucbones.bones(d, models[f'{r}_obj'])[1:] if f'{r}_obj' in models else []

# dónde está cada modelo
lib = {}
for f in glob.glob(f'{src}/*.brres'):
    dd = open(f, 'rb').read()
    for n, _ in brres.tree(dd).get('3DModels(NW4R)', []):
        lib.setdefault(n, f)
cache = {}
def geo(name):
    if name not in cache:
        f = lib[name]; tmp = f'{out}/_m/{name}'
        if not os.path.exists(f'{tmp}/{name}.obj'):
            os.makedirs(tmp, exist_ok=True); mdl0.export(f, tmp, only=name)
        cache[name] = (objload.load(f'{tmp}/{name}.obj'), tmp)
    return cache[name]

lines = ['mtllib objetos.mtl\n']; mtl = []; vb = 1; usados = []; faltan = []
for b in place:
    n = b['name']
    cand = [n, re.sub(r'_\d+$', '', n), re.sub(r'_?\d+$', '', n), re.sub(r'_?[A-Z]?\d*$', '', n)]
    cand += [c + '_M' for c in cand]
    m = next((c for c in cand if c in lib and c != f'{r}_obj'), None)
    if m is None: faltan.append(n); continue
    (V, T, F, M, G, mats), tmp = geo(m)
    if len(V) == 0 or len(F) == 0: faltan.append(n + '(vacío)'); continue
    W = V @ b['mtx'][:, :3].T + b['mtx'][:, 3]
    lines += [f'v {x:.4f} {y:.4f} {z:.4f}\n' for x, y, z in W]
    lines += [f'vt {u:.5f} {v:.5f}\n' for u, v in T]
    nt = len(T)
    cur = None
    for f_, mm in zip(F, M):
        key = f'{m}_{mm}'
        if mm != cur: lines.append(f'usemtl {key}\n'); cur = mm
        lines.append('f ' + ' '.join(f'{vb + f_[k]}/{vb_t + f_[k + 3]}' for k in range(3)) + '\n') if False else None
    usados.append((n, m))
    # índices: objload devuelve F con v y vt por separado
    vt0 = sum(1 for l in lines if l.startswith('vt ')) - nt + 1
    v0 = vb
    lines = [l for l in lines if l is not None]
    for f_, mm in zip(F, M):
        lines.append(f'usemtl {m}_{mm}\n')
        lines.append('f ' + ' '.join(f'{v0 + f_[k]}/{vt0 + f_[k + 3]}' for k in range(3)) + '\n')
    vb += len(W)
    for mm, tex in mats.items():
        key = f'{m}_{mm}'
        if key in mtl: continue
        mtl.append(key)
        if tex and not os.path.exists(f'{out}/{tex}'):
            os.link(f'{tmp}/{tex}', f'{out}/{tex}') if not os.path.exists(f'{out}/{tex}') else None
open(f'{out}/objetos.obj', 'w').writelines(l for l in lines if l is not None)
with open(f'{out}/objetos.mtl', 'w') as f:
    for key in mtl:
        m, mm = key.rsplit('_', 1)
        tex = cache[m][0][5].get(mm)
        f.write(f'newmtl {key}\nKd 1 1 1\n' + (f'map_Kd {tex}\n' if tex else ''))
print(r, 'objetos', len(usados), [u[1].replace(r + '_', '') for u in usados], 'sin modelo', faltan)
