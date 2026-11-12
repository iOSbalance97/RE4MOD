import struct,sys
def parse(path):
    d=open(path,'rb').read()
    nsec,secoff=struct.unpack('>II',d[0x0C:0x14])
    relo,impo,imps=struct.unpack('>III',d[0x24:0x30])
    secs=[]
    for i in range(nsec):
        o,s=struct.unpack('>II',d[secoff+i*8:secoff+i*8+8]); secs.append((o&~1,s,o&1))
    calls=[]
    for k in range(imps//8):
        mid,ro=struct.unpack('>II',d[impo+k*8:impo+k*8+8])
        p=ro; sec=None; off=0
        while True:
            o,t,s,a=struct.unpack('>HBBI',d[p:p+8]); p+=8
            if t==203: break
            off+=o
            if t==202: sec=s; off=0; continue
            if t==201: continue
            if mid==0: calls.append((sec,off,t,a))
    return d,secs,calls
if __name__=='__main__':
    d,secs,calls=parse(sys.argv[1])
    want=int(sys.argv[2],0) if len(sys.argv)>2 else None
    for sec,off,t,a in calls:
        if t!=10: continue
        so=secs[sec][0]
        prev=[struct.unpack('>I',d[so+off-4*j:so+off-4*j+4])[0] for j in range(1,7)]
        lis=[w for w in prev if (w>>16)==0x3860]  # li r3,imm
        if want is None or any((w&0xffff)==want for w in prev[:4] if (w>>16)==0x3860):
            print(sys.argv[1].split('/')[-1],sec,hex(off),hex(a),[hex(w) for w in prev[:4]])
