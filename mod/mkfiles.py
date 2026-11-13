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

# C0-10b: the Insignia Key's pick-up model (item 0x3B), taken from r105's ITM, appended at the end of em12.drs
# (past everything the game reads of it); ch0.c reads it from there when r111 is set up and registers it.
sys.path.insert(0, '../tools/ch0')
import arc as _arc
_r = open('/tmp/r105.bin', 'rb').read() if os.path.exists('/tmp/r105.bin') else None
if _r is None:
    subprocess_ok = os.system('/tmp/yz2 /home/claude/disc/ext1/files/St1/r105.das 0x400 /tmp/r105.bin >/dev/null') == 0
    _r = open('/tmp/r105.bin', 'rb').read()
_o = _arc.get(_r, 'ITM')
_x0, _oi, _ob, _ot = struct.unpack('>4I', _r[_o:_o + 16]); _n = struct.unpack('>I', _r[_o + _oi:_o + _oi + 4])[0]
_ids = [struct.unpack('>H', _r[_o + _oi + 4 + k * 8:_o + _oi + 6 + k * 8])[0] for k in range(_n)]
_k = _ids.index(0x3B)
def _tbl(base, i): return struct.unpack('>I', _r[_o + base + 4 + i * 4:_o + base + 8 + i * 4])[0]
_bin = _r[_o + _ob + _tbl(_ob, _k):_o + _ob + _tbl(_ob, _k + 1)]
_tpl = _r[_o + _ot + _tbl(_ot, _k):_o + _ot + _tbl(_ot, _k + 1)]
_blob = pad32(_bin) + pad32(_tpl)
_nd = open('files/em/em12.drs', 'rb').read(); _nd = pad32(_nd); _km = len(_nd)
open('files/em/em12.drs', 'wb').write(_nd + _blob)
open('c/ch0_key.h', 'w').write('/* mkfiles.py: the key model at the end of em12.drs */\n#define KM_OFS 0x%X\n#define KM_LEN 0x%X\n#define KM_TPL 0x%X\n' % (_km, len(_blob), len(pad32(_bin))))
print('key model at', hex(_km), len(_blob))

# C0-18: the torch. r111's Ganado module (em17) has no torch model (Em17WeaponSet leaves mot[69]/[70] = 0, so the
# list flag 0x04000000 gives nothing). The torch of em11 (archive entries 0x26A BIN / 0x26B TPL, ARC words
# 0x26E/0x26F) is put in em17's two empty slots (inserted before the REL like em12's extra entries) and
# Em17WeaponSet (REL .text 0x43F9C) is changed to fill mot[69]/[70] like em11 does: the game itself then makes the
# torch (em10MakeWeapon 6), puts it in the right hand and lights it (setEffAlways 0x10/0x49, in em17's own EFF).
# The two zero stores of mot[67]/[68] and the four of mot[73..76] go: the work is cleared on create (memClear).
def _ppc_lwz(d, a, o): return 0x80000000 | d << 21 | a << 16 | (o & 0xFFFF)
def _ppc_stw(s, a, o): return 0x90000000 | s << 21 | a << 16 | (o & 0xFFFF)
def _ppc_add(d, a, b): return 0x7C000214 | d << 21 | a << 16 | b << 11
def _arc_parts(d):
    psize, pofs = struct.unpack('>I', d[0x24:0x28])[0], struct.unpack('>I', d[0x2c:0x30])[0]
    p1size, p1ofs = struct.unpack('>I', d[0x44:0x48])[0], struct.unpack('>I', d[0x4c:0x50])[0]
    assert pofs == 0x400 and p1ofs == pofs + psize and p1ofs + p1size <= len(d)
    a = d[pofs:pofs + psize]; n, rel = struct.unpack('>II', a[:8])
    offs = list(struct.unpack('>%dI' % n, a[0x10:0x10 + 4 * n])); tags = [a[0x10 + 4 * n + 4 * j:0x14 + 4 * n + 4 * j] for j in range(n)]
    return psize, pofs, p1ofs, a, n, rel, offs, tags
_d11 = open(SRC + 'em11.drs', 'rb').read(); _, _, _, _a11, _, _, _o11, _t11 = _arc_parts(_d11)
def _ent(a, offs, j): o = offs[j]; return a[o:min([x for x in offs if x > o] + [len(a)])]
assert _t11[0x26A] == b'BIN\0' and _t11[0x26B] == b'TPL\0'
_tb, _tt = pad32(_ent(_a11, _o11, 0x26A)), pad32(_ent(_a11, _o11, 0x26B))
_d17 = open(SRC + 'em17.drs', 'rb').read(); psize, pofs, p1ofs, arc, n, rel, offs, tags = _arc_parts(_d17)
assert tags[0x26A] == b'\0' * 4 and tags[0x26B] == b'\0' * 4
ins = _tb + _tt; delta = len(ins); assert delta % 32 == 0
noffs = [o + delta if o >= rel else o for o in offs]
noffs[0x26A], noffs[0x26B] = rel, rel + len(_tb)
ntags = list(tags); ntags[0x26A] = b'BIN\0'; ntags[0x26B] = b'TPL\0'
head = struct.pack('>4I', n, rel + delta, 0, 0) + struct.pack('>%dI' % n, *noffs) + b''.join(ntags)
relb = bytearray(arc[rel:])
T = 0xB4                                              # .text in the REL file (section 1 offset 0xB5 & ~1)
assert struct.unpack('>I', relb[0x4:0x8])[0] == 0 and struct.unpack('>I', relb[0x4C + 8:0x4C + 12])[0] == 0xB5
def _w(o): return struct.unpack('>I', relb[T + o:T + o + 4])[0]
def _put(o, v): relb[T + o:T + o + 4] = struct.pack('>I', v)
OLD = {0x440a8: _ppc_lwz(0, 11, 2484), 0x440ac: _ppc_stw(10, 9, 316), 0x440b0: _ppc_add(0, 0, 11), 0x440b4: _ppc_stw(10, 9, 320),
       0x440b8: _ppc_stw(0, 9, 312), 0x440bc: _ppc_stw(10, 9, 324), 0x440c0: _ppc_stw(10, 9, 328),
       0x440dc: _ppc_stw(10, 9, 352), 0x440e4: _ppc_stw(10, 9, 340), 0x440ec: _ppc_stw(10, 9, 344), 0x440f0: _ppc_stw(10, 9, 348)}
for o, v in OLD.items(): assert _w(o) == v, hex(o)
NEW = {0x440a8: _ppc_lwz(0, 11, 0x26D * 4), 0x440ac: _ppc_add(0, 0, 11), 0x440b0: _ppc_stw(0, 9, 312),
       0x440b4: _ppc_lwz(12, 11, 0x26E * 4), 0x440b8: _ppc_add(12, 12, 11), 0x440bc: _ppc_stw(12, 9, 324),
       0x440c0: _ppc_lwz(12, 11, 0x26F * 4), 0x440dc: _ppc_add(12, 12, 11), 0x440e4: _ppc_stw(12, 9, 328),
       0x440ec: 0x60000000, 0x440f0: 0x60000000}
for o in range(0x440c4, 0x440dc, 4): assert ((_w(o) >> 21) & 31) != 12 and ((_w(o) >> 16) & 31) != 12   # r12 untouched between
for o, v in NEW.items(): _put(o, v)
narc = head + arc[len(head):rel] + ins + bytes(relb)
assert len(narc) == psize + delta
nd = bytearray(_d17[:pofs] + narc + _d17[p1ofs:])
nd[0x24:0x28] = struct.pack('>I', psize + delta); nd[0x4c:0x50] = struct.pack('>I', p1ofs + delta)
for j in range(n):
    if j in (0x26A, 0x26B): continue
    assert narc[noffs[j]:noffs[j] + 32] == arc[offs[j]:offs[j] + 32], j
assert nd[p1ofs + delta:p1ofs + delta + 64] == _d17[p1ofs:p1ofs + 64]
open('files/em/em17.drs', 'wb').write(nd)
print('em17.drs: torch in, grows', delta)

# C0-18: the island's container (r310, disc 2) for the hiding places: its body (SMD bin 9, its one material
# pointed at texture 0, texture count 1) and its texture (TPL image 8, 512x128 CMPR with 5 mip levels) with the
# image header, after the key at the end of em12.drs. ch0.c puts the body in place of r111's barrel (et1100.bin)
# and points the barrel's texture (et11.eff, EFM 9) at ours.
_r3 = '/tmp/r310.bin'
if not os.path.exists(_r3): os.system('/tmp/yz2 /home/claude/disc/ext2/files/St3/r310.das 0x400 /tmp/r310.bin >/dev/null')
_r = open(_r3, 'rb').read(); _s0 = _arc.get(_r, 'SMD'); _s = _r[_s0:_arc.get(_r, 'SMX')]
def _u(b, o): return struct.unpack('>I', b[o:o + 4])[0]
_bt = _u(_s, 4); _bins = [_bt + _u(_s, _bt + 4 * i) for i in range(_u(_s, _bt) // 4)]
_body = bytearray(_s[_bins[9]:_bins[10]]); assert len(_body) == 3424 and _body[0x28] == 5
_pp = _u(_body, 0x1C); assert _body[_pp + 0x0C] == 8 and _u(_body, 0x24) == 0x36
_body[_pp + 0x0C] = 0; _body[0x24:0x28] = struct.pack('>I', 1)
_tt0 = _u(_s, 8); _tp = _tt0 + _u(_s, _tt0); assert _s[_tp:_tp + 4] == b'\x00\x20\xaf\x30'
_th = _tp + _u(_s, _tp + 0xC + 8 * 8); _hdr = bytearray(_s[_th:_th + 0x24])
assert struct.unpack('>HHI', _hdr[:8]) == (128, 512, 14) and _hdr[0x22] == 5
_img = _s[_tp + _u(_hdr, 8):_tp + _u(_hdr, 8) + 43712]
_hdr[8:12] = b'\0' * 4; _hdr[0x23] = 0
_cb = pad32(bytes(_hdr)) + pad32(bytes(_body)) + _img
assert len(pad32(bytes(_hdr))) == 0x40 and (0x40 + len(pad32(bytes(_body)))) % 32 == 0
_nd = pad32(open('files/em/em12.drs', 'rb').read()); _co = len(_nd)
open('files/em/em12.drs', 'wb').write(_nd + _cb)
open('c/ch0_cont.h', 'w').write('/* mkfiles.py: the container at the end of em12.drs: texture header, body bin, texture */\n'
    '#define CT_OFS 0x%X\n#define CT_LEN 0x%X\n#define CT_BIN 0x40\n#define CT_BIN_LEN 0x%X\n#define CT_TEX 0x%X\n' %
    (_co, len(_cb), len(_body), 0x40 + len(pad32(bytes(_body)))))
print('container at', hex(_co), len(_cb))
