# RE4MOD

Mod de Resident Evil 4 (GameCube PAL, G4BP08 rev 0) con control y cámara modernos.

- `mod/`: código fuente (ensamblador PowerPC) y scripts que lo integran en `main.dol` y generan los parches.
- `patches/<versión>/`: parches xdelta para cada disco sobre la ISO PAL limpia.
- Cada vez que cambia `patches/`, GitHub Actions construye las ISO parcheadas y las publica en Releases.
