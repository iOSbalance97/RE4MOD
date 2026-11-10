# RE4 MOD — estado del proyecto (para continuar en otro chat)

Última versión entregada: **B60** (10-11-2026). Responder **siempre en español**.

## 1. Qué es
Mod de **Resident Evil 4 GameCube PAL (G4BP08 rev 0)** para que se juegue como el **RE4 Remake**:
moverse apuntando, cámara al hombro moderna, cambio rápido de arma, retícula y apuntado modernos,
agacharse y sigilo. Se juega en la app propia **OmniStation** (iOS, núcleo libretro Dolphin) con
**DualSense**.

Reglas de trabajo del usuario:
- Revisar los archivos y versiones reales **antes** de entregar (nada de probar a ciegas).
- Entrega = **parches xdelta** (disc1/disc2) sobre las ISO PAL limpias + commit al repo.
- Las imágenes del juego viven en un repo **privado**; nunca buscar ni dar descargas del juego.
- Este chat es solo de RE4; lo de OmniStation va en su propia conversación.
- No se pueden hacer pruebas en emulador aquí: el usuario prueba y manda vídeos (se analizan
  sacando fotogramas con ffmpeg y `tile`).

## 2. Repositorio y compilación
- Repo: **github.com/iOSbalance97/re4mod**, rama **mod-builds**.
  - `mod/` → todo el código (asm `*.s`, `mod/c/*.c`, `bake.py`, `mkiso.py`, `shrink.py`).
  - `anim/tools/` → conversión de animaciones Mixamo; `anim/mixamo/` → los FBX.
  - `patches/BNN/disc1.xdelta, disc2.xdelta` + `patches/LATEST`.
- ISOs limpias (sha1): disc1 `9e58a28b32cbbddd215f2fcbecb79c41812f5f54`,
  disc2 `5dc7461496040f6656ecd7e187ab9f54d05d58fd`. Se esperan en `/home/claude/disc/iso/discN.iso`;
  el `main.dol` limpio extraído en `/home/claude/disc/ext1/sys/main.dol`.
- **Herramientas (no compilar binutils: hace falta flex/bison y no hay)**. Están ya compiladas en el
  repo, en `tools/`:
  ```
  mkdir -p /home/claude/tools/binutils
  unzip -o tools/binutils-2.42-1-linux-x86_64.zip -d /home/claude/tools/binutils
  chmod +x /home/claude/tools/binutils/* tools/xdelta3; cp tools/xdelta3 /home/claude/tools/
  ```
  (binarios estáticos x86-64 de encounter/gc-wii-binutils 2.42-1: `powerpc-eabi-as`, `-ld`,
  `-objcopy`...; `bake.py` los busca en `/home/claude/tools/binutils/powerpc-eabi-*`).
  Si no estuvieran: `https://github.com/encounter/gc-wii-binutils/releases/download/2.42-1/linux-x86_64.zip`.
- Además: clang 18 (suele venir instalado; si falta: `apt-get install clang`)
  (`--target=powerpc-unknown-eabi -mcpu=750`). Decomp de referencia: **adonis-singh/re4** (NTSC;
  las direcciones PAL hay que buscarlas en el dol PAL, no son un desplazamiento fijo).
- Flujo:
  1. `cd mod && python3 bake.py bNN` → `bake/main_bNN.dol` (inyecta todo en el dol).
  2. `python3 mkiso.py bNN` → `out/RE4_PAL_discN_bNN.iso` + `.xdelta`.
  3. Verificar: `xdelta3 -d -s discN.iso parche out.iso` y comparar sha1 con la ISO generada.
  4. Borrar las ISO de `out/` (el disco se llenó una vez), copiar parches a `patches/BNN`,
     actualizar `LATEST`, commit + push, enviar los dos .xdelta al usuario.
- Estructura de `bake.py`: código C en `C_SRCS` (lista `c/*.c`), hooks en `C_HOOKS`
  (dirección, símbolo) con stubs en `c/hooks.s` y retornos en `c/hooksyms.ld`; parches de una
  palabra en el diccionario `W04`; bloques asm propios (`m15.s` movimiento, `c12.s` cámara,
  `a12.s` respuesta del apuntado, `camfree.s` cámara libre...) con constantes en `P_*`.
  Variables compartidas asm↔C en `modvars` (VB, `VARS_SIZE=0x48`).
- Espacio: el mod va desde 0x802BD5E0 hasta ~0x802E4xxx (límite 0x80300000; sube ArenaLo).

## 3. Lo que ya funciona (B1–B59; B60 pendiente de probar)
- **Moverse apuntando** (m15.s) y **andar apuntando con animación completa** (legs.c: piernas Mixamo
  en 4 direcciones aplicadas tras la actualización del juego; torso con balanceo; el arma se
  recoloca en la mano tras el balanceo).
- **Cambio de arma con la cruceta** sin tirones (lectura previa del archivo del arma en memoria,
  prefetch.c), también corriendo y apuntando; panel a la derecha estilo Remake.
- **Aviso al recoger objetos** estilo Remake (barra degradada + icono + texto, item.c/icon.c).
- **Cámara**: libre con el stick derecho (camfree.s), al hombro (c12.s), la cámara sigue a León al
  andar apuntando, suavizado fijo al apuntar (0.5).
- **Retícula moderna fija en el centro** (hud.c): 4 trazos finos + punto, se abre al moverse/girar/
  disparar y se cierra quieto; roja sobre enemigos. El láser ya no se dibuja.
  - El rayo de puntería sale del **centro de la cámara** (hook LaserRay) y los disparos se dirigen a
    ese punto (SpreadShot); **dispersión real** dentro del círculo; escopeta mantiene su abanico.
  - **Retroceso** de cámara que se recupera solo (más fuerte con escopeta).
  - Apuntado: curva de respuesta + aceleración, diagonales igual de rápidas, arriba = abajo,
    balanceo del arma al 35 %. Con escopeta la cámara de apuntar sube 9 cm.
  - Al apuntar con la cámara libre girada, León se gira hacia la cámara (AimCamEnter).
- **Agacharse** (crouch.c, Círculo): quieto, andar en 4 direcciones (Mixamo, altura igualada con
  IK de piernas offline), transiciones, de agachado a correr (L3), apuntar agachado (piernas),
  cámara más baja. **Altura y brazos: OK según el usuario.**
- **Cuchillo agachado**: al sacarlo, animación del juego con piernas agachadas (torso 65 %);
  postura y tajo bajo de Mixamo (Sword_And_Shield_Slash); tajos encadenados (B59).
- **Sigilo** (stealth.c): los ganados te notan por proximidad a 2,5 m andando, 0,8 m agachado (sin
  ruido de pasos); corriendo como el original. Se reescriben las constantes del módulo REL de cada
  tipo de ganado en memoria.
- **Escalera**: la cámara libre no acumula giro durante acciones; durante acciones solo la
  inclinación vuelve a nivel (B59).

## 4. En curso / pendiente (orden del usuario)
1. **Ejecución sigilosa estilo Remake (B60, sin probar)**. B59: el sigilo funcionaba (X, golpe del
   juego). B60 lo sustituye por una secuencia completa:
   - Condiciones de la X (stealth.c FindTarget): León agachado y libre; ganado (id 0x10–0x20 menos
     0x18) vivo, en su rutina normal (r_no_0 1), **sin haber detectado a León** (Be_flg +0x3E0 bit
     0x100 y Lose_timer +0xA18 < 90 → alerta), a < 1,5 m, ±60 cm de altura, por la espalda (> ~105°).
   - Ganado: se reproduce la muerte "agarrado por detrás" del propio juego (rotura de cuello de HUNK en
     Mercenarios): movimiento em10.drs 0x2BA + secuencia 0x2BB (índice arc.py = juego − 4), copiados
     en `take_data.h` porque solo em10.drs los tiene, con la rutina Dm_NeckBreak (R0 2 / R1 0x15)
     arrancada en el paso 1 (el paso 0 lanzaría la mitad de HUNK sobre León). Evento "cuello" en el
     frame 37 (voz, suelta el arma), cae hacia delante y pasa a Die_Cramp (objetos, puntos).
   - León: clip propio `anim/tools/mktake.py` (IK de brazos y piernas contra el movimiento del
     ganado, mismo esqueleto 0–25): mano izquierda a la boca, cuchillo hacia atrás, puñalada al lado
     derecho del cuello (frames 30–35), lo saca (49–58), suelta (74–86), vuelve a agachado (100).
     crouch.c CR_TAKE (cuerpo entero, frame sincronizado con Seq_frame del ganado); León colocado cada
     frame (x/z del clip en el marco inicial del ganado), colisión con personajes desactivada.
     Hoja del cuchillo supuesta en el +z local de la mano (lado del pulgar): **comprobar en vídeo**.
   - Sangre (EstSet 0x80105A90, EFF_CORE 0/1/2) en la punta en el 35 y al sacarlo; sonido 0x51.
   - Cámara (hook 0x800BDB00 en CameraQuasiFPS::hitCheck → StealthCam): se acerca por el lado
     derecho, algo adelantada, y vuelve a la normal entre los frames 70 y 96.
   - Diagnóstico de números quitado.
2. **Rastro del cuchillo**: el efecto del tajo sigue a la animación de pie del juego. Para que siga a
   la nuestra hay que aplicar las poses (legs.c/crouch.c) al final del movimiento de León (antes de
   los efectos) en vez de en ModFrame. Pendiente de encontrar ese punto en el dol PAL.
3. Ganados más listos (que investiguen ruidos antes de detectarte), opcional.
4. Más adelante: gesto de cambio de arma corriendo, interruptor Moderno/Clásico, tabla de controles
   para Dolphin, revisar puertas, suavizar la entrada del stick.

## 5. Direcciones PAL útiles (verificadas)
- pPL (jugador) `*(r13-26332)` · Joy 0x8028D0D0 · Key 0x8028DA70 · pG `*(r13-29912)`.
- **Gestor de enemigos 0x80283160** (¡`EmMgr` en game.h 0x8028DDD0 NO es la lista de enemigos!).
- CamCtrl 0x80216E8C · QuasiFPS 0x80217104 (m_pl_mat +0x174, m_depression +0x200,
  m_direction +0x204, m_walk_ratio +0x1AC) · CamSmth 0x80217948 (ratio +0xFC, efecto +0x100).
- pG->Camera = pG+0x74 (v_mat +0x30, ProjMat +0x64) · itemCamera 0x80284420.
- weapon_no = pG+0x4FBC (NTSC 0x4FB0 + 0xC) · m3r (pitch apuntado) 0x8021D970 · lpos 0x8021D820,
  lcross 0x8021D82C.
- Jugador: r_no 0xFC–0xFF (r_no_1: 0 quieto, 1 andar, 2 atrás, 3 correr, 6 arma, 0xB cuchillo;
  cuchillo r_no_2: 0 sacar, 1 guardia, 2 tajo, 3 guardar) · pos 0x94 · ang.y 0xA4 · mat 0x0C ·
  Wep 0x788 (m_pWep +0x34, pitch +0x28) · partes: l_mat +0x3C.
- EstSet (efectos) 0x80105A90 · CameraQuasiFPS::hitCheck tras el prólogo 0x800BDB00 (r5 = QFPS_OFFSET).
- Ganado (cEm + work em10 en +0x3E0): Motion +0x1D8 (Seq_frame +0x290), atari.m_flag +0x2CE,
  Be_flg +0x3E0, Timer +0x3E4, Lose_timer +0xA18. Decomp: los índices de motion del juego son los
  de arc.py + 4 (arc.py empieza en ofs[4]).
- Funciones: PlWepHitCheck2 0x80145A0C · PlWepLockCtrl hook 0x80146D50 · PlWepLockRand 0x80147284 ·
  drawLaserSight 0x8003EA48/0x8003EB6C · calcDepressionRatio rama apuntado 0x800BCD54 ·
  atan2f 0x8005FFE8 · MotionSetCore 0x8012B480 · lista de módulos REL 0x800030C8.

## 6. Animaciones (Mixamo, sin piel, FBX binario, 30 fps)
- Pipeline: `anim/tools/conv.py` (retarget a Leon, esqueleto de pl00.drs, S=10.51),
  `mkwalk.py` (andar apuntando → c/walk_data.h), `mkcrouch.py` (agachado → c/crouch_data.h,
  15 fps, s16 1e-4 rad, altura 760 mm con IK de piernas).
- `mktake.py` (takedown): `python3 mktake.py --png 6,24,36 out.png` dibuja León + ganado para
  revisar; escribe c/take_data.h (necesita em10.drs extraído en /home/claude/disc/ext1/files/em/;
  extractor de ficheros de ISO: `python3 gciso.py iso extract 'em/em10.drs' destino`).
- Ojo: archivos con piel (>1,8 MB) llegan cortados en la subida → pedir "Without Skin".
