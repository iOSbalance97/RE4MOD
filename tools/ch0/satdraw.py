import struct,sys,arc
from PIL import Image,ImageDraw
def sat(path):
    d=open(path,'rb').read(); o=arc.get(d,'SAT')
    h=d[o]; 
    files=[]
    cnt=d[o+1]
    files=[o+struct.unpack('>I',d[o+4+4*k:o+8+4*k])[0] for k in range(cnt)]
    tris=[]
    for f in files:
        nv,nn,ne,_,npo,nf,ns,nw,nb=struct.unpack('>9H',d[f+2:f+0x14])
        vo=f+0x14; V=[struct.unpack('>3f',d[vo+12*i:vo+12*i+12]) for i in range(nv)]
        po=vo+12*(nv+nn+ne)
        for i in range(npo):
            v=struct.unpack('>3H',d[po+20*i:po+20*i+6]); kind='f' if i<nf else ('s' if i<nf+ns else 'w')
            tris.append(([V[j] for j in v],kind))
    return tris
if __name__=='__main__':
    tris=sat(sys.argv[1]); print(len(tris))
    xs=[p[0] for t,_ in tris for p in t]; zs=[p[2] for t,_ in tris for p in t]
    print(min(xs),max(xs),min(zs),max(zs))
