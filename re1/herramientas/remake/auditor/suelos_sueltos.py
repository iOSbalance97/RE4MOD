"""suelos_sueltos.py sala.obj colision.obj [ymin] : triángulos horizontales que miran arriba (suelos/alfombras)
sin suelo de colisión debajo (a <0.35 m): suelo puesto donde no se pisa (p.ej. sobre el hueco central)."""
import sys, numpy as np
from collections import defaultdict
def load(f):
    V=[];F=[];M=[];cur=None
    for l in open(f):
        if l.startswith('v '):V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('usemtl'):cur=l.split()[1]
        elif l.startswith('f '):F.append([int(x.split('/')[0])-1 for x in l.split()[1:4]]);M.append(cur)
    return np.array(V)[np.array(F)],np.array(M)
T,M=load(sys.argv[1]); C,_=load(sys.argv[2]); ymin=float(sys.argv[3]) if len(sys.argv)>3 else -99
n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);A=np.linalg.norm(n,axis=1)/2;n/=2*A[:,None]+1e-12
cn=np.cross(C[:,1]-C[:,0],C[:,2]-C[:,0]);cn/=np.linalg.norm(cn,axis=1,keepdims=True)+1e-12
CF=C[cn[:,1]>0.45]
def alturas(x,z):
    a,b,c=CF[:,0],CF[:,1],CF[:,2]; v0=c-a;v1=b-a; v2=np.array([x,0,z])-a
    d=v0[:,0]*v1[:,2]-v1[:,0]*v0[:,2]
    with np.errstate(all='ignore'):
        u=(v2[:,0]*v1[:,2]-v1[:,0]*v2[:,2])/d; w=(v0[:,0]*v2[:,2]-v2[:,0]*v0[:,2])/d
    ok=(abs(d)>1e-9)&(u>=-0.02)&(w>=-0.02)&(u+w<=1.02)
    return (a[:,1]+u*v0[:,1]+w*v1[:,1])[ok]
sel=np.nonzero((n[:,1]>0.95)&(A>0.005)&(T[:,:,1].mean(1)>ymin))[0]
bad=defaultdict(list)
for i in sel:
    y=T[i][:,1].mean(); ps=[T[i].mean(0)]+[T[i][k]*0.8+T[i].mean(0)*0.2 for k in range(3)]
    if all(np.any(abs(alturas(p[0],p[2])-y)<0.35) for p in ps): continue
    bad[M[i]].append(i)
for m,l in bad.items():
    P=T[l].reshape(-1,3); print(m,len(l),'tri  área',round(float(A[l].sum()),2),' bbox',P.min(0).round(2),P.max(0).round(2))
np.save('/tmp/_sueltos.npy',np.concatenate([np.array(l) for l in bad.values()]) if bad else np.array([],int))
