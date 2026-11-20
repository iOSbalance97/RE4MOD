"""gen_build.py dir [dir...] : sala generada -> mod/sala.smd (re4room) + col/sala.sat/eat"""
import sys, os, subprocess, numpy as np
sys.path.insert(0, '/home/claude/tools'); from re4col import write_sat
for d in sys.argv[1:]:
    r = subprocess.run(['python3', '/home/claude/tools/re4room.py', f'{d}/sala.obj', f'{d}/mod', '--tex-max', '256', '--colocar=0,0,0,0,0,0,0'], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-800:]); raise SystemExit(1)
    z = np.load(f'{d}/col.npz'); K, T = z['K'], z['T']
    P = T.reshape(-1, 3); key = np.round(P).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    V = P[first]; F = inv.reshape(-1, 3)
    ar = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1); ok = ar > 1.0
    # suelos con normal hacia arriba
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    fl = (K < 2) & (n[:, 1] < 0); F[fl] = F[fl][:, [0, 2, 1]]
    sat = write_sat(V, F[ok], K[ok], np.zeros(ok.sum(), int), block_size=2000.0)
    os.makedirs(f'{d}/col', exist_ok=True); open(f'{d}/col/sala.sat', 'wb').write(sat); open(f'{d}/col/sala.eat', 'wb').write(sat)
    print(os.path.basename(d), r.stdout.strip().splitlines()[0], '| SAT', ok.sum(), 'tri', len(sat) // 1024, 'KB')
