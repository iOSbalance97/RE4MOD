# RE1 en el motor de RE4 (rama `re1-remake`)

Proyecto aparte del mod de RE4: salas de Resident Evil 1 (modelos de Umbrella Chronicles sacados
de un pack para *The Movies*) metidas en RE4 GameCube PAL (G4BP08) como si fueran salas del juego.

- `herramientas/`: cadena de conversión (Python 3; usan el decomp adonis-singh/re4 en /home/claude/re4src)
  - `msh2obj.py`: .msh de The Movies -> OBJ (+ texturas PNG)
  - `re4room.py`: OBJ -> SMD (modelos BIN + TPL CMPR/I4) con el formato de las salas reales
  - `re4col.py`: OBJ -> SAT/EAT (suelos, escaleras como rampa, paredes) en contenedor de sala
  - `yz2enc.py`: compresor yz2 de los .das (verificado con el descompresor del decomp)
  - `re4inject.py`: mete SMD/SAT/EAT en un rNNN.das existente (conserva el resto de la sala)
  - `satcheck.py`, `smd2obj.py`, `render.py`: comprobaciones
- `mkiso_re1.py TAG`: ISO de prueba + parche xdelta sobre la ISO limpia del disco 1.
- `patches/HNN/`: parches de prueba (H = hall).

Receta de H01 (hall en r102, entrada por la puerta 25 de r101):
```
P="-6.2,-6.72,0.3,-19691,0,-19088,-0.584"
python3 herramientas/re4room.py MainHall/p_RE1_MainHall.obj hall --decimar 0.4 --tex-max 256 --colocar="$P"
python3 herramientas/re4col.py  MainHall/p_RE1_MainHall.obj col  --colocar="$P"
python3 herramientas/re4inject.py St1/r102.das hall col out --modo das
cp out/r102.das files/St1/ && python3 mkiso_re1.py H01
```
