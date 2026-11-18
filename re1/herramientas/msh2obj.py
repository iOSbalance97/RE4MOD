"""Convierte un .msh de The Movies a OBJ+MTL+PNG.  uso: msh2obj.py entrada.msh carpeta_texturas carpeta_salida"""
import sys,os,numpy as np
sys.path.insert(0,os.path.dirname(__file__)); import tmmsh
from PIL import Image
src,texdir,out=sys.argv[1:4]; os.makedirs(out,exist_ok=True)
m=tmmsh.load(src); PERM=eval(os.environ.get('PERM','[1,2,0]')); AX=eval(os.environ.get('AX','[0,1,2]')); SG=np.array(eval(os.environ.get('SG','[1,1,1]')),float); M=m['M']; name=os.path.splitext(os.path.basename(src))[0].replace(' ','_')
texlist={f.lower():f for f in os.listdir(texdir)}
missing=set(); used={}
mtl=open(os.path.join(out,name+'.mtl'),'w'); obj=open(os.path.join(out,name+'.obj'),'w')
obj.write(f'mtllib {name}.mtl\n')
for mi,mt in enumerate(m['mats']):
    mtl.write(f'newmtl mat{mi:03d}\nKd 1 1 1\n')
    if mt['tex'] is not None and mt['tex']<len(m['texs']):
        t=m['texs'][mt['tex']]; png=os.path.splitext(t)[0].replace(' ','_')+'.png'
        if t.lower() in texlist:
            if png not in used:
                im=Image.open(os.path.join(texdir,texlist[t.lower()])); im.save(os.path.join(out,png)); used[png]=im.mode
            mtl.write(f'map_Kd {png}\n')
            if used[png] in('RGBA','LA'): mtl.write(f'map_d {png}\n')
        else: missing.add(t)
vb=1
for si,s in enumerate(m['subs']):
    v=s['v']
    if os.environ.get('DEC','bb')=='bb': bb=s['bb']; P=bb[:3]+v['p'].view('<u2')[:,PERM]/65535.*(bb[3:]-bb[:3])
    else: P=(v['p']/32767.)@M[:3]+M[3]
    a,b,c,d=s['uvr'][:4]; q=v['uv']/65535.
    U=a+(b-a)*q[:,0]; V=c+(d-c)*q[:,1]
    obj.write(f'o sub{si:03d}\nusemtl mat{s["mat"]:03d}\n')
    obj.write(''.join(f'v {x:.5f} {y:.5f} {z:.5f}\n' for x,y,z in P[:,AX]*SG))
    obj.write(''.join(f'vt {u:.5f} {1-w:.5f}\n' for u,w in zip(U,V)))
    obj.write(''.join(f'f {i+vb}/{i+vb} {j+vb}/{j+vb} {k+vb}/{k+vb}\n' for i,j,k in s['idx'].astype(np.int64)))
    vb+=len(P)
print(name,'subs',len(m['subs']),'tris',sum(len(s['idx']) for s in m['subs']),'texturas',len(used),'faltan',sorted(missing))
