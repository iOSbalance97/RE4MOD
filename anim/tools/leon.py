import numpy as np, math
from arc import load_arc, entry, skeleton
from mot import rotm, euler_zyx
arc=load_arc('/home/claude/disc/ext1/files/em/pl00.drs')
SK=skeleton(entry(arc,0))
PAR=[s[1] for s in SK]; OFF=[np.array(s[2:5]) for s in SK]
BINDW=[]
for i in range(len(SK)):
    BINDW.append(OFF[i] if PAR[i]==255 else BINDW[PAR[i]]+OFF[i])
MAP={1:'Hips',17:'Hips',2:'Spine2',3:'Neck',4:'Head',
     5:'RightShoulder',6:'RightArm',7:'RightArm',113:'RightArm',8:'RightForeArm',117:'RightForeArm',9:'RightForeArm',10:'RightHand',
     11:'LeftShoulder',12:'LeftArm',13:'LeftArm',114:'LeftArm',14:'LeftForeArm',118:'LeftForeArm',15:'LeftForeArm',16:'LeftHand',
     18:'RightUpLeg',19:'RightLeg',20:'RightFoot',21:'RightToeBase',22:'LeftUpLeg',23:'LeftLeg',24:'LeftFoot',25:'LeftToeBase'}
def fk_from_worldrots(Wrot, rootpos):
    """Wrot: dict part->3x3 world rotation (missing: inherit). returns world rot list & pos list"""
    n=len(SK); R=[None]*n; P=[None]*n
    for i in range(n):
        p=PAR[i]
        if p==255: R[i]=np.eye(3); P[i]=np.array(rootpos); continue
        R[i]=Wrot.get(i,R[p]); P[i]=P[p]+R[p]@OFF[i]
    return R,P
def ang_up(i,ch):
    axis={4:(0,0,1),5:(0,0,-1),0:(0,1,0),1:(0,-1,0),2:(1,0,0),3:(-1,0,0)}[ch]
    return np.array(axis,float)
def ik_setup(root,eff,ch):
    d=BINDW[eff]-BINDW[root]; ax=ang_up(root,ch)
    vz=d/np.linalg.norm(d); vy=ax/np.linalg.norm(ax); vx=np.cross(vy,vz); vx/=np.linalg.norm(vx); vy=np.cross(vz,vx); vy/=np.linalg.norm(vy)
    mtx=np.stack([vx,vy,vz],1); return mtx.T, vx   # ik_inv_mat, up_vector
def orient_zx(z,x):
    vz=z/np.linalg.norm(z); vx=x/np.linalg.norm(x); vy=np.cross(vz,vx); vy/=np.linalg.norm(vy); vx=np.cross(vy,vz); vx/=np.linalg.norm(vx)
    return np.stack([vx,vy,vz],1)
def axis_rot(ax,a):
    ax=ax/np.linalg.norm(ax); x,y,z=ax; c,s=math.cos(a),math.sin(a); C=1-c
    return np.array([[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]])
def ikcalc(rootR,rootP,effP,la,lb,inv,up):
    d=np.linalg.norm(effP-rootP); a1=a2=0.0
    if d<la+lb:
        c1=max(-1,min(1,(la*la+d*d-lb*lb)/(2*la*d))); c2=max(-1,min(1,(d*d+lb*lb-la*la)/(2*d*lb)))
        a1=math.acos(c1); a2=math.acos(c2)
    axis=rootR@up; m=orient_zx(effP-rootP,axis)@inv
    R1=m@axis_rot(up,-a1); R2=m@axis_rot(up,a2)
    return R1,R2
