"""Mini desensamblador PowerPC (lo habitual en código de CodeWarrior) para leer el dol PAL.
uso: ppcdis.py main.dol dirección [antes] [después]"""
import struct, sys
def load(path):
    d = open(path, 'rb').read(); h = d[:0x100]
    offs = struct.unpack('>18I', h[0:72]); addr = struct.unpack('>18I', h[72:144]); size = struct.unpack('>18I', h[144:216])
    return d, [(o, a, s) for o, a, s in zip(offs, addr, size) if s]
def word(d, secs, a):
    for o, b, s in secs:
        if b <= a < b + s: return struct.unpack('>I', d[o + a - b:o + a - b + 4])[0]
    return None
def sx(v, b): return v - (1 << b) if v & (1 << (b - 1)) else v
def dis(w, pc):
    op = w >> 26; rd = (w >> 21) & 31; ra = (w >> 16) & 31; rb = (w >> 11) & 31; imm = sx(w & 0xFFFF, 16); uimm = w & 0xFFFF
    D = {32: 'lwz', 33: 'lwzu', 34: 'lbz', 35: 'lbzu', 36: 'stw', 37: 'stwu', 38: 'stb', 39: 'stbu', 40: 'lhz', 41: 'lhzu',
         42: 'lha', 43: 'lhau', 44: 'sth', 45: 'sthu', 46: 'lmw', 47: 'stmw', 48: 'lfs', 49: 'lfsu', 50: 'lfd', 51: 'lfdu',
         52: 'stfs', 53: 'stfsu', 54: 'stfd', 55: 'stfdu'}
    if op in D:
        r = f'f{rd}' if op >= 48 else f'r{rd}'
        return f'{D[op]} {r}, {imm:#x}(r{ra})'
    if op == 14: return f'li r{rd}, {imm:#x}' if ra == 0 else f'addi r{rd}, r{ra}, {imm:#x}'
    if op == 15: return f'lis r{rd}, {uimm:#x}' if ra == 0 else f'addis r{rd}, r{ra}, {uimm:#x}'
    if op == 24: return f'ori r{ra}, r{rd}, {uimm:#x}' if w != 0x60000000 else 'nop'
    if op == 25: return f'oris r{ra}, r{rd}, {uimm:#x}'
    if op == 28: return f'andi. r{ra}, r{rd}, {uimm:#x}'
    if op == 11: return f'cmpwi cr{rd >> 2}, r{ra}, {imm:#x}'
    if op == 10: return f'cmplwi cr{rd >> 2}, r{ra}, {uimm:#x}'
    if op == 7: return f'mulli r{rd}, r{ra}, {imm:#x}'
    if op == 8: return f'subfic r{rd}, r{ra}, {imm:#x}'
    if op == 12: return f'addic r{rd}, r{ra}, {imm:#x}'
    if op == 18:
        li = sx(w & 0x3FFFFFC, 26); t = (pc + li) & 0xFFFFFFFF if not w & 2 else li
        return ('bl' if w & 1 else 'b') + f' {t:#010x}'
    if op == 16:
        bd = sx(w & 0xFFFC, 16); t = (pc + bd) & 0xFFFFFFFF
        cond = {(12, 0): 'blt', (4, 0): 'bge', (12, 1): 'bgt', (4, 1): 'ble', (12, 2): 'beq', (4, 2): 'bne'}.get((rd, ra & 3), f'bc {rd},{ra}')
        return f'{cond}{"l" if w & 1 else ""} cr{ra >> 2}, {t:#010x}'
    if op == 21:
        sh, mb, me = rb, (w >> 6) & 31, (w >> 1) & 31
        return f'rlwinm r{ra}, r{rd}, {sh}, {mb}, {me}'
    if op == 19:
        xo = (w >> 1) & 1023
        return {16: 'blr' if rd == 20 else f'bclr {rd}', 528: 'bctr' if not w & 1 else 'bctrl'}.get(xo, f'op19 xo{xo}')
    if op == 31:
        xo = (w >> 1) & 1023
        X = {266: 'add', 40: 'subf', 23: 'lwzx', 151: 'stwx', 87: 'lbzx', 215: 'stbx', 279: 'lhzx', 444: 'or', 28: 'and',
             0: 'cmpw', 32: 'cmplw', 339: 'mfspr', 467: 'mtspr', 235: 'mullw', 24: 'slw', 536: 'srw', 824: 'srawi', 922: 'extsh', 954: 'extsb', 104: 'neg', 459: 'divwu', 491: 'divw', 535: 'lfsx'}
        n = X.get(xo, f'op31 xo{xo}')
        if xo == 444 and rd == rb: return f'mr r{ra}, r{rd}'
        if xo in (0, 32): return f'{n} cr{rd >> 2}, r{ra}, r{rb}'
        if xo == 339: return f'mfspr r{rd}, {((rb << 5) | ra)}'
        if xo == 467: return f'mtspr {((rb << 5) | ra)}, r{rd}'
        return f'{n} r{rd}, r{ra}, r{rb}'
    if op == 59 or op == 63: return f'fp{op} xo{(w >> 1) & 31}'
    return f'.word {w:#010x}'
if __name__ == '__main__':
    d, secs = load(sys.argv[1]); a = int(sys.argv[2], 16)
    b = int(sys.argv[3]) if len(sys.argv) > 3 else 20; f = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    for pc in range(a - 4 * b, a + 4 * f, 4):
        w = word(d, secs, pc)
        print(f'{"=>" if pc == a else "  "} {pc:08x}: {w:08x}  {dis(w, pc)}')
