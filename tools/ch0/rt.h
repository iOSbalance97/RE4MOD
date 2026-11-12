#include <stdint.h>
typedef uint32_t u32; typedef int32_t s32; typedef int16_t s16;
extern uint8_t* M;
static inline u32 LW(u32 a){return ((u32)M[a]<<24)|((u32)M[a+1]<<16)|((u32)M[a+2]<<8)|M[a+3];}
static inline u32 LH(u32 a){return ((u32)M[a]<<8)|M[a+1];}
static inline u32 LB(u32 a){return M[a];}
static inline void SW(u32 a,u32 v){M[a]=v>>24;M[a+1]=v>>16;M[a+2]=v>>8;M[a+3]=v;}
static inline void SH(u32 a,u32 v){M[a]=v>>8;M[a+1]=v;}
static inline void SB(u32 a,u32 v){M[a]=v;}
#define CMP(a,b) ((a)<(b)?-1:((a)>(b)?1:0))
extern u32 r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12,r13,r14,r15,r16,r17,r18,r19,r20,r21,r22,r23,r24,r25,r26,r27,r28,r29,r30,r31,ctr; extern int cr; extern double f2,f3,f4,f5;
