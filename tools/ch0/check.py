import numpy as np,json,math,satdraw,aev
from PIL import Image,ImageDraw
fwd=np.load('map_fwd.npy')  # world->map: [x z 1] @ fwd
K=2.0
def P(x,z): v=np.array([x,z,1.0])@fwd; return (v[0]*K,v[1]*K)
im=Image.new('RGB',(int(540*K),int(355*K)),(40,32,24)); dr=ImageDraw.Draw(im)
tris=satdraw.sat('/tmp/r111.bin')
for t,k in tris:
    if k=='f':
        y=sum(p[1] for p in t)/3
        if y>1500: continue
        dr.polygon([P(p[0],p[2]) for p in t],fill=(150,130,105))
for t,k in tris:
    if k=='w' and min(p[1] for p in t)<1500: dr.line([P(p[0],p[2]) for p in t],fill=(90,60,40),width=1)
for n,s,a,p2 in json.load(open('guards.json')):
    q=P(s[0],s[2]); dr.ellipse([q[0]-6,q[1]-6,q[0]+6,q[1]+6],fill=(230,40,40))
    e=P(s[0]+1500*math.sin(a),s[2]+1500*math.cos(a)); dr.line([q,e],fill=(255,120,120),width=3)
    dr.text((q[0]+7,q[1]-7),n,fill=(255,255,255))
    if p2: r=P(p2[0],p2[2]); dr.line([q,r],fill=(255,200,0),width=1)
for nm,(x,z) in [('A',(-52144,22524)),('B',(19713,2003)),('C',(2850,-9534))]:
    q=P(x,z); dr.ellipse([q[0]-7,q[1]-7,q[0]+7,q[1]+7],outline=(60,140,255),width=3); dr.text((q[0]+9,q[1]),nm,fill=(60,180,255))
im.save('/tmp/check.png')
