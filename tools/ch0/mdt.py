import arc,struct,sys
def ch(v):
    if v==0x80: return ' '
    if 0xA7<=v<=0xC0: return chr(ord('A')+v-0xA7)
    if 0xC1<=v<=0xDA: return chr(ord('a')+v-0xC1)
    return {0x9a:'.',0x95:'!',0x123:"'"}.get(v,'{%x}'%v)
def msgs(path,L=5,tag='MDT',k=0):
    d=open(path,'rb').read(); e=arc.entries(d); idx=[i for i,(t,o) in enumerate(e) if t==tag][k]; o=e[idx][1]
    m=d[o:e[idx+1][1]] if idx+1<len(e) else d[o:]
    lo=struct.unpack('>6I',m[4:28]); b=lo[L]
    n=struct.unpack('>I',m[b+4:b+8])[0]; offs=struct.unpack('>%dI'%n,m[b+8:b+8+4*n]); out=[]
    for k in range(n):
        j=b+offs[k]; s=[]
        while j<len(m)-1:
            v=struct.unpack('>H',m[j:j+2])[0]; j+=2; s.append(v)
            if v==1: break
        out.append(s)
    return out
def text(s): return ''.join(ch(v) for v in s)
if __name__=='__main__':
    for i,s in enumerate(msgs(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 5)): print(i,text(s))
