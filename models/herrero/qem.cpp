// quadric edge-collapse decimation. in: nv nf target | float32 v[nv*3] | int32 f[nf*3] | int32 mat[nv]
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <queue>
#include <algorithm>
#include <cstdint>
using namespace std;
struct Q { double a[10]; Q(){for(int i=0;i<10;i++)a[i]=0;}
  void plane(double x,double y,double z,double d,double w){ double p[4]={x,y,z,d}; int k=0; for(int i=0;i<4;i++)for(int j=i;j<4;j++)a[k++]+=w*p[i]*p[j]; }
  void add(const Q&o){for(int i=0;i<10;i++)a[i]+=o.a[i];}
  double ev(const double*p)const{ double x=p[0],y=p[1],z=p[2];
    return a[0]*x*x+2*a[1]*x*y+2*a[2]*x*z+2*a[3]*x+a[4]*y*y+2*a[5]*y*z+2*a[6]*y+a[7]*z*z+2*a[8]*z+a[9]; } };
struct E { double c; int a,b,sa,sb; double p[3]; bool operator<(const E&o)const{return c>o.c;} };
int nv,nf,target; vector<double> V; vector<int> F,M; vector<Q> QV; vector<vector<int>> VF; vector<int> st; vector<char> fdead,vdead; vector<int> mark;
priority_queue<E> H; double matpen=6.0;
static void fnorm(const double*a,const double*b,const double*c,double*n){ double u[3]={b[0]-a[0],b[1]-a[1],b[2]-a[2]},w[3]={c[0]-a[0],c[1]-a[1],c[2]-a[2]};
  n[0]=u[1]*w[2]-u[2]*w[1]; n[1]=u[2]*w[0]-u[0]*w[2]; n[2]=u[0]*w[1]-u[1]*w[0]; }
static void push(int a,int b){ if(a==b)return; Q q=QV[a]; q.add(QV[b]); E e; e.a=a;e.b=b;e.sa=st[a];e.sb=st[b];
  const double*A=q.a; double m[3][3]={{A[0],A[1],A[2]},{A[1],A[4],A[5]},{A[2],A[5],A[7]}}, r[3]={-A[3],-A[6],-A[8]};
  double det=m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]);
  double best=1e300; double cand[4][3]; int nc=0; const double*pa=&V[3*a],*pb=&V[3*b];
  double tr=m[0][0]+m[1][1]+m[2][2];
  if(fabs(det)>1e-7*tr*tr*tr+1e-30){ double x=(r[0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(r[1]*m[2][2]-m[1][2]*r[2])+m[0][2]*(r[1]*m[2][1]-m[1][1]*r[2]))/det;
    double y=(m[0][0]*(r[1]*m[2][2]-m[1][2]*r[2])-r[0]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*r[2]-r[1]*m[2][0]))/det;
    double z=(m[0][0]*(m[1][1]*r[2]-r[1]*m[2][1])-m[0][1]*(m[1][0]*r[2]-r[1]*m[2][0])+r[0]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))/det;
    double L=sqrt((pa[0]-pb[0])*(pa[0]-pb[0])+(pa[1]-pb[1])*(pa[1]-pb[1])+(pa[2]-pb[2])*(pa[2]-pb[2]));
    double mx=0.5*(pa[0]+pb[0]),my=0.5*(pa[1]+pb[1]),mz=0.5*(pa[2]+pb[2]);
    if(sqrt((x-mx)*(x-mx)+(y-my)*(y-my)+(z-mz)*(z-mz))<2.0*L){cand[nc][0]=x;cand[nc][1]=y;cand[nc][2]=z;nc++;} }
  for(int k=0;k<3;k++){cand[nc][k]=pa[k];cand[nc+1][k]=pb[k];cand[nc+2][k]=0.5*(pa[k]+pb[k]);} nc+=3;
  for(int i=0;i<nc;i++){ double c=q.ev(cand[i]); if(c<best){best=c;e.p[0]=cand[i][0];e.p[1]=cand[i][1];e.p[2]=cand[i][2];} }
  if(best<0)best=0; double L2=(pa[0]-pb[0])*(pa[0]-pb[0])+(pa[1]-pb[1])*(pa[1]-pb[1])+(pa[2]-pb[2])*(pa[2]-pb[2]);
  e.c=best+1e-4*L2; if(M[a]!=M[b]) e.c=e.c*matpen+0.5*L2; H.push(e); }
int main(int argc,char**argv){ FILE*fi=fopen(argv[1],"rb"); int hd[3]; fread(hd,4,3,fi); nv=hd[0];nf=hd[1];target=hd[2];
  vector<float> vf(nv*3); fread(vf.data(),4,nv*3,fi); F.resize(nf*3); fread(F.data(),4,nf*3,fi); M.resize(nv); fread(M.data(),4,nv,fi); fclose(fi);
  V.assign(vf.begin(),vf.end()); QV.resize(nv); VF.resize(nv); st.assign(nv,0); fdead.assign(nf,0); vdead.assign(nv,0); mark.assign(nv,-1);
  vector<pair<pair<int,int>,int>> ed; ed.reserve(nf*3);
  for(int f=0;f<nf;f++){ int*t=&F[3*f]; double n[3]; fnorm(&V[3*t[0]],&V[3*t[1]],&V[3*t[2]],n); double l=sqrt(n[0]*n[0]+n[1]*n[1]+n[2]*n[2]);
    if(l<1e-12){fdead[f]=1;continue;} double w=l*0.5; n[0]/=l;n[1]/=l;n[2]/=l; double d=-(n[0]*V[3*t[0]]+n[1]*V[3*t[0]+1]+n[2]*V[3*t[0]+2]);
    for(int k=0;k<3;k++){QV[t[k]].plane(n[0],n[1],n[2],d,w); VF[t[k]].push_back(f); int a=t[k],b=t[(k+1)%3]; ed.push_back({{min(a,b),max(a,b)},f});} }
  sort(ed.begin(),ed.end());
  for(size_t i=0;i<ed.size();){ size_t j=i; while(j<ed.size()&&ed[j].first==ed[i].first)j++;
    int a=ed[i].first.first,b=ed[i].first.second;
    if(j-i==1){ int f=ed[i].second; int*t=&F[3*f]; double n[3]; fnorm(&V[3*t[0]],&V[3*t[1]],&V[3*t[2]],n);
      double e[3]={V[3*b]-V[3*a],V[3*b+1]-V[3*a+1],V[3*b+2]-V[3*a+2]}; double p[3]={e[1]*n[2]-e[2]*n[1],e[2]*n[0]-e[0]*n[2],e[0]*n[1]-e[1]*n[0]};
      double l=sqrt(p[0]*p[0]+p[1]*p[1]+p[2]*p[2]); if(l>1e-12){ p[0]/=l;p[1]/=l;p[2]/=l; double d=-(p[0]*V[3*a]+p[1]*V[3*a+1]+p[2]*V[3*a+2]);
        double w=10.0*(e[0]*e[0]+e[1]*e[1]+e[2]*e[2]); QV[a].plane(p[0],p[1],p[2],d,w); QV[b].plane(p[0],p[1],p[2],d,w);} }
    i=j; }
  for(size_t i=0;i<ed.size();){ size_t j=i; while(j<ed.size()&&ed[j].first==ed[i].first)j++; push(ed[i].first.first,ed[i].first.second); i=j; }
  int live=0; for(int f=0;f<nf;f++) if(!fdead[f]) live++;
  int stamp=0; vector<int> nb;
  while(live>target && !H.empty()){ E e=H.top(); H.pop(); int a=e.a,b=e.b; if(vdead[a]||vdead[b]||st[a]!=e.sa||st[b]!=e.sb) continue;
    // link condition
    stamp++; int shared=0, common=0; nb.clear();
    for(int f:VF[a]) if(!fdead[f]) for(int k=0;k<3;k++){int v=F[3*f+k]; if(v!=a&&v!=b) mark[v]=stamp;}
    for(int f:VF[a]) if(!fdead[f]) { int*t=&F[3*f]; if(t[0]==b||t[1]==b||t[2]==b) shared++; }
    vector<int> seen;
    for(int f:VF[b]) if(!fdead[f]) for(int k=0;k<3;k++){int v=F[3*f+k]; if(v!=a&&v!=b&&mark[v]==stamp){ mark[v]=-stamp; common++; } }
    if(common!=shared || shared==0) continue;
    // flip check
    bool bad=false;
    for(int pass=0;pass<2&&!bad;pass++){ int v=pass?b:a,o=pass?a:b; for(int f:VF[v]){ if(fdead[f])continue; int*t=&F[3*f]; if(t[0]==o||t[1]==o||t[2]==o)continue;
        double n0[3],n1[3]; const double*P[3]; for(int k=0;k<3;k++)P[k]=&V[3*t[k]]; fnorm(P[0],P[1],P[2],n0); for(int k=0;k<3;k++) if(t[k]==v)P[k]=e.p; fnorm(P[0],P[1],P[2],n1);
        double l0=sqrt(n0[0]*n0[0]+n0[1]*n0[1]+n0[2]*n0[2]),l1=sqrt(n1[0]*n1[0]+n1[1]*n1[1]+n1[2]*n1[2]);
        if(l1<1e-9||(n0[0]*n1[0]+n0[1]*n1[1]+n0[2]*n1[2])<0.25*l0*l1){bad=true;break;} } }
    if(bad) continue;
    // collapse b -> a
    for(int k=0;k<3;k++)V[3*a+k]=e.p[k]; QV[a].add(QV[b]);
    for(int f:VF[b]){ if(fdead[f])continue; int*t=&F[3*f]; if(t[0]==a||t[1]==a||t[2]==a){fdead[f]=1;live--;continue;} for(int k=0;k<3;k++) if(t[k]==b)t[k]=a; VF[a].push_back(f); }
    vector<int> keep; for(int f:VF[a]) if(!fdead[f]) keep.push_back(f); VF[a].swap(keep); VF[b].clear(); vdead[b]=1; st[a]++;
    stamp++; for(int f:VF[a]) for(int k=0;k<3;k++){int v=F[3*f+k]; if(v!=a&&mark[v]!=stamp){mark[v]=stamp; push(a,v);} }
  }
  vector<int> remap(nv,-1); int n2=0; vector<float> ov; vector<int> of,om;
  for(int f=0;f<nf;f++) if(!fdead[f]) for(int k=0;k<3;k++){int v=F[3*f+k]; if(remap[v]<0){remap[v]=n2++; ov.push_back(V[3*v]);ov.push_back(V[3*v+1]);ov.push_back(V[3*v+2]); om.push_back(M[v]);} of.push_back(remap[v]);}
  FILE*fo=fopen(argv[2],"wb"); int oh[2]={n2,(int)of.size()/3}; fwrite(oh,4,2,fo); fwrite(ov.data(),4,ov.size(),fo); fwrite(of.data(),4,of.size(),fo); fwrite(om.data(),4,om.size(),fo); fclose(fo);
  fprintf(stderr,"out %d verts %d tris\n",n2,oh[1]); return 0; }
