"""esquinas_col_r105.py: el REmake deja pisar dos rincones del comedor que en UC quedan dentro de la pared
(desde ahí se veía el vacío): se cierran con colisión -> re4/re_r105/col"""
import subprocess, shutil, os
base = '/home/claude/re1gc/re4/re_r105/col'
src = f'{base}/colision_original.obj'
if not os.path.exists(src): shutil.copy(f'{base}/colision.obj', src)
CAJAS = [(8.55, 9.72, 2.66, 3.8, -0.1, 2.5), (-10.25, -8.53, -3.8, -2.61, -0.1, 2.5), (-9.9, -8.56, 2.7, 3.8, -0.1, 2.5), (8.52, 9.7, -3.8, -2.62, -0.1, 2.5),
         (-9.95, -8.92, -2.65, -0.45, -0.1, 2.5), (-9.95, -8.92, 0.45, 2.72, -0.1, 2.5)]          # franja oeste detrás de la pared de UC (la chimenea queda libre)
L = open(src).read().rstrip('\n').split('\n'); nv = sum(1 for l in L if l.startswith('v '))
for x0, x1, z0, z1, y0, y1 in CAJAS:
    P = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    for k in range(4):
        (ax, az), (bx, bz) = P[k], P[(k + 1) % 4]
        for v in ((ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az)): L.append('v %.3f %.3f %.3f' % v)
        b = nv; nv += 4
        L += [f'f {b+1} {b+2} {b+3}', f'f {b+1} {b+3} {b+4}', f'f {b+3} {b+2} {b+1}', f'f {b+4} {b+3} {b+1}']
open('/tmp/colision_r105_esquinas.obj', 'w').write('\n'.join(L) + '\n')
print(subprocess.run(['python3', '/home/claude/tools/obj2sat.py', '/tmp/colision_r105_esquinas.obj', base], capture_output=True, text=True).stdout)
