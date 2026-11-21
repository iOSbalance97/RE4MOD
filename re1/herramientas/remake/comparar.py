"""comparar.py dirA dirB salida.jpg : vistas de las cámaras del REmake y vistas inversas a la altura del jugador"""
import json,numpy as np,subprocess,sys,os
from PIL import Image
A,B,out=sys.argv[1:4]; m=json.load(open(f'{B}/meta.json'))
n=len(m['camaras']); idx=sorted(set(np.linspace(0,n-1,min(4,n)).astype(int)))
vs=[]
for ci in idx:
    c=m['camaras'][ci]; e=np.array(c['ojo'])/1000; o=np.array(c['obj'])/1000
    a=o.copy(); a[1]=e[1]*0+1.6+min(e[1],o[1]); b=e.copy(); b[1]=a[1]-0.2
    vs+= [(tuple(a),tuple(b)),(tuple(e),tuple(o))]
M=Image.new('RGB',(800,300*len(vs)))
for k,(e,o) in enumerate(vs):
    for j,d in enumerate([A,B]):
        p=f'/tmp/_cmp_{j}_{k}.png'
        subprocess.run(['python3','/home/claude/tools/render.py',f'{d}/sala.obj',p,str(e),str(o),'60','400','300'],capture_output=True)
        try: M.paste(Image.open(p).convert('RGB'),(j*400,k*300))
        except Exception: pass
M.save(out,quality=80)
