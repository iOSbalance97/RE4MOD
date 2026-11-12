"""RE4 GameCube character model (.BIN inside em/*.drs) reader"""
import struct, numpy as np
def parse(m):
    H = struct.unpack('>24I', m[:0x60])
    nw, nb, nmat = m[0x18], m[0x19], struct.unpack('>H', m[0x1a:0x1c])[0]
    npos, nnrm = struct.unpack('>HH', m[0x38:0x3c])
    o = dict(bones=H[0], col=H[3], uv=H[4], wt=H[5], mat=H[7], pos=H[12], nrm=H[13])
    bones = [(m[o['bones']+16*i], m[o['bones']+16*i+1]) + struct.unpack('>3f', m[o['bones']+16*i+4:o['bones']+16*i+16]) for i in range(nb)]
    pos = np.frombuffer(m, '>i2', npos*4, o['pos']).reshape(-1, 4)
    nrm = np.frombuffer(m, 'i1', nnrm*4, o['nrm']).reshape(-1, 4)
    wt = np.frombuffer(m, 'u1', nw*8, o['wt']).reshape(-1, 8)
    nuv = (o['wt'] - o['uv']) // 4; uv = np.frombuffer(m, '>i2', nuv*2, o['uv']).reshape(-1, 2)
    mats = []; p = o['mat']
    for k in range(nmat):
        hd = m[p:p+0x20]; size = struct.unpack('>I', hd[0x18:0x1c])[0]; q = p + 0x20; tris = []
        while q < p + 0x20 + size and m[q] in (0x90, 0x98, 0xA0, 0x80):
            op = m[q]; n = struct.unpack('>H', m[q+1:q+3])[0]; vs = np.frombuffer(m, '>u2', n*4, q+3).reshape(n, 4); q += 3 + n*8
            if op == 0x98:
                for i in range(n-2): tris.append((vs[i], vs[i+1], vs[i+2]) if i % 2 == 0 else (vs[i+1], vs[i], vs[i+2]))
            elif op == 0x90:
                for i in range(0, n-2, 3): tris.append((vs[i], vs[i+1], vs[i+2]))
            elif op == 0xA0:
                for i in range(1, n-1): tris.append((vs[0], vs[i], vs[i+1]))
            else:
                for i in range(0, n-3, 4): tris += [(vs[i], vs[i+1], vs[i+2]), (vs[i], vs[i+2], vs[i+3])]
        t = np.array(tris).reshape(-1, 3, 4)
        if len(t): t = t[(t[:, 0, 0] != t[:, 1, 0]) & (t[:, 1, 0] != t[:, 2, 0]) & (t[:, 0, 0] != t[:, 2, 0])]
        mats.append(dict(hdr=hd, tris=t, ntri=struct.unpack('>I', hd[0x1c:0x20])[0], tex=hd[0x0c]))
        p += 0x20 + size
    return dict(H=H, bones=bones, pos=pos, nrm=nrm, wt=wt, uv=uv, mats=mats, nw=nw)
if __name__ == '__main__':
    import sys; sys.path.insert(0, '/tmp/sal')
    from binfo import model
    m = model(sys.argv[1], int(sys.argv[2])); r = parse(m)
    print('bones', len(r['bones']), 'pos', len(r['pos']), 'nrm', len(r['nrm']), 'uv', len(r['uv']), 'weights', r['nw'], 'mats', len(r['mats']))
    print('tris per material', [len(t['tris']) for t in r['mats']], 'TOTAL', sum(len(t['tris']) for t in r['mats']))
    for t in r['mats'][:14]: print(t['hdr'].hex(' ', 4))
    print('max idx', [max(int(t['tris'][:, :, c].max()) for t in r['mats'] if len(t['tris'])) for c in range(4)])
    print('weights/vertex', np.bincount(r['wt'][:, 3]))
