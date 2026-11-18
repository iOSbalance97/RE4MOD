"""Lector de .msh de The Movies (props estaticos, formato 0x30)."""
import struct, numpy as np
def _probe(d,base,ntex,nmat):
    o=base+32*ntex+24*nmat+4+48
    return struct.unpack_from('<I',d,o+12)[0]==0x30 and d[base:base+32].split(b'\0')[0].endswith(b'.dds')
def load(path):
    d=open(path,'rb').read()
    ver,ntex,nmat,_,flag=struct.unpack_from('<5I',d,0)
    for base in (24,36,28,32,40,20):
        try:
            if _probe(d,base,ntex,nmat): break
        except Exception: pass
    else: raise ValueError('cabecera desconocida '+path)
    texs=[d[base+32*i:base+32*i+32].split(b'\0')[0].decode('latin1') for i in range(ntex)]
    o=base+32*ntex
    mats=[]
    for i in range(nmat):
        r=d[o+24*i:o+24*i+24]; mats.append(dict(tex=r[0] if r[0]!=0xff else None, raw=r))
    o+=24*nmat
    nsub=struct.unpack_from('<I',d,o)[0]; o+=4
    M=np.array(struct.unpack_from('<12f',d,o)).reshape(4,3); o+=48
    subs=[]
    for i in range(nsub):
        mi,nt,nv,fmt,hsh,e,f=struct.unpack_from('<IIIIIiI',d,o)
        assert fmt==0x30,(path,i,hex(o),fmt)
        bb=np.array(struct.unpack_from('<6f',d,o+28)); uvr=struct.unpack_from('<8f',d,o+52)
        o+=84
        idx=np.frombuffer(d,'<u2',nt*3,o).reshape(-1,3); ib=nt*6; o+=ib+(-ib)%4
        v=np.frombuffer(d,np.dtype([('p','<i2',3),('n','<i2',3),('uv','<u2',2)]),nv,o); o+=16*nv
        subs.append(dict(mat=mi,idx=idx,v=v,bb=bb,uvr=uvr))
    return dict(texs=texs,mats=mats,M=M,subs=subs,end=o,size=len(d))
