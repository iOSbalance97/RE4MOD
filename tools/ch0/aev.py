import struct,sys,arc
def areas(path):
    d=open(path,'rb').read(); o=arc.get(d,'AEV')
    mag=d[o:o+4]; ver,num=struct.unpack('>HH',d[o+4:o+8]); out=[]
    for i in range(num):
        r=d[o+0x10+i*0x9C:o+0x10+(i+1)*0x9C]
        typ=r[5]; fl,h,rad=struct.unpack('>3f',r[8:20])
        if typ==1: shape=('cyl',struct.unpack('>2f',r[0x14:0x1C]))
        else: shape=('xz4',[struct.unpack('>2f',r[0x14+8*k:0x1C+8*k]) for k in range(4)])
        rec=dict(i=i,id=r[0x35],no=r[0x36],areatype=typ,floor=fl,h=h,shape=shape,act=r[0x4A],trg=r[0x38])
        if r[0x35]==1:
            x,y,z,a=struct.unpack('>4f',r[0x5C:0x6C]); rec['door']=(hex(r[0x6C]<<8|r[0x6D]),round(x),round(y),round(z),round(a,3),'key',r[0x6E],r[0x6F])
        out.append(rec)
    return out
if __name__=='__main__':
    for a in areas(sys.argv[1]):
        if 'door' in a or (len(sys.argv)>2):
            sh=a['shape']; c=sh[1] if sh[0]=='cyl' else tuple(round(sum(p[k] for p in sh[1])/4) for k in (0,1))
            print(a['i'],'id',a['id'],'no',a['no'],'act',a['act'],'floor',round(a['floor']),'center',tuple(round(v) for v in c), a.get('door',''))
