import sys, struct
sys.path.insert(0,'/home/claude/re4mod/anim/tools')
from arc import load_arc, entry, arc_entries, drs_parts
def model(path, i=0):
    return entry(load_arc(path), i)
if __name__ == '__main__':
    m = model(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    print('size', len(m))
    for o in range(0, 0x60, 4): print('%02x: %08x' % (o, struct.unpack('>I', m[o:o+4])[0]), end='   ' if (o//4) % 4 != 3 else '\n')
