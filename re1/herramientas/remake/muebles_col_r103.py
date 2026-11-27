"""muebles_col_r103.py: colisión del REmake de r103 + cajas de los muebles de la salita (sofá, butaca, mesita) -> re4/re_r103/col"""
import subprocess
src = '/home/claude/re1gc/salas/r103/colision.obj'; dst = '/tmp/colision_r103_muebles.obj'
CAJAS = [(-11.79, -10.92, 0.30, 2.39, 4.0, 5.1),      # sofá contra la pared oeste
         (-10.03, -9.20, -1.25, 0.01, 4.0, 5.0),      # butaca en la esquina frente a la puerta
         (-9.82, -9.18, 0.08, 0.73, 4.0, 5.0)]        # mesita con lámpara
L = open(src).read().rstrip('\n').split('\n'); nv = sum(1 for l in L if l.startswith('v '))
for x0, x1, z0, z1, y0, y1 in CAJAS:
    P = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    for k in range(4):
        (ax, az), (bx, bz) = P[k], P[(k + 1) % 4]
        for v in ((ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az)): L.append('v %.3f %.3f %.3f' % v)
        b = nv; nv += 4
        L += [f'f {b+1} {b+2} {b+3}', f'f {b+1} {b+3} {b+4}', f'f {b+3} {b+2} {b+1}', f'f {b+4} {b+3} {b+1}']
open(dst, 'w').write('\n'.join(L) + '\n')
print(subprocess.run(['python3', '/home/claude/tools/obj2sat.py', dst, '/home/claude/re1gc/re4/re_r103/col'], capture_output=True, text=True).stdout)
