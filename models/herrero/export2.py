import numpy as np, pickle, struct, json
import rig
parts = pickle.load(open('parts.pkl', 'rb'))
joints = rig.ORDER; jidx = {k: i for i, k in enumerate(joints)}
bufs = []; views = []; acc = []
def add(arr, target=None):
    b = arr.tobytes(); off = sum(len(x) for x in bufs); bufs.append(b + b'\0' * ((-len(b)) % 4))
    v = dict(buffer=0, byteOffset=off, byteLength=len(b))
    if target: v['target'] = target
    views.append(v); return len(views) - 1
def accessor(arr, ctype, typ, target=None, mm=False, norm=False):
    a = dict(bufferView=add(arr, target), componentType=ctype, count=len(arr), type=typ)
    if mm: a['min'] = arr.min(0).tolist(); a['max'] = arr.max(0).tolist()
    if norm: a['normalized'] = True
    acc.append(a); return len(acc) - 1
nodes = []
for k in joints:
    par, pos = rig.B[k]; t = (pos - (rig.B[par][1] if par >= 0 else 0)) / 1000
    nodes.append(dict(name='part%02d' % k, translation=[float(x) for x in t]))
for k in joints:
    ch = [jidx[c] for c in joints if rig.B[c][0] == k]
    if ch: nodes[jidx[k]]['children'] = ch
ibm = np.tile(np.eye(4, dtype='<f4'), (len(joints), 1, 1))
for i, k in enumerate(joints): ibm[i, 3, :3] = -rig.B[k][1] / 1000          # column-major: translation in the last row
ibm_acc = accessor(ibm.reshape(-1, 16), 5126, 'MAT4')
meshes = []; tot = 0; objv = []
for p in parts:
    f = p['f']; nf = len(f)
    key = np.concatenate([f.reshape(-1, 1).astype(np.float64), np.round(p['cn'].reshape(-1, 3) * 40), np.round(p['uv'].reshape(-1, 2) * 8)], 1)
    u, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
    vi = f.reshape(-1)[first]
    pos = (p['v'][vi] / 1000).astype('<f4'); nor = p['cn'].reshape(-1, 3)[first].astype('<f4'); uv = (p['uv'].reshape(-1, 2)[first] / 1024).astype('<f4')
    J = np.zeros((len(vi), 4), '<u1'); W = np.zeros((len(vi), 4), '<f4')
    for c in range(2): J[:, c] = [jidx[int(k)] if w > 0 else 0 for k, w in zip(p['J'][vi, c], p['W'][vi, c])]; W[:, c] = p['W'][vi, c]
    idx = inv.astype('<u2')
    at = dict(POSITION=accessor(pos, 5126, 'VEC3', 34962, True), NORMAL=accessor(nor, 5126, 'VEC3', 34962), TEXCOORD_0=accessor(uv, 5126, 'VEC2', 34962),
              JOINTS_0=accessor(J, 5121, 'VEC4', 34962), WEIGHTS_0=accessor(W, 5126, 'VEC4', 34962))
    meshes.append(dict(name=p['name'], primitives=[dict(attributes=at, indices=accessor(idx, 5123, 'SCALAR', 34963), material=p['atlas'])]))
    nodes.append(dict(name=p['name'], mesh=len(meshes) - 1, skin=0)); tot += nf
    p['x_pos'], p['x_nor'], p['x_uv'], p['x_idx'] = pos, nor, uv, inv.reshape(-1, 3)
images = []; 
for i in (0, 1):
    b = open('herrero_tex%d.png' % i, 'rb').read(); off = sum(len(x) for x in bufs); bufs.append(b + b'\0' * ((-len(b)) % 4))
    views.append(dict(buffer=0, byteOffset=off, byteLength=len(b))); images.append(dict(bufferView=len(views) - 1, mimeType='image/png'))
g = dict(asset=dict(version='2.0', generator='herrero'), scene=0, scenes=[dict(nodes=[0] + list(range(len(joints), len(nodes))))], nodes=nodes, meshes=meshes,
         skins=[dict(joints=list(range(len(joints))), inverseBindMatrices=ibm_acc, skeleton=0)],
         materials=[dict(name='herrero_%d' % i, pbrMetallicRoughness=dict(baseColorTexture=dict(index=i), metallicFactor=0.0, roughnessFactor=0.9)) for i in (0, 1)],
         textures=[dict(source=0, sampler=0), dict(source=1, sampler=0)], samplers=[dict(magFilter=9729, minFilter=9987, wrapS=33071, wrapT=33071)], images=images,
         accessors=acc, bufferViews=views, buffers=[dict(byteLength=sum(len(x) for x in bufs))])
js = json.dumps(g, separators=(',', ':')).encode(); js += b' ' * ((-len(js)) % 4); bn = b''.join(bufs)
with open('herrero.glb', 'wb') as fo:
    fo.write(struct.pack('<4sII', b'glTF', 2, 20 + len(js) + 8 + len(bn))); fo.write(struct.pack('<I4s', len(js), b'JSON')); fo.write(js); fo.write(struct.pack('<I4s', len(bn), b'BIN\0')); fo.write(bn)
with open('herrero.obj', 'w') as fo:
    fo.write('# El Herrero v2 - metres, Y up, faces +Z, T-pose (bind)\nmtllib herrero.mtl\n'); o = 1
    for p in parts:
        fo.write('g %s\nusemtl herrero_%d\n' % (p['name'], p['atlas']))
        for v in p['x_pos']: fo.write('v %.5f %.5f %.5f\n' % tuple(v))
        for t in p['x_uv']: fo.write('vt %.5f %.5f\n' % (t[0], 1 - t[1]))
        for n in p['x_nor']: fo.write('vn %.4f %.4f %.4f\n' % tuple(n))
        for t in p['x_idx'] + o: fo.write('f %d/%d/%d %d/%d/%d %d/%d/%d\n' % (t[0], t[0], t[0], t[1], t[1], t[1], t[2], t[2], t[2]))
        o += len(p['x_pos'])
open('herrero.mtl', 'w').write(''.join('newmtl herrero_%d\nKd 1 1 1\nmap_Kd herrero_tex%d.png\n' % (i, i) for i in (0, 1)))
print('tris', tot, 'joints', len(joints), 'verts', sum(len(p['x_pos']) for p in parts))
