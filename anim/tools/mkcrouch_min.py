# Crouch pose tables for crouch.c: per frame, the local rotation (Euler ZYX, s16 in 1e-4 rad) of
# every body part, and the root height (mm). Clips are turned about Y so that loops move the way
# their name says (fwd +z, left +x, right -x) and the others face where Leon faces.
import numpy as np, math
from conv import convert
from leon import PAR
from mot import euler_zyx
D='/home/claude/re4mod/anim/mixamo/crouch/'
BODY=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,113,114,117,118]
def Ry(deg):
    a=math.radians(deg); c,s=math.cos(a),math.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
from leon import OFF
TARGET_Y=760.0          # all crouch loops sit at this mean root height (legs re-solved, feet kept)
def rot_between(u,v):
    u=u/np.linalg.norm(u); v=v/np.linalg.norm(v); c=float(np.dot(u,v)); ax=np.cross(u,v); s=np.linalg.norm(ax)
    if s<1e-9: return np.eye(3)
    ax/=s; K=np.array([[0,-ax[2],ax[1]],[ax[2],0,-ax[0]],[-ax[1],ax[0],0]])
    return np.eye(3)+K*s+K@K*(1-c)
def relevel(fr,target):
    my=np.mean([x[2][0][1] for x in fr]); d=target-my; out=[]
    for vals,R,P in fr:
        R=list(R); P=[p.copy() for p in P]
        for hip,knee,ank in ((18,19,20),(22,23,24)):
            a=np.linalg.norm(OFF[knee]); b=np.linalg.norm(OFF[ank])
            H0=P[hip].copy(); K0=P[knee].copy(); A=P[ank].copy(); H=H0+np.array([0,d,0])
            L=np.linalg.norm(A-H); L=min(L,a+b-0.5); u=(A-H)/np.linalg.norm(A-H); u0=(A-H0)/np.linalg.norm(A-H0)
            v=(K0-H0)-u0*np.dot(K0-H0,u0); v=v-u*np.dot(v,u); v/=np.linalg.norm(v)
            x=(a*a-b*b+L*L)/(2*L); h=np.sqrt(max(a*a-x*x,0)); K=H+u*x+v*h
            R[hip]=rot_between(K0-H0,K-H)@R[hip]; R[knee]=rot_between(A-K0,A-K)@R[knee]
            P[hip]=H; P[knee]=K
        P[0]=P[0]+np.array([0,d,0])
        out.append((vals,R,P))
    return out,d
ARMS=[5,6,7,8,9,10,11,12,13,14,15,16,113,114,117,118]
def facing(fr):
    v=[np.cross(x[2][11]-x[2][5],[0,1,0]) for x in fr]; v=np.mean(v,0); return math.degrees(math.atan2(v[0],v[2]))
def move(fr):
    d=fr[-1][2][0]-fr[0][2][0]; return math.degrees(math.atan2(d[0],d[2])), float(np.hypot(d[0],d[2]))
