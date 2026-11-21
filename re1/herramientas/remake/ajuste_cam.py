import sys; sys.path.insert(0,'/home/claude/re1gc/work'); import remake, numpy as np
from PIL import Image, ImageFilter
def aristas(V,T):
    E={}
    n=np.cross(V[T[:,1]]-V[T[:,0]],V[T[:,2]]-V[T[:,0]]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-9
    for i,t in enumerate(T):
        for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
            k=(min(a,b),max(a,b)); E.setdefault(k,[]).append(i)
    out=[]
    for (a,b),fs in E.items():
        if len(fs)==1 or (len(fs)==2 and abs(np.dot(n[fs[0]],n[fs[1]]))<0.8): out.append((a,b))   # bordes y pliegues
    return np.array(out)
def grad(im):
    g=np.asarray(im.convert('L').filter(ImageFilter.FIND_EDGES),float); return g
def puntuar(cam,V,E,g,proj):
    p,z=proj(cam,V)
    s=0;n=0
    for a,b in E:
        if z[a]<50 or z[b]<50: continue
        for t in np.linspace(0,1,12):
            q=p[a]*(1-t)+p[b]*t; x,y=int(q[0]),int(q[1])
            if 1<=x<511 and 1<=y<447: s+=g[y-1:y+2,x-1:x+2].max(); n+=1
    return s/max(n,1), n
