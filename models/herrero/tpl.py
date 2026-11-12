import struct, numpy as np
def rgb565(v): return ((v>>11)&31)*255//31, ((v>>5)&63)*255//63, (v&31)*255//31
def rgb5a3(v):
    if v&0x8000: return ((v>>10)&31)*255//31, ((v>>5)&31)*255//31, (v&31)*255//31, 255
    return ((v>>8)&15)*17, ((v>>4)&15)*17, (v&15)*17, ((v>>12)&7)*255//7
def dec(d, fmt, w, h, pal=None):
    img = np.zeros((h, w, 4), np.uint8); p = 0
    if fmt == 14:
        for by in range(0, h, 8):
            for bx in range(0, w, 8):
                for sy in (0, 4):
                    for sx in (0, 4):
                        c0, c1 = struct.unpack('>HH', d[p:p+4]); bits = struct.unpack('>I', d[p+4:p+8])[0]; p += 8
                        r0 = rgb565(c0); r1 = rgb565(c1)
                        if c0 > c1: cs = [r0+(255,), r1+(255,), tuple((2*a+b)//3 for a, b in zip(r0, r1))+(255,), tuple((a+2*b)//3 for a, b in zip(r0, r1))+(255,)]
                        else: cs = [r0+(255,), r1+(255,), tuple((a+b)//2 for a, b in zip(r0, r1))+(255,), (0, 0, 0, 0)]
                        for i in range(16):
                            x = bx+sx+i%4; y = by+sy+i//4
                            if x < w and y < h: img[y, x] = cs[(bits >> (30-2*i)) & 3]
        return img
    bw, bh, bpp = {0: (8, 8, 4), 1: (8, 4, 8), 2: (8, 4, 8), 3: (4, 4, 16), 4: (4, 4, 16), 5: (4, 4, 16), 6: (4, 4, 32), 8: (8, 8, 4), 9: (8, 4, 8), 10: (4, 4, 16)}[fmt]
    for by in range(0, h, bh):
        for bx in range(0, w, bw):
            if fmt == 6:
                blk = d[p:p+64]; p += 64
                for i in range(16):
                    x = bx+i%4; y = by+i//4
                    if x < w and y < h: img[y, x] = (blk[2*i+1], blk[32+2*i], blk[33+2*i], blk[2*i])
                continue
            for yy in range(bh):
                for xx in range(bw):
                    x = bx+xx; y = by+yy
                    if bpp == 4:
                        b = d[p + (yy*bw+xx)//2]; v = (b >> 4) if xx % 2 == 0 else (b & 15)
                    elif bpp == 8: v = d[p + yy*bw+xx]
                    else: v = struct.unpack('>H', d[p+2*(yy*bw+xx):p+2*(yy*bw+xx)+2])[0]
                    if x >= w or y >= h: continue
                    if fmt == 0: c = (v*17,)*3 + (255,)
                    elif fmt == 1: c = (v,)*3 + (255,)
                    elif fmt == 2: c = ((v & 15)*17,)*3 + ((v >> 4)*17,)
                    elif fmt == 3: c = (v & 255,)*3 + (v >> 8,)
                    elif fmt == 4: c = rgb565(v) + (255,)
                    elif fmt == 5: c = rgb5a3(v)
                    else: c = pal[v & 0x3FFF] if pal else (v & 255,)*3 + (255,)
                    img[y, x] = c
            p += bw*bh*bpp//8
    return img
def tpl_images(d, base):
    n, tab = struct.unpack('>II', d[base+4:base+12]); out = []
    for i in range(n):
        io, po = struct.unpack('>II', d[base+tab+8*i:base+tab+8*i+8])
        h, w, fmt, off = struct.unpack('>HHII', d[base+io:base+io+12])
        pal = None
        if po:
            cnt, _, pf, pofs = struct.unpack('>HHII', d[base+po:base+po+12])[:4] if False else (struct.unpack('>H', d[base+po:base+po+2])[0], 0, struct.unpack('>I', d[base+po+4:base+po+8])[0], struct.unpack('>I', d[base+po+8:base+po+12])[0])
            raw = struct.unpack('>%dH' % cnt, d[base+pofs:base+pofs+2*cnt])
            pal = [rgb5a3(v) if pf == 2 else (rgb565(v)+(255,) if pf == 1 else ((v & 255,)*3+(v >> 8,))) for v in raw]
        out.append((w, h, fmt, base+off, pal))
    return out
