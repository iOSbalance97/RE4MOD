# Bakes the v26 Gecko codes into main.dol (PAL G4BP08 rev 0) and builds patched ISOs.
# Layout: new data + text sections placed at the old ArenaLo (0x802BD5E0, free slack up to the
# fixed DVD buffer at 0x80300000 per SystemMemInit), and OSInit's __ArenaLo constants are bumped.
import struct,subprocess,re,sys,shutil,os,zlib
sys.path.insert(0,'.')
import shrink
from shrink import transform
B='/home/claude/tools/binutils/powerpc-eabi-'
TAG=sys.argv[1] if len(sys.argv)>1 else 'b1'
BASE=0x802BD5E0          # retail __ArenaLo (OSInit 0x80069160 / 0x80069198)
HI=BASE>>16
VARS_SIZE=0x28
def asm(src,name):
    open(name+'.gen.s','w').write(src)
    subprocess.check_call([B+'as','-mgekko','-mregnames',name+'.gen.s','-o',name+'.o'])
    subprocess.check_call([B+'objcopy','-O','binary','-j','.text',name+'.o',name+'.bin'])
    return open(name+'.bin','rb').read()
P_move=dict(KTURN=0.35,WALK_K=48.0/72,STRAFE_K=-42.0/72,EASE=0.15,MAXTURN=0.12,FOLLOW=0.97,RELOAD_K=-0.0012,QUICK=2.6,
       BACKANG=1.75,BACKLIM=0.8,WAISTMAX=1.0,WAISTRATE=0.25,STRAFE_SMOOTH=0.55)
P_cf={'YAW_K':-0.0012,'PITCH_K':0.0016}
P_cam={'CAM_BACK':0.25,'CAM_FOV':1.10,'DEASE':0.12,'DMIN':1500.0,'WSTEP':0.15}
P_pr={'RANGE2':2200.0**2}
LOW=0.3; P_aim={'YAWK':1.05,'PITCHK':0.7,'LOWK':LOW,'CURVEK':(1-LOW)/59.0}
def addrs(src,PB,VB):
    def rep(m):
        val=eval(m.group(0).replace('VB',str(VB)).replace('PB',str(PB)))
        return hex(val & 0xFFFF if val>=0x80000000 else val)
    src=re.sub(r'(VB|PB)(\s*[+-]\s*(0x[0-9A-Fa-f]+|\d+|VB|PB))*',rep,src)
    # every `lis rX,0x8000` in these sources is the high half of VB/PB (checked by grep)
    return re.sub(r'(lis\s+r\d+,)0x8000\b',lambda m:m.group(1)+hex(HI),src)
POOLSET="    lis   r10,0x8000\n    ori   r10,r10,PB        # constant pool\n"
def build(PB,VB):
    shrink.pool.clear()
    mv=transform(open('m14.s').read().replace('PWINDOW','15'),P_move,'r30',PB-VB)
    cf=POOLSET+transform(open('camfree.s').read(),P_cf,'r10',0)
    cm=POOLSET+transform(open('c12.s').read(),P_cam,'r10',0)
    pr=POOLSET+transform(open('p13.s').read(),P_pr,'r10',0)
    am=transform(open('a12.s').read(),P_aim,'r11',0)
    if "(r1)" not in cm.replace("stwu  r1,-0x10(r1)","").replace("stwu  r1,-432(r1)",""):
        cm=cm.replace("    stwu  r1,-0x10(r1)\n","").replace("    addi  r1,r1,0x10\n","")
    srcs={'ns':open('nosnap.s').read(),'mv':mv,'cf':cf,'cm':cm,'pr':pr,'am':am,'dot':open('dot2.s').read()}
    return {k:addrs(s,PB,VB) for k,s in srcs.items()}, list(shrink.pool)
_,pool=build(BASE,BASE+0x100)
PB=BASE; VB=PB+4*len(pool)
srcs,pool2=build(PB,VB); assert pool2==pool
for k,s in srcs.items(): assert '0x8000\n' not in s and 'VB' not in re.sub(r'#.*','',s), k
DATA=b''.join(struct.pack('>I',x) for x in pool)+b'\0'*VARS_SIZE
TEXT_ADDR=(VB+VARS_SIZE+0x1F)&~0x1F
HOOKS=[('mv',0x80051F30),('cf',0x800BCD6C),('cm',0x800BDAE4),('pr',0x800D0478),('am',0x80146D50),('dot',0x8003EB6C),('ns',0x800BEE88)]
def bran(src,dst):
    d=dst-src; assert -0x2000000<=d<0x2000000 and d%4==0
    return 0x48000000|(d&0x03FFFFFC)
text=b''; hookw={}
for k,a in HOOKS:
    code=asm(srcs[k],'k_'+k)
    start=TEXT_ADDR+len(text)
    code+=struct.pack('>I',bran(start+len(code),a+4))   # Gecko C2 return branch
    text+=code
    hookw[a]=bran(a,start)
    while len(text)%0x20: text+=b'\0'
END=(TEXT_ADDR+len(text)+0x1F)&~0x1F
assert END<0x80300000 and END<(HI+1)<<16
W04={0x80146D60:0x7009FFFF,0x80146E50:0x880A0003,0x80146EEC:0x880A0003,0x80147004:0x881ED0D2,0x801470AC:0x881ED0D2,0x8014713C:0x881ED0D2,
     0x80146E04:0x38000000,0x80146EA0:0x38000000,0x80146FD8:0x38000000,0x80147070:0x38000000,0x80147104:0x38000000,
     0x80146D8C:0xC0091FA8,0x800BCD5C:0x813E0788,0x800BCD64:0xC0090030,0x80157A20:0x60000000,0x80157A2C:0x48000060}
# __ArenaLo: lis r3,hi / addi r3,r3,lo at both sites
ha=(END+0x8000)>>16; lo=END-(ha<<16)
W04[0x80069160]=0x3C600000|ha; W04[0x80069164]=0x38630000|(lo&0xFFFF)
W04[0x80069198]=0x3C600000|ha; W04[0x8006919C]=0x38630000|(lo&0xFFFF)
def patch_dol(dol):
    d=bytearray(dol)
    off=list(struct.unpack('>18I',d[0:72]));addr=list(struct.unpack('>18I',d[72:144]));sz=list(struct.unpack('>18I',d[144:216]))
    def fo(a):
        for i in range(18):
            if sz[i] and addr[i]<=a<addr[i]+sz[i]: return off[i]+a-addr[i]
        raise Exception(hex(a))
    expect={0x80069160:0x3C60802C,0x80069164:0x3863D5E0,0x80069198:0x3C60802C,0x8006919C:0x3863D5C0}
    for a,v in expect.items(): assert struct.unpack('>I',d[fo(a):fo(a)+4])[0]==v,hex(a)
    for a,v in list(W04.items())+list(hookw.items()): d[fo(a):fo(a)+4]=struct.pack('>I',v)
    assert sz[2]==0 and sz[12]==0
    end=(len(d)+0x1F)&~0x1F; d+=b'\0'*(end-len(d))
    off[12],addr[12],sz[12]=len(d),PB,(len(DATA)+0x1F)&~0x1F; d+=DATA+b'\0'*(sz[12]-len(DATA))
    off[2],addr[2],sz[2]=len(d),TEXT_ADDR,len(text); d+=text
    d[0:72]=struct.pack('>18I',*off); d[72:144]=struct.pack('>18I',*addr); d[144:216]=struct.pack('>18I',*sz)
    return bytes(d)
orig=open('/home/claude/disc/ext1/sys/main.dol','rb').read()
import hashlib
assert hashlib.sha1(orig).hexdigest()=='3467e9e0b0659cf7c4d35acb5661ad4848ea147c'
new=patch_dol(orig)
os.makedirs('bake',exist_ok=True)
open(f'bake/main_{TAG}.dol','wb').write(new)
print(f"pool {len(pool)} at {PB:#x}, vars {VB:#x}, text {TEXT_ADDR:#x}+{len(text):#x}, new ArenaLo {END:#x}; dol {len(orig):#x}->{len(new):#x}")
for k,a in HOOKS: print(f"  hook {k} {a:#x} -> {hookw[a]:#010x}")
