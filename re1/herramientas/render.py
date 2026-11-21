"""Rasterizador simple con texturas para previsualizar OBJ.  render.py obj out.png eye(x,y,z) target(x,y,z) [fov] [W H]"""
import sys,os,numpy as np
from PIL import Image
objp,outp=sys.argv[1],sys.argv[2]
eye=np.array(eval(sys.argv[3]),float); tgt=np.array(eval(sys.argv[4]),float)
fov=float(sys.argv[5]) if len(sys.argv)>5 else 70; W,H=(int(sys.argv[6]),int(sys.argv[7])) if len(sys.argv)>7 else (640,480)
base=os.path.dirname(objp)
V=[];T=[];F=[];FM=[];cur=None;mtlfile=None
for l in open(objp):
    if l.startswith('v '): V.append(l.split()[1:4])
    elif l.startswith('vt '): T.append(l.split()[1:3])
    elif l.startswith('f '):
        p=[x.split('/') for x in l.split()[1:4]]; F.append([int(a[0])-1 for a in p]+[int(a[1])-1 for a in p]); FM.append(cur)
    elif l.startswith('usemtl'): cur=l.split()[1]
    elif l.startswith('mtllib'): mtlfile=l.split()[1]
V=np.array(V,float);T=np.array(T,float);F=np.array(F);
mats={};m=None
for l in open(os.path.join(base,mtlfile)):
    if l.startswith('newmtl'): m=l.split()[1]; mats[m]=None
    elif l.startswith('map_Kd'): mats[m]=l.split(None,1)[1].strip()
texc={}
def tex(name):
    if name not in texc:
        im=Image.open(os.path.join(base,name)).convert('RGBA'); texc[name]=np.asarray(im).astype(np.float32)/255
    return texc[name]
fw=tgt-eye; fw/=np.linalg.norm(fw); up=np.array([0,1,0.]) if abs(fw[1])<0.95 else np.array([0,0,-1.]); r=np.cross(fw,up); r/=np.linalg.norm(r); u=np.cross(r,fw)
C=(V-eye)@np.stack([r,u,fw],1)
f=(H/2)/np.tan(np.radians(fov/2))
zb=np.full((H,W),np.inf); img=np.zeros((H,W,3)); img[:]=0.15
near=0.05
YMAX=float(os.environ['YMAX']) if os.environ.get('YMAX') else None
def clip(c,t):
    P=list(zip(c,t)); out=[]
    for k in range(len(P)):
        a,b=P[k],P[(k+1)%len(P)]; ina,inb=a[0][2]>=near,b[0][2]>=near
        if ina: out.append(a)
        if ina!=inb:
            u=(near-a[0][2])/(b[0][2]-a[0][2]); out.append((a[0]+u*(b[0]-a[0]),a[1]+u*(b[1]-a[1])))
    return [(np.array([out[0][0],out[k][0],out[k+1][0]]),np.array([out[0][1],out[k][1],out[k+1][1]])) for k in range(1,len(out)-1)]
def draw(c,t,mn,vw):
    sx=W/2+f*c[:,0]/c[:,2]; sy=H/2-f*c[:,1]/c[:,2]
    x0,x1=int(max(0,np.floor(sx.min()))),int(min(W-1,np.ceil(sx.max()))); y0,y1=int(max(0,np.floor(sy.min()))),int(min(H-1,np.ceil(sy.max())))
    if x0>x1 or y0>y1: return
    den=(sy[1]-sy[2])*(sx[0]-sx[2])+(sx[2]-sx[1])*(sy[0]-sy[2])
    if abs(den)<1e-9: return
    xs,ys=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
    w0=((sy[1]-sy[2])*(xs-sx[2])+(sx[2]-sx[1])*(ys-sy[2]))/den
    w1=((sy[2]-sy[0])*(xs-sx[2])+(sx[0]-sx[2])*(ys-sy[2]))/den
    w2=1-w0-w1; ins=(w0>=0)&(w1>=0)&(w2>=0)
    if not ins.any(): return
    iz=w0/c[0,2]+w1/c[1,2]+w2/c[2,2]; z=1/iz
    sub=zb[y0:y1+1,x0:x1+1]; ok=ins&(z<sub)
    if not ok.any(): return
    tn=None if os.environ.get('NOTEX') else mats.get(mn)
    if tn:
        uu=(w0*t[0,0]/c[0,2]+w1*t[1,0]/c[1,2]+w2*t[2,0]/c[2,2])*z; vv=(w0*t[0,1]/c[0,2]+w1*t[1,1]/c[1,2]+w2*t[2,1]/c[2,2])*z
        tx=tex(tn); th,tw=tx.shape[:2]
        px=tx[((1-vv[ok])%1*th).astype(int)%th,(uu[ok]%1*tw).astype(int)%tw]
        a=px[:,3]>0.3; col=px[:,:3]
    else:
        n=np.cross(vw[1]-vw[0],vw[2]-vw[0]); n=np.abs(n)/(np.linalg.norm(n)+1e-12)
        a=np.ones(ok.sum(),bool); col=np.tile(0.25+0.75*n,(ok.sum(),1))
    yy,xx=np.nonzero(ok); yy=yy[a];xx=xx[a]
    sub[yy,xx]=z[ok][a]; img[y0:y1+1,x0:x1+1][yy,xx]=col[a]

import os
CULL=os.environ.get('CULL')
for fi,(tri,mn) in enumerate(zip(F,FM)):
    c=C[tri[:3]]
    if CULL:
        vw=V[tri[:3]]; nn=np.cross(vw[1]-vw[0],vw[2]-vw[0])
        if np.dot(nn, vw.mean(0)-eye)>=0: continue
    if YMAX is not None and V[tri[:3],1].min()>YMAX: continue
    if (c[:,2]<near).all(): continue
    tt=T[tri[3:]] if len(T) else np.zeros((3,2))
    if (c[:,2]<near).any():
        for cc,t2 in clip(c,tt): draw(cc,t2,mn,V[tri[:3]])
    else: draw(c,tt,mn,V[tri[:3]])
Image.fromarray((np.clip(img,0,1)*255).astype(np.uint8)).save(outp); print('ok',outp)
