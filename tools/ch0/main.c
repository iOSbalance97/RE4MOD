#include "rt.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
uint8_t* M;
u32 r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,r15,r16,r17,r18,r19,r20,r21,r22,r23,r24,r25,r26,r27,r28,r29,r30,r31,ctr; int cr; double f2,f3,f4,f5;
void yz2Decode_Decode(void);
#define EV 0x100
#define CTX 0x200
static u32 fre;
static u32 alloc(u32 n){u32 p=fre; fre+=n; return p;}
static void freq_reset(u32 fd){ /* Yz2Freq at fd: freq 0, max 4, bits 8, range 0xC, cum 0x10, n 0x14, acc 0x18 */
  u32 n=LW(fd+0x14), f=LW(fd); int i, bits=0; for(i=0;i<(int)n;i++) SH(f+2*i,1);
  u32 max=n;
  if (max >= (1u<<bits)) { do { bits++; if (bits>14) break; } while (max >= (1u<<bits)); }
  SW(fd+8,bits); SW(fd+4,max); SW(fd+0xC,1u<<bits); SW(fd+0x18,0);
}
static void model_setup(u32 m,u32 d,u32 cnt){ /* Yz2Model: dec 0, fd 4, table 0x20 */
  u32 fd=m+4; int i,j=0; u32 s=0;
  SW(m,d); SW(fd+0x14,cnt);
  u32 f=alloc(cnt*2); memset(M+f,0,cnt*2); SW(fd,f);
  u32 c=alloc(cnt*4); SW(fd+0x10,c);
  for(i=0;i<0x8000;i++){ SH(f+2*j,LH(f+2*j)+1); j++; if(j>=(int)cnt) j=0; }
  for(i=0;i<(int)cnt;i++){ SH(c+4*i,LH(f+2*i)); SH(c+4*i+2,s); s=(s+LH(f+2*i))&0xFFFF; }
  freq_reset(fd);
  SW(m+0x20,alloc(0x20000));
}
int main(int argc,char**argv){
  FILE*fp=fopen(argv[1],"rb"); fseek(fp,0,2); long n=ftell(fp); fseek(fp,0,0);
  M=calloc(1,0x6000000); u32 SRC=0x1000; fread(M+SRC,1,n,fp); fclose(fp);
  u32 hdr=SRC+strtoul(argv[2],0,0);
  char*p=(char*)M+hdr; u32 size0=strtoul(p,&p,16); p++; u32 size1=strtoul(p,&p,16);
  u32 src=(((u32)((uint8_t*)p-M))+0x20)&~0x1Fu;
  fre=0x1000000; SW(EV+4,fre); SW(EV+0xC,size0); SW(EV+0x10,size1);
  u32 d=CTX+4;
  SW(d,0x80); SW(d+4,M[src]); src++;
  SW(CTX+0x58,0x500);
  model_setup(CTX+0x0C,d,0x500);
  model_setup(CTX+0x30,d,0x100);
  u32 dic=alloc(0x100*0x1004); memset(M+dic,0,0x100*0x1004); SW(CTX,dic);
  freq_reset(CTX+0x10); freq_reset(CTX+0x34);
  SW(EV,src); SW(EV+8,fre);
  u32 DST=0x3000000;
  r3=CTX; r4=DST; r5=size1; r6=EV; r1=0x800;
  yz2Decode_Decode();
  fp=fopen(argv[3],"wb"); fwrite(M+DST,1,size1,fp); fclose(fp);
  printf("packed %x unpacked %x\n",size0,size1); return 0;
}
