"""ISO del RE1 REmake (H15+): como mkiso_re1.py pero puede AÑADIR archivos nuevos (salas con ids nuevos) y
recoloca el FST. Los archivos de files/ sustituyen a los del disco (misma ruta) o se añaden a su carpeta.
Espacio: el hueco entre 0x1000000 y el primer archivo + el que dejan libre los archivos sustituidos.
uso: python3 mkiso_re1b.py TAG [carpeta_files]
"""
import hashlib, os, shutil, struct, subprocess, sys

TAG = sys.argv[1]
CLEAN = '9e58a28b32cbbddd215f2fcbecb79c41812f5f54'
SRC = '/home/claude/disc/iso/disc1.iso'
XDELTA = os.environ.get('XDELTA', '/home/claude/tools/xdelta3')
here = os.path.dirname(os.path.abspath(__file__))
FILES = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, 'files')
os.makedirs(os.path.join(here, 'out'), exist_ok=True)
dst = os.path.join(here, 'out', f'RE1_PAL_disc1_{TAG}.iso')
FST_NEW = 0x1000000
DISC_END = 0x57058000
AL = 0x8000

with open(SRC, 'rb') as f:
    h = f.read(0x440)
    fst, fsz = struct.unpack('>II', h[0x424:0x42c])
    f.seek(fst); t = bytes(f.read(fsz))
cnt = struct.unpack('>I', t[8:12])[0]; st = cnt * 12
# árbol: lista de nodos (nombre, es_dir, hijos | (off, size))
def leer(i, fin):
    hijos = []
    while i < fin:
        typ = t[i * 12]; no = int.from_bytes(t[i * 12 + 1:i * 12 + 4], 'big')
        nm = t[st + no:t.index(b'\0', st + no)].decode('latin1')
        a, b = struct.unpack('>II', t[i * 12 + 4:i * 12 + 12])
        if typ:
            sub, i = leer(i + 1, b); hijos.append([nm, True, sub])
        else:
            hijos.append([nm, False, [a, b]]); i += 1
    return hijos, i
raiz, _ = leer(1, cnt)
def buscar(path):
    nodo = raiz
    partes = path.split('/')
    for k, p in enumerate(partes):
        hit = [n for n in nodo if n[0].lower() == p.lower()]
        if k < len(partes) - 1:
            if not hit or not hit[0][1]: raise KeyError(path)
            nodo = hit[0][2]
        else:
            return nodo, (hit[0] if hit else None)
first = None
def todos(n, pre=''):
    for nm, d, x in n:
        if d: yield from todos(x, pre + nm + '/')
        else: yield pre + nm, x
first = min(x[0] for _, x in todos(raiz))

sha = hashlib.sha1()
with open(SRC, 'rb') as f:
    for blk in iter(lambda: f.read(1 << 24), b''): sha.update(blk)
assert sha.hexdigest() == CLEAN, 'la ISO de partida no es la limpia'

# archivos nuevos o sustituidos
cambios = []
for root, _, fs in os.walk(FILES):
    for fn in sorted(fs):
        rel = os.path.relpath(os.path.join(root, fn), FILES).replace(os.sep, '/')
        cambios.append((rel, os.path.join(root, fn), os.path.getsize(os.path.join(root, fn))))
libres = []   # (inicio, fin)
nuevos = []
for rel, path, size in cambios:
    dirn, nodo = buscar(rel)
    if nodo is None:
        nodo = [rel.split('/')[-1], False, [0, 0]]; dirn.append(nodo); nuevos.append(rel)
        dirn.sort(key=lambda n: n[0].lower())
    else:
        a, b = nodo[2]
        if b: libres.append([a, a + b])
    nodo[2][1] = size
    nodo.append(path)
# FST nuevo
nombres = bytearray(); ents = []
def emitir(n, padre):
    for nd in n:
        no = len(nombres); nombres.extend(nd[0].encode('latin1') + b'\0')
        if nd[1]:
            k = len(ents); ents.append([1, no, padre, 0]); emitir(nd[2], k); ents[k][3] = len(ents)
        else:
            ents.append([0, no, nd, None])
ents.append([1, 0, 0, 0])
emitir(raiz, 0); ents[0][3] = len(ents)
fst_size = len(ents) * 12 + len(nombres)
libres.append([(FST_NEW + fst_size + AL - 1) // AL * AL, first])
# fusionar huecos y asignar (los más grandes primero, mejor ajuste)
libres.sort(); fus = []
for a, b in libres:
    if fus and a <= fus[-1][1]: fus[-1][1] = max(fus[-1][1], b)
    else: fus.append([a, b])
libres = fus
porcolocar = sorted([c for c in cambios], key=lambda c: -c[2])
pos = {}
for rel, path, size in porcolocar:
    need = (size + 0x1F) & ~0x1F
    for h in libres: h[0] = (h[0] + 0x1F) & ~0x1F
    cand = [h for h in libres if h[1] - h[0] >= need]
    if not cand: raise SystemExit(f'no cabe {rel} ({size} bytes); huecos libres {sum(b - a for a, b in libres) / 1e6:.1f} MB')
    h_ = min(cand, key=lambda h: h[1] - h[0])
    pos[rel] = h_[0]; h_[0] += need
print(f'{len(cambios)} archivos ({len(nuevos)} nuevos); libre tras colocar: {sum(b - a for a, b in libres) / 1e6:.1f} MB')

shutil.copyfile(SRC, dst)
tb = bytearray(fst_size)
for k, e in enumerate(ents):
    if e[0]:
        tb[k * 12] = 1; tb[k * 12 + 1:k * 12 + 4] = e[1].to_bytes(3, 'big'); struct.pack_into('>II', tb, k * 12 + 4, e[2], e[3])
    else:
        nd = e[2]; tb[k * 12 + 1:k * 12 + 4] = e[1].to_bytes(3, 'big')
        off = nd[2][0]
        if len(nd) > 3:
            rel = [c[0] for c in cambios if c[1] == nd[3]][0]; off = pos[rel]
        struct.pack_into('>II', tb, k * 12 + 4, off, nd[2][1])
tb[len(ents) * 12:] = nombres
with open(dst, 'r+b') as f:
    for rel, path, size in cambios:
        f.seek(pos[rel]); f.write(open(path, 'rb').read())
    f.seek(FST_NEW); f.write(tb)
    f.seek(0x424); f.write(struct.pack('>III', FST_NEW, fst_size, fst_size))
    f.seek(0, 2); assert f.tell() == DISC_END
print('FST en', hex(FST_NEW), fst_size, 'bytes,', len(ents), 'entradas')
pat = os.path.join(here, 'out', f'RE1_PAL_disc1_{TAG}.xdelta')
if os.path.exists(pat): os.remove(pat)
subprocess.check_call([XDELTA, '-e', '-9', '-S', 'djw', '-s', SRC, dst, pat])
print('parche', pat, os.path.getsize(pat), 'bytes')
