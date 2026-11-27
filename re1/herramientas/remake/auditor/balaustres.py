"""balaustres.py sala.obj : balaustres (wood16) cuyo tope asoma por encima del pasamanos (handrail01) que tienen encima"""
import sys, numpy as np
from scipy.spatial import cKDTree
from scipy.cluster.hierarchy import fcluster, linkage
V=[];F=[];M=[];cur=None
for l in open(sys.argv[1]):
    if l.startswith('v '):V.append([float(x) for x in l.split()[1:4]])
    elif l.startswith('usemtl'):cur=l.split()[1]
    elif l.startswith('f '):F.append([int(x.split('/')[0])-1 for x in l.split()[1:4]]);M.append(cur)
V=np.array(V);F=np.array(F);M=np.array(M)
bal=np.isin(M,[m for m in set(M) if 'wood16' in m]); rail=np.isin(M,[m for m in set(M) if 'handrail01' in m])
# muestras del pasamanos
T=V[F]; rng=np.random.default_rng(0); R=[]
for t in T[rail]:
    a=np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))/2; R.append(rng.dirichlet([1,1,1],int(np.clip(a/0.0005,3,300)))@t)
R=np.concatenate(R); KR=cKDTree(R[:,[0,2]])
# balaustres: agrupar vértices por cercanía horizontal
P=np.unique(V[F[bal].ravel()],axis=0)
from collections import defaultdict
g=defaultdict(list)
for p in P: g[(int(np.floor(p[0]/0.12)),int(np.floor(p[2]/0.12)))].append(p)
out=[]
for k,ps in g.items():
    ps=np.array(ps); top=ps[:,1].max(); c=ps.mean(0)
    ii=[j for j in KR.query_ball_point(c[[0,2]],0.1) if top-0.5<R[j,1]<top+0.6]
    if len(ii)<3: continue
    ylo=R[ii,1].max()
    if top>ylo-0.01: out.append((round(top-ylo,3),np.round(c,2).tolist(),round(top,2),round(ylo,2)))
out.sort(reverse=True)
print(len(out),'celdas de balaustre que asoman por encima del pasamanos')
for o in out[:40]: print(o)
