import numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from leon import *
from mot import rotm, eval_chan
BONES=[(0,1),(1,2),(2,3),(3,4),(2,5),(5,7),(7,8),(8,10),(2,11),(11,13),(13,14),(14,16),(0,17),(17,18),(18,19),(19,20),(20,21),(17,22),(22,23),(23,24),(24,25)]
def game_pose(vals):
    """vals: dict (no,kind)->vec in our converter key style, evaluated with game semantics"""
    n=len(SK); L=[np.eye(3)]*n; pos=[o.copy() for o in OFF]
    for (no,k),v in vals.items():
        if k=='pos': pos[no]=np.array(v)
        else: L[no]=rotm(v)
    R=[None]*n;P=[None]*n
    for i in range(n):
        p=PAR[i]
        if p==255: R[i]=L[i]; P[i]=pos[i]; continue
        R[i]=R[p]@L[i]; P[i]=P[p]+R[p]@pos[i] if i not in (10,16,20,24) else None
        if i in (10,16): R[i]=L[i]; P[i]=pos[i]
        if i in (20,24): R[i]=L[i]; P[i]=pos[i]-L[i]@OFF[i+1]
        if P[i] is None: P[i]=P[p]+R[p]@OFF[i]
    for root,eff,ch,mid in ((7,10,5,8),(13,16,5,14),(18,20,4,19),(22,24,4,23)):
        inv,up=ik_setup(root,eff,ch); la=np.linalg.norm(OFF[mid]); lb=np.linalg.norm(BINDW[eff]-BINDW[mid])
        R1,R2=ikcalc(R[root],P[root],P[eff],la,lb,inv,up); P[mid]=P[root]+R1@OFF[mid]
    P[21]=P[20]+R[20]@OFF[21]; P[25]=P[24]+R[24]@OFF[25]
    return P
def draw(poses,titles,out):
    fig,axs=plt.subplots(2,len(poses),figsize=(2.2*len(poses),6))
    for j,P in enumerate(poses):
        for r,(a,b,lab) in enumerate(((0,1,'frente'),(2,1,'lado'))):
            ax=axs[r][j]
            for u,v in BONES:
                c='r' if (u in (5,7,8) or v in(7,8,10,18,19,20,21) and u not in(0,) and (v in (7,8,10) or u in (17,18,19,20)) and (P[v][0]<0 if v not in(18,19,20,21) else True) ) else 'k'
                c='r' if v in (7,8,10,18,19,20,21) else 'b' if v in (13,14,16,22,23,24,25) else 'k'
                ax.plot([P[u][a],P[v][a]],[P[u][b],P[v][b]],c,lw=2)
            ax.set_aspect('equal'); ax.set_xlim(-900,900); ax.set_ylim(-50,1900); ax.set_xticks([]); ax.set_yticks([])
            if r==0: ax.set_title(titles[j],fontsize=8)
    plt.tight_layout(); plt.savefig(out,dpi=70)
