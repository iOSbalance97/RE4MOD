import numpy as np, pickle, struct, json
parts = pickle.load(open('parts.pkl', 'rb'))
# OBJ (mm -> m), vertex colours, one group per part
with open('herrero.obj', 'w') as fo:
    fo.write('# El Herrero - original enemy model. units: metres, Y up, faces +Z\n'); vo = 1; no = 1
    for p in parts:
        fo.write('g %s\n' % p['name'])
        for v, c in zip(p['v'], p['col']): fo.write('v %.5f %.5f %.5f %.3f %.3f %.3f\n' % (*(v / 1000), *c))
        cn = p['cn'].reshape(-1, 3)
        for n in cn: fo.write('vn %.4f %.4f %.4f\n' % tuple(n))
        for i, t in enumerate(p['f']):
            fo.write('f %d//%d %d//%d %d//%d\n' % (t[0] + vo, no + 3 * i, t[1] + vo, no + 3 * i + 1, t[2] + vo, no + 3 * i + 2))
        vo += len(p['v']); no += len(cn)
# GLB: one mesh per part, split vertices by normal
bufs = []; acc = []; views = []; meshes = []; nodes = []
def add(arr, target=None):
    b = arr.tobytes(); off = sum(len(x) for x in bufs); pad = (-len(b)) % 4; bufs.append(b + b'\0' * pad)
    views.append(dict(buffer=0, byteOffset=off, byteLength=len(b), **({'target': target} if target else {})))
    return len(views) - 1
tot = 0
for p in parts:
    key = np.concatenate([np.repeat(p['f'].reshape(-1, 1), 1, 1).astype(np.float64), np.round(p['cn'].reshape(-1, 3) * 50)], 1)
    u, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    first = np.zeros(len(u), int); first[inv] = np.arange(len(inv))
    vi = p['f'].reshape(-1)[first]
    pos = (p['v'][vi] / 1000).astype('<f4'); nor = p['cn'].reshape(-1, 3)[first].astype('<f4'); col = p['col'][vi].astype('<f4')
    idx = inv.astype('<u2' if len(u) < 65536 else '<u4')
    a0 = len(acc)
    acc.append(dict(bufferView=add(pos, 34962), componentType=5126, count=len(pos), type='VEC3', min=pos.min(0).tolist(), max=pos.max(0).tolist()))
    acc.append(dict(bufferView=add(nor, 34962), componentType=5126, count=len(nor), type='VEC3'))
    acc.append(dict(bufferView=add(col, 34962), componentType=5126, count=len(col), type='VEC3'))
    acc.append(dict(bufferView=add(idx, 34963), componentType=5123 if idx.dtype.itemsize == 2 else 5125, count=len(idx), type='SCALAR'))
    meshes.append(dict(name=p['name'], primitives=[dict(attributes=dict(POSITION=a0, NORMAL=a0 + 1, COLOR_0=a0 + 2), indices=a0 + 3, material=0)]))
    nodes.append(dict(name=p['name'], mesh=len(meshes) - 1)); tot += len(idx) // 3
g = dict(asset=dict(version='2.0', generator='herrero'), scene=0, scenes=[dict(nodes=list(range(len(nodes))))], nodes=nodes, meshes=meshes,
         materials=[dict(name='vertex_colour', pbrMetallicRoughness=dict(baseColorFactor=[1, 1, 1, 1], metallicFactor=0.0, roughnessFactor=0.85))],
         accessors=acc, bufferViews=views, buffers=[dict(byteLength=sum(len(x) for x in bufs))])
js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4); bn = b''.join(bufs)
with open('herrero.glb', 'wb') as fo:
    fo.write(struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + 8 + len(bn))); fo.write(struct.pack('<I4s', len(js), b'JSON')); fo.write(js)
    fo.write(struct.pack('<I4s', len(bn), b'BIN\0')); fo.write(bn)
print('tris', tot)
