"""ISO de prueba del remake de RE1: copia la ISO PAL limpia (disco 1), sustituye los archivos de
re1/files/ (misma ruta que en el disco) y genera el parche xdelta.
Si un archivo crece, se coloca en el hueco libre que hay entre el FST y el primer archivo del disco
(desde 0x1000000, lejos de donde el mod de RE4 mueve el main.dol) y se actualiza su entrada del FST.
uso: python3 mkiso_re1.py TAG
"""
import hashlib, os, shutil, struct, subprocess, sys

TAG = sys.argv[1]
CLEAN = '9e58a28b32cbbddd215f2fcbecb79c41812f5f54'
SRC = '/home/claude/disc/iso/disc1.iso'
GAP_START = 0x1000000
XDELTA = os.environ.get('XDELTA', '/home/claude/tools/xdelta3')
here = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(here, 'out'), exist_ok=True)
dst = os.path.join(here, 'out', f'RE1_PAL_disc1_{TAG}.iso')

with open(SRC, 'rb') as f:
    h = f.read(0x440)
    fst, fsz = struct.unpack('>II', h[0x424:0x42c])
    f.seek(fst); t = bytearray(f.read(fsz))
cnt = struct.unpack('>I', t[8:12])[0]
st = cnt * 12
first = min(struct.unpack('>I', t[i * 12 + 4:i * 12 + 8])[0] for i in range(1, cnt) if not t[i * 12])
ents = {}; stack = [(cnt, '')]; i = 1
while i < cnt:
    while stack and i >= stack[-1][0]: stack.pop()
    typ = t[i * 12]; no = int.from_bytes(t[i * 12 + 1:i * 12 + 4], 'big')
    nm = t[st + no:t.index(b'\0', st + no)].decode('latin1'); base = stack[-1][1] if stack else ''
    if typ: stack.append((struct.unpack('>I', t[i * 12 + 8:i * 12 + 12])[0], base + nm + '/'))
    else: ents[(base + nm).lower()] = i
    i += 1

sha = hashlib.sha1()
with open(SRC, 'rb') as f:
    for blk in iter(lambda: f.read(1 << 24), b''): sha.update(blk)
assert sha.hexdigest() == CLEAN, 'la ISO de partida no es la limpia'
shutil.copyfile(SRC, dst)
bump = GAP_START
with open(dst, 'r+b') as f:
    files_dir = os.path.join(here, 'files')
    for root, _, fs in os.walk(files_dir):
        for fn in sorted(fs):
            rel = os.path.relpath(os.path.join(root, fn), files_dir).replace(os.sep, '/')
            new = open(os.path.join(root, fn), 'rb').read()
            e = ents[rel.lower()]
            off, size = struct.unpack('>II', t[e * 12 + 4:e * 12 + 12])
            if len(new) > size:
                off = bump; bump = (off + len(new) + 0x7FFF) & ~0x7FFF
                assert bump <= first, 'no cabe en el hueco'
            t[e * 12 + 4:e * 12 + 12] = struct.pack('>II', off, len(new))
            f.seek(off); f.write(new)
            print(rel, 'en', hex(off), f'{len(new)} bytes ({len(new) - size:+d})')
    f.seek(fst); f.write(t)
pat = os.path.join(here, 'out', f'RE1_PAL_disc1_{TAG}.xdelta')
if os.path.exists(pat): os.remove(pat)
subprocess.check_call([XDELTA, '-e', '-9', '-S', 'djw', '-s', SRC, dst, pat])
print('parche', pat, os.path.getsize(pat), 'bytes')
sha = hashlib.sha1()
with open(dst, 'rb') as f:
    for blk in iter(lambda: f.read(1 << 24), b''): sha.update(blk)
print('sha1 ISO parcheada', sha.hexdigest())
