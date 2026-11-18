"""Huesos de un MDL0 (nombre, escala, giro en grados, traslación, matriz de mundo 3x4)."""
import struct, sys
import numpy as np
sys.path.insert(0, '/home/claude/tools')
import brres

def bones(d, mo):
    mag, size, ver, outer = struct.unpack('>4sIIi', d[mo:mo + 16])
    nsec = {8: 11, 9: 11, 10: 14, 11: 14}[ver]
    secs = struct.unpack(f'>{nsec}i', d[mo + 16:mo + 16 + 4 * nsec])
    out = []
    for name, bo in brres.group(d, mo + secs[1]):
        sc = struct.unpack('>3f', d[bo + 0x20:bo + 0x2C]); rot = struct.unpack('>3f', d[bo + 0x2C:bo + 0x38])
        tr = struct.unpack('>3f', d[bo + 0x38:bo + 0x44])
        parent = struct.unpack('>i', d[bo + 0x5C:bo + 0x60])[0]
        M = np.array(struct.unpack('>12f', d[bo + 0x70:bo + 0xA0])).reshape(3, 4)
        out.append(dict(name=name, scale=sc, rot=rot, trans=tr, parent=parent, mtx=M))
    return out

if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    for mname, mo in brres.tree(d).get('3DModels(NW4R)', []):
        if len(sys.argv) > 2 and mname != sys.argv[2]: continue
        bs = bones(d, mo)
        print(mname, len(bs), 'huesos')
        for b in bs[:60]:
            print('  %-28s t=%s r=%s s=%s' % (b['name'], np.round(b['trans'], 2), np.round(b['rot'], 1), np.round(b['scale'], 2)))
