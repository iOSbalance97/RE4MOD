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
int  ItemMgr_arm(void* mgr, void* item);
int  WeaponId2WeaponNo(u32 id);
int  WeaponId2WeaponType(u32 id);
void SndBlkStop(int blk);
void weaponRelease(void* pl);
void weaponLoad(void* pl, int no, int type);
void weaponInit(void* pl);
#define pPL (*(u8**)0x802B8344)
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
#define MOD_SLOT_OFS 0x8640   /* 4 x u16: quick weapon slots up/right/down/left, item id + 1 (0 = empty) */

/* ---- GX (Dolphin SDK in main.dol) ---- */
typedef f32 Mtx[3][4];
typedef f32 Mtx44[4][4];
typedef struct { u32 d[8]; } GXTexObj;
void GXSetAlphaCompare(int c0, int r0, int op, int c1, int r1);
void GXSetColorUpdate(int on);
void GXSetAlphaUpdate(int on);
void GXSetCullMode(int m);
void C_MTXOrtho(Mtx44 m, f32 t, f32 b, f32 l, f32 r, f32 n, f32 f);
void GXSetProjection(Mtx44 m, int type);
void PSMTXIdentity(Mtx m);
void GXLoadPosMtxImm(Mtx m, int id);
void GXSetCurrentMtx(int id);
void GXSetBlendMode(int type, int src, int dst, int op);
void GXSetNumTevStages(int n);
void GXSetNumChans(int n);
void GXSetNumTexGens(int n);
void GXSetTexCoordGen2(int dst, int type, int src, int mtx, int norm, int pt);
void GXSetChanCtrl(int chan, int enable, int amb, int mat, int lights, int diff, int attn);
void GXSetTevOrder(int stage, int coord, int map, int color);
void GXSetTevOp(int stage, int mode);
void GXSetZMode(int enable, int func, int update);
void GXSetFog(int type, f32 startz, f32 endz, f32 nearz, f32 farz, const u32* color);
void GXInitTexObj(GXTexObj* o, const void* img, int w, int h, int fmt, int ws, int wt, int mip);
void GXInitTexObjLOD(GXTexObj* o, int minf, int magf, f32 minlod, f32 maxlod, f32 bias, int bclamp, int edge, int aniso);
void GXLoadTexObj(GXTexObj* o, int map);
void GXClearVtxDesc(void);
void GXSetVtxDesc(int attr, int type);
void GXSetVtxAttrFmt(int fmt, int attr, int cnt, int type, int frac);
void GXBegin(int prim, int fmt, int n);
int  AddOtDirect(int ot, void* data, void (*func)(void*), u32 no, u16 flag, void* pos, f32 radius);
void* pzlBoard_getPiece(void* board, int x, int y);
#define GXFIFO_F32 (*(volatile f32*)0xCC008000)
#define GXFIFO_U32 (*(volatile u32*)0xCC008000)
