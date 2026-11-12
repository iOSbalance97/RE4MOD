# Builds mod/files/ (data files replaced in the ISO by mkiso.py) from the clean extracted disc.
# B88: El Herrero is a NEW enemy (no Ganado is replaced any more). em12.drs (the farm's Ganados, room r103)
# gets four extra entries in its empty slots just before the module (REL), the original entries untouched:
#   HR_SLOT_BIN  the Herrero body (data/herrero.bin, its motions inside)       tag BIN
#   HR_SLOT_TPL  its textures: [0] the Ganado's face/hands (kept), [1] [2] ours tag TPL
#   HR_SLOT_ARC  a copy of the archive's offset table, every offset re-based on this entry, with the body
#                BIN/TPL words (0x1BC/0x1BD, Em10Set's EM10_BIN_BODY/TPL_BODY) pointing at the two above.
#                barn.c points the spawned enemy's subArc at it: ARC(no) = base + ofs[no] stays right for
#                every other entry and gives our body for those two.
#   HR_SLOT_TXT  the stealth tutorial panel, I4 texture (data/tut_stealth.i4)
# Archive: [count][REL offset][0][0], offsets[count], 4-char tags[count], data; the REL is the last data.
import sys, glob, os, struct, shutil
SRC = '/home/claude/disc/ext1/files/em/'; N = 32352
d0 = open(SRC + 'em10.drs', 'rb').read(); donor = d0[0x3ab040:0x3ab040 + N]
def pad32(b): return b + b'\0' * ((-len(b)) % 32)
blob = pad32(open('data/herrero.bin', 'rb').read())
tx = [open('data/herrero_tex%d.cmpr' % i, 'rb').read() for i in (0, 1)]
txt = pad32(open('data/tut_stealth.i4', 'rb').read())
SLOTS = dict(BIN=690, TPL=691, ARC=692, TXT=693)
BODY_W, TPL_W = 0x1BC, 0x1BD                         # ARC word numbers (arc entry + 4)
os.makedirs('files/em', exist_ok=True)
for f in glob.glob('files/em/*.drs'): os.remove(f)     # B88: every other em file goes back to the original
f = SRC + 'em12.drs'
d = open(f, 'rb').read(); i = d.find(donor); assert i > 0
psize, pofs = struct.unpack('>I', d[0x24:0x28])[0], struct.unpack('>I', d[0x2c:0x30])[0]
p1size, p1ofs = struct.unpack('>I', d[0x44:0x48])[0], struct.unpack('>I', d[0x4c:0x50])[0]
assert pofs == 0x400 and p1ofs == pofs + psize and p1ofs + p1size <= len(d)
arc = d[pofs:pofs + psize]; n, rel = struct.unpack('>II', arc[:8]); offs = list(struct.unpack('>%dI' % n, arc[0x10:0x10 + 4 * n]))
tags = [arc[0x10 + 4 * n + 4 * j:0x14 + 4 * n + 4 * j] for j in range(n)]
for s in SLOTS.values(): assert tags[s] == b'\0' * 4 and offs[s] == rel, s
k = BODY_W - 4; assert offs[k] == i - pofs and tags[k] == b'BIN\0' and tags[k + 1] == b'TPL\0'
t = arc[offs[k + 1]:offs[k + 2]]; assert t[:0xa0] == d0[0x3ab040 + N:][:0xa0], 'unexpected TPL layout'
th = bytearray(t[:0xa0])                                  # 3 images: [0] the Ganado's face (kept), [1] [2] ours, 512x512
th[0x48:0x4c] = struct.pack('>HH', 512, 512); th[0x50:0x54] = struct.pack('>I', 0xa0 + 32768)
th[0x6c:0x70] = struct.pack('>HH', 512, 512); th[0x74:0x78] = struct.pack('>I', 0xa0 + 32768 + 131072)
ntpl = pad32(bytes(th) + t[0xa0:0xa0 + 32768] + tx[0] + tx[1])
# the new data goes where the REL was; the REL and the empty slots after ours move by delta
o_bin = rel; o_tpl = o_bin + len(blob); o_arc = o_tpl + len(ntpl)
nw = 4 + n; fake_len = pad32(b'\0' * (4 * nw)); o_txt = o_arc + len(fake_len)
delta = o_txt + len(txt) - rel; assert delta % 32 == 0
noffs = [o + (delta if o >= rel and j > SLOTS['TXT'] else 0) for j, o in enumerate(offs)]
noffs[SLOTS['BIN']], noffs[SLOTS['TPL']], noffs[SLOTS['ARC']], noffs[SLOTS['TXT']] = o_bin, o_tpl, o_arc, o_txt
words = [n, rel + delta, 0, 0] + noffs
fake = [(w - o_arc) & 0xFFFFFFFF for w in words]; fake[:4] = words[:4]
fake[BODY_W] = (o_bin - o_arc) & 0xFFFFFFFF; fake[TPL_W] = (o_tpl - o_arc) & 0xFFFFFFFF
fakeb = pad32(struct.pack('>%dI' % nw, *fake))
ntags = list(tags); ntags[SLOTS['BIN']] = b'BIN\0'; ntags[SLOTS['TPL']] = b'TPL\0'
head = struct.pack('>4I', n, rel + delta, 0, 0) + struct.pack('>%dI' % n, *noffs) + b''.join(ntags)
assert len(head) == 0x10 + 8 * n
narc = bytearray(head + arc[len(head):rel] + blob + ntpl + fakeb + txt + arc[rel:])
nd = bytearray(d[:pofs] + narc + d[p1ofs:])
nd[0x24:0x28] = struct.pack('>I', psize + delta); nd[0x4c:0x50] = struct.pack('>I', p1ofs + delta)
# checks: every original entry reads the same (through the real and the fake table), the REL and part 1 moved intact
for j in range(n):
    if j in SLOTS.values() or (tags[j] == b"\0" * 4 and offs[j] == rel and j < SLOTS["BIN"]): continue
    a = narc[noffs[j]:noffs[j] + 32]; b = arc[offs[j]:offs[j] + 32]; assert a == b, j
    if j + 4 not in (BODY_W, TPL_W): assert (o_arc + fake[j + 4]) & 0xFFFFFFFF == noffs[j], j
assert narc[(o_arc + fake[BODY_W]) & 0xFFFFFFFF:][:0x60] == blob[:0x60] and narc[(o_arc + fake[TPL_W]) & 0xFFFFFFFF:][:0xa0] == ntpl[:0xa0]
assert narc[rel + delta:rel + delta + 64] == arc[rel:rel + 64] and nd[p1ofs + delta:p1ofs + delta + 64] == d[p1ofs:p1ofs + 64]
open('files/em/em12.drs', 'wb').write(nd)
open('c/herrero_arc.h', 'w').write('/* mkfiles.py: em12.drs extra entries (ARC word = entry + 4) */\n'
    '#define HR_ARC_W %d\n#define HR_TXT_W %d\n#define HR_TXT_W_PX %d\n#define HR_TXT_H_PX %d\n' %
    (SLOTS['ARC'] + 4, SLOTS['TXT'] + 4, *struct.unpack('>HH', open('data/tut_stealth.dim', 'rb').read())))
print('em12.drs grows', delta, 'bin', hex(o_bin), 'tpl', hex(o_tpl), 'arc', hex(o_arc), 'txt', hex(o_txt))
