# Writes a baked main.dol into copies of the clean PAL ISOs (DOL moved into the free gap after the
# FST, header 0x420 updated) and makes xdelta patches. Usage: mkiso.py TAG
import struct,sys,os,shutil,hashlib,subprocess
TAG=sys.argv[1]
dol=open(f'bake/main_{TAG}.dol','rb').read()
CLEAN={'disc1':'9e58a28b32cbbddd215f2fcbecb79c41812f5f54','disc2':'5dc7461496040f6656ecd7e187ab9f54d05d58fd'}
NEW_OFF=0x240000
os.makedirs('out',exist_ok=True)
for n in ('disc1','disc2'):
    src=f'/home/claude/disc/iso/{n}.iso'; dst=f'out/RE4_PAL_{n}_{TAG}.iso'
    with open(src,'rb') as f:
        h=f.read(0x440)
        dolo,fst,fsz=struct.unpack('>III',h[0x420:0x42c])
        f.seek(fst); t=f.read(fsz)
        cnt=struct.unpack('>I',t[8:12])[0]
        first=min(struct.unpack('>III',t[i*12:i*12+12])[1] for i in range(1,cnt) if not t[i*12])
        assert fst+fsz<=NEW_OFF and NEW_OFF+len(dol)<=first
        f.seek(dolo); assert hashlib.sha1(f.read(0x216120)).hexdigest()=='3467e9e0b0659cf7c4d35acb5661ad4848ea147c'
        f.seek(NEW_OFF); gap=f.read(len(dol))
    shutil.copyfile(src,dst)
    with open(dst,'r+b') as f:
        f.seek(0x420); f.write(struct.pack('>I',NEW_OFF))
        f.seek(NEW_OFF); f.write(dol)
    pat=f'out/RE4_PAL_{n}_{TAG}.xdelta'
    if os.path.exists(pat): os.remove(pat)
    subprocess.check_call(['/home/claude/tools/xdelta3','-e','-9','-S','djw','-s',src,dst,pat])
    print(n,'gap was zero' if gap==b'\0'*len(dol) else 'gap had data', 'patch',os.path.getsize(pat),'bytes')
