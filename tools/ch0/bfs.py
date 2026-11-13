import chk2,collections
def path(a,b,S=400,box=None):
    A=(round(a[0]/S),round(a[1]/S)); B=(round(b[0]/S),round(b[1]/S))
    prev={A:None}; q=collections.deque([A])
    while q:
        c=q.popleft()
        if c==B: break
        for dx,dz in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            n=(c[0]+dx,c[1]+dz)
            if n in prev: continue
            if box and not (box[0]<=n[0]*S<=box[2] and box[1]<=n[1]*S<=box[3]): continue
            if not chk2.seg((c[0]*S,c[1]*S),(n[0]*S,n[1]*S)) and chk2.place.walld(n[0]*S,n[1]*S)>450: prev[n]=c; q.append(n)
    if B not in prev: return None
    p=[];c=B
    while c: p.append((c[0]*S,c[1]*S)); c=prev[c]
    return p[::-1]
def simplify(p):
    out=[p[0]]; i=0
    while i<len(p)-1:
        j=len(p)-1
        while j>i+1 and chk2.seg(p[i],p[j]): j-=1
        out.append(p[j]); i=j
    return out
