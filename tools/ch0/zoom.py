import numpy as np, place, sys
from PIL import Image, ImageDraw
f=np.load('map_fwd.npy')
def P(x,z): v=np.array([x,z,1.0])@f; return (v[0]*2,v[1]*2)
def zoom(x0,z0,x1,z1,out,marks=(),S=4):
    im=Image.open('plan_c008.png').convert('RGB')
    a=P(x0,z0); b=P(x1,z1)
    box=(int(min(a[0],b[0])),int(min(a[1],b[1])),int(max(a[0],b[0])),int(max(a[1],b[1])))
    im=im.crop(box).resize(((box[2]-box[0])*S,(box[3]-box[1])*S))
    d=ImageDraw.Draw(im)
    def Q(x,z): p=P(x,z); return ((p[0]-box[0])*S,(p[1]-box[1])*S)
    for s in place.WSEG: d.line([Q(s[0],s[1]),Q(s[2],s[3])],fill=(0,255,255),width=2)
    for gx in range(int(x0)//1000*1000,int(x1)+1,1000):
        for gz in range(int(z0)//1000*1000,int(z1)+1,1000):
            q=Q(gx,gz); d.ellipse([q[0]-1,q[1]-1,q[0]+1,q[1]+1],fill=(255,255,255))
            if gx%2000==0 and gz%2000==0: d.text((q[0]+3,q[1]-5),'%g,%g'%(gx/1000,gz/1000),fill=(255,255,0))
    for (x,z,t,c) in marks:
        q=Q(x,z); d.ellipse([q[0]-5,q[1]-5,q[0]+5,q[1]+5],outline=c,width=2); d.text((q[0]+6,q[1]+4),t,fill=c)
    im.save(out)
