import numpy as np, time, sys
from skimage import measure
import model
def grid_eval(fn, lo, hi, vox):
    n = np.ceil((hi - lo) / vox).astype(int) + 1
    C = 4; nc = (n + C - 1) // C + 1
    def pts(nn, step, off=0.0):
        ax = [lo[i] + off + np.arange(nn[i], dtype=np.float32) * step for i in range(3)]
        return ax
    ax = pts(nc, vox * C)
    G = np.stack(np.meshgrid(*ax, indexing='ij'), -1).reshape(-1, 3)
    dc = np.concatenate([model.field(fn, G[i:i + 300000])[0] for i in range(0, len(G), 300000)]).reshape(nc)
    near = np.abs(dc) < vox * C * 1.9
    # dilate by one coarse cell
    from scipy.ndimage import binary_dilation, zoom
    near = binary_dilation(near, iterations=1)
    D = np.repeat(np.repeat(np.repeat(dc, C, 0), C, 1), C, 2)
    nearf = np.repeat(np.repeat(np.repeat(near, C, 0), C, 1), C, 2)
    # fine grid i corresponds to coarse i//C: shift so coarse sample sits at block start
    D = D[:n[0], :n[1], :n[2]].copy(); nearf = nearf[:n[0], :n[1], :n[2]]
    # also mark the block before (a coarse sample is at the block's first corner)
    idx = np.argwhere(nearf)
    P = lo + idx.astype(np.float32) * vox
    out = np.empty(len(P), np.float32)
    for i in range(0, len(P), 300000): out[i:i + 300000] = model.field(fn, P[i:i + 300000])[0]
    D[nearf] = out
    D[~nearf] = np.where(D[~nearf] > 0, 1e3, -1e3)
    return D, n
def build(name, fn, box, vox):
    lo, hi = box; t = time.time()
    D, n = grid_eval(fn, lo, hi, vox)
    v, f, _, _ = measure.marching_cubes(D, 0.0)
    v = lo + v.astype(np.float32) * vox
    vol = np.einsum('ij,ij->i', v[f[:, 0]].astype(np.float64), np.cross(v[f[:, 1]], v[f[:, 2]]).astype(np.float64)).sum()
    if vol < 0: f = f[:, ::-1].copy()          # outward winding (CCW seen from outside)
    print(name, n, 'verts', len(v), 'tris', len(f), '%.1fs' % (time.time() - t)); sys.stdout.flush()
    return v, f
import subprocess, struct
def ev(fn, P, mats=False):
    d = np.empty(len(P), np.float32); mm = np.empty(len(P), np.int32)
    for i in range(0, len(P), 300000): d[i:i + 300000], mm[i:i + 300000] = model.field(fn, P[i:i + 300000])
    return (d, mm) if mats else d
def others(name, P):
    d = np.full(len(P), 1e3, np.float32)
    for n2, fn, box, vox, bud in model.PARTS:
        if n2 == name: continue
        lo, hi = box; ins = np.all((P > lo) & (P < hi), 1)
        if ins.any(): d[ins] = np.minimum(d[ins], ev(fn, P[ins]))
    return d
def decimate(v, f, mat, target):
    with open('/tmp/q_in.bin', 'wb') as fo:
        fo.write(struct.pack('<3i', len(v), len(f), target)); fo.write(v.astype('<f4').tobytes()); fo.write(f.astype('<i4').tobytes()); fo.write(mat.astype('<i4').tobytes())
    subprocess.run(['./qem', '/tmp/q_in.bin', '/tmp/q_out.bin'], check=True)
    b = open('/tmp/q_out.bin', 'rb').read(); n, m_ = struct.unpack('<2i', b[:8])
    v2 = np.frombuffer(b, '<f4', n * 3, 8).reshape(n, 3).copy(); f2 = np.frombuffer(b, '<i4', m_ * 3, 8 + n * 12).reshape(m_, 3).copy()
    m2 = np.frombuffer(b, '<i4', n, 8 + n * 12 + m_ * 12).copy()
    return v2, f2, m2
def cull(name, v, f, thr):
    d = others(name, v)
    keep = ~np.all(d[f] < thr, 1)
    f = f[keep]; used = np.unique(f); re = np.full(len(v), -1); re[used] = np.arange(len(used))
    return v[used], re[f]
if __name__ == '__main__':
    for name, fn, box, vox, bud in model.PARTS:
        if len(sys.argv) > 1 and name not in sys.argv[1:]: continue
        v, f = build(name, fn, box, vox)
        v, f = cull(name, v, f, -7.0)
        _, mat = ev(fn, v, True)
        v, f, mat = decimate(v, f, mat, bud)
        np.savez('dec_%s.npz' % name, v=v, f=f, mat=mat)
