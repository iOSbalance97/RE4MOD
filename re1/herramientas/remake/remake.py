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
    offs = struct.unpack('>20I', d[0x40:0x90]); a = sorted(x for x in offs if x)[k]
    nv, nt = struct.unpack('>HH', d[a:a + 4])
    T = np.frombuffer(d[a + 16:a + 16 + nt * 12], '>u2').reshape(-1, 6)
    V = np.frombuffer(d[a + 16 + nt * 12:a + 16 + nt * 12 + nv * 12], '>f4').reshape(-1, 3).astype(float)
    return V, T[:, :3].astype(int), T[:, 3:]
def camaras(st, r):
    d = open(f'{D}/st{st}/{r}.bgz', 'rb').read(); out = []
    for k in range(0, len(d) - 32, 0x800):
        w = struct.unpack('>8I', d[k:k + 32])
        if w[0] in (0x20, 0x40, 0x60, 0x80, 0xa0, 0xc0) and w[0] < w[1] < w[2] < w[3] < w[4] < 0x400000 and 1 <= w[5] <= 16 and w[6] == 0 and w[7] == 0:
            cam = struct.unpack('>8f', d[k + w[1]:k + w[1] + 32])
            ims = []; p = k + w[4]
            for m in re.finditer(rb'\xff\xd8\xff\xe0\x00\x10JFIF', d[p:p + 0x200000]):
                try:
                    im = Image.open(io.BytesIO(d[p + m.start():p + m.start() + 0x100000])); im.load()
                except Exception: continue
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
