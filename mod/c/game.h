/* RE4 PAL (G4BP08 rev 0) game interface for the mod's C code. Addresses in game.ld. */
typedef unsigned char u8; typedef signed char s8; typedef unsigned short u16; typedef short s16;
typedef unsigned int u32; typedef int s32; typedef float f32;

typedef struct { u16 id; u8 type; u8 defNum; u16 maxNum; } ITEM_INFO;

/* globals (pointers held in small data) */
#define pG   (*(u8**)0x802B7548)
#define pS   (*(u8**)0x802B847C)   /* SceAtSys work: r13-26020 */
#define G8(o)  (*(u8*)(pG + (o)))
#define G32(o) (*(u32*)(pG + (o)))

/* objects */
#define ItemMgr     ((void*)0x802182C0)
#define cMes        ((u8*)0x80218758)
#define SubScreenWk ((u8*)0x8021E51C)
#define ObjMgr      ((void*)0x80283160)
#define EmMgr       ((void*)0x8028DDD0)

/* functions */
void itemInfo(u32 id, ITEM_INFO* info);
int  ItemMgr_get(void* mgr, u32 id, u32 num);
int  PutInCase(u32 id, u32 num, int size);
int  SndCall(int a, int b, int c, int d, int e, int f);
void MesSet(void* mes, int no, int px, int py, u32 attr, int wk, int col, int font);
void MesSetNumber(void* slot, int n, int digits);
void sceAtItemFlgOn(void* it);
void SceAtSetEnable(int no, int on);
void EffectEspDelete(int a, int kind, void* model, int d);
void EffectEspgenDelete(int a, int kind, void* model, int d);
void EffectEfmDelete(int a, int kind, void* model, int d);
void ObjMgr_destroy(void* mgr, void* obj);
void EmMgr_destroy(void* mgr, void* obj);
void memclr_asm(void* p, u32 n);
void Mem_free(void* p);
void DelPrim(void* ot, void* p);
void MesDelete(void* mes, int no);
int  GetSystemVcnt(void);

/* the mod's asm variables (VB, see bake.py); +0x20: gameplay frames left (set by the move hook) */
extern u8 modvars[];
#define VB_GAMEPLAY 0x20

/* GameCube PADStatus (Pad_data[0] is what PadRead turns into Joy[0] / Key) */
typedef struct { u16 button; s8 stickX, stickY, substickX, substickY; u8 triggerLeft, triggerRight, analogA, analogB; s8 err; u8 pad; } PADStatus;
#define Pad_data ((PADStatus*)0x8028E4F0)
enum { PAD_LEFT=1, PAD_RIGHT=2, PAD_DOWN=4, PAD_UP=8, PAD_Z=0x10, PAD_R=0x20, PAD_L=0x40,
       PAD_A=0x100, PAD_B=0x200, PAD_X=0x400, PAD_Y=0x800, PAD_START=0x1000,
       PAD_MOD_RELOAD=0x4000, PAD_MOD_CROUCH=0x8000 };   /* free bits, no Key_type_tbl entry */

/* mod storage inside the saved global block (retail pG+0x8368..0x8683 is unused, verified) */
#define MOD_SEEN_OFS 0x8600   /* 64 bytes: item ids 0..511 already presented */
