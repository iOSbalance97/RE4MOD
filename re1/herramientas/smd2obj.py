"""Lee un SMD de RE4 (con las herramientas del decomp) y lo vuelca a OBJ para comprobarlo."""
import sys,struct,os
sys.path.insert(0,'/home/claude/re4src/tools/motion'); import meshbin,gxtex
from PIL import Image
smd=open(sys.argv[1],'rb').read(); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
ver,flag,nw,bt,tt,mt=struct.unpack_from('>BBHIII',smd,0)
tpl_o=tt+struct.unpack_from('>I',smd,tt)[0]; tx=gxtex.parse_tpl(smd[tpl_o:])
for i,t in enumerate(tx): Image.fromarray(t.decode()).save(f'{out}/t{i:03d}.png')
with open(f'{out}/m.mtl','w') as f:
    for i in range(len(tx)): f.write(f'newmtl t{i}\nmap_Kd t{i:03d}.png\n')
o_obj=open(f'{out}/sala.obj','w'); o_obj.write('mtllib m.mtl\n'); vb=1
nbin=max(struct.unpack_from('>B',smd,0x10+0x48*w+0x24)[0] for w in range(nw))+1
offs=[bt+struct.unpack_from('>I',smd,bt+4*i)[0] for i in range(nbin)]+[tpl_o]
for w in range(nw):
    pos=struct.unpack_from('>3f',smd,0x10+0x48*w); b=smd[0x10+0x48*w+0x24]
    m=meshbin.parse(smd[offs[b]:offs[b+1]])
    for i in range(len(m.vtx)):
        x,y,z=m.position(i); o_obj.write(f'v {(x+pos[0])/1000} {(y+pos[1])/1000} {(z+pos[2])/1000}\n')
    for s,t in m.tex: o_obj.write(f'vt {s/256} {1-t/256}\n')
    for p in m.parts:
        o_obj.write(f'usemtl t{p.tex_id}\n')
        for a,b2,c in p.triangles():
            o_obj.write(f'f {a[0]+vb}/{a[3]+vb} {b2[0]+vb}/{b2[3]+vb} {c[0]+vb}/{c[3]+vb}\n')
    vb+=len(m.vtx)
print('ok')
