import place
def ys(x,z):
    out=[]
    for t in place.fl:
        (x0,y0,z0),(x1,y1,z1),(x2,y2,z2)=t
        d=(z1-z2)*(x0-x2)+(x2-x1)*(z0-z2)
        if abs(d)<1e-6: continue
        a=((z1-z2)*(x-x2)+(x2-x1)*(z-z2))/d; b=((z2-z0)*(x-x2)+(x0-x2)*(z-z2))/d; c=1-a-b
        if a>=-1e-4 and b>=-1e-4 and c>=-1e-4: out.append(round(a*y0+b*y1+c*y2))
    g=[y for y in out if y<3200]
    return max(g) if g else None
def inter(p,q,r,s):
    def cr(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    return cr(p,q,r)*cr(p,q,s)<0 and cr(r,s,p)*cr(r,s,q)<0
def seg(a,b):
    return [s for s in place.WSEG if inter(a,b,(s[0],s[1]),(s[2],s[3]))]
