# H08 — arreglo del cuelgue de H07 (límite de texturas por sala)

Igual que H07 (ver ../H07/NOTAS.md) salvo esto:

**Fallo de H07**: al cargar la partida en la granja (sala r113 = vestíbulo) la primera vez no se veía nada y la segunda
"Invalid read from 0x00200108, PC = 0x8014e224".
- 0x8014e224 (PAL) es getNearPoint (route_ck.cpp): un enemigo busca su punto de ruta y lee pG->Rtp->nPoint.
- pG->Rtp (GLOBAL_WK +0x4F2C, mismo desplazamiento en PAL: ReadAreaData PAL 0x8014b31c guarda 4F2C/4F20/4F34/4F30)
  valía 0x00200102: pisado.
- Justo antes está GLOBAL_WK::texObj[0xF8] (0x3010..0x4F10): un GXTexObj por textura de la sala, **máximo 248**.
  El vestíbulo y el comedor llevaban 253 (color + transparencias) → las 5 de más pisaban prim_*, RoomMes, las cámaras
  (pantalla sin nada) y Rtp (cuelgue).

**Arreglo**: re4room.py limita a 240 texturas por sala (MAX_TEX). Vestíbulo y comedor: 240; el resto ya iba por debajo
(máx. 187). Comprobado leyendo el TPL de cada .das final.

Herramienta nueva: herramientas/ppcdis.py (desensamblador PowerPC mínimo para mirar el dol PAL).
