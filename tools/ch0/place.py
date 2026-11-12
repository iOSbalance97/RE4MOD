import numpy as np,satdraw,math
from PIL import Image,ImageDraw
tris=satdraw.sat('/tmp/r111.bin')
fl=[t for t,k in tris if k in('f','s')]; walls=[t for t,k in tris if k=='w']
def floor_y(x,z):
    best=None
    for t in fl:
        (x0,y0,z0),(x1,y1,z1),(x2,y2,z2)=t
        d=(z1-z2)*(x0-x2)+(x2-x1)*(z0-z2)
        if abs(d)<1e-6: continue
        a=((z1-z2)*(x-x2)+(x2-x1)*(z-z2))/d; b=((z2-z0)*(x-x2)+(x0-x2)*(z-z2))/d; c=1-a-b
        if a>=-1e-4 and b>=-1e-4 and c>=-1e-4:
            y=a*y0+b*y1+c*y2
            if best is None or y<best: best=y
    return best
def segd(px,pz,ax,az,bx,bz):
    vx,vz=bx-ax,bz-az; L=vx*vx+vz*vz
    t=0 if L==0 else max(0,min(1,((px-ax)*vx+(pz-az)*vz)/L))
    return math.hypot(px-ax-t*vx,pz-az-t*vz)
WSEG=[]
for t in walls:
    ys=[p[1] for p in t]
    if min(ys)>1500: continue
    for i in range(3): WSEG.append((t[i][0],t[i][2],t[(i+1)%3][0],t[(i+1)%3][2]))
def walld(x,z): return min(segd(x,z,*s) for s in WSEG)
def snap(x,z,clear=900):
    best=None
    for r in range(0,4000,250):
        for k in range(max(1,int(2*math.pi*r/250))):
            a=2*math.pi*k/max(1,int(2*math.pi*r/250))
            px,pz=x+r*math.cos(a),z+r*math.sin(a)
            y=floor_y(px,pz)
            if y is None or y>600: continue
            if walld(px,pz)<clear: continue
            return (round(px),round(y),round(pz))
    return None
