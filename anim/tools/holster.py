import numpy as np
from leon import *
from mot import rotm, euler_zyx, parse, eval_chan
from arc import load_arc, entry
from conv import convert, JOINTS
from mkmot import build
def game_fk(vals):
    n=len(SK); L=[np.eye(3)]*n; pos=[o.copy() for o in OFF]
    for (no,k),v in vals.items():
        if k=='pos': pos[no]=np.array(v)
        else: L[no]=rotm(v)
    R=[None]*n;P=[None]*n
    for i in range(n):
        p=PAR[i]
        if p==255: R[i]=L[i];P[i]=pos[i];continue
        R[i]=R[p]@L[i]; P[i]=P[p]+R[p]@OFF[i]
    return R,P
def idle_vals(f=0):
    a=load_arc('/home/claude/disc/ext1/files/em/wep01.drs'); mf,ch=parse(entry(a,0x0B)); v={}
    for c in ch:
        if c['kind'] in (1,0x40) or c['ch'] in (6,7) or c['no'] in (32,110): continue
        v[(c['no'],'pos' if c['kind']&4 else 'rot')]=eval_chan(c,f)
    return v
def holster_pose(src_frame=18):
    g=idle_vals(0); Rg,Pg=game_fk(g)
    m=convert('/home/claude/re4mod/anim/mixamo/Drawing_Gun_2.fbx')[src_frame]
    mv,Rm,Pm=m
    out=dict(g)
    C=Rg[2]@Rm[2].T          # Mixamo chest frame -> idle chest frame
    for sh,arm,hand in ((5,7,10),(11,13,16)):
        out[(sh,'rot')]=mv[(sh,'rot')]       # local to chest: same
        out[(arm,'ikarm')]=mv[(arm,'ikarm')]
        out.pop((arm,'rot'),None)
        out[(hand,'pos')]=list(Pg[2]+C@(Pm[hand]-Pm[2]))
        out[(hand,'rot')]=euler_zyx(C@Rm[hand])
    # keys from the game's idle use 'rot' for ik roots: rename to converter kinds
    for no,k in ((7,'ikarm'),(13,'ikarm'),(18,'ikleg'),(22,'ikleg')):
        if (no,'rot') in out: out[(no,k)]=out.pop((no,'rot'))
    return out
if __name__=='__main__':
    p=holster_pose()
    fr=[(p,None,None),(p,None,None)]
    b=build(fr); open('holster.bin','wb').write(b); print('holster bytes',len(b))
    from render import game_pose, draw
    draw([game_pose(idle_vals(0)),game_pose(p)],['idle','holster'],'holster.png')
