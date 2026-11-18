"""Colisión de Umbrella Chronicles (BGHT v10, rNNN_chit.col / rNNN_ehit.col) -> OBJ.
Cabecera: 'BGHT', ver, off_nodos, n_nodos(quadtree), off_vert, n_vert, off_norm, n_tri, 0, 0, off_attr
vértices: 3 floats por esquina, sin índices (3 por triángulo); normales: 3 floats por triángulo; attr: u32 por triángulo.
uso: ucol.py fichero.col salida.obj [escala]"""
import struct, sys
import numpy as np

def load(path):
    d = open(path, 'rb').read()
    h = struct.unpack('>16I', d[:64])
    assert d[:4] == b'BGHT' and h[1] == 10, path
    offv, nv, offn, nt, offa = h[4], h[5], h[6], h[7], h[10]
    assert nv == 3 * nt
    V = np.frombuffer(d[offv:offv + nv * 12], '>f4').reshape(-1, 3, 3).astype(np.float64)
    N = np.frombuffer(d[offn:offn + nt * 12], '>f4').reshape(-1, 3).astype(np.float64)
    A = np.frombuffer(d[offa:offa + nt * 4], '>u4').astype(np.int64)
    return V, N, A

if __name__ == '__main__':
    V, N, A = load(sys.argv[1]); s = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    with open(sys.argv[2], 'w') as f:
        f.write('mtllib col.mtl\nvt 0 0\n')
        for t in V:
            for p in t: f.write(f'v {p[0]*s:.4f} {p[1]*s:.4f} {p[2]*s:.4f}\n')
        for i, a in enumerate(A):
            f.write(f'g attr{a}\nf {3*i+1}/1 {3*i+2}/1 {3*i+3}/1\n')
    import os
    open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])), 'col.mtl'), 'w').write('newmtl x\nKd 1 1 1\n')
    # ¿el orden de vértices coincide con la normal?
    c = np.cross(V[:, 1] - V[:, 0], V[:, 2] - V[:, 0]); c /= np.maximum(np.linalg.norm(c, axis=1, keepdims=True), 1e-9)
    print(len(V), 'triángulos; acuerdo normal/orden', np.round(np.mean((c * N).sum(1) > 0), 3), 'attr', np.unique(A, return_counts=True))
