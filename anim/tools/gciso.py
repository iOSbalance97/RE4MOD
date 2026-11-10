# list / extract files from a GameCube ISO. usage: gciso.py iso [list|extract pattern outdir]
import struct,sys,os,fnmatch
iso=open(sys.argv[1],'rb'); h=iso.read(0x440)
fst,fsz=struct.unpack('>II',h[0x424:0x42c]); iso.seek(fst); t=iso.read(fsz)
n=struct.unpack('>I',t[8:12])[0]; st=n*12
def name(o): e=t.index(b'\0',st+o); return t[st+o:e].decode('latin1')
files=[]; stack=[(n,'')]
i=1; dirs={0:''}
ends=[]
path=['']; endstack=[n]
while i<n:
    while i>=endstack[-1]: endstack.pop(); path.pop()
    fl=t[i*12]; no=struct.unpack('>I',b'\0'+t[i*12+1:i*12+4])[0]; a,b=struct.unpack('>II',t[i*12+4:i*12+12])
    nm=path[-1]+name(no)
    if fl: path.append(nm+'/'); endstack.append(b)
    else: files.append((nm,a,b))
    i+=1
if sys.argv[2]=='list':
    for f,a,b in files: print(b,f)
else:
    pat,out=sys.argv[3],sys.argv[4]
    for f,a,b in files:
        if fnmatch.fnmatch(f,pat):
            p=os.path.join(out,f); os.makedirs(os.path.dirname(p),exist_ok=True); iso.seek(a); open(p,'wb').write(iso.read(b))
