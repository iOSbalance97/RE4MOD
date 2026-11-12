# Builds mod/files/ (data files replaced in the ISO by mkiso.py) from the clean extracted disc.
# El Herrero (data/herrero.bin + two 512x512 CMPR textures, from models/herrero/lowpoly/game.py) replaces the
# Ganado body model "34 bones / 770 vertices" (a BIN entry) and the TPL entry after it, in every em1x.drs
# that has it. The archive is rebuilt: [count][offset of the REL inside the last entry][0][0], offsets[count],
# 4-char tags[count], data. Entries after the two replaced ones move by the size difference; so do the REL
# offset, the .drs part-0 size (0x24) and the part-1 offset (0x4C).
import sys, glob, os, struct
SRC = '/home/claude/disc/ext1/files/em/'; N = 32352
d0 = open(SRC + 'em10.drs', 'rb').read(); donor = d0[0x3ab040:0x3ab040 + N]
def pad32(b): return b + b'\0' * ((-len(b)) % 32)
blob = pad32(open('data/herrero.bin', 'rb').read())
tx = [open('data/herrero_tex%d.cmpr' % i, 'rb').read() for i in (0, 1)]
os.makedirs('files/em', exist_ok=True)
for f in sorted(glob.glob(SRC + 'em1*.drs')):
    d = open(f, 'rb').read(); i = d.find(donor)
    if i < 0: continue
    psize, pofs = struct.unpack('>I', d[0x24:0x28])[0], struct.unpack('>I', d[0x2c:0x30])[0]
    p1size, p1ofs = struct.unpack('>I', d[0x44:0x48])[0], struct.unpack('>I', d[0x4c:0x50])[0]
    assert pofs == 0x400 and p1ofs == pofs + psize and p1ofs + p1size <= len(d)
    arc = d[pofs:pofs + psize]; n, rel = struct.unpack('>II', arc[:8]); offs = list(struct.unpack('>%dI' % n, arc[0x10:0x10 + 4 * n]))
    k = max(j for j, o in enumerate(offs) if o == i - pofs); assert arc[0x10 + 4 * n + 4 * k:][:3] == b'BIN' and arc[0x10 + 4 * n + 4 * (k + 1):][:3] == b'TPL'
    assert offs[k + 1] == offs[k] + N
    t = arc[offs[k + 1]:offs[k + 2]]; assert t[:0xa0] == d0[0x3ab040 + N:][:0xa0], 'unexpected TPL layout'
    th = bytearray(t[:0xa0])                                  # 3 images: [0] the Ganado's face (kept), [1] [2] ours, 512x512
    th[0x48:0x4c] = struct.pack('>HH', 512, 512); th[0x50:0x54] = struct.pack('>I', 0xa0 + 32768)
    th[0x6c:0x70] = struct.pack('>HH', 512, 512); th[0x74:0x78] = struct.pack('>I', 0xa0 + 32768 + 131072)
    ntpl = pad32(bytes(th) + t[0xa0:0xa0 + 32768] + tx[0] + tx[1])
    delta = len(blob) + len(ntpl) - (offs[k + 2] - offs[k]); assert delta % 32 == 0 and rel > offs[k + 2]
    noffs = [o + (delta if j > k + 1 else 0) for j, o in enumerate(offs)]; noffs[k + 1] = offs[k] + len(blob)
    narc = bytearray(arc[:offs[k]] + blob + ntpl + arc[offs[k + 2]:])
    narc[4:8] = struct.pack('>I', rel + delta); narc[0x10:0x10 + 4 * n] = struct.pack('>%dI' % n, *noffs)
    nd = bytearray(d[:pofs] + narc + d[p1ofs:])
    nd[0x24:0x28] = struct.pack('>I', psize + delta); nd[0x4c:0x50] = struct.pack('>I', p1ofs + delta)
    # every other entry must read the same through the new table
    for j in (0, k + 2, n - 2): assert offs[j] == offs[k] or narc[noffs[j]:noffs[j] + 64] == arc[offs[j]:offs[j] + 64]
    assert narc[rel + delta:rel + delta + 64] == arc[rel:rel + 64] and nd[p1ofs + delta:p1ofs + delta + 64] == d[p1ofs:p1ofs + 64]
    open('files/em/' + os.path.basename(f), 'wb').write(nd); print(os.path.basename(f), 'entry', k, 'grows', delta)
