# Minimal FBX binary reader: nodes as (name, props, children)
import struct, zlib, sys
def read(path):
    d=open(path,'rb').read(); ver=struct.unpack('<I',d[23:27])[0]
    big=ver>=7500; hdr='<QQQ' if big else '<III'; hs=struct.calcsize(hdr)
    def prop(p):
        t=chr(d[p]); p+=1
        sc={'Y':'<h','C':'<B','I':'<i','F':'<f','D':'<d','L':'<q'}
        if t in sc:
            f=sc[t]; return struct.unpack(f,d[p:p+struct.calcsize(f)])[0], p+struct.calcsize(f)
        if t in 'SR':
            n=struct.unpack('<I',d[p:p+4])[0]; v=d[p+4:p+4+n]; return (v.decode('utf8','replace') if t=='S' else v), p+4+n
        al,enc,cl=struct.unpack('<III',d[p:p+12]); raw=d[p+12:p+12+cl]
        if enc: raw=zlib.decompress(raw)
        f={'f':'f','d':'d','l':'q','i':'i','b':'B'}[t]
        return list(struct.unpack('<%d%s'%(al,f),raw)), p+12+cl
    def node(p):
        end,np_,pl=struct.unpack(hdr,d[p:p+hs]); p+=hs
        if end==0: return None,p
        nl=d[p]; name=d[p+1:p+1+nl].decode(); p+=1+nl
        props=[]
        for _ in range(np_):
            v,p=prop(p); props.append(v)
        ch=[]
        while p<end:
            c,p=node(p)
            if c is None: break
            ch.append(c)
        return (name,props,ch),end
    p=27; top=[]
    while p<len(d)-hs:
        n,p=node(p)
        if n is None: break
        top.append(n)
    return top
def find(nodes,name):
    for n in nodes:
        if n[0]==name: yield n
def child(n,name):
    for c in n[2]:
        if c[0]==name: return c
