/* Weapon archive prefetch.
 *
 * ReadWepData reads em/wepXX.drs with a BLOCKING read (mode 0x8001) into the one weapon buffer,
 * which the weapon in hand still uses until weaponRelease: ~250 ms frozen on the iPhone. It
 * cannot be read there piece by piece (B29: models still read that buffer while it is being
 * overwritten). So the file is read beforehand, asynchronously, into a temporary block of the
 * game heap, while the old weapon stays intact; then, during ReadWepData's blocking read, the
 * DVD queue's low-level read (cDvdQueue::fileReadAsync) is answered from that copy: the same
 * game code parses the parts (REL, archive, sound bank) at memory speed.
 * Without a free heap block (or for another character) nothing changes: plain disc read. */
#include "game.h"

#define DVD_OBJ     ((void*)0x8027EFF8)             /* cDvd Dvd */
#define WEP_TBL     ((u8*)0x802102D8)               /* wep_data_leon[no]: u16 file, u16 dll, ... */
#define FILE_TBL    ((u8*)0x80205588)               /* FileTbl[file]: char* name, ... */
#define OLD_WEP_ID  (*(u8*)0x802B8358)              /* ReadWepData oldWepId (r13 - 26056) */
#define FST_PTR     (*(u8**)0x80000038)             /* OS globals: FST in memory */

int  DVDReadAsyncPrio(void* fi, void* addr, s32 len, s32 ofs, void (*cb)(s32, void*), s32 prio);
int  DvdFileExistCheck(void* dvd, const char* name, u32* len);
void* mem_alloc(u32 size, const char* file, int line, int flag, int heap);

void PrefetchEnd(void);
static void Flush(void* p, u32 n);
static u8* pf_buf;
static u32 pf_start, pf_len, pf_alloc;
static int pf_ready, pf_hits;
static volatile int pf_done;                         /* 0 reading, 1 done, -1 failed */
static int pf_req = -1;                              /* >= 0 while the DMA may still write */
static u32 pf_fi[0x10];                              /* DVDFileInfo: command block, startAddr, length */
static void PfDone(s32 result, void* fi) { (void)fi; pf_done = result >= 0 ? 1 : -1; }
static char pf_name[40];

/* ReadWepData's module mapping for Leon (pl_type 0) */
static int ModuleNo(int no, int type)
{
    if (no == 0x19 || no == 0x1F || no == 0x20 || no == 0x16 || no == 0x17) return 0x13;
    if (no == 3 && type == 2) return 0x12;
    if (no == 0xB && type > 1) return 0x14;
    if (no == 9) return type == 1 ? 0x15 : type == 2 ? 0x18 : 9;
    if (no == 0xA) return type == 1 ? 0x1F : type == 2 ? 0x20 : 0xA;
    if (no == 0xE && type == 1) return 0x19;
    if (no == 0xD && type == 2) return 0x1E;
    return no;
}

/* Starts reading the archive of weapon item `id`; 0 when there is nothing to prefetch. */
int PrefetchStart(u32 id)
{
    int no, type, i, entry;
    u32 file, dll, len;
    const char* src;
    u8* fe;
    if (pf_req >= 0) return 0;                       /* a previous read still runs */
    PrefetchEnd();
    if (G8(0x4FC4) != 0) return 0;                   /* Leon only */
    no = WeaponId2WeaponNo(id);
    type = WeaponId2WeaponType(id);
    if (no < 0 || no > 0x21) return 0;
    no = ModuleNo(no, type);
    if (no == OLD_WEP_ID) return 0;                  /* same module: ReadWepData skips the read */
    file = *(u16*)(WEP_TBL + no * 8);
    dll = *(u16*)(WEP_TBL + no * 8 + 2);
    if (!file) return 0;
    src = *(const char**)(FILE_TBL + file * 8);
    for (i = 0; i < 39 && src[i]; i++) pf_name[i] = src[i];
    pf_name[i] = 0;
    if (dll) {                                       /* SET_DRS_NAME */
        for (i = 0; pf_name[i] && pf_name[i] != '.'; i++) ;
        if (!pf_name[i] || !pf_name[i + 1] || !pf_name[i + 2] || !pf_name[i + 3]) return 0;
        pf_name[i + 1] = 'd'; pf_name[i + 2] = 'r'; pf_name[i + 3] = 's';
    }
    len = 0;
    entry = DvdFileExistCheck(DVD_OBJ, pf_name, &len);
    if (entry < 0 || !len || !FST_PTR) return 0;
    fe = FST_PTR + entry * 12;
    if (*(u32*)(fe + 8) != len) return 0;            /* not the entry we think it is */
    pf_alloc = (len + 0x1F) & ~0x1F;
    pf_buf = mem_alloc(pf_alloc + 0x40, 0, 0, 0, 13);
    if (!pf_buf) return 0;                           /* no room in the heap now: plain read */
    pf_start = *(u32*)(fe + 4);
    pf_len = len;
    /* one raw DMA of the whole file through the SDK (no 128 KB piece per frame of the game queue):
       as fast as the drive gives it; the lines are flushed first so the CPU later reads RAM */
    for (i = 0; i < 0x10; i++) pf_fi[i] = 0;
    pf_fi[0x30 / 4] = pf_start;
    pf_fi[0x34 / 4] = pf_len;
    Flush(pf_buf, pf_alloc + 0x40);
    pf_done = 0;
    pf_req = 1;
    if (!DVDReadAsyncPrio(pf_fi, pf_buf, (s32)pf_alloc, 0, PfDone, 2)) { pf_req = -1; PrefetchEnd(); return 0; }
    return 1;
}

/* Polls the prefetch: 1 ready, 0 still reading, -1 failed (or none). */
int PrefetchPoll(void)
{
    if (pf_ready) return 1;
    if (pf_req < 0 || !pf_buf) return -1;
    if (pf_done == 0) return 0;
    pf_req = -1;
    if (pf_done < 0) { PrefetchEnd(); return -1; }
    pf_ready = 1;
    return 1;
}

void PrefetchEnd(void)
{
    if (pf_req >= 0) return;                         /* never free a block a read still targets */
    pf_ready = 0;
    if (pf_buf) Mem_free(pf_buf);
    pf_buf = 0;
}

int PrefetchBusy(void) { return pf_req >= 0; }
int PrefetchHits(void) { return pf_hits; }

static void Flush(void* p, u32 n)
{
    u32 a = (u32)p & ~0x1F, e = (u32)p + n;
    for (; a < e; a += 32) __asm__ volatile("dcbf 0,%0" : : "r"(a) : "memory");
    __asm__ volatile("sync" : : : "memory");
}

/* Hook on cDvdQueue::fileReadAsync(this, addr, size, ofs): 1 = served from the prefetched copy
   (the busy flag 0x02000000 is never set, so the queue goes on at once), 0 = do the disc read. */
int PrefetchRead(u8* q, u8* addr, u32 size, u32 ofs)
{
    u32 n = (size + 0x1F) & ~0x1F, i;
    if (!pf_ready || *(u32*)(q + 0x38) != pf_start) return 0;   /* m_Info.startAddr */
    if (ofs + n > pf_alloc + 0x40) return 0;
    if (!(((u32)addr | ofs | (u32)pf_buf) & 3))
        for (i = 0; i < n; i += 4) *(u32*)(addr + i) = *(u32*)(pf_buf + ofs + i);
    else
        for (i = 0; i < n; i++) addr[i] = pf_buf[ofs + i];
    Flush(addr, n);
    pf_hits++;
    return 1;
}
