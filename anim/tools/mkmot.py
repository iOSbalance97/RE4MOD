import struct, numpy as np, sys
from conv import convert, JOINTS
from mot import parse, eval_chan
KIND={'pos':(0x0004,), 'rot':(0x0002,), 'ikarm':(0x05A0,), 'ikleg':(0x0420,)}
def reduce(v,tol):
    n=len(v); d=np.gradient(v) if n>1 else np.zeros(n)
    keys=[0]; s=0
    while s<n-1:
        e=s+1
        while e+1<n:
            L=e+1-s; ok=True
            for f in range(s+1,e+1):
                t=(f-s)/L; t2=t*t;t3=t2*t;h01=-2*t3+3*t2;h11=t3-t2;h10=h11-t2+t;h00=1-h01
                x=v[s]*h00+v[e+1]*h01+d[s]*L*h10+d[e+1]*L*h11
                if abs(x-v[f])>tol: ok=False;break
            if not ok: break
            e+=1
        keys.append(e); s=e
    out=[]
    for j,k in enumerate(keys):
        lin=(k-keys[j-1]) if j>0 else 0; lout=(keys[j+1]-k) if j+1<len(keys) else 0
        out.append((k,float(v[k]),float(d[k]*lin),float(d[k]*lout)))
    return out
def build(frames,rot_tol=0.003,pos_tol=1.0):
    n=len(JOINTS); N=len(frames)
    kinds=[];nos=[];blobs=[]
    for no,k in JOINTS:
        arr=np.array([f[0][(no,k)] for f in frames],float)
        if k!='pos': arr=np.unwrap(arr,axis=0)
        kinds.append(KIND[k][0]); nos.append(no)
        b=b''
        for ax in range(3):
            ks=reduce(arr[:,ax],pos_tol if k=='pos' else rot_tol)
            b+=struct.pack('>H',len(ks))+b''.join(struct.pack('>H',f) for f,_,_,_ in ks)
            b+=b''.join(struct.pack('>fff',val,tin,tout) for _,val,tin,tout in ks)
        blobs.append(b)
    hdr=struct.pack('>HB',N-1,n)+b''.join(struct.pack('>H',x) for x in kinds)+bytes(nos)
    hdr+=b'\0'*((-len(hdr))%4)
    tbl_at=len(hdr); base=tbl_at+4+4*n
    offs=[];data=b'';p=base
    for b in blobs: offs.append(p); data+=b; p+=len(b)
    total=base+len(data)
    out=hdr+struct.pack('>I',(total+31)&~31)+b''.join(struct.pack('>I',o) for o in offs)+data
    out+=b'\0'*((-len(out))%32)
    return out
if __name__=='__main__':
    path,name,t0,t1=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4])
    fr=convert(path,t0=t0,t1=t1)
    b=build(fr)
    # self-check: parse back and compare
    mf,ch=parse(b); err=0
    for c,(no,k) in zip(ch,JOINTS):
        for f in range(len(fr)):
            v=np.array(eval_chan(c,f)); w=np.array(fr[f][0][(no,k)])
            dd=np.abs(((v-w+np.pi)%(2*np.pi))-np.pi) if k!='pos' else np.abs(v-w)
            err=max(err,dd.max()/(1 if k=='pos' else 0.001))
    print(name,'frames',mf,'bytes',len(b),'max err (mm or mrad)',round(err,2))
    open(name+'.bin','wb').write(b)
