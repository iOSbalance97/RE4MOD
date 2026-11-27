"""aletas.py sala.obj colision.obj : busca 'aletas' (caras verticales cuyo borde libre queda al aire, visibles desde zona pisable)"""
import sys, os, subprocess, numpy as np
from collections import defaultdict
AQ=os.path.dirname(os.path.abspath(__file__))
def load(f):
    V=[];F=[];M=[];cur=None
    for l in open(f):
        if l.startswith('v '):V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('usemtl'):cur=l.split()[1]
        elif l.startswith('f '):F.append([int(x.split('/')[0])-1 for x in l.split()[1:4]]);M.append(cur)
    return np.array(V),np.array(F),M
V,F,M=load(sys.argv[1]); T=V[F]
q=np.round(V/0.005).astype(np.int64); key={}; idx=np.array([key.setdefault(tuple(k),len(key)) for k in q])
Fi=idx[F]; cnt=defaultdict(int); vis=set()
for f in Fi:
    k=tuple(sorted(f))
    if k in vis: continue
    vis.add(k)
    for a,b in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])): cnt[(min(a,b),max(a,b))]+=1
n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); A=np.linalg.norm(n,axis=1); n/=A[:,None]+1e-12
C,CF,_=load(sys.argv[2]); CT=C[CF]
cn=np.cross(CT[:,1]-CT[:,0],CT[:,2]-CT[:,0]); cn/=np.linalg.norm(cn,axis=1,keepdims=True)+1e-12
suelo=CT[cn[:,1]>0.45]
ym=float(os.environ.get('SUELO_YMAX',99))
O=[];D=[];info=[]
for i,f in enumerate(Fi):
    if abs(n[i,1])>0.3 or A[i]<1e-4: continue
    for j,(a,b) in enumerate(((f[0],f[1]),(f[1],f[2]),(f[2],f[0]))):
        if cnt[(min(a,b),max(a,b))]!=1: continue
        p,qq=T[i][j],T[i][(j+1)%3]; e=qq-p; L=np.linalg.norm(e)
        if L<0.4: continue
        if abs(e[1])/L<0.7: continue   # borde casi vertical
        c=T[i][(j+2)%3]; m=(p+qq)/2
        d=np.cross(e/L,n[i]); 
        if np.dot(d,m-c)<0: d=-d
        # cerca de suelo pisable (en planta, a <1.5m)?
        info.append((i,m,d,L)); O.append(m+d*0.01); D.append(d)
O=np.array(O,np.float32);D=np.array(D,np.float32)
T.astype(np.float32).tofile('/tmp/fin/t.bin');O.tofile('/tmp/fin/o.bin');D.tofile('/tmp/fin/d.bin')
subprocess.run([f'{AQ}/rayos','/tmp/fin/t.bin','/tmp/fin/o.bin','/tmp/fin/d.bin','/tmp/fin/r.bin','t'],check=True)
t=np.fromfile('/tmp/fin/r.bin',np.float32)
sc=suelo.mean(1)
out=[]
for (i,m,d,L),tt in zip(info,t):
    libre = tt<0 or tt>0.12
    if not libre: continue
    dd=np.hypot(sc[:,0]-m[0],sc[:,2]-m[2]); k=dd.argmin()
    if dd[k]>1.2: continue
    if not (sc[k,1]-0.3 < m[1] < sc[k,1]+3.5) and not (T[i][:,1].min()<sc[k,1]+2.5 and T[i][:,1].max()>sc[k,1]): continue
    out.append((i,M[i],np.round(m,2),round(float(L),2),round(float(tt),2),np.round(d,2)))
for o in out: print(*o)
print(len(out),'aletas')
