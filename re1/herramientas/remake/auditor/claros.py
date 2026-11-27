"""claros.py sala_dir [umbral] : triángulos grandes cuya textura (muestreada en sus UV) es muy clara: parches blancos/crema sueltos"""
import sys, os, numpy as np
from PIL import Image
from collections import defaultdict
d=sys.argv[1]; th=float(sys.argv[2]) if len(sys.argv)>2 else 150
mt={};cur=None
for l in open(f'{d}/sala.mtl'):
    if l.startswith('newmtl'):cur=l.split()[1]
    elif l.startswith('map_Kd'):mt[cur]=l.split()[1]
tex={}
V=[];VT=[];F=[];M=[]
for l in open(f'{d}/sala.obj'):
    if l.startswith('v '):V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('vt '):VT.append([float(x) for x in l.split()[1:3]])
    elif l.startswith('usemtl'):cur=l.split()[1]
    elif l.startswith('f '):
        q=[x.split('/') for x in l.split()[1:4]]; F.append([int(a[0])-1 for a in q]+[int(a[1])-1 for a in q]); M.append(cur)
V=np.array(V);VT=np.array(VT);F=np.array(F)
P=V[F[:,:3]]; A=np.linalg.norm(np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]),axis=1)/2
rng=np.random.default_rng(0); res=defaultdict(float); ej={}
for i in np.nonzero(A>0.01)[0]:
    m=M[i]
    if m not in tex:
        try: tex[m]=np.asarray(Image.open(f'{d}/{mt[m]}').convert('RGB'),float).mean(2)
        except Exception: tex[m]=None
    t=tex[m]
    if t is None: continue
    w=rng.dirichlet([1,1,1],12); uv=w@VT[F[i,3:]]; H,W=t.shape
    x=((uv[:,0]%1)*W).astype(int)%W; y=((1-uv[:,1]%1)*H).astype(int)%H
    if t[y,x].mean()>th: res[m]+=A[i]; ej.setdefault(m,[]).append(P[i].mean(0))
for m,a in sorted(res.items(),key=lambda kv:-kv[1]):
    c=np.array(ej[m]); print(f'{m:30s} {a:6.2f} m2  centros x[{c[:,0].min():.1f},{c[:,0].max():.1f}] y[{c[:,1].min():.1f},{c[:,1].max():.1f}] z[{c[:,2].min():.1f},{c[:,2].max():.1f}]  n={len(c)}')
