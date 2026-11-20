"""topview.py sala.obj colision.obj out.png [ylo yhi] : planta (visible transformado a RE4 m) suelos por altura, paredes en rojo"""
import sys,numpy as np, re4room
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
COL="19.4,0,15.0,-47609,12,7084,-1.253"
def load(p):
    V=[];F=[]
    for l in open(p):
        if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('f '): F.append([int(x.split('/')[0])-1 for x in l.split()[1:4]])
    return np.array(V),np.array(F)
Vs,Fs=load(sys.argv[1]); import os
if not os.environ.get("NOPLACE"): Vs=re4room.place(Vs,COL,1000.0)
Vc,Fc=load(sys.argv[2])
lo,hi=(float(sys.argv[4]),float(sys.argv[5])) if len(sys.argv)>5 else (-99,99)
bb=(Vs.min(0)-1,Vs.max(0)+1)
fig,axs=plt.subplots(1,2,figsize=(18,10))
for ax,(V,F,ti) in zip(axs,[(Vs,Fs,'visible'),(Vc,Fc,'colision')]):
    T=V[F]; n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
    cy=T[:,:,1].mean(1); inb=(cy>lo)&(cy<hi)&(T[:,:,0].mean(1)>bb[0][0])&(T[:,:,0].mean(1)<bb[1][0])&(T[:,:,2].mean(1)>bb[0][2])&(T[:,:,2].mean(1)<bb[1][2])
    m=inb&(np.abs(n[:,1])>0.5)
    pc=PolyCollection(T[m][:,:,[0,2]],array=cy[m],cmap='viridis',edgecolors='none',clim=(lo if lo>-99 else -2, hi if hi<99 else 9))
    ax.add_collection(pc); w=inb&(np.abs(n[:,1])<0.3)
    ax.add_collection(PolyCollection(T[w][:,:,[0,2]],facecolors='none',edgecolors='r',linewidths=0.3))
    ax.set_xlim(bb[0][0],bb[1][0]); ax.set_ylim(bb[0][2],bb[1][2]); ax.set_aspect('equal'); ax.set_title(f'{ti} y {lo}..{hi}'); plt.colorbar(pc,ax=ax); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(sys.argv[3],dpi=55)
