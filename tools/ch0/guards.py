import numpy as np,math,place
inv=np.load('map_inv.npy')
def w(px,py): v=inv@np.array([px,py,1.0]); return v[0],v[1]
def wd(dx,dy): v=inv[:2,:2]@np.array([dx,dy],float); return v
# (map x, map y, look dir in map px (dx,dy), patrol to (map x,y) or None)
G=[('road',165,210,(1,0),(140,212)),
   ('cl1',225,130,(-1,-0.2),None),('cl2',242,158,(0.2,1),None),
   ('p1',290,172,(-1,0.3),None),('p2',312,170,(1,-0.5),None),('p3',305,190,(0,1),None),('p4',322,183,(1,0.6),None),
   ('s1',238,250,(0,1),None),('s2',262,278,(-0.6,-1),None),('s3',240,300,(0,1),None),
   ('ne',392,80,(-1,0.2),None)]
out=[]
for n,mx,my,d,pt in G:
    x,z=w(mx,my); s=place.snap(x,z)
    v=wd(*d); ang=math.atan2(v[0],v[1])
    p2=None
    if pt: p2=place.snap(*w(*pt))
    out.append((n,s,round(ang,3),p2)); print(n,(round(x),round(z)),'->',s,round(ang,2),p2)
import json; json.dump(out,open('guards.json','w'))
