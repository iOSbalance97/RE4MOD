import re
L=[l.strip() for l in open('/home/claude/work/yz2.s') if l.strip() and l.strip()!='asm_regs.h']
L=L[:L.index('.rodata')]
funcs={}; cur=None; order=[]
for l in L:
    if l.endswith(':') and not l.startswith('.L'):
        cur=l[:-1]; funcs[cur]=[]; order.append(cur); continue
    funcs[cur].append(l)
# yz2Decode_* pieces are one function (fallthrough), FrequencyDecode_* are separate
main=[n for n in order if n.startswith('yz2Decode')]
fd=[n for n in order if n.startswith('Frequency')]
def R(x): 
    x=x.strip()
    if re.fullmatch(r'r\d+',x): return x
    return None
def imm(x):
    x=x.strip(); return str(int(x,0))
def mem(x):
    m=re.fullmatch(r'(-?0x[0-9a-f]+|-?\d+)\((r\d+)\)',x.strip()); return '(%s+(u32)(%d))'%(m.group(2),int(m.group(1),0))
def tr(l):
    if l.endswith(':'): return l[:-1].replace('.','_')+':;'
    op,_,a=l.partition(' '); a=[x.strip() for x in a.split(',')] if a else []
    t=lambda s: s
    if op=='li': return f'{a[0]}=(u32)(s16)({imm(a[1])});'
    if op=='lis' and '@' in a[1]: return '/*'+l+'*/'
    if op=='lis': return f'{a[0]}=(u32)({imm(a[1])})<<16;'
    if op=='mr': return f'{a[0]}={a[1]};'
    if op=='addi': return f'{a[0]}={a[1]}+(u32)({imm(a[2])});'
    if op=='subi': return f'{a[0]}={a[1]}-(u32)({imm(a[2])});'
    if op=='add': return f'{a[0]}={a[1]}+{a[2]};'
    if op=='subf': return f'{a[0]}={a[2]}-{a[1]};'
    if op=='subfic': return f'{a[0]}=(u32)({imm(a[2])})-{a[1]};'
    if op=='or': return f'{a[0]}={a[1]}|{a[2]};'
    if op=='slwi': return f'{a[0]}={a[1]}<<{imm(a[2])};'
    if op=='srwi': return f'{a[0]}={a[1]}>>{imm(a[2])};'
    if op=='slw': return f'{a[0]}=({a[2]}&32)?0:({a[1]}<<({a[2]}&31));'
    if op=='clrlwi': return f'{a[0]}={a[1]}&(0xFFFFFFFFu>>{imm(a[2])});'
    if op=='mullw': return f'{a[0]}=(u32)((s32){a[1]}*(s32){a[2]});'
    if op=='divwu': return f'{a[0]}={a[2]}?{a[1]}/{a[2]}:0;'
    if op=='lwz': return f'{a[0]}=LW({mem(a[1])});'
    if op=='lhz': return f'{a[0]}=LH({mem(a[1])});'
    if op=='lbz': return f'{a[0]}=LB({mem(a[1])});'
    if op=='stw': return f'SW({mem(a[1])},{a[0]});'
    if op=='sth': return f'SH({mem(a[1])},{a[0]});'
    if op=='stb': return f'SB({mem(a[1])},{a[0]});'
    if op=='lwzx': return f'{a[0]}=LW({a[1]}+{a[2]});'
    if op=='lhzx': return f'{a[0]}=LH({a[1]}+{a[2]});'
    if op=='lbzx': return f'{a[0]}=LB({a[1]}+{a[2]});'
    if op=='stwx': return f'SW({a[1]}+{a[2]},{a[0]});'
    if op=='sthx': return f'SH({a[1]}+{a[2]},{a[0]});'
    if op=='stbx': return f'SB({a[1]}+{a[2]},{a[0]});'
    if op=='cmpw': return f'cr=CMP((s32){a[0]},(s32){a[1]});'
    if op=='cmplw': return f'cr=CMP({a[0]},{a[1]});'
    if op=='cmpwi': return f'cr=CMP((s32){a[0]},(s32)({imm(a[1])}));'
    if op=='cmplwi': return f'cr=CMP({a[0]},(u32)({imm(a[1])}));'
    if op=='fcmpu': return f'cr=CMP({a[1]},{a[2]});'
    if op=='fmr': return f'{a[0]}={a[1]};'
    if op=='mtctr': return f'ctr={a[0]};'
    if op=='bdnz': return f'if(--ctr) goto {a[0].replace(".","_")};'
    br={'b':'1','bge':'cr>=0','ble':'cr<=0','bgt':'cr>0','blt':'cr<0','bne':'cr!=0','beq':'cr==0'}
    if op in br: return f'if({br[op]}) goto {a[0].replace(".","_")};'
    if op=='bl': return f'{a[0]}();'
    if op=='blr': return 'return;'
    if op=='lfs':
        return f'{a[0]}={"1.0" if "one" in a[1] else "0.0"};'
    if op in ('stwu','mflr','stmw','mtlr','lmw'): return '/*'+l+'*/'
    raise Exception(l)
out=['#include "rt.h"']
for n in fd:
    out.append(f'static void {n}(void);')
for n in fd:
    out.append(f'static void {n}(void){{')
    out+= [tr(l) for l in funcs[n]]
    out.append('}')
out.append('void yz2Decode_Decode(void){')
for n in main:
    out.append(n+':;')
    for l in funcs[n]:
        s=tr(l)
        if s=='return;' : s='return;'
        out.append(s)
out.append('}')
src='\n'.join(out)
src=re.sub(r'goto (yz2Decode_\w+)',r'goto \1',src)
open('dec.c','w').write(src)
