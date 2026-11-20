"""hmap.py obj [x0 x1 z0 z1 paso] : alturas de suelo (todas las capas) en una rejilla"""
import sys,numpy as np
def load(p):
    V=[];F=[]
    for l in open(p):
        if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('f '): F.append([int(x.split('/')[0])-1 for x in l.split()[1:4]])
    return np.array(V),np.array(F)
def floors(p):
    V,F=load(p); T=V[F]; n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
    return T[np.abs(n[:,1])>0.5]
def heights(T,x,z):
    a,b,c=T[:,0],T[:,1],T[:,2]
    d=(b[:,2]-c[:,2])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,2]-c[:,2])
    w0=((b[:,2]-c[:,2])*(x-c[:,0])+(c[:,0]-b[:,0])*(z-c[:,2]))/d
    w1=((c[:,2]-a[:,2])*(x-c[:,0])+(a[:,0]-c[:,0])*(z-c[:,2]))/d
    w2=1-w0-w1; m=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)
    return np.sort(w0[m]*a[m,1]+w1[m]*b[m,1]+w2[m]*c[m,1])
