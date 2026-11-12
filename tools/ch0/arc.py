import struct
def entries(d):
    n=struct.unpack('>I',d[0:4])[0]
    offs=struct.unpack('>%dI'%n,d[0x10:0x10+4*n])
    tags=[d[0x10+4*n+4*i:0x10+4*n+4*i+4].rstrip(b'\0').decode() for i in range(n)]
    return list(zip(tags,offs))
def get(d,tag,k=0):
    e=[o for t,o in entries(d) if t==tag]
    return e[k] if len(e)>k else None
