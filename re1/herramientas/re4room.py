"""OBJ de una sala -> datos de escenario de RE4 GameCube (SMD con modelos BIN + una TPL, y SMX vacío).

Formatos según el decomp (adonis-singh/re4): tools/motion/meshbin.py (BIN, se serializa con su
propio `serialise`), tools/motion/gxtex.py (TPL), include/scroll.h + game/scroll.cpp (SMD/SMX).
Coordenadas: las de RE4 son las de glTF/OBJ (Y arriba, mano derecha, caras CCW), en milímetros.

uso: re4room.py sala.obj salida_dir [--escala 1000] [--celda 6.0] [--decimar] [--tex-max 512]
"""
import argparse
import os
import struct
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, '/home/claude/re4src/tools/motion')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gxtex      # noqa: E402
import meshbin    # noqa: E402
import objload    # noqa: E402
import strips     # noqa: E402

ALIGN = 0x20


def al(n, a=ALIGN):
    return (n + a - 1) & ~(a - 1)


# ---------------------------------------------------------------- texturas (CMPR + mipmaps)

def _to565(c):
    c = c.astype(np.int32)
    return ((c[..., 0] >> 3) << 11) | ((c[..., 1] >> 2) << 5) | (c[..., 2] >> 3)


def _from565(v):
    r = (v >> 11) & 31; g = (v >> 5) & 63; b = v & 31
    return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], -1).astype(np.int32)


def cmpr_encode(img):
    """RGBA8 (h, w, 4), h y w múltiplos de 8 -> bytes CMPR (bloques 4x4 tipo DXT1, orden GX)."""
    h, w = img.shape[:2]
    tiles = gxtex._untile(img, 8, 8)                         # (n, 8, 8, 4)
    blk = tiles.reshape(-1, 2, 4, 2, 4, 4).transpose(0, 1, 3, 2, 4, 5).reshape(-1, 16, 4).astype(np.int32)
    rgb = blk[..., :3]; a = blk[..., 3]
    trans = a < 128                                           # texeles transparentes
    anyt = trans.any(1)
    # extremos por eje principal
    mean = rgb.mean(1, keepdims=True)
    d = rgb - mean
    cov = np.einsum('nki,nkj->nij', d, d)
    axis = np.ones((len(blk), 3))
    for _ in range(6):
        axis = np.einsum('nij,nj->ni', cov, axis)
        axis /= np.linalg.norm(axis, axis=1, keepdims=True) + 1e-9
    proj = np.einsum('nki,ni->nk', d, axis)
    big = np.where(trans, -1e9, proj); small = np.where(trans, 1e9, proj)
    i_max = big.argmax(1); i_min = small.argmin(1)
    cA = rgb[np.arange(len(blk)), i_max]; cB = rgb[np.arange(len(blk)), i_min]
    e0 = _to565(cA); e1 = _to565(cB)
    # modo 4 colores (e0 > e1) sin transparencia; 3 colores + transparente (e0 <= e1) si hay alfa
    swap4 = (~anyt) & (e0 < e1)
    e0, e1 = np.where(swap4, e1, e0), np.where(swap4, e0, e1)
    swap3 = anyt & (e0 > e1)
    e0, e1 = np.where(swap3, e1, e0), np.where(swap3, e0, e1)
    r0 = _from565(e0); r1 = _from565(e1)
    four = (e0 > e1)[:, None]
    pal = np.zeros((len(blk), 4, 3), np.int32)
    pal[:, 0] = r0; pal[:, 1] = r1
    pal[:, 2] = np.where(four, (r1 * 3 + r0 * 5) >> 3, (r0 + r1) // 2)
    pal[:, 3] = np.where(four, (r0 * 3 + r1 * 5) >> 3, (r0 + r1) // 2)
    dist = ((rgb[:, :, None, :] - pal[:, None, :, :]) ** 2).sum(-1)    # (n, 16, 4)
    dist[:, :, 3] = np.where(four, dist[:, :, 3], 1 << 30)              # índice 3 = transparente en modo 3
    idx = dist.argmin(-1)
    idx = np.where(trans & ~four, 3, idx)
    idx = idx.reshape(-1, 4, 4)
    rows = (idx[:, :, 0] << 6) | (idx[:, :, 1] << 4) | (idx[:, :, 2] << 2) | idx[:, :, 3]
    out = np.zeros((len(blk), 8), np.uint8)
    out[:, 0] = e0 >> 8; out[:, 1] = e0 & 0xFF; out[:, 2] = e1 >> 8; out[:, 3] = e1 & 0xFF
    out[:, 4:8] = rows
    return out.tobytes()


def build_tpl(images, mip=True):
    """images: lista de PIL RGBA -> bytes TPL (CMPR, REPEAT, mipmaps hasta 8x8)."""
    n = len(images)
    hdr = 12; desc = hdr; th0 = al(desc + 8 * n)
    texhdr_size = 0x24
    data_start = al(th0 + texhdr_size * n)
    blobs = []; heads = []
    o = data_start
    for im in images:
        w, h = im.size
        levels = []
        cur = im
        fmt = gxtex.FMT_I4 if im.mode == 'L' else gxtex.FMT_CMPR
        while True:
            a = np.asarray(cur.convert('RGBA'))
            levels.append(gxtex.encode(fmt, a) if fmt == gxtex.FMT_I4 else cmpr_encode(a))
            if not mip or min(cur.size) <= 8:
                break
            cur = cur.resize((max(8, cur.size[0] // 2), max(8, cur.size[1] // 2)), Image.LANCZOS)
        blob = b''.join(levels)
        heads.append((h, w, o, len(levels), fmt))
        blobs.append(blob + b'\0' * (al(len(blob)) - len(blob)))
        o += len(blobs[-1])
    out = bytearray(data_start)
    struct.pack_into('>III', out, 0, gxtex.TPL_VERSION, n, desc)
    for i, (h, w, off, nl, fmt) in enumerate(heads):
        struct.pack_into('>II', out, desc + 8 * i, th0 + texhdr_size * i, 0)
        minf = 5 if nl > 1 else 1      # GX_LIN_MIP_LIN / GX_LINEAR
        struct.pack_into('>HHIIIIIIfBBBB', out, th0 + texhdr_size * i, h, w, fmt, off,
                         1, 1, minf, 1, 0.0, 0, 0, nl - 1, 0)
    return bytes(out) + b''.join(blobs)


def prep_texture(path, tex_max):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    s = 1.0
    while max(w, h) * s > tex_max: s /= 2
    nw, nh = max(8, int(w * s)), max(8, int(h * s))
    if (nw, nh) != (w, h):
        im = im.resize((nw, nh), Image.LANCZOS)
    alpha = np.asarray(im)[..., 3]
    return im, bool((alpha < 128).any())


# ---------------------------------------------------------------- geometría

def weld(V, T, faces):
    """faces (m, 6) [v0 v1 v2 t0 t1 t2] -> P, UV, tris (soldado por posición + UV)."""
    corners_p = V[faces[:, :3].ravel()]; corners_t = T[faces[:, 3:].ravel()]
    key = np.c_[np.round(corners_p / 1e-5), np.round(corners_t / 1e-5)].astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    tris = inv.ravel().reshape(-1, 3)
    good = (tris[:, 0] != tris[:, 1]) & (tris[:, 1] != tris[:, 2]) & (tris[:, 0] != tris[:, 2])
    return corners_p[first], corners_t[first], tris[good]


def vertex_normals(P, tris):
    n = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    N = np.zeros_like(P)
    for j in range(3): np.add.at(N, tris[:, j], n)
    # suavizado entre vértices de la misma posición (costuras de UV)
    key = np.round(P / 1e-5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
    acc = np.zeros((inv.max() + 1, 3)); np.add.at(acc, inv, N); N = acc[inv]
    ln = np.linalg.norm(N, axis=1, keepdims=True)
    return np.where(ln > 1e-12, N / np.maximum(ln, 1e-12), [0, 1, 0])


MAT_DEFAULT = dict(flags=0, bump_tex=0xFF, spec_tex=0xFF, spec_rgb=(0, 0, 0), spec_type=0,
                   alpha_ref=0, spec_pow=0, pad_16=0, spec_tex_org=0xFF)   # valores de los modelos de sala reales (r102)


def build_bin(groups, origin, scale, alpha_tex, n_tex):
    """groups: lista de (tex_id, P (m), UV, N, tris). Devuelve bytes BIN (meshbin.Mesh serializado)."""
    allP = np.concatenate([g[1] for g in groups]) * scale - origin
    ext = np.abs(allP).max() if len(allP) else 1
    shift = 0
    while shift < 15 and ext * (1 << (shift + 1)) < 32000: shift += 1
    vtx = []; nrm = []; tex = []; parts = []
    for tex_id, P, UV, N, tris in groups:
        base = len(vtx)
        q = np.round((P * scale - origin) * (1 << shift)).astype(int)
        vtx += [(int(x), int(y), int(z), 0) for x, y, z in q]
        nq = np.clip(np.round(N * 64), -64, 63).astype(int)
        nrm += [(int(x), int(y), int(z), 0) for x, y, z in nq]
        tq = np.clip(np.round(np.c_[UV[:, 0], 1.0 - UV[:, 1]] * 256), -32768, 32767).astype(int)
        tex += [(int(s), int(t)) for s, t in tq]
        prims = []
        sts, singles = strips.stripify(tris + base)
        for st in sts:
            for k in range(0, len(st) - 2, 60000):
                seg = st[k:k + 60002]
                if k % 2: raise RuntimeError('tira partida en impar')
                prims.append(meshbin.Prim(meshbin.OP_STRIP, [(v, v, 0, v) for v in seg]))
        for k in range(0, len(singles), 21000):
            chunk = singles[k:k + 21000]
            prims.append(meshbin.Prim(meshbin.OP_TRIANGLES, [(v, v, 0, v) for t in chunk for v in t]))
        stream = sum(3 + 8 * len(p.verts) for p in prims)
        md = dict(MAT_DEFAULT)
        flags = 0
        a_tex = 0
        if alpha_tex.get(tex_id) is not None:
            flags |= 4; a_tex = alpha_tex[tex_id]     # textura I4 aparte con el alfa, como en el juego
        parts.append(meshbin.Part(flags, tex_id, md['bump_tex'], a_tex, md['spec_tex'], md['spec_rgb'],
                                  md['spec_type'], md['alpha_ref'], md['spec_pow'], md['pad_16'], md['spec_tex_org'],
                                  len(tris), al(stream), prims))
    if len(vtx) > 0xFFFF:
        raise ValueError(f'{len(vtx)} vértices en un BIN (máx 65535)')
    # cabecera como la de los modelos de escenario del juego: versión antigua, sin pesos ni tablas
    m = meshbin.Mesh(version=meshbin.VERSION_OLD, flags=meshbin.FLAG_TEX_S16_CLR | meshbin.FLAG_NRM_S8, shift=shift,
                     n_tex=n_tex, weight_palette_num=0, weight_ext_num=0, x8=0,
                     heads=[meshbin.Head(0, 0xFF, 0, 0, (0.0, 0.0, 0.0))], vtx=vtx, nrm=nrm, clr=[0xFFFFFFFF],
                     tex=tex, weights=[], parts=parts, blend_table=None, flip_table=None, shapes=None)
    return meshbin.serialise(m), shift


def build_smd(bins, tpls, works, version=0x40):
    """works: lista de (pos mm, bin_id, tpl_id, work_no). Tablas de offsets relativas a cada tabla."""
    nw = len(works)
    head = 0x10 + 0x48 * nw
    bin_tbl = al(head)
    tpl_tbl = al(bin_tbl + 4 * len(bins))
    mot_tbl = al(tpl_tbl + 4 * len(tpls))
    data = al(mot_tbl + 4)
    out = bytearray(data)
    struct.pack_into('>BBHIII', out, 0, version, 0, nw, bin_tbl, tpl_tbl, mot_tbl)
    for i, (pos, b, t, wn) in enumerate(works):
        o = 0x10 + 0x48 * i
        struct.pack_into('>9f4BfI', out, o, *pos, 0, 0, 0, 1, 1, 1, b, t, 0xFF, wn, 0.0, 0)
        struct.pack_into('>I', out, o + 0x44, 8)       # Attribute 8, el valor habitual en las salas
    for tbl, items in ((bin_tbl, bins), (tpl_tbl, tpls)):
        for i, blob in enumerate(items):
            struct.pack_into('>I', out, tbl + 4 * i, len(out) - tbl)
            out += blob + b'\0' * (al(len(blob)) - len(blob))
    return bytes(out)


def build_smx_empty():
    return struct.pack('>BBBBIII', 1, 0, 0, 0, 0, 0, 0) + b'\0' * 0x10


def place(V, spec, scale):
    """Coloca la sala en el mundo del juego (en metros todavía; se pasa a mm al cuantizar)."""
    if not spec:
        return V
    hx, hy, hz, x, y, z, rot = [float(v) for v in spec.split(',')]
    c, s = np.cos(rot), np.sin(rot)
    P = V - [hx, hy, hz]
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])      # giro en Y (mano derecha)
    return P @ R.T + np.array([x, y, z]) / scale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('obj'); ap.add_argument('out')
    ap.add_argument('--escala', type=float, default=1000.0)
    ap.add_argument('--celda', type=float, default=6.0)
    ap.add_argument('--decimar', type=float, default=0.0, help='proporción a conservar en piezas muy densas (0 = no)')
    ap.add_argument('--densidad', type=float, default=400.0)
    ap.add_argument('--tex-max', type=int, default=512)
    ap.add_argument('--mipmaps', action='store_true', help='las salas del juego no llevan')
    ap.add_argument('--colocar', default='', help='hx,hy,hz,x,y,z,giro: el punto (hx,hy,hz) de la sala en metros va a (x,y,z) mm del juego, girando la sala `giro` rad en Y')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    V, T, F, M, G, mats = objload.load(a.obj)
    base = os.path.dirname(a.obj)
    V = place(V, a.colocar, a.escala)
    texnames = sorted({mats[m] for m in set(M) if mats.get(m)})
    tex_id = {t: i for i, t in enumerate(texnames)}
    images = []; alpha_tex = {}
    for t in texnames:
        im, has_a = prep_texture(os.path.join(base, t), a.tex_max)
        images.append(im)
    for t in texnames:
        im = images[tex_id[t]]
        al_ = np.asarray(im)[..., 3]
        if (al_ < 128).any():
            alpha_tex[tex_id[t]] = len(images)
            images.append(Image.fromarray(np.where(al_ >= 128, 255, 0).astype(np.uint8), 'L'))
    # grupos por material (sub-malla original)
    if a.decimar:
        import decimate
    groups = []
    stats = dict(tris_in=len(F), tris_out=0)
    for g in dict.fromkeys(G):
        sel = G == g
        tn = mats.get(M[sel][0])
        if not tn:
            continue          # sin textura (la que falta): se omite
        P, UV, tris = weld(V, T, F[sel])
        if a.decimar and len(tris) > 1000:
            area = np.linalg.norm(np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]]), axis=1).sum() / 2
            if len(tris) / max(area, 1e-6) > a.densidad:
                P, UV, tris = decimate.decimate(P, UV, tris, a.decimar)
        groups.append((tex_id[tn], P, UV, tris))
        stats['tris_out'] += len(tris)
    # trocear por celdas XZ (cada celda = un BIN)
    allc = np.concatenate([g[1][g[3]].mean(1) for g in groups])
    lo = allc.min(0)
    cells = {}
    for tid, P, UV, tris in groups:
        c = P[tris].mean(1)
        ij = np.floor((c[:, [0, 2]] - lo[[0, 2]]) / a.celda).astype(int)
        N = vertex_normals(P, tris)
        for key in {tuple(x) for x in ij}:
            s = (ij[:, 0] == key[0]) & (ij[:, 1] == key[1])
            tt = tris[s]; used = np.unique(tt); rm = -np.ones(len(P), int); rm[used] = np.arange(len(used))
            cells.setdefault(key, []).append((tid, P[used], UV[used], N[used], rm[tt]))
    bins = []; works = []; report = []
    for key in sorted(cells):
        grp = cells[key]
        # repartir si pasa de 65535 vértices
        packs = [[]]; nv = 0
        for g in grp:
            if nv + len(g[1]) > 60000 and packs[-1]:
                packs.append([]); nv = 0
            packs[-1].append(g); nv += len(g[1])
        for pk in packs:
            P = np.concatenate([g[1] for g in pk]) * a.escala
            origin = np.round((P.min(0) + P.max(0)) / 2)
            b, shift = build_bin(pk, origin, a.escala, alpha_tex, len(images))
            works.append((tuple(float(x) for x in origin), len(bins), 0, 0xFE))
            bins.append(b)
            report.append((key, sum(len(g[4]) for g in pk), sum(len(g[1]) for g in pk), len(b), shift))
    tpl = build_tpl(images, mip=a.mipmaps)
    smd = build_smd(bins, [tpl], works)
    open(os.path.join(a.out, 'sala.smd'), 'wb').write(smd)
    open(os.path.join(a.out, 'sala.smx'), 'wb').write(build_smx_empty())
    open(os.path.join(a.out, 'texturas.tpl'), 'wb').write(tpl)
    for i, b in enumerate(bins):
        open(os.path.join(a.out, f'modelo_{i:02d}.bin'), 'wb').write(b)
    print(f'triángulos {stats["tris_in"]} -> {stats["tris_out"]}; {len(bins)} BIN, {len(texnames)} texturas')
    for r in report:
        print(f'  celda {r[0]}: {r[1]} tri, {r[2]} vért, {r[3] / 1024:.0f} KB, shift {r[4]}')
    print(f'TPL {len(tpl) / 1024:.0f} KB; SMD total {len(smd) / 1024:.0f} KB')


if __name__ == '__main__':
    main()
