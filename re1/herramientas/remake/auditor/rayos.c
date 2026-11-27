// rayos.c: trazado de rayos con BVH. Uso: rayos tris.bin orig.bin dirs.bin out.bin
// tris: float32 N*9; orig: float32 M*3; dirs: float32 K*3; out: uint8 M*K (1 = el rayo no choca con nada en 200 m)
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
typedef struct { float mn[3], mx[3]; int l, r, s, n; } Node;
static float *T; static int NT; static int *idx; static Node *nodes; static int nn = 0;
static float cen(int t, int a) { return (T[t*9+a] + T[t*9+3+a] + T[t*9+6+a]) / 3.f; }
static int build(int s, int n) {
  int id = nn++; Node *nd = &nodes[id];
  for (int a = 0; a < 3; a++) { nd->mn[a] = 1e30f; nd->mx[a] = -1e30f; }
  for (int i = s; i < s + n; i++) { int t = idx[i]; for (int k = 0; k < 3; k++) for (int a = 0; a < 3; a++) { float v = T[t*9+k*3+a]; if (v < nd->mn[a]) nd->mn[a] = v; if (v > nd->mx[a]) nd->mx[a] = v; } }
  nd->s = s; nd->n = n; nd->l = nd->r = -1;
  if (n <= 4) return id;
  int ax = 0; float ext = -1; for (int a = 0; a < 3; a++) if (nd->mx[a] - nd->mn[a] > ext) { ext = nd->mx[a] - nd->mn[a]; ax = a; }
  float mid = (nd->mn[ax] + nd->mx[ax]) / 2; int i = s, j = s + n - 1;
  while (i <= j) { if (cen(idx[i], ax) < mid) i++; else { int t = idx[i]; idx[i] = idx[j]; idx[j] = t; j--; } }
  int nl = i - s; if (nl == 0 || nl == n) nl = n / 2;
  int L = build(s, nl); int R = build(s + nl, n - nl);
  nodes[id].l = L; nodes[id].r = R; nodes[id].n = 0; return id;
}
static int hitbox(Node *nd, float *o, float *inv, float tmax) {
  float t0 = 0, t1 = tmax;
  for (int a = 0; a < 3; a++) { float ta = (nd->mn[a] - o[a]) * inv[a], tb = (nd->mx[a] - o[a]) * inv[a]; if (ta > tb) { float x = ta; ta = tb; tb = x; } if (ta > t0) t0 = ta; if (tb < t1) t1 = tb; if (t0 > t1) return 0; }
  return 1;
}
static float TH;
static int hittri(int t, float *o, float *d, float tmax) {
  float *a = &T[t*9], *b = &T[t*9+3], *c = &T[t*9+6]; float e1[3], e2[3], p[3], q[3], s[3];
  for (int k = 0; k < 3; k++) { e1[k] = b[k] - a[k]; e2[k] = c[k] - a[k]; }
  p[0] = d[1]*e2[2]-d[2]*e2[1]; p[1] = d[2]*e2[0]-d[0]*e2[2]; p[2] = d[0]*e2[1]-d[1]*e2[0];
  float det = e1[0]*p[0]+e1[1]*p[1]+e1[2]*p[2]; if (fabsf(det) < 1e-12f) return 0; float id = 1.f/det;
  for (int k = 0; k < 3; k++) s[k] = o[k] - a[k];
  float u = (s[0]*p[0]+s[1]*p[1]+s[2]*p[2]) * id; if (u < -1e-5f || u > 1+1e-5f) return 0;
  q[0] = s[1]*e1[2]-s[2]*e1[1]; q[1] = s[2]*e1[0]-s[0]*e1[2]; q[2] = s[0]*e1[1]-s[1]*e1[0];
  float v = (d[0]*q[0]+d[1]*q[1]+d[2]*q[2]) * id; if (v < -1e-5f || u + v > 1+1e-5f) return 0;
  float tt = (e2[0]*q[0]+e2[1]*q[1]+e2[2]*q[2]) * id; if (tt > 1e-4f && tt < tmax) { TH = tt; return 1; } return 0;
}
static int anyhit(float *o, float *d) {
  float inv[3]; for (int a = 0; a < 3; a++) inv[a] = 1.f / (fabsf(d[a]) > 1e-12f ? d[a] : 1e-12f);
  int st[256], sp = 0; st[sp++] = 0;
  while (sp) { Node *nd = &nodes[st[--sp]]; if (!hitbox(nd, o, inv, 200.f)) continue;
    if (nd->l < 0) { for (int i = nd->s; i < nd->s + nd->n; i++) if (hittri(idx[i], o, d, 200.f)) return 1; }
    else { st[sp++] = nd->l; st[sp++] = nd->r; } }
  return 0;
}
static float *rd(const char *f, long *n) { FILE *fp = fopen(f, "rb"); fseek(fp, 0, SEEK_END); long sz = ftell(fp); fseek(fp, 0, SEEK_SET); float *b = malloc(sz); fread(b, 1, sz, fp); fclose(fp); *n = sz / 4; return b; }
static float nearest(float *o, float *d) {
  float inv[3]; for (int a = 0; a < 3; a++) inv[a] = 1.f / (fabsf(d[a]) > 1e-12f ? d[a] : 1e-12f);
  float best = 1e30f; int st[256], sp = 0; st[sp++] = 0;
  while (sp) { Node *nd = &nodes[st[--sp]]; if (!hitbox(nd, o, inv, best < 200.f ? best : 200.f)) continue;
    if (nd->l < 0) { for (int i = nd->s; i < nd->s + nd->n; i++) if (hittri(idx[i], o, d, best < 200.f ? best : 200.f)) best = TH; }
    else { st[sp++] = nd->l; st[sp++] = nd->r; } }
  return best < 1e29f ? best : -1.f;
}
int main(int argc, char **argv) {
  if (argc > 5 && argv[5][0] == 't') {          // modo pares: orig[i] con dirs[i] -> distancia al primer choque
    long n; T = rd(argv[1], &n); NT = n / 9; long no; float *O = rd(argv[2], &no); no /= 3; long nd; float *D = rd(argv[3], &nd);
    idx = malloc(sizeof(int) * NT); for (int i = 0; i < NT; i++) idx[i] = i; nodes = malloc(sizeof(Node) * 2 * NT + 16); build(0, NT);
    float *o2 = malloc(4 * no); for (long i = 0; i < no; i++) o2[i] = nearest(&O[i*3], &D[i*3]);
    FILE *fp = fopen(argv[4], "wb"); fwrite(o2, 4, no, fp); fclose(fp); return 0; }
  long n; T = rd(argv[1], &n); NT = n / 9; long no; float *O = rd(argv[2], &no); no /= 3; long nd; float *D = rd(argv[3], &nd); nd /= 3;
  idx = malloc(sizeof(int) * NT); for (int i = 0; i < NT; i++) idx[i] = i; nodes = malloc(sizeof(Node) * 2 * NT + 16); build(0, NT);
  unsigned char *out = malloc(no * nd);
  for (long i = 0; i < no; i++) for (long k = 0; k < nd; k++) out[i*nd+k] = !anyhit(&O[i*3], &D[k*3]);
  FILE *fp = fopen(argv[4], "wb"); fwrite(out, 1, no * nd, fp); fclose(fp);
  fprintf(stderr, "tris %d origenes %ld rayos %ld\n", NT, no, nd); return 0;
}
