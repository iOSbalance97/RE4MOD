# Builds mod/files/ (data files replaced in the ISO by mkiso.py) from the clean extracted disc:
# El Herrero (mod/data/herrero.bin + two CMPR textures, made by models/herrero/lowpoly/game.py) written
# in place over the Ganado body model 34 bones / 770 vertices and textures 1-2 of the TPL that follows it.
import sys, glob, os
sys.path.insert(0, '../models/tools'); import tpl
SRC = '/home/claude/disc/ext1/files/em/'; N = 32352
d0 = open(SRC + 'em10.drs', 'rb').read(); donor = d0[0x3ab040:0x3ab040 + N]
blob = open('data/herrero.bin', 'rb').read(); assert len(blob) <= N; blob += b'\0' * (N - len(blob))
tx = [open('data/herrero_tex%d.cmpr' % i, 'rb').read() for i in (0, 1)]
os.makedirs('files/em', exist_ok=True)
for f in sorted(glob.glob(SRC + 'em1*.drs')):
    d = bytearray(open(f, 'rb').read()); i = d.find(donor)
    if i < 0: continue
    ims = tpl.tpl_images(bytes(d), i + N); assert [(w, h, fm) for w, h, fm, _, _ in ims] == [(256, 256, 14)] * 3
    d[i:i + N] = blob
    for k in (1, 2): d[ims[k][3]:ims[k][3] + 32768] = tx[k - 1]
    open('files/em/' + os.path.basename(f), 'wb').write(d); print(os.path.basename(f), hex(i))
