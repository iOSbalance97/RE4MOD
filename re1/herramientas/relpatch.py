"""Salas de la etapa 1 de RE4: las Init/Main de cada sala se registran en setTbl() (en uno de los st1_N.rel; los
cuatro módulos se cargan juntos y se referencian entre sí). Cada registro es
    lis r5,Main@ha ; lis r4,Init@ha ; addi r5,Main@l ; addi r4,Init@l ; li r3,N ; bl set
con reubicaciones ADDR16_HA/LO contra el módulo donde está el código de la sala. Para quitar los scripts de una
sala se cambia el addend de esas reubicaciones a una función vacía (blr) del MISMO módulo destino.
uso: relpatch.py dir_rels [dir_salida salas_hex,...]"""
import glob, os, struct, sys

def parse(d):
    h = struct.unpack('>IIIIIIIIIIIIBBBBIII', d[:0x40])
    mid, nsec, secoff, impoff, impsize = h[0], h[3], h[4], h[10], h[11]
    secs = [struct.unpack('>II', d[secoff + 8 * i:secoff + 8 * i + 8]) for i in range(nsec)]
    secs = [(o & ~1, sz) for o, sz in secs]
    imps = [struct.unpack('>II', d[impoff + 8 * i:impoff + 8 * i + 8]) for i in range(impsize // 8)]
    relocs = []
    for m, ro in imps:
        p = ro; cur = None; off = 0
        while True:
            delta, typ, sec, add = struct.unpack('>HBBI', d[p:p + 8])
            if typ == 203: break
            if typ == 202: cur = sec; off = 0
            else:
                off += delta
                if typ != 201: relocs.append(dict(pos=p, mod=m, sec=cur, off=off, typ=typ, tsec=sec, add=add))
            p += 8
    return mid, secs, relocs

def load(dirn):
    mods = {}
    for f in sorted(glob.glob(f'{dirn}/' + os.environ.get('RELPREF', 'st1') + '_*.rel')):
        d = bytearray(open(f, 'rb').read()); mid, secs, rel = parse(d)
        mods[mid] = dict(file=f, d=d, secs=secs, rel=rel)
    return mods

def tabla(mods):
    out = {}
    for mid, M in mods.items():
        d, secs = M['d'], M['secs']; to = secs[1][0]
        rs = [r for r in M['rel'] if r['sec'] == 1 and r['typ'] in (4, 6) and r['tsec'] == 1]
        by_ins = {}
        for r in rs: by_ins.setdefault(r['off'] & ~3, []).append(r)
        for ins_off in sorted(by_ins):
            # bloque de 4 instrucciones con reubicación seguido de li r3,N
            blk = [by_ins.get(ins_off + 4 * k) for k in range(4)]
            if any(b is None for b in blk): continue
            nxt = struct.unpack('>I', d[to + ins_off + 16:to + ins_off + 20])[0]
            if nxt >> 16 != 0x3860: continue
            n = nxt & 0xFFFF
            regs = {}
            for k in range(4):
                w = struct.unpack('>I', d[to + ins_off + 4 * k:to + ins_off + 4 * k + 4])[0]
                regs.setdefault((w >> 21) & 31, []).append(blk[k][0])
            if set(regs) != {4, 5}: continue
            init = regs[4]; main = regs[5]
            if init[0]['add'] != init[1]['add'] or main[0]['add'] != main[1]['add']: continue
            out.setdefault(n, []).append(dict(tabla_en=mid, mod_init=init[0]['mod'], init=init[0]['add'], mod_main=main[0]['mod'], main=main[0]['add'],
                          relocs=init + main))
    return out

def codigo(mods, mid, off):
    M = mods[mid]; to = M['secs'][1][0]
    return bytes(M['d'][to + off:to + off + 4])

if __name__ == '__main__':
    mods = load(sys.argv[1]); t = tabla(mods)
    print('salas registradas:', ' '.join(f'r1{n:02x}({len(vs)}x, código en {vs[0]["mod_init"]})' for n, vs in sorted(t.items())))
    vacias = {}
    for n, vs in t.items():
      for v in vs:
        for m, a in ((v['mod_init'], v['init']), (v['mod_main'], v['main'])):
            if codigo(mods, m, a) == b'\x4e\x80\x00\x20': vacias.setdefault(m, a)
    print('función vacía por módulo:', {m: hex(a) for m, a in vacias.items()})
    if len(sys.argv) > 3:
        quitar = [int(x, 16) & 0xFF for x in sys.argv[3].split(',')]
        hechas = []
        for n in quitar:
            if n not in t: print('  r1%02x no está en la tabla' % n); continue
            for v in t[n]:
                for r in v['relocs']:
                    assert r['mod'] in vacias, f'sin función vacía en el módulo {r["mod"]}'
                    struct.pack_into('>I', mods[v['tabla_en']]['d'], r['pos'] + 4, vacias[r['mod']])
            hechas.append('r1%02x' % n)
        os.makedirs(sys.argv[2], exist_ok=True)
        for mid, M in mods.items():
            open(os.path.join(sys.argv[2], os.path.basename(M['file'])), 'wb').write(M['d'])
        # comprobar releyendo
        t2 = tabla(load(sys.argv[2]))
        for n in quitar:
            for v in t2.get(n, []):
                assert codigo(mods, v['mod_init'], v['init']) == b'\x4e\x80\x00\x20'
                assert codigo(mods, v['mod_main'], v['main']) == b'\x4e\x80\x00\x20'
        print('vaciadas:', hechas)
