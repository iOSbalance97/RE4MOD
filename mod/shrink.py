import re,struct,subprocess
def fbits(v): return struct.unpack('>I',struct.pack('>f',v))[0]
POOL_ADDR=0x80002F40
pool=[]  # list of u32
def pidx(bits):
    if bits not in pool: pool.append(bits)
    return pool.index(bits)*4
def transform(text,consts,base_reg,base_off):
    text=re.sub(r'^(\w+):[ \t]+(\S)',r'\1:\n    \2',text,flags=re.M)
    L=text.split('\n'); out=[]; i=0
    def val(tok):
        tok=tok.strip()
        m=re.fullmatch(r'(\w+)@[hl]',tok)
        return m.group(1)
    while i<len(L):
        w=[x.split('#')[0].strip() for x in L[i:i+4]]
        def lfs_line(fc,bits): return f"    lfs   {fc},{base_off+pidx(bits)}({base_reg})"
        m=None
        if len(w)>=4:
            a=re.fullmatch(r'lis\s+(r\d+),(\S+)',w[0]); b=re.fullmatch(r'ori\s+(r\d+),(r\d+),(\S+)',w[1])
            c=re.fullmatch(r'stw\s+(r\d+),(\S+)\((r\d+)\)',w[2]); d=re.fullmatch(r'lfs\s+(f\d+),(\S+)\((r\d+)\)',w[3])
            if a and b and c and d and a.group(1)==b.group(1)==b.group(2)==c.group(1) and c.group(2)==d.group(2) and c.group(3)==d.group(3):
                hi,lo=a.group(2),b.group(3)
                if '@' in hi: bits=fbits(consts[val(hi)])
                else: bits=(int(hi,0)<<16)|int(lo,0)
                out.append(lfs_line(d.group(1),bits)); i+=4; continue
        if len(w)>=3:
            a=re.fullmatch(r'lis\s+(r\d+),(0x[0-9A-Fa-f]+)',w[0]); c=re.fullmatch(r'stw\s+(r\d+),(\S+)\((r\d+)\)',w[1]); d=re.fullmatch(r'lfs\s+(f\d+),(\S+)\((r\d+)\)',w[2])
            if a and c and d and a.group(1)==c.group(1) and c.group(2)==d.group(2) and c.group(3)==d.group(3):
                out.append(lfs_line(d.group(1),int(a.group(2),0)<<16)); i+=3; continue
            a=re.fullmatch(r'li\s+(r\d+),0',w[0])
            if a and c and d and a.group(1)==c.group(1) and c.group(2)==d.group(2) and c.group(3)==d.group(3):
                out.append(lfs_line(d.group(1),0)); i+=3; continue
        out.append(L[i]); i+=1
    return '\n'.join(out)
