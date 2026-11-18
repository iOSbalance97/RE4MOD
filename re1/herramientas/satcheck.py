"""Lee un SAT/EAT como lo hace el juego (cSat::operator= y cSat::blockInit) y comprueba que todo cuadra."""
import struct,sys,numpy as np
d=open(sys.argv[1],'rb').read()
if d[0]&0x80 and d[0]!=0xFF: d=d[struct.unpack_from('>I',d,4)[0]:]   # contenedor de sala
ver,_,nv,nn,ne,x8,npoly,nf,ns,nw,nb=struct.unpack_from('>BBHHHHHHHHH',d,0)
o=0x14
V=np.array(struct.unpack_from(f'>{3*nv}f',d,o)).reshape(-1,3); o+=12*nv
N=np.array(struct.unpack_from(f'>{3*nn}f',d,o)).reshape(-1,3); o+=12*nn
E=np.array(struct.unpack_from(f'>{3*ne}f',d,o)).reshape(-1,3); o+=12*ne
P=[struct.unpack_from('>3HH3HHI',d,o+0x14*i) for i in range(npoly)]; o+=0x14*npoly
assert ver in (0xFF,0x20) and npoly<=0x1FFF and nf+ns+nw==npoly
err=0
for i,p in enumerate(P):
    a,b,c=V[list(p[:3])]; n=np.cross(b-a,c-a); n/=np.linalg.norm(n)
    if np.abs(n-N[p[3]]).max()>1e-3: err+=1
    if np.abs(E[p[4]]-(b-a)).max()>1e-2 or np.abs(E[p[6]]-(a-c)).max()>1e-2: err+=1
    kind=0 if i<nf else 1 if i<nf+ns else 2
    if kind<2 and n[1]<0.5: err+=1
    if kind==2 and abs(n[1])>0.2: err+=1
# bloques encadenados
blk=o; seen=0; cover=set()
while True:
    mn=struct.unpack_from('>3f',d,blk); sz=struct.unpack_from('>3f',d,blk+12)
    f,s,w,flag=struct.unpack_from('>HHHH',d,blk+0x18); nxt=struct.unpack_from('>I',d,blk+0x20)[0]
    idx=struct.unpack_from(f'>{f+s+w}H',d,blk+0x24)
    ks=[0 if x<nf else 1 if x<nf+ns else 2 for x in idx]
    assert ks==sorted(ks) and ks.count(0)==f and ks.count(1)==s and ks.count(2)==w and max(idx)<npoly and flag==0
    cover|=set(idx); seen+=1
    if nxt==0: break
    blk+=nxt
assert seen==nb, (seen,nb)
print(f'{sys.argv[1]}: {npoly} polígonos ({nf} suelo, {ns} pendiente, {nw} pared), {nb} bloques, '
      f'polígonos en bloques {len(cover)}/{npoly}, errores {err}')
