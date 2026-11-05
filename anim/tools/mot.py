import struct, math
import numpy as np
KSIZE={0:12,1:8,2:6,4:10,5:6,6:4,8:9,9:5,10:3,15:4}
def _f(b,o): return struct.unpack('>f',b[o:o+4])[0]
def _s(b,o): return struct.unpack('>h',b[o:o+2])[0]*1e-4
def _c(b,o): return struct.unpack('>b',b[o:o+1])[0]*1e-4
def key(fmt,d,i):
    # returns value, tin, tout for key i
    if fmt==0: o=i*12; return _f(d,o),_f(d,o+4),_f(d,o+8)
    if fmt==1: o=i*8; return _f(d,o),_s(d,o+4),_s(d,o+6)
    if fmt==2: o=i*6; return _f(d,o),_c(d,o+4),_c(d,o+5)
    if fmt==4: o=i*10; return _s(d,o),_f(d,o+2),_f(d,o+6)
    if fmt==5: o=i*6; return _s(d,o),_s(d,o+2),_s(d,o+4)
    if fmt==6: o=i*4; return _s(d,o),_c(d,o+2),_c(d,o+3)
    if fmt==8: o=i*9; return _c(d,o),_f(d,o+1),_f(d,o+5)
    if fmt==9: o=i*5; return _c(d,o),_s(d,o+1),_s(d,o+3)
    if fmt==10: o=i*3; return _c(d,o),_c(d,o+1),_c(d,o+2)
    if fmt==15: return _f(d,i*4),0,0
    raise ValueError(fmt)
def parse(m):
    mf=struct.unpack('>H',m[0:2])[0]&0x3fff; n=m[2]
    kinds=struct.unpack('>%dH'%n,m[3:3+2*n]); nos=list(m[3+2*n:3+3*n])
    t=(3+3*n+3)&~3; t+=4
    offs=struct.unpack('>%dI'%n,m[t:t+4*n])
    chans=[]
    for i in range(n):
        fmt=kinds[i]>>12; p=offs[i]; axes=[]
        for ax in range(3):
            k=struct.unpack('>H',m[p:p+2])[0]
            fr=struct.unpack('>%dH'%k,m[p+2:p+2+2*k]); d=m[p+2+2*k:]
            keys=[(fr[j],)+key(fmt,d,j) for j in range(k)]
            axes.append(keys); p=p+2+2*k+KSIZE[fmt]*k
        chans.append(dict(no=nos[i],kind=kinds[i]&0xff,ch=(kinds[i]>>8)&0xf,fmt=fmt,axes=axes))
    return mf,chans
def hermite(x0,x1,v0,v1,t):
    t2=t*t;t3=t*t2;h01=-2*t3+3*t2;h11=t3-t2;h10=h11-t2+t;h00=1-h01
    return x0*h00+x1*h01+v0*h10+v1*h11
def sample(keys,f):
    if f<=keys[0][0]: return keys[0][1]
    if f>=keys[-1][0]: return keys[-1][1]
    for a,b in zip(keys,keys[1:]):
        if a[0]==f: return a[1]
        if a[0]<f<b[0]:
            # out tangent of a = a[3]; in tangent of b = b[2]
            return hermite(a[1],b[1],a[3],b[2],(f-a[0])/(b[0]-a[0]))
    return keys[-1][1]
def eval_chan(c,f): return [sample(ax,f) for ax in c['axes']]
def rotm(a):
    x,y,z=a; sx,sy,sz=math.sin(x),math.sin(y),math.sin(z); cx,cy,cz=math.cos(x),math.cos(y),math.cos(z)
    Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rz@Ry@Rx
def euler_zyx(R):
    # inverse of Rz Ry Rx
    sy=-R[2,0]; sy=max(-1,min(1,sy)); y=math.asin(sy)
    if abs(sy)<0.9999:
        x=math.atan2(R[2,1],R[2,2]); z=math.atan2(R[1,0],R[0,0])
    else:
        x=math.atan2(-R[1,2],R[1,1]); z=0.0
    return [x,y,z]
