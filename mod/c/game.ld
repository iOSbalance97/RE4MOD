itemInfo           = 0x80019C90;
ItemMgr_get        = 0x8001A934;
PutInCase          = 0x8014A928;
SndCall            = 0x8005661C;
MesSet             = 0x80023F24;
MesSetNumber       = 0x8002496C;
sceAtItemFlgOn     = 0x801539D4;
SceAtSetEnable     = 0x801527D8;
EffectEspDelete    = 0x80106050;
EffectEspgenDelete = 0x80106070;
EffectEfmDelete    = 0x80106090;
ObjMgr_destroy     = 0x800C99D4;
EmMgr_destroy      = 0x8012EA88;
memclr_asm         = 0x80128C58;
Mem_free           = 0x80125D50;
DelPrim            = 0x8011FF64;
SECTIONS {
  . = CMOD_ADDR;
  .text : { *(.text.hooks) *(.text*) *(.rodata*) *(.data*) *(.sdata*) *(.sbss*) *(.bss*) }
  /DISCARD/ : { *(.comment) *(.eh_frame) *(.note*) }
}
