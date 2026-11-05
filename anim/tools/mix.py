import sys, math, numpy as np
from fbxbin import read, find, child
TICK=46186158000
def props(n):
    p=child(n,'Properties70'); r={}
    if p:
        for c in p[2]: r[c[1][0]]=c[1][4:] if len(c[1])>4 else c[1][1:]
    return r
def R_xyz(deg):
    x,y,z=[math.radians(v) for v in deg]
    sx,sy,sz=math.sin(x),math.sin(y),math.sin(z); cx,cy,cz=math.cos(x),math.cos(y),math.cos(z)
    Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rz@Ry@Rx
class Fbx:
    def __init__(s,path):
        t=read(path); objs=next(find(t,'Objects')); con=next(find(t,'Connections'))
        s.ids={c[1][0]:c for c in objs[2]}
        s.bones={}; s.parent={}
        for c in objs[2]:
            if c[0]=='Model' and c[1][2] in ('LimbNode','Root','Null'):
                nm=c[1][1].split('\x00')[0].replace('mixamorig:','')
                pr=props(c)
                s.bones[c[1][0]]=dict(name=nm,T=np.array(pr.get('Lcl Translation',[0,0,0]),float),
                    R=np.array(pr.get('Lcl Rotation',[0,0,0]),float),pre=np.array(pr.get('PreRotation',[0,0,0]),float),
                    post=np.array(pr.get('PostRotation',[0,0,0]),float),ro=pr.get('RotationOrder',[0])[0] if 'RotationOrder' in pr else 0)
        cn_model={}; cv_cn={}
        for c in con[2]:
            a,b=c[1][1],c[1][2]
            if a in s.bones and b in s.bones: s.parent[a]=b
            if a in s.ids and b in s.ids:
                if s.ids[a][0]=='AnimationCurveNode' and b in s.bones and len(c[1])>3: cn_model[a]=(b,c[1][3])
                if s.ids[a][0]=='AnimationCurve' and s.ids[b][0]=='AnimationCurveNode': cv_cn[a]=(b,c[1][3])
        s.curves={}  # (bone, 'Lcl Rotation', axis) -> (times, values)
        for cv,(cn,ax) in cv_cn.items():
            if cn in cn_model:
                b,prop=cn_model[cn]; nd=s.ids[cv]
                kt=np.array(child(nd,'KeyTime')[1][0],float)/TICK; kv=np.array(child(nd,'KeyValueFloat')[1][0],float)
                s.curves[(b,prop,'XYZ'.index(ax[-1]))]=(kt,kv)
        s.byname={v['name']:k for k,v in s.bones.items()}
        ts=[v[0][-1] for v in s.curves.values()]; s.dur=max(ts) if ts else 0
        assert all(b['ro']==0 for b in s.bones.values()), 'rotation order'
    def local(s,b,t=None):
        B=s.bones[b]; T=B['T'].copy(); R=B['R'].copy()
        if t is not None:
            for i in range(3):
                k=(b,'Lcl Translation',i)
                if k in s.curves: T[i]=np.interp(t,*s.curves[k])
                k=(b,'Lcl Rotation',i)
                if k in s.curves: R[i]=np.interp(t,*s.curves[k])
        M=R_xyz(B['pre'])@R_xyz(R)@R_xyz(B['post']).T
        return M,T
    def world(s,t=None):
        out={}
        def go(b):
            if b in out: return out[b]
            M,T=s.local(b,t)
            p=s.parent.get(b)
            if p is None: res=(M,T)
            else:
                PM,PT=go(p); res=(PM@M, PT+PM@T)
            out[b]=res; return res
        for b in s.bones: go(b)
        return {s.bones[b]['name']:v for b,v in out.items()}
