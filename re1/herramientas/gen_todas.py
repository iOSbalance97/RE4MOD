import sys, json; sys.path.insert(0, '/home/claude/tools')
import rgen, mundo_suites
sel = sys.argv[1:]
for sp in mundo_suites.SUITES:
    if sel and sp['nombre'] not in sel: continue
    S = rgen.construir(dict(sp)); ntri, ntex = S.guardar(f"/home/claude/gen/{sp['nombre']}")
    print(f"{sp['nombre']:12s} tri {ntri:5d} tex {ntex:3d} puertas {len(S.puertas)} llamas {len(S.llamas)} lámparas {len(S.lamparas)}")
