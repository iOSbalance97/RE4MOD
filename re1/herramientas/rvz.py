"""Lector de discos de Wii en formato RVZ (Dolphin), solo lo necesario para sacar archivos:
la partición de datos se guarda ya descifrada y sin hashes, así que basta con descomprimir.
Formato según Dolphin (docs/WiaAndRvz.md). zstd por ctypes (libzstd del sistema).

uso: rvz.py disco.rvz list            -> archivos de la partición de juego
     rvz.py disco.rvz extract PATRÓN DESTINO
"""
import ctypes
import fnmatch
import os
import struct
import sys
from functools import lru_cache

_z = ctypes.CDLL('libzstd.so.1')
_z.ZSTD_decompress.restype = ctypes.c_size_t
_z.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
_z.ZSTD_isError.argtypes = [ctypes.c_size_t]
_z.ZSTD_getFrameContentSize.restype = ctypes.c_ulonglong
_z.ZSTD_getFrameContentSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]


def zdec(src, cap):
    out = ctypes.create_string_buffer(cap)
    n = _z.ZSTD_decompress(out, cap, src, len(src))
    if _z.ZSTD_isError(n):
        raise ValueError('zstd')
    return out.raw[:n]


SEC = 0x8000
SECD = 0x7C00


class RVZ:
    def __init__(self, path):
        self.f = open(path, 'rb')
        h = self.f.read(0x48)
        assert h[:4] == b'RVZ\x01', 'no es RVZ'
        dsize = struct.unpack('>I', h[12:16])[0]
        d = self.f.read(dsize)
        (self.disc_type, self.comp, self.level, self.chunk) = struct.unpack('>IIiI', d[:16])
        assert self.comp == 5, 'solo zstd'
        self.dhead = d[16:16 + 0x80]
        o = 16 + 0x80
        n_part, part_sz, part_off = struct.unpack('>IIQ', d[o:o + 16]); o += 16 + 20
        n_raw, raw_off, raw_size, n_grp, grp_off, grp_size = struct.unpack('>IQIIQI', d[o:o + 32])
        self.f.seek(part_off)
        pt = self.f.read(n_part * part_sz)
        self.parts = []
        for i in range(n_part):
            p = pt[i * part_sz:(i + 1) * part_sz]
            pds = [struct.unpack('>4I', p[16 + 16 * k:32 + 16 * k]) for k in range(2)]
            self.parts.append(pds)
        self.f.seek(raw_off)
        rt = zdec(self.f.read(raw_size), n_raw * 24)
        self.raws = [struct.unpack('>QQII', rt[24 * i:24 * i + 24]) for i in range(n_raw)]
        self.f.seek(grp_off)
        gt = zdec(self.f.read(grp_size), n_grp * 12)
        self.groups = [struct.unpack('>III', gt[12 * i:12 * i + 12]) for i in range(n_grp)]

    # ------------------------------------------------------------- grupos
    @lru_cache(maxsize=64)
    def group(self, gi, is_part, expect):
        off, size, packed = self.groups[gi]
        comp = bool(size & 0x80000000); size &= 0x7FFFFFFF
        if size == 0:
            return b'\0' * expect
        self.f.seek(off << 2)
        raw = self.f.read(size)
        data = zdec(raw, max(expect * 2 + 0x10000, packed + 0x10000)) if comp else raw
        p = 0
        if is_part:
            nl = max(1, self.chunk // 0x200000)
            for _ in range(nl):
                n = struct.unpack('>H', data[p:p + 2])[0]; p += 2 + n * 22
            if not comp:
                p = (p + 3) & ~3
        body = data[p:]
        if packed:
            body = self._unpack(body, expect)
        return body[:expect].ljust(expect, b'\0')

    @staticmethod
    def _unpack(b, expect):
        out = bytearray(); p = 0
        while p < len(b) and len(out) < expect:
            n = struct.unpack('>I', b[p:p + 4])[0]; p += 4
            if n & 0x80000000:
                n &= 0x7FFFFFFF; p += 68           # semilla del generador de relleno: el relleno no nos hace falta
                out += b'\0' * n
            else:
                out += b[p:p + n]; p += n
        return bytes(out)

    # ------------------------------------------------------------- GameCube: disco entero en datos "raw"
    def dump_iso(self, out):
        with open(out, 'wb') as o:
            for off, size, gi, ng in self.raws:
                end = off + size; start = off - off % SEC
                for g in range(ng):
                    pos = start + g * self.chunk
                    n = min(self.chunk, end - pos)
                    if n <= 0: break
                    data = self.group(gi + g, False, n)
                    o.seek(pos); o.write(data)
            o.seek(0); o.write(self.dhead)

    # ------------------------------------------------------------- partición
    def part_read(self, pi, off, n):
        """Lee n bytes de los datos (descifrados) de la partición pi, desde off."""
        pds = self.parts[pi]
        base = pds[0][0]
        spg = self.chunk // SEC
        out = bytearray()
        while n > 0:
            s = off // SECD; within = off % SECD
            abs_s = base + s
            for first, ns, gidx, ngrp in pds:
                if first <= abs_s < first + ns:
                    rel = abs_s - first
                    g = gidx + rel // spg
                    gsecs = min(spg, ns - (rel // spg) * spg)
                    data = self.group(g, True, gsecs * SECD)
                    o2 = (rel % spg) * SECD + within
                    take = min(n, SECD - within)
                    out += data[o2:o2 + take]
                    break
            else:
                raise ValueError(f'sector {abs_s} fuera de la partición')
            off += take; n -= take
        return bytes(out)

    def game_partition(self):
        want = self.dhead[:6]
        for i, pds in enumerate(self.parts):
            h = self.part_read(i, 0, 0x20)
            if h[:6] == want:
                return i, h[:6]
        raise ValueError('no encuentro la partición del juego')

    def fst(self, pi):
        h = self.part_read(pi, 0x420, 12)
        fst_off, fst_size = struct.unpack('>II', h[4:12])
        t = self.part_read(pi, fst_off << 2, fst_size << 2)
        cnt = struct.unpack('>I', t[8:12])[0]; st = cnt * 12
        files = []; stack = [(cnt, '')]; i = 1
        while i < cnt:
            while stack and i >= stack[-1][0]: stack.pop()
            typ = t[i * 12]; no = int.from_bytes(t[i * 12 + 1:i * 12 + 4], 'big')
            nm = t[st + no:t.index(b'\0', st + no)].decode('latin1'); base = stack[-1][1] if stack else ''
            a, b = struct.unpack('>II', t[i * 12 + 4:i * 12 + 12])
            if typ: stack.append((b, base + nm + '/'))
            else: files.append((base + nm, a << 2, b))
            i += 1
        return files


def main():
    r = RVZ(sys.argv[1])
    if sys.argv[2] == 'iso':
        r.dump_iso(sys.argv[3]); return
    pi, gid = r.game_partition()
    files = r.fst(pi)
    if sys.argv[2] == 'list':
        print('partición', pi, gid.decode(), len(files), 'archivos')
        for p, o, s in files: print(s, p)
    elif sys.argv[2] == 'extract':
        pat, dst = sys.argv[3], sys.argv[4]
        for p, o, s in files:
            if fnmatch.fnmatch(p.lower(), pat.lower()):
                out = os.path.join(dst, p); os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, 'wb') as fo:
                    for k in range(0, s, 1 << 22):
                        fo.write(r.part_read(pi, o + k, min(1 << 22, s - k)))
                print(p, s)


if __name__ == '__main__':
    main()
