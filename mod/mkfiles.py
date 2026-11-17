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

# C0-20: the grab. em17's br_Catch sends a grab of the playable Ashley (pl_type 1) to the strangle hold, R1 0x36
# (stw of 0x01360000 into r_no at REL .text 0x1D670), whose prompt reads a garbage text pointer (hang at
# 0x8012DA30). It goes to R1 0x66 (R300TakeAshley: a plain MotionMove) instead; ch0.c sees it and plays the carry.
_d17 = bytearray(open(SRC + 'em17.drs', 'rb').read())
_rel17 = 0x400 + struct.unpack('>I', _d17[0x404:0x408])[0]
_o = _rel17 + 0xB4 + 0x1D670
assert _d17[_o:_o + 8] == bytes.fromhex('3c000136901f00fc') and _d17[_o - 0x14:_o - 0x10] == bytes.fromhex('880b4fc4')
_d17[_o:_o + 4] = bytes.fromhex('3c000166')
open('files/em/em17.drs', 'wb').write(_d17)
print('em17.drs: catch of Ashley -> R1 0x66')
# C0-19: no change to em17 any more. C0-18 put em11's weapon in mot[69]/[70] for Wep 6: that is the scythe (the
# zealots' weapon), its motions (0x13A/0x140/0x144) are empty in em17 (odd voices, no run). The village torch is
# Wep 7 (list flag 0x800, mot[71]/[72] = ARC 0x270/0x271, already in em17; fire = setEffAlways 0x10/0x14).
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
_hd = open('data/ch0_hide.bin', 'rb').read()      # anim/tools/mkhide.py: hiding and carried-off clips
_cb = pad32(bytes(_hdr)) + pad32(bytes(_body)) + pad32(_img) + pad32(_hd)
assert len(pad32(bytes(_hdr))) == 0x40 and (0x40 + len(pad32(bytes(_body)))) % 32 == 0
_nd = pad32(open('files/em/em12.drs', 'rb').read()); _co = len(_nd)
open('files/em/em12.drs', 'wb').write(_nd + _cb)
open('c/ch0_cont.h', 'w').write('/* mkfiles.py: the container at the end of em12.drs: texture header, body bin, texture */\n'
    '#define CT_OFS 0x%X\n#define CT_LEN 0x%X\n#define CT_BIN 0x40\n#define CT_BIN_LEN 0x%X\n#define CT_TEX 0x%X\n#define CT_HD 0x%X\n' %
    (_co, len(_cb), len(_body), 0x40 + len(pad32(bytes(_body))), 0x40 + len(pad32(bytes(_body))) + len(pad32(_img))))
print('container at', hex(_co), len(_cb))
