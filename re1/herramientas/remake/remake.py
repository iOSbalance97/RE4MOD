"""Lectura de salas del REmake de GameCube (rNNN.dat + rNNN.bgz).
dat: tabla de secciones en 0x40 (20 desplazamientos). Secciones 0 y 1: mallas (u16 nv, u16 nt, ...; nt tri de 12 bytes
(3 índices u16 + 3 u16); nv vértices float3). bgz: bloques con cabecera [0x20, cam, ?, shd, jpeg, n, 0, 0]; la cámara
son 8 floats: ojo xyz, objetivo xyz, giro, apertura (grados)."""
import io, re, struct
import numpy as np
from PIL import Image
D = '/home/claude/re1gc/files'
def malla(st, r, k=1):
    d = open(f'{D}/st{st}/{r}.dat', 'rb').read()
    a = struct.unpack('>16I', d[:64])[(1, 9)[k]]  # cabecera: 1 = malla simple, 9 = detallada
    nv, nt = struct.unpack('>HH', d[a:a + 4])
    T = np.frombuffer(d[a + 16:a + 16 + nt * 12], '>u2').reshape(-1, 6)
    V = np.frombuffer(d[a + 16 + nt * 12:a + 16 + nt * 12 + nv * 12], '>f4').reshape(-1, 3).astype(float)
    return V, T[:, :3].astype(int), T[:, 3:]
def jpeg(d, s):
    try:
        im = Image.open(io.BytesIO(d[s:s + 0x100000])); im.load(); return im
    except Exception: pass
    # variante del REmake sin relleno de 0xFF en los datos (fondos animados): se rellena y se decodifica
    try:
        i = s + 2
        while True:
            L = struct.unpack('>H', d[i + 2:i + 4])[0]
            if d[i + 1] == 0xda: hs = i + 2 + L; break
            i += 2 + L
            if i - s > 4096: return None
        sig = d.find(b'\xff\xd8\xff', hs); sig = sig if sig > 0 else s + 0x100000
        fin = d.rfind(b'\xff\xd9', hs, sig)
        scan = d[hs:fin if fin > 0 else sig]
        im = Image.open(io.BytesIO(d[s:hs] + scan.replace(b'\xff', b'\xff\x00') + b'\xff\xd9')); im.load(); return im
    except Exception: return None
def camaras(st, r):
    d = open(f'{D}/st{st}/{r}.bgz', 'rb').read(); out = []
    for k in range(0, len(d) - 32, 0x800):
        w = struct.unpack('>8I', d[k:k + 32])
        if w[0] % 0x20 == 0 and 0x20 <= w[0] < 0x1000 and w[0] < w[1] < w[2] < w[3] < w[4] < 0x400000 and 1 <= w[5] <= 16 and w[6] == 0 and w[7] == 0:
            cam = struct.unpack('>8f', d[k + w[1]:k + w[1] + 32])
            ims = []; p = k + w[4]
            for m in re.finditer(rb'\xff\xd8\xff[\xe0\xdb\xc4\xc0]', d[p:p + 0x200000]):
                im = jpeg(d, p + m.start())
                if im is None: continue
                if im.size[0] >= 500: ims.append(im.convert('RGB'))
                if len(ims) >= w[5]: break
            out.append(dict(ojo=np.array(cam[:3]), obj=np.array(cam[3:6]), giro=cam[6], fov=cam[7], img=ims[0] if ims else None, bloque=k))
    return out
def proyectar(cam, P, W=512, H=448, aspecto=4 / 3, fov_vertical=True):
    f = cam['obj'] - cam['ojo']; f /= np.linalg.norm(f)
    up = np.array([0, 1.0, 0]); rgt = np.cross(f, up); rgt /= np.linalg.norm(rgt); u = np.cross(rgt, f)
    Q = (P - cam['ojo']) @ np.stack([rgt, u, f], 1)
    t = np.tan(np.radians(cam['fov']) / 2)
    if fov_vertical: sy = 1 / t; sx = sy / aspecto
    else: sx = 1 / t; sy = sx * aspecto
    x = Q[:, 0] / Q[:, 2] * sx; y = Q[:, 1] / Q[:, 2] * sy
    return np.stack([(x + 1) / 2 * W, (1 - y) / 2 * H], 1), Q[:, 2]
def disparadores(st, r):
    d = open(f'{D}/st{st}/{r}.dat', 'rb').read(); a = struct.unpack('>I', d[32:36])[0]
    if not a: return []
    n = struct.unpack('>H', d[a + 10:a + 12])[0]; sz = struct.unpack('>H', d[a + 12:a + 14])[0]; out = []
    for k in range(n):
        o = a + 16 + k * sz; rec = d[o:o + sz]
        q = np.array(struct.unpack('>8f', rec[4:36])).reshape(4, 2)
        out.append(dict(flags=rec[:4].hex(), tipo=rec[36], sub=rec[37], par=struct.unpack('>H', rec[38:40])[0], quad=q))
    return out
def bbox(st, r):
    V, T, _ = malla(st, r, 0); return V.min(0), V.max(0)
