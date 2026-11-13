import sys, math, numpy as np
sys.path.insert(0,'/home/claude/re4mod/models/herrero/anim')
import mkanim as m
from scipy.spatial.transform import Rotation as Rr
def aa(axis, a): return Rr.from_rotvec(np.asarray(axis)*a).as_matrix()
N=48
def keyv(f, keys):
    """piecewise smoothstep through (frame, value) keys"""
    if f<=keys[0][0]: return keys[0][1]
    for (f0,v0),(f1,v1) in zip(keys,keys[1:]):
        if f<=f1: return v0+(v1-v0)*m.sm((f-f0)/(f1-f0))
    return keys[-1][1]
TH=[(0,0),(9,-0.42),(13,-0.2),(19,1.75),(23,1.95),(27,1.95),(40,0.0),(48,0)]     # shoulder flexion (rad): back, then up in front
EB=[(0,1.0),(9,0.85),(16,0.35),(23,0.30),(27,0.35),(40,1.0),(48,1.0)]           # elbow bend (x drag's)
CK=[(0,0),(9,0.15),(15,0.0),(20,0.55),(25,0.6),(30,0.3),(40,0),(48,0)]           # wrist cock (rad)
YW=[(0,0),(9,-0.38),(14,-0.1),(20,0.32),(26,0.28),(40,0),(48,0)]                 # torso yaw (+ = to his left)
PT=[(0,0),(9,0.05),(18,-0.10),(24,-0.06),(40,0),(48,0)]                          # torso pitch
DR=[(0,0),(9,70),(16,40),(22,20),(40,0),(48,0)]                                  # hips down
def upswing2(f, cock_fix=True):
    p, Wm = m.mixpose('mutant breathing idle', (f % 120) / 30.0)
    yaw=keyv(f,YW); pit=keyv(f,PT)
    m.turn(p, 1, m.ry(yaw*0.6) @ m.rx(pit))
    m.turn(p, 2, m.ry(yaw*0.4))
    p.root[1]-=keyv(f,DR)
    m.drag_right(p)
    W0={k:p.W[k].copy() for k in (6,7,8,9,10)}
    Le0=W0[7].T@W0[8]; rv=Rr.from_matrix(Le0).as_rotvec(); a0=np.linalg.norm(rv); ax=rv/a0
    Lh0=W0[9].T@W0[10]
    Rb=p.W[2]; th=keyv(f,TH)
    F=Rb@m.rx(-th)@Rb.T
    p.W[7]=F@W0[7]; p.W[6]=p.W[7]
    p.W[8]=p.W[7]@aa(ax, a0*keyv(f,EB)); p.W[9]=p.W[8]
    def hand(g): return p.W[9]@aa(ax, -g)@Lh0
    g=keyv(f,CK); p.W[10]=hand(g)
    P=m.fk(p)
    def anvil(): 
        P=m.fk(p); grip=P[10]+p.W[10]@np.array([-m.GRIP_OFF,0,0]); return grip+p.W[10]@np.array([0,0,-1.0])*m.BEAM
    if cock_fix:
        k=0
        while anvil()[1]<m.SW_FLOOR and k<40: g+=0.03; p.W[10]=hand(g); k+=1
    P=m.fk(p)
    low=min(P[20][1]-m.BP[20][1],P[24][1]-m.BP[24][1],P[21][1]-m.BP[21][1],P[25][1]-m.BP[25][1]); p.root[1]-=low
    return p
if __name__=='__main__':
    sys.path.insert(0,'/tmp'); import jchk
    seq=[upswing2(f) for f in range(N+1)]
    jchk.analyze(seq,'up2')
    for f in range(0,N+1,2):
        p=seq[f];P=m.fk(p);grip=P[10]+p.W[10]@np.array([-m.GRIP_OFF,0,0]);an=grip+p.W[10]@np.array([0,0,-1.0])*m.BEAM
        print(f,'anvil',an.round(0),'grip',grip.round(0))

CLAW_HS=-1.0
CLAW_TB=300.0
def rigpose(f, TH, EB, CK, YW, PT, DR, claw=None, idle_t=None, AD=None, gset=None, info=None):
    """B110: the right arm moved as one piece from his dragging stance (shoulder flexion TH, elbow bend EB
    x the stance's, wrist cock CK): no IK, so no elbow flips or wrist twists; the anvil kept above the floor
    by the wrist; claw: weight (0-1) of the claw on the beam"""
    p, Wm = m.mixpose('mutant breathing idle', ((f if idle_t is None else idle_t) % 120) / 30.0)
    yaw=keyv(f,YW); pit=keyv(f,PT)
    m.turn(p, 1, m.ry(yaw*0.6) @ m.rx(pit))
    m.turn(p, 2, m.ry(yaw*0.4))
    p.root[1]-=keyv(f,DR)
    m.drag_right(p)
    W0={k:p.W[k].copy() for k in (6,7,8,9,10)}
    Le0=W0[7].T@W0[8]; rv=Rr.from_matrix(Le0).as_rotvec(); a0=np.linalg.norm(rv); ax=rv/a0
    Lh0=W0[9].T@W0[10]
    Rb=p.W[2]; th=keyv(f,TH)
    ad=keyv(f,AD) if AD else 0.0
    F=Rb@m.ry(ad)@m.rx(-th)@Rb.T
    p.W[7]=F@W0[7]; p.W[6]=p.W[7]
    p.W[8]=p.W[7]@aa(ax, a0*keyv(f,EB)); p.W[9]=p.W[8]
    def hand(g): return p.W[9]@aa(ax, -g)@Lh0
    def anvil():
        P=m.fk(p); grip=P[10]+p.W[10]@np.array([-m.GRIP_OFF,0,0]); return grip+p.W[10]@np.array([0,0,-1.0])*m.BEAM, grip
    g=keyv(f,CK) if gset is None else gset; p.W[10]=hand(g)
    if gset is None and anvil()[0][1]<m.SW_FLOOR:
        best=None
        for k in range(1,50):
            for sg in (1,-1):
                p.W[10]=hand(g+sg*0.02*k)
                if anvil()[0][1]>=m.SW_FLOOR: best=g+sg*0.02*k; break
            if best is not None: break
        g=best if best is not None else g; p.W[10]=hand(g)
    if info is not None: info['g']=g
    P=m.fk(p)
    low=min(P[20][1]-m.BP[20][1],P[24][1]-m.BP[24][1],P[21][1]-m.BP[21][1],P[25][1]-m.BP[25][1]); p.root[1]-=low
    if claw is not None:
        w=keyv(f,claw)
        if w>0.01:
            P=m.fk(p); an,grip=anvil(); sh=m.nrm(an-grip)
            tb=CLAW_TB                                        # a fixed place on the beam (a nearest point jumped with the swing)
            tgt=grip+sh*tb-np.array([0,0,0])
            cur=P[16]; reach=(m.L_UA+m.L_FA)*0.86
            d=tgt-P[13]
            if np.linalg.norm(d)>reach: tgt=P[13]+m.nrm(d)*reach
            wl=cur+(tgt-cur)*w
            pole=m.nrm(np.array([1.0,-0.35,-0.25]))                # elbow out to his left (the beam never goes there: no plane spin)
            Lh=p.W[15].T@p.W[16]
            # B110: the claw arm by its own two bones, twisted by the plane of the arm (arm() aimed the bind z
            # at the pole: when the pole lay along the upper arm it flipped 180 degrees in a frame)
            sh_=P[13]; el,wr=m.two_bone(sh_, wl, m.L_UA, m.L_FA, pole)
            hn=np.cross(el-sh_, wr-el)
            if np.linalg.norm(hn)<1e-3: hn=np.array([0,1.0,0])
            hn=m.nrm(hn)*CLAW_HS
            p.W[13]=m.aim([1.0,0,0],[0,1.0,0],el-sh_,hn); p.W[12]=p.W[13]
            p.W[14]=m.aim([1.0,0,0],[0,1.0,0],wr-el,hn); p.W[15]=p.W[14]
            p.W[16]=p.W[15]@Lh                                   # the claw keeps its own set on the forearm
    return p

SM_TH=[(0,0),(10,1.6),(16,3.0),(20,3.05),(25,1.45),(27,1.35),(38,1.35),(54,0.0),(60,0)]
SM_EB=[(0,1.0),(10,0.6),(16,0.45),(20,0.45),(25,0.25),(38,0.3),(54,1.0),(60,1.0)]
SM_CK=[(0,0),(10,0.2),(16,0.35),(20,0.4),(25,-0.3),(38,-0.3),(54,0),(60,0)]
SM_YW=[(0,0),(16,-0.22),(20,-0.25),(25,0.12),(38,0.1),(54,0),(60,0)]
SM_PT=[(0,0),(16,-0.18),(20,-0.2),(25,0.45),(38,0.4),(54,0),(60,0)]
SM_DR=[(0,0),(16,-20),(20,-30),(25,170),(38,150),(54,0),(60,0)]
SM_CL=[(0,0),(8,0),(15,1),(38,1),(46,0),(60,0)]
def smash2(f): return rigpose(f, SM_TH, SM_EB, SM_CK, SM_YW, SM_PT, SM_DR, SM_CL)

# B110: the whole combo, one timeline
CB_TH=[(0,0),(9,-0.42),(13,-0.2),(20,2.1),(24,2.45),(28,2.45),(40,1.5),(48,1.5),(62,3.3),(65,3.3),(72,1.62),(84,1.62),(92,1.1),(102,0.0),(106,0)]
CB_EB=[(0,1.0),(9,0.85),(16,0.35),(23,0.30),(28,0.35),(40,0.6),(48,0.6),(62,0.9),(65,0.9),(72,0.5),(84,0.5),(102,1.0),(106,1.0)]
CB_CK=[(0,0),(9,0.1),(14,-0.1),(20,-0.6),(26,-0.65),(40,-0.2),(48,-0.2),(62,-0.6),(65,-0.6),(72,-0.7),(84,-0.7),(90,-0.1),(102,0),(106,0)]
CB_YW=[(0,0),(9,-0.38),(14,-0.1),(20,0.32),(26,0.28),(40,0.05),(48,0.0),(62,-0.22),(65,-0.25),(72,0.12),(84,0.1),(102,0),(106,0)]
CB_PT=[(0,0),(9,0.05),(18,-0.10),(24,-0.06),(40,0.08),(48,0.08),(62,-0.18),(65,-0.2),(72,0.45),(84,0.4),(102,0),(106,0)]
CB_DR=[(0,0),(9,70),(16,40),(22,20),(40,40),(48,40),(62,-20),(65,-30),(72,170),(84,150),(102,0),(106,0)]
CB_CL=[(0,0),(32,0),(40,1),(86,1),(94,0),(106,0)]
CB_N=106
CB_HIT1=(17,24); CB_HIT2=(68,74)
CB_AD=[(0,0),(32,0),(40,0.6),(48,0.6),(62,0.35),(65,0.35),(72,0.65),(84,0.65),(94,0),(106,0)]
def combo_seq():
    gs=[]
    for f in range(CB_N+1):
        inf={}; rigpose(f, CB_TH, CB_EB, CB_CK, CB_YW, CB_PT, CB_DR, None, AD=CB_AD, info=inf); gs.append(inf['g'])
    gs=np.array(gs); k=np.exp(-0.5*(np.arange(-6,7)/2.5)**2); k/=k.sum()
    gp=np.pad(gs,6,mode='edge'); g2=np.convolve(gp,k,mode='valid')
    for it in range(6):                                  # where the smoothing put the anvil in the floor, back toward the need
        bad=False
        for f in range(CB_N+1):
            inf={}; p=rigpose(f, CB_TH, CB_EB, CB_CK, CB_YW, CB_PT, CB_DR, None, AD=CB_AD, gset=g2[f]); P=m.fk(p)
            grip=P[10]+p.W[10]@np.array([-m.GRIP_OFF,0,0]); an=grip+p.W[10]@np.array([0,0,-1.0])*m.BEAM
            if an[1]<m.SW_FLOOR-25: g2[f]+=(gs[f]-g2[f])*0.6; bad=True
        if not bad: break
        gp=np.pad(g2,3,mode='edge'); k2=np.exp(-0.5*(np.arange(-3,4)/1.2)**2); k2/=k2.sum(); g2=np.convolve(gp,k2,mode='valid')
    return [rigpose(f, CB_TH, CB_EB, CB_CK, CB_YW, CB_PT, CB_DR, CB_CL, AD=CB_AD, gset=g2[f]) for f in range(CB_N+1)], gs, g2
