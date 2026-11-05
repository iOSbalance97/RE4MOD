import struct,sys
def drs_parts(d):
    parts=[];p=0x20
    while p<0x400:
        a,size,b,ofs=struct.unpack('>IIII',d[p:p+16])
        if size==0 and ofs==0: break
        parts.append((a,size,ofs)); p+=0x20
    return parts
def arc_entries(a):
    n=struct.unpack('>I',a[0:4])[0]
    offs=struct.unpack('>%dI'%n,a[0x10:0x10+4*n])
    ends=sorted(set(offs+(len(a),)))
    res=[]
    for i,o in enumerate(offs):
        e=min([x for x in ends if x>o] or [len(a)])
        res.append((i,o,e-o))
    return res
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read()
    for pt in drs_parts(d): print('part',pt)
    a,size,ofs=drs_parts(d)[0]
    arc=d[ofs:ofs+size]
    for i,o,s in arc_entries(arc):
        h=arc[o:o+12]
        print(i,hex(o),s,h.hex())

def load_arc(path):
    d=open(path,'rb').read(); a,size,ofs=drs_parts(d)[0]; return d[ofs:ofs+size]
def entry(arc,i):
    for j,o,s in arc_entries(arc):
        if j==i: return arc[o:o+s]
def skeleton(m):
    ph=struct.unpack('>I',m[0:4])[0]; n=m[0x19]
    res=[]
    for i in range(n):
        p=ph+i*16
        pno,par=m[p],m[p+1]; x,y,z=struct.unpack('>fff',m[p+4:p+16])
        res.append((pno,par,x,y,z))
    return res

def motion_hdr(m):
    mf=struct.unpack('>H',m[0:2])[0]; n=m[2]
    kinds=struct.unpack('>%dH'%n,m[3:3+2*n]); nos=list(m[3+2*n:3+3*n])
    return mf,n,kinds,nos
