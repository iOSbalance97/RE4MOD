"""huecos.py sala.smd colision.obj : % de rayos que se escapan (no chocan en 60 m) desde puntos pisables, a la altura de la cámara"""
import sys, os, subprocess, numpy as np
sys.path.insert(0,'/home/claude/tools'); from uc_relleno_rays import rays; from hmap import load, floors, heights
smd, colp = sys.argv[1], sys.argv[2]; tag = sys.argv[3] if len(sys.argv)>3 else 'x'
d=f'/tmp/hue_{tag}'; subprocess.run(['python3','/home/claude/tools/smd2obj.py',smd,d],capture_output=True)
V,F=load(f'{d}/sala.obj'); tri=V[F]
Tc=floors(colp); rng=np.random.default_rng(1)
c=Tc.mean(1); ar=np.linalg.norm(np.cross(Tc[:,1]-Tc[:,0],Tc[:,2]-Tc[:,0]),axis=1)/2
# puntos: muestreo por área dentro de la caja del modelo
lo,hi=V.min(0),V.max(0); P=[]
idx=rng.choice(len(Tc),400,p=ar/ar.sum())
for k in idx:
    a,b=rng.random(2); 
    if a+b>1: a,b=1-a,1-b
    p=Tc[k,0]+a*(Tc[k,1]-Tc[k,0])+b*(Tc[k,2]-Tc[k,0])
    if (p>lo).all() and (p<hi).all():
        hv=heights(tri[np.abs(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])[:,1])>1e-6],p[0],p[2])
        if ((hv>p[1]+1.8)).any(): P.append(p)
    if len(P)>=8: break
az=np.radians(np.arange(0,360,30)); el=np.radians([-15,10,35,60])
D=np.array([[np.cos(e)*np.sin(a),np.sin(e),np.cos(e)*np.cos(a)] for a in az for e in el])
esc=0;tot=0;malos=[]
for p in P:
    O=np.tile(p+[0,1.6,0],(len(D),1)); t=rays(tri,O,D,60.0)
    e=(t>=60).sum(); esc+=e; tot+=len(D)
    if e: malos.append((p.round(1).tolist(), int(e)))
print(f'{tag}: puntos {len(P)}, rayos escapados {esc}/{tot} = {100*esc/max(tot,1):.1f}%  {malos[:4]}')
