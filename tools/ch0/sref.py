import struct,sys
dol=open('/home/claude/disc/ext1/sys/main.dol','rb').read()
offs=struct.unpack('>18I',dol[0:72]); addr=struct.unpack('>18I',dol[0x48:0x90]); sz=struct.unpack('>18I',dol[0x90:0xD8])
segs=[(addr[i],offs[i],sz[i]) for i in range(18) if sz[i]]
def a2o(a):
    for b,o,s in segs:
        if b<=a<b+s: return o+a-b
def o2a(x):
    for b,o,s in segs:
        if o<=x<o+s: return b+x-o
def rd(a): return struct.unpack('>I',dol[a2o(a):a2o(a)+4])[0]
def strs(t):
    i=0;out=[]
    while True:
        i=dol.find(t,i)
        if i<0: return out
        out.append(o2a(i)); i+=1
def refs(target):
    hi=(target+0x8000)>>16; lo=target&0xFFFF; out=[]
    b,o,s=segs[0]
    for a in range(b,b+s,4):
        w=rd(a)
        if (w>>26)==15 and (w&0xFFFF)==hi:  # lis
            r=(w>>21)&31
            for k in range(1,12):
                w2=rd(a+4*k)
                if (w2>>26) in (14,24) and ((w2>>16)&31)==r and (w2&0xFFFF)==lo: out.append(a+4*k)
    return out
def fstart(a):
    while True:
        w=rd(a)
        if (w>>16)==0x9421: return a
        a-=4
for t in sys.argv[1:]:
    for s in strs(t.encode()):
        for r in refs(s): print(t,hex(s),hex(r),'func',hex(fstart(r)))
