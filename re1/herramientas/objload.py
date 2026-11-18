import numpy as np, os
def load(path):
    V=[];T=[];F=[];G=[];M=[];cur=None;grp=None;mtl=None
    for l in open(path):
        if l.startswith('v '): V.append(l.split()[1:4])
        elif l.startswith('vt '): T.append(l.split()[1:3])
        elif l.startswith('f '):
            p=[x.split('/') for x in l.split()[1:4]]; F.append([int(a[0])-1 for a in p]+[int(a[1])-1 for a in p]); M.append(cur); G.append(grp)
        elif l.startswith('usemtl'): cur=l.split()[1]
        elif l.startswith('o '): grp=l.split()[1]
        elif l.startswith('mtllib'): mtl=l.split()[1]
    mats={};m=None
    for l in open(os.path.join(os.path.dirname(path),mtl)):
        if l.startswith('newmtl'): m=l.split()[1]; mats[m]=None
        elif l.startswith('map_Kd'): mats[m]=l.split(None,1)[1].strip()
    return np.array(V,float),np.array(T,float),np.array(F,int),np.array(M),np.array(G),mats
