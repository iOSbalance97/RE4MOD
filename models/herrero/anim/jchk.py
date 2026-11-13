import sys, math, numpy as np
sys.path.insert(0,'/home/claude/re4mod/models/herrero/anim')
import mkanim as m
def ang(R): return math.degrees(math.acos(max(-1,min(1,(np.trace(R)-1)/2))))
def analyze(seq,name):
    print('==',name,len(seq))
    J=[1,2,5,7,8,10,11,13,14,16]
    prev=None
    for f,p in enumerate(seq):
        P=m.fk(p)
        # right elbow bend: angle between upper and fore
        ua=P[8]-P[7]; fa=P[10]-P[8]; bend=math.degrees(math.acos(np.dot(ua,fa)/np.linalg.norm(ua)/np.linalg.norm(fa)))
        # wrist twist: local hand rot rel forearm
        wl=ang(p.W[9].T@p.W[10]); wlL=ang(p.W[15].T@p.W[16])
        ua2=P[14]-P[13]; fa2=P[16]-P[14]; bend2=math.degrees(math.acos(np.dot(ua2,fa2)/np.linalg.norm(ua2)/np.linalg.norm(fa2)))
        loc={k:m.local(p,k) for k in J}
        vel={}
        if prev is not None: vel={k:ang(prev[k].T@loc[k]) for k in J}
        mv=max(vel.items(),key=lambda x:x[1]) if vel else (0,0)
        print('%3d Relb %5.1f Rwr %5.1f | Lelb %5.1f Lwr %5.1f | maxvel j%d %5.1f'%(f,bend,wl,bend2,wlL,mv[0],mv[1]))
        prev=loc
if __name__=='__main__':
    UP=[m.upswing(f) for f in range(m.UP_N+1)]
    analyze(UP,'upswing')
