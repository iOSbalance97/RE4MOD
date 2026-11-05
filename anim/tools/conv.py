import numpy as np, math, sys
from mix import Fbx
from leon import *
from mot import euler_zyx, rotm
BIND=Fbx('/home/claude/re4mod/anim/mixamo/X Bot.fbx').world()
S=(BINDW[0][1]-BINDW[21][1])/ (BIND['Hips'][1][1]-BIND['RightToeBase'][1][1])
JOINTS=[(0,'pos'),(1,'rot'),(2,'rot'),(3,'rot'),(4,'rot'),(5,'rot'),(7,'ikarm'),(10,'rot'),(10,'pos'),
        (11,'rot'),(13,'ikarm'),(16,'rot'),(16,'pos'),(17,'rot'),(18,'ikleg'),(20,'rot'),(20,'pos'),(21,'rot'),
        (22,'ikleg'),(24,'rot'),(24,'pos'),(25,'rot')]
WORLDROT={10,16,20,24}
def frame_pose(fbx,t,root0=None):
    W=fbx.world(t)
    Wrot={i:W[n][0]@BIND[n][0].T for i,n in MAP.items()}
    hips=W['Hips'][1]
    rp=(hips-BIND['Hips'][1])*S+BINDW[0]
    if root0 is not None: rp=rp.copy(); rp[0]-=root0[0]; rp[2]-=root0[2]
    R,P=fk_from_worldrots(Wrot,rp)
    vals={}
    for no,k in JOINTS:
        if k=='pos':
            vals[(no,k)]=list(P[21] if no==20 else P[25] if no==24 else P[no])
        elif no in WORLDROT:
            vals[(no,k)]=euler_zyx(R[no])
        else:
            vals[(no,k)]=euler_zyx(R[PAR[no]].T@R[no])
    return vals,R,P
def convert(path,fps=30,inplace=True,t0=0,t1=None):
    f=Fbx(path); t1=f.dur if t1 is None else t1
    n=int(round((t1-t0)*fps))+1
    W0=f.world(t0); root0=((W0['Hips'][1]-BIND['Hips'][1])*S) if inplace else None
    frames=[frame_pose(f,t0+i/fps,root0) for i in range(n)]
    return frames
