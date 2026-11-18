"""Compresor yz2 (el formato de las salas St*/rNNN.das de RE4 GameCube).

Es el espejo exacto del descompresor del decomp (tools/motion/yz2.py, portado de yz2asm.cpp):
mismo codificador de rango, mismos modelos adaptativos y mismo diccionario por contexto. Se
comprueba siempre descomprimiendo el resultado con el decoder original.

uso: yz2enc.py entrada salida      (salida = cabecera de texto + flujo, como Yz2DecodeSet espera)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 're4src', 'tools', 'motion'))
sys.path.insert(0, '/home/claude/re4src/tools/motion')
import yz2  # noqa: E402

RING = yz2.RING


class _Enc:
    def __init__(self):
        self.out = bytearray()
        self.low = 0
        self.W = 0x100      # 2 * R del decoder (R empieza en 0x80, una ventana de 1 byte)
        self.nwin = 1       # bytes del código dentro de la ventana del decoder (máx 4)

    def _carry(self):
        i = len(self.out) - 1
        while True:
            if i < 0:
                raise RuntimeError('acarreo fuera del flujo')
            if self.out[i] == 0xFF:
                self.out[i] = 0; i -= 1
            else:
                self.out[i] += 1; return

    def renorm(self):
        while self.W <= 0x1000000:          # R <= 0x800000
            self.low <<= 8; self.W <<= 8; self.nwin += 1
            if self.nwin > 4:
                self.out.append(self.low >> 32); self.low &= 0xFFFFFFFF; self.nwin = 4

    def encode(self, m, s):
        self.renorm()
        R = self.W >> 1
        step = R >> 14
        self.low += step * m.cum_s[s]
        lim = 1 << (8 * self.nwin)
        if self.low >= lim:
            self.low -= lim; self._carry()
        self.W = 2 * ((step * m.cum_f[s]) >> 1)
        if self.W == 0:
            raise RuntimeError('rango agotado')
        _update(m, s)

    def finish(self):
        # el valor final = low; se vuelcan los bytes de la ventana y relleno
        b = self.low.to_bytes(self.nwin, 'big')
        return bytes(self.out + b + b'\0' * 8)


def _update(m, s):
    freq = m.freq
    freq[s] += 1
    m.total += 1
    if m.bits <= 14:
        if m.total == m.range:
            sh = 15 - m.bits; run = 0
            for i in range(m.n):
                v = freq[i] << sh; m.cum_s[i] = run; run += v; m.cum_f[i] = v
            m.bits += 1; m.range = 1 << m.bits
    elif m.total > 0x7FFF:
        run = 0; total = 0
        for i in range(m.n):
            v = freq[i]; m.cum_f[i] = v; m.cum_s[i] = run; run += v
            if v > 1:
                v >>= 1; freq[i] = v
            total += v
        m.total = total


def _match_len(d, a, b, limit):
    """Bytes iguales entre d[a:] y d[b:] (a < b), hasta limit."""
    n = 0
    step = 64
    while n < limit:
        k = min(step, limit - n)
        if d[a + n:a + n + k] == d[b + n:b + n + k]:
            n += k; step *= 2
        else:
            if k == 1: break
            step = max(1, k // 2)
    return n


def compress(data, min_match=3):
    data = bytes(data)
    N = len(data)
    enc = _Enc()
    main = yz2._Model(yz2.N_MAIN)
    side = yz2._Model(yz2.N_SIDE)
    dic_ptr = [-1] * (256 * RING)
    dic_len = [0] * (256 * RING)
    dic_cnt = [0] * 256
    index = {}            # (ctx, 2 bytes siguientes) -> lista de slots
    o = 0
    scan = 0
    while o < N:
        length = 1
        best = None
        if o > 0 and o + 2 <= N:
            ctx = data[scan]
            key = (ctx, data[o:o + 2])
            lst = index.get(key)
            if lst:
                base = ctx * RING
                keep = []
                for slot in reversed(lst):
                    p = dic_ptr[base + slot]
                    if p < 0 or data[p:p + 2] != data[o:o + 2] or slot in keep:
                        continue
                    keep.append(slot)
                    L = _match_len(data, p, o, N - o)
                    el = dic_len[base + slot]
                    if el <= L and el >= min_match and (best is None or el >= best[1]) and el >= L - 2:
                        best = (slot, el, True)
                    if L >= min_match and (best is None or L > best[1] + 2):
                        best = (slot, L, False)
                    if len(keep) >= 48:
                        break
                index[key] = list(reversed(keep))
        if best is None:
            enc.encode(main, 0x400 + data[o])
        else:
            slot, length, exact = best
            ctx = data[scan]
            s = (slot - dic_cnt[ctx]) & 0x1FF
            if exact:
                enc.encode(main, 0x200 + s)
            else:
                enc.encode(main, s)
                v = length + 1
                if v <= 0xFF and v > 2:
                    enc.encode(side, v)
                elif v <= 0xFFFF:
                    enc.encode(side, 2); enc.encode(side, v >> 8); enc.encode(side, v & 0xFF)
                elif v <= 0xFFFFFF:
                    enc.encode(side, 1)
                    for sh in (16, 8, 0): enc.encode(side, (v >> sh) & 0xFF)
                else:
                    enc.encode(side, 0)
                    for sh in (24, 16, 8, 0): enc.encode(side, (v >> sh) & 0xFF)
        o += length
        last = o - 1
        if scan < last:
            ctx = data[scan]
            cnt = dic_cnt[ctx]
            dic_ptr[ctx * RING + cnt] = scan + 1
            dic_len[ctx * RING + cnt] = length
            dic_cnt[ctx] = (cnt + 1) & 0x1FF
            if scan + 3 <= N:
                k = (ctx, data[scan + 1:scan + 3])
                index.setdefault(k, []).append(cnt)
            scan = last
    stream = enc.finish()
    # cabecera: "<empaquetado hex>\t<desempaquetado hex>\n", flujo en el siguiente múltiplo de 32
    for _ in range(3):
        hdr = b'%x\t%x\n' % (len(stream), N)
        start = (len(hdr) - 1 + 0x20) & ~0x1F     # (fin del 2º número + 0x20) & ~0x1F
        out = hdr + b'\0' * (start - len(hdr)) + stream
    return out


def verify(packed, original):
    dec, _, _ = yz2.decode(packed, 0)
    return dec == bytes(original)


if __name__ == '__main__':
    src = open(sys.argv[1], 'rb').read()
    out = compress(src)
    assert verify(out, src), 'la descompresión no coincide'
    open(sys.argv[2], 'wb').write(out)
    print(f'{len(src)} -> {len(out)} bytes ({100 * len(out) / max(1, len(src)):.1f}%), verificado')
