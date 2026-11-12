# Finds PAL addresses of NTSC decomp functions by matching runs of function sizes.
import struct,re,sys,bisect
dol=open('/home/claude/disc/ext1/sys/main.dol','rb').read()
offs=struct.unpack('>18I',dol[0:72]); addr=struct.unpack('>18I',dol[0x48:0x90]); sz=struct.unpack('>18I',dol[0x90:0xD8])
mem={}
segs=[(addr[i],offs[i],sz[i]) for i in range(7) if sz[i]]
def rd(a):
    for b,o,s in segs:
        if b<=a<b+s: return struct.unpack('>I',dol[o+a-b:o+a-b+4])[0]
    return None
syms=[]
for l in open('/home/claude/decomp/config/GCLE08/symbols.txt' if False else [p for p in __import__('glob').glob('/home/claude/decomp/config/*/symbols.txt')][0]):
    m=re.match(r'(\S+) = \.text:0x([0-9A-F]+); // type:function size:0x([0-9A-F]+)',l)
    if m: syms.append((int(m.group(2),16),int(m.group(3),16),m.group(1)))
syms.sort()
def isstart(a):
    w=rd(a); p=rd(a-4)
    if w is None: return 0
    s=0
    if (w>>16)==0x9421 or w==0x7C0802A6: s+=1
    if p==0x4E800020 or p==0 : s+=1
    return s
def find(name,win=12):
    i=[k for k,s in enumerate(syms) if s[2]==name or s[2].startswith(name)][0]
    lo=max(0,i-win); hi=min(len(syms),i+win)
    run=syms[lo:hi]
    rel=[s[0]-run[0][0] for s in run]
    best=[]
    for b,o,s in segs[:2]:
        for A in range(b,b+s,4):
            sc=0
            for r in rel:
                sc+=isstart(A+r)
            best.append((sc,A))
    best.sort(reverse=True)
    out=[]
    for sc,A in best[:3]:
        out.append((sc,hex(A+syms[i][0]-run[0][0])))
    return syms[i],2*len(rel),out
for n in sys.argv[1:]:
    print(n,find(n))
