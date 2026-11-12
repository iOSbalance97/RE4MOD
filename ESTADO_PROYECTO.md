# RE4 MOD — estado del proyecto (para continuar en otro chat)

Última versión entregada: **B93** (12-11-2026). Responder **siempre en español**.

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
   - Cámara (hook 0x800BDB00 en CameraQuasiFPS::hitCheck → StealthCam; hitCheck es miembro: r3 = this, r4 = m, r5 = QFPS_OFFSET; los puntos están en el espacio de m (B63: B61/B62 usaban r3 por error, cámara en el suelo); B62: punto cercano al 80 % hacia el ojo para que el rayo de colisión no choque con León y el ganado): se acerca por el lado
     derecho, algo adelantada, y vuelve a la normal entre los frames 70 y 96.
   - Diagnóstico de números quitado.
   - B63 (vídeo): ya se ve; fallos: cuello retorcido (la rotura de cuello gira la cabeza 80–200°),
     cámara pegada, horca atravesando a León, hoja pasando por delante del cuello.
   - B64: mktake.py edita la copia del movimiento (cabeza/cuello 3–4 sin giro entre 33 y 94: cabeza
     caída), adelanta el evento 0x11 de la secuencia del frame 37 al 9 (suelta el arma al agarrar),
     cuchillo 330 de muñeca a punta y estocada hacia delante-izquierda; cámara a ~1,8 m, punto
     cercano a 65 cm del objetivo, entrada en 16 frames.
   - B65 (vídeo B64: brazo raro, cuchillo enorme): brazo derecho nuevo en mktake.py (guardia baja
     junto a la cadera, una estocada hacia arriba bajo la mandíbula al lado del cuello, saca hacia
     atrás y abajo, codo hacia abajo); cuchillo dibujado al 72 % durante la ejecución (crouch.c
     KnifeScale, TK_KNIFE_K); la cámara entra/sale orbitando alrededor del objetivo en el mundo.
   - B66 (vídeo B65: mucho mejor): la hoja se aplasta a lo largo de su eje mientras está clavada
     para que la punta quede dentro del cuello (crouch.c KnifeInto, frames 33–55); arranque en 10
     frames con los brazos por delante y más inclinación; final: baja a agachado (78–94), guarda el
     cuchillo en la funda del pecho (84–96, desaparece en 96, L hasta 98) y el guardado del juego no
     se ve (knife_hide); clip de 111 frames. Sangre: se queda como está (usuario).
   - B67: brazo del cuchillo desde Mixamo 'Stabbing' (anim/mixamo/crouch/Stabbing_takedown.fbx):
     trayectoria de la mano y codo del clip (marco del pecho, desde el hombro) girada y escalada
     para que la estocada caiga en la parte trasera-derecha del cuello; tiempo 3→0, 30→10, 35→15,
     49→26, 58→37; giro del pecho del clip al 15 %. Para que haya sitio, León se queda a 36 cm
     (antes 20) y la mano izquierda va a la frente (no a la boca). Cuchillo al 66 %.
   - B67 (vídeo): "muy raro" (brazo rígido, cuchillo, sin unión con el ganado).
   - **B68: León = la mitad de HUNK de la rotura de cuello** (em10.drs juego 0x2B9 = arc.py 0x2B5,
     77 frames, brazos FK / piernas IK; EmCatchPLSet: ganado a (−75.21, 0, 1076.1) delante de HUNK y
     girado 180°). Se reproduce **en espejo** (izq↔der) para que la mano derecha (cuchillo) vaya
     a la garganta y la izquierda a la nuca (IK para corregir el espejo), y en vez de girar el
     cuello **raja la garganta** (frames 33–39, sangre ×3). El ganado arranca su movimiento en el
     frame 18 (MotionSetCore frame = TK_S0; evento 0x11 movido al 19). León queda al lado derecho
     del ganado mirando de través (TK_YAW ≈ +85°); de 56 a 92 baja a agachado, funda 66–78,
     pies corregidos contra el suelo. Cámara al lado izquierdo-delante del ganado.
     mktake_ik.py = versión anterior (IK/Mixamo) por si se quiere volver.
   - **B68: sin bandas negras**: SetScissorState (0x8012641C) siempre sin tijera (0x80126434 → b),
     filtros 09/0b a pantalla completa (0x80117A90/94, 0x80190708/0C). **No bastó** (vídeo): las
     bandas las pinta Draw_cinesco (0x801758C4) siempre (CinescoMove pide las bandas cada frame).
   - B69: Draw_cinesco siempre sale sin dibujar (0x801758DC → b 0x80175B5C). Ejecución más lenta:
     Seq_speed del ganado (Motion +0xC0 = em+0x298) al 70 % y al 42 % alrededor del corte
     (26–50); León sigue su frame (kill_f), eventos por cruce de frame; al acabar vuelve a 1.
   - B69 (vídeo): el cuchillo pasaba por delante de la boca, en el aire. B70: garganta más baja y
     pegada (cuello +45 mm delante, a la altura del cuello), cuchillo en la garganta desde el 22–28
     y corte 33–41; velocidad 60 % / 32 % en el corte.
   - Bandas: en los vídeos el juego ocupa las filas 189–1187 de 1290 tanto antes como después de
     B68/B69; el negro de fuera es el área de la vista de OmniStation (entre L/Z/R y START), no
     del juego → arreglarlo en la conversación de OmniStation (o un modo panorámico en el juego).
     **Corrección (captura de partida del usuario)**: sí son del juego. Con VI de 480 líneas y XFB
     de 448, las bandas son exactamente las líneas 0–56 y 393–448 del XFB (las 16 líneas de borde
     del VI muestran restos); el menú (640×448) no las tiene. Cinesco y tijera están anulados (B70
     verificado) y no hay otro GXSetScissor/quad con 56/393 en el dol ni en los REL → origen sin
     encontrar. B71 = prueba: pone el color de borrado de la copia EFB en rojo oscuro (FIFO BP 0x4F/
     0x50, una vez, ClearRedTest en hud.c): rojo = zona sin dibujar; negro = algo la pinta.
   - B71: cuchillo +40 mm (B70 quedaba por debajo de la garganta).
   - **B72 – bandas resueltas**: el vídeo de B71 (rojo solo en la carga, negro en partida) y el parche
     público jrupinski/RE4-gamecube-letterbox-patch (NTSC) explican el origen: son TRES cosas:
     Draw_cinesco, los sprites de barra del HUD (grupo 0x30) y la bandera "modo letterbox"
     (System_flg 0x800, pG+0x54) que recorta el render 3D a las filas 56–392. Portado a PAL (preset
     "gameplay": barras solo con Stop_flg≠0 = menús, inventario, escenas, vídeos, o en el título):
     HUD 0x8011DF9C (5 palabras), andi.0x800→0 en 0x801695F0 (bucle de render), 0x800FC6B8,
     0x8017C608, 0x8017CA28, 0x80180760, 0x80186C58 (efectos), float 56→0 en 0x801F0184 (fundido),
     cine_polling 0x801757A0–B8 (7 palabras). Revertidos los parches B68/B69 (tijera, filtros,
     Draw_cinesco). Medidor de vida bajado 60 u (56 px) en partida: hook_hud 0x8011D47C (idSysMove00,
     clase 0x21 sin padre, Stop_flg==0). Quitado ClearRedTest.
   - **B72 – cuchillo**: causa real de que unas veces quedara alto y otras bajo: em10 da a cada ganado
     una escala aleatoria 1.01–1.1 (cModel scale +0xAC, work Scale +0x9DC) y la toma está calculada
     a escala 1 (hasta ~140 mm de diferencia en el cuello). Ahora durante la muerte ScaleOne() lleva
     el ganado a escala 1. mktake: la garganta se calcula del propio cuello (55 % entre base del cuello
     y cabeza, 60 mm delante de su eje), el centro de la hoja sobre ella; tras el corte la mano baja
     pegada (no se abre hacia fuera) y los brazos van directos a la pose agachada (no a la de HUNK).
   - **B73**: (usuario: B72 sin bandas en partida OK; quiere quitarlas en todo, un recuadro rojo
     arriba, muñeca de León doblada, corte "casi" en el cuello, ajuste automático por tamaño).
     Bandas en todo el juego: preset "everywhere" (0x801757AC bne→nop, sin las 7 palabras de B72).
     Recuadro rojo = objeto del HUD aparcado en la franja de arriba (antes tapado por las barras):
     hook_hud empuja fuera de pantalla los objetos sin padre con y > 182 mientras System_flg 0x800.
     Muñeca: B72 la doblaba 100–130° (la hoja sale del puño en ángulo recto y se la ponía cruzada).
     Ahora la punta entra en el lado del cuello y se arrastra por delante (θ +30°→−70°, de su
     izquierda-delante hacia el lado de León), mano en línea con el antebrazo (arm_free: elige el codo
     en su círculo para alinear antebrazo; flexión ≤ ~25° durante el corte). Garganta al 62 % del
     cuello. Ajuste automático: mktake exporta las poses de brazos con el cuello ±70 mm (tk_rot_up/dn,
     frames 18–67) y tk_neck (altura esperada); stealth.c NeckMeasure mide la altura real (partes 3/4
     del ganado − pos.y, filtrada) y crouch.c ClipQ mezcla hacia la variante (StealthNeckK ±1). Se
     mantiene ScaleOne.
   - **B74**: bandas otra vez solo en partida (preset "gameplay"): el usuario vio que en menús e
     inventario las barras tapan fallos a arreglar (pendiente). Se mantiene el ocultado del HUD de la
     franja de arriba (solo actúa con System_flg 0x800). Cuchillo (vídeo B73: "casi"; el brazo se
     doblaba hacia dentro): corte más corto θ +15°→−30° (con −70° la muñeca se metía en el pecho de
     León), arm_free premia el codo hacia fuera (lado derecho de León) y León se inclina 9 cm hacia el
     ganado en 28–56 (el cuerpo de HUNK se aleja y el brazo no llegaba); salida: mano hacia fuera y
     abajo. Codo fuera en todo el corte, punta en el cuello 30–42 (13 mm), muñeca ≤ 25°.
   - **B75** (vídeo B74: "casi listo"): mano izquierda en la nuca (75 % del cuello, 78 mm detrás), dedos
     hacia arriba por detrás de la cabeza, palma al cuello; antes la palma en la parte de atrás de la
     cabeza asomaba por el lado y al soltar volvía a la pose de HUNK (puño levantado junto a la
     cabeza). Ahora ninguno de los dos brazos vuelve a HUNK: el IK se mantiene y la mezcla a la pose
     agachada (b_arm 50–66) los lleva. arm_free con preferencia por el codo de HUNK (sin saltos del
     codo entre frames). Cadáver: el "parpadeo y aparece de pie" era Die_Lost (disolución normal del
     juego, efecto EFF_EM10 0x19 = columna rosa); la víctima del sigilo lleva em->flag 0x10000000 y
     Die_Cramp deja el cuerpo en el suelo (en etapa 4+ el juego lo disuelve igualmente).
   - **B76**: el vídeo a cámara lenta que mandó el usuario era la grabación de B74 (Fotos: "Hoy 2:25").
     Fotograma a fotograma: el cuerpo ya se había desvanecido (Die_Lost) y 1 fotograma después aparece
     el ganado encorvado junto al carro, luego "COGER" + columna rosa: todo es Die_Lost, que B75 ya
     evita. Verificado en em10.drs PAL que Die_Cramp lee em->flag +0x3C8 bit 0x10000000 (también hay
     una condición etapa>3 y sala≤4 → disuelve). B76 refuerza: `corpse` vigila a la víctima tras
     KillEnd y vuelve a poner el bit cada frame hasta que Die_Cramp la deja (r_no 3,0,2). El usuario
     quiere conservar el cadáver (se usará para otra cosa).
   - **B77**: con B76 el usuario sigue viendo el parpadeo (el flag no basta: algo la manda a Die_Lost
     igualmente). Ahora StealthKillFrame vigila `corpse` cada frame y si la ve en Die_Lost sin empezar
     (r_no 3,3,0) la devuelve a Die_Cramp reposo (3,0,2). Si aun así parpadea, no es Die_Lost: pedir
     vídeo a velocidad normal con la cámara en el cuerpo.
   - **B78** (vídeo B77): el cadáver ya se queda en el suelo (B77 funciona), pero ~0,8 s después de caer
     aparece 1 fotograma una figura encorvada de pie junto al cuerpo = el final del movimiento del
     ganado (130 frames): se pasa del último frame antes de que Dm_NeckBreak vea el final. El vigilante
     `corpse` lo para 2 frames antes (Seq_speed 0) y lo manda a Die_Cramp (3,0,0,1). El usuario acepta
     que se disuelva si eso lo arreglara; de momento se conserva el cadáver (lo quiere para otra cosa).
2. **Fallos tapados por las bandas en menús e inventario** (el usuario los vio con B73 sin bandas):
   pedir capturas y arreglarlos; luego se podrán quitar las bandas también ahí.
3. **Rastro del cuchillo**: el efecto del tajo sigue a la animación de pie del juego. Para que siga a
   la nuestra hay que aplicar las poses (legs.c/crouch.c) al final del movimiento de León (antes de
   los efectos) en vez de en ModFrame. Pendiente de encontrar ese punto en el dol PAL.
4. Ganados más listos (que investiguen ruidos antes de detectarte), opcional.
5. Usar el cadáver que se queda tras el sigilo (idea del usuario, sin concretar).
5b. **Enemigo nuevo "El Herrero"** (diseño propio; el usuario pidió copiar el Bruto del remake y otro
   personaje: no se copian diseños ajenos; le gusta el diseño). models/herrero/, todo procedural:
   `g++ -O2 -o qem qem.cpp; python3 mesh.py && python3 finish.py && python3 tex.py && python3 show.py
   && python3 export2.py`. Campos de distancia (model.py) → marching cubes → decimado QEM → 14.835
   triángulos en 6 piezas (body, mask, fist, claw, acc, weapon).
   - v2: espalda redondeada (joroba en cúpula, dorsales en cuña, vértebras), bultos de Plaga en cuello/
     hombro izq., **pose de enlace en T** (como el esqueleto del juego: brazos en ±x, rotaciones
     identidad), **UV + 2 texturas 1024²** (tex.py: cartas por proyección de caja, empaquetado skyline,
     textura horneada con AO, relieve y detalle procedural; 0 = cuerpo/manos, 1 = máscara/hierros/arma),
     **esqueleto y pesos** (rig.py: partes 0–25 con la numeración y jerarquía del juego, máx. 2 huesos
     por vértice; máscara→4, puño y arma→10, garra→16, hombrera→5, accesorios rígidos), pose de muestra
     por skinning. Export: herrero.glb (malla + piel + texturas) y OBJ+MTL.
   - v3 (el usuario: antes del formato, más realismo, tono de ganado y que se note la infección): piel
     más oscura/tostada, ropa y hierros más oscuros; infección desde los bultos (lado izquierdo: cuello,
     hombro, brazo, pecho): venas negras que engordan hacia el foco, piel necrosada gris, borde
     inflamado; 4 tentáculos de Plaga saliendo del cuello (material PLAGA, en body); ojos rojos tras la
     rendija (EYE, en mask); icor negro chorreando de las ranuras de la máscara al peto.
   - v4 (el usuario: "subida grande, camino correcto"; el brazo sano estaba sin tocar y parece de juego
     arcade: quiere que parezca una persona de verdad): anatomía real en los brazos (deltoides, bíceps/
     tríceps separados, masas del antebrazo que se estrechan a una muñeca fina, codo y muñeca óseos),
     clavículas y tendones del cuello; brazo derecho con venda de lino ensangrentada, trapo anudado,
     vello, moreno de antebrazos, articulaciones enrojecidas, lunares, quemaduras de chispa y una
     quemadura vieja; material CLOTH. La pieza body se parte en body (y>1100) y legs → 3 texturas 1024²
     (0 torso/brazos/manos, 1 máscara/hierros/arma, 2 piernas/faldón/botas).
   - v5 (el usuario: proporciones bien; falta detalle en cada punto; "fíjate en el Dr. Salvador y copia
     la forma en que está hecho", que parezca un personaje original del juego). Estudiadas texturas
     reales del disco con models/herrero/tpl.py (decodificador TPL: CMPR, C8+paleta, I4/I8...):
     em18.drs = el Buhonero (no el de la motosierra), em2b.drs = El Gigante. **Aún no localizado el
     .drs del Dr. Salvador** (buscar entre em1x/em2x-em3x por sus texturas). Hallazgos de formato:
     .drs parte 0 = archivo con entradas; em2b: por variante [modelo ~200 KB][~111 KB][~41 KB][TPL
     229 KB con 256²+512²+256²+256² CMPR]; em18: TPL de 256², 256×128 y 128² CMPR + C8 pequeñas. O sea:
     un personaje usa ~1×512² + 3×256² (el Herrero usa 3×1024²: habrá que reducir). Estilo aplicado a
     tex.py: paleta gris-parda desaturada, arrugas finas oscuras con borde claro siguiendo el miembro,
     pliegues largos pintados en la tela, parches cosidos y pespuntes, cuero cuarteado, óxido en
     regueros y arañazos en el hierro.
   - v6: sombreado suave como en el juego (normales del gradiente del campo de distancia en carne/tela/
     cuero; aristas solo en hierro y madera).
   - **FORMATO DEL MODELO DESCIFRADO** (models/tools/re4bin.py lee, view.py dibuja, tpl.py texturas;
     comprobado: los triángulos leídos coinciden con el contador de cada material). Modelo .BIN (GC,
     big-endian), cabecera 0x60:
       0x00 → huesos (16 B: nº parte u8, padre u8, 2 pad, xyz float mm); 0x0C → colores (RGBA8);
       0x10 → UV (s16,s16); 0x14 → tabla de pesos (8 B: 3 huesos u8, nº influencias u8, 3 pesos en %,
       pad); 0x18 u8 nº pesos; 0x19 u8 nº huesos; 0x1A u16 nº materiales; 0x1C → materiales;
       0x30 → posiciones (4×s16: x,y,z, índice de peso; ~15 unidades/mm, escala por confirmar);
       0x34 → normales (4×s8); 0x38 u16 nº posiciones, u16 nº normales; 0x3C fecha; 0x40/0x44 → tablas.
     Material: cabecera 0x20 (0x0C u8 índice de textura, 0x18 u32 tamaño de la lista redondeado a 32,
     0x1C u32 nº triángulos) + lista GX: opcode 0x98 (tira)/0x90/0xA0/0x80, u16 nº vértices, por vértice
     4×u16 = [posición, normal, color, UV]. Los modelos están sueltos dentro de los .drs (buscar
     0x00000060 con fecha 0x2003/0x2004 en +0x3C).
     **Presupuesto real del juego**: Leon 1.484 vértices / ~2.500 triángulos; cuerpo de ganado 770
     vértices / 1.460 triángulos (34 huesos, 5 materiales) + cabeza aparte (114 vért./217 tri) + manos
     aparte; el soldado de la ametralladora (em1d) 2.534 vért./4.520 tri. Hasta 3 huesos por vértice.
     Normales suaves con índice propio (por eso no se ven aristas); el detalle va pintado en texturas
     de 256² (512² como mucho). El Herrero (14.981 tri, 3×1024²) hay que rehacerlo a ~3.000–4.500
     triángulos y 1×512² + 3×256² para que entre.
   - **B79 = primera prueba del Herrero dentro del juego** (el usuario: dejar a Salvador, implementar
     ya). Sustitución EN SITIO (mismos tamaños, sin mover nada) del cuerpo de ganado 34 huesos/770
     vértices (em10.drs entrada 440 @0x3ab040, 32.352 B; el mismo modelo está en em12, em13, em15 y
     em17) y de las texturas 1 y 2 (256² CMPR) del TPL que le sigue (entrada 441; la 0 = cara/manos
     del ganado, intacta). models/herrero/lowpoly/: versión de 887 triángulos/545 vértices (sin arma,
     cadenas ni herraduras; decimado automático, tosco) → game.py escribe el .BIN sobre la plantilla
     del donante (tabla de huesos del donante con NUESTRAS posiciones de las partes 0–25 ×0,95, porque
     s16 a 16 u/mm solo llega a ±2047 mm; pesos de 2 huesos en pasos del 20 %; tiras GX; tablas 0x40/
     0x44 copiadas) y codifica CMPR. mod/mkfiles.py genera mod/files/ (no se sube: datos del juego) y
     mkiso.py reemplaza en la ISO los archivos de mod/files/ (mismo tamaño, por FST). Comprobado
     leyendo el modelo y las texturas desde la ISO parcheada. Escala de posiciones = 16 u/mm (byte
     0x28 = 4 bits fraccionarios, sin confirmar que se pueda cambiar). UV = téxeles (s16).
     Archivo .drs parte 0: [nº][fin de datos][..] + offsets desde 0x10; tras "fin de datos" hay
     ~0x68b20 B sin descifrar (¿tabla de reubicación?) → por eso aún no se mueven entradas ni se
     agrandan. POR VER en la prueba: si carga, qué aldeanos usan ese cuerpo, si el esqueleto toma
     nuestras proporciones, si cabeza y manos del ganado asoman.
   - **B80** (el usuario: B79 "fatal que se vea así" y no sabe qué ganado es). Resuelto el tamaño:
     el archivo de la parte 0 del .drs es [nº][offset del REL dentro de la última entrada][0][0],
     offsets[nº], etiquetas de 4 letras[nº] (BIN, TPL, FCV, SEQ, EFF...), datos; lo de detrás de "fin
     de datos" era el REL (código), no una tabla. mod/mkfiles.py RECONSTRUYE el archivo: entradas BIN+TPL
     nuevas, offsets posteriores +delta, offset del REL +delta, tamaño parte 0 (0x24) y offset parte 1
     (0x4C) +delta (+245.376 B por archivo; comprobado: las otras 696 entradas, el REL y la parte 1
     idénticos). mkiso.py recoloca los archivos que crecen en el hueco de relleno entre el main.dol
     movido y el primer archivo (0x488000…) y actualiza el FST; por eso los parches pasan a ~20 MB por
     disco (xdelta no encuentra los datos movidos; -B grande se queda sin memoria aquí).
     Modelo de juego nuevo (models/herrero/lowpoly, 2.930 triángulos / 1.635 vértices, con arma):
     malla SOLO de formas grandes (model.py simplificado) y todo lo fino (tirantes, bolsillo,
     pespuntes, remaches, vendas, bandas de la máscara, ojos) PINTADO desde el modelo detallado
     (model_hi.py: material + AO evaluados sobre su superficie). TPL nuevo: [0] cara del ganado 256²
     (intacta), [1][2] nuestras 512² CMPR. UV = 1/256 de la textura (comprobado con Leon: texturas
     128×256 con UV hasta 255), así que sirve para 512². Pesos en pasos del 20 % (104 filas ≤ 127,
     el índice de peso de las normales es s8).
     Qué aldeano es: las 5 copias (em10/12/13/15/17) llevan la MISMA ropa: camisa/jersey claro
     grisáceo y pantalón marrón oscuro.
   - **B80 probado: CARGA Y FUNCIONA** (vídeo: casa del principio, el ganado del hacha sale con el cuerpo
     del Herrero, se mueve con sus animaciones). El usuario: la idea final es AÑADIR un enemigo, no
     sustituir; esto es solo prueba. Fallos vistos: (1) se veía el interior → la orientación de los
     triángulos estaba invertida (volumen firmado del juego > 0 en orden de lectura; el nuestro < 0);
     (2) asomaban la cabeza y las manos del ganado original: son modelos aparte (em10: pRHand +0x564,
     pLHand +0x568, pHead +0x56C, cModelInfo*; pHood +0x580); (3) lleva el hacha del ganado (pWeapon
     +0x54C, se deja por ahora).
   - **B81**: game.py escribe la orientación correcta y 'HERR' en +0x58 del BIN; stealth.c
     HerreroFrame busca cada ganado cuyo cuerpo (em+0x15C cModelInfo → +0x0C datos BIN) lleve 'HERR' y
     aplasta la matriz (+0x5C, diagonal a 0, como cPlBody::setKnife) de su cabeza y manos.
   - **B81 probado: "ahora sí, la implementación es bastante buena"**. Modelo sólido, sin cabeza/manos
     del ganado. Vídeo: aún lleva el hacha del ganado además de la viga; texturas lavadas y blandas.
   - **B82**: HerreroFrame oculta también el arma del ganado (cEmWep +0x54C, es un cEm: su cModelInfo
     +0x15C, matriz a 0). Texturas: medido en el disco que las del juego tienen ~1,6× más contraste
     (desviación de luminancia 30–37 frente a 20, misma media ~50): game.py estira el contraste ×1,6 y
     enfoca un poco antes de codificar CMPR.
   - **B82 probado: "muchísimo mejor el aspecto"**. Pide animaciones que peguen con él y quitar el
     rastro del ganado (sigue golpeando como el ganado del hacha).
   - **B83: animaciones propias** (models/herrero/anim/mkanim.py → mod/c/herrero_mot.h; animprev.py
     las dibuja con la malla). Formato de movimiento: canal kind 1 de la parte 0 = avance de raíz (lo
     que MotionMove usa para mover al enemigo), kind 4 parte 0 = cadera, kind 2 = rotaciones locales
     (euler zyx). Todo FK (como el HUNK del disco), posiciones ×0,95. Andar pesado (64 frames, 17 mm/
     frame, encorvado, balanceo, arrastra el yunque detrás) y golpe por encima de la cabeza (84 frames:
     carga 0–24, golpe 24–33, impacto quieto, vuelta; secuencia: Free 8 en 0–19 sigue girando hacia
     León, 0x20 en 24 sonido, Free 1 en 28–34 comprobación de golpe). HerreroFrame los pone en lugar
     de los del ganado: rutina 1 0x10 Walk / 0x11 Dash → andar; 0x26 AxeAtk → golpe; 0x24 ThrowAxe →
     AxeAtk. El daño sigue siendo el del juego (AxeAtk barre desde la matriz del hacha oculta, ~1 m
     a lo largo del mango): POR COMPROBAR si coincide con el yunque.
   - **B84**: el usuario pasa un golpe de Mixamo que le gusta (anim/mixamo/herrero/
     Heavy_Weapon_Swing.fbx, arma a dos manos, 5,2 s). mkanim.swing(): retarget por rotaciones de
     mundo (los dos esqueletos enlazan en T), frames 36–140 del clip (golpe abajo en 76–86 → Free 1;
     sonido 4 antes; sigue girando hacia León hasta 8 antes). El puño se gira para que la viga siga el
     mango (mano izq. → mano der. del clip), la viga se levanta si el yunque atravesaría el suelo, la
     garra va por IK al mango 270 mm detrás de la empuñadura, la cadera se ajusta para que los pies
     toquen el suelo. Modelo: mango alargado (empuñadura hasta −330 mm, pomo −365) para las dos manos
     (model.py y model_hi.py). Sustituye al golpe procedural de B83 (smash() se queda en el archivo).
   - **B85**: golpe dañino propio (stealth.c HerreroHit): una vez por golpe, entre los frames HR_HIT0–1,
     posición del yunque = matriz de la parte 10 × HR_ANVIL_*; si León está a <850 mm en horizontal
     y −600<dy<1200 → LifeDownSet2(pl, 760, 0, flag 1 = nunca mata) + PlSetDamage(4 frente / 5
     espalda = derribo). La seq ya no lleva Free 1 (el chequeo del hacha del Ganado se queda fuera).
     Pack Creature_NPC_Pack (anim/mixamo/herrero/pack): walk2 = 'mutant walking' al 0,55 (78 fr) con
     el arma arrastrando, idle = 'mutant breathing idle' (Wait/Stay/AttackWait), flex = 'mutant flexing
     muscles' (Find/Threat). Las animaciones ya NO van en el código (no cabían en el hueco del dol,
     assert de bake.py): mkanim.py escribe mod/data/herrero_anim.bin (8 offsets: mot/seq de walk,
     smash, idle, flex) y game.py lo añade al final del BIN con su offset en BIN+0x5C; HerreroFrame
     las coge de ahí. BIN 160 KB. Sin usar aún del pack: swiping (2º ataque), dying, run, turns.
   - **B86** (el usuario: daño perfecto, pero que tire al suelo; hueco por el que se ve el interior; andar
     y golpe algo más rápidos; grito si tarda en alcanzarte): derribo = PlSetDamage(8) (el del
     barril/dinamita 0x800CF6B8 y el empujón 0x800D744C; 4/5 solo eran tambaleo de golpe bajo; 6/7/9
     son otros) + vibración 0x80138624(pG+72…, 7, 1); antes se gira a León hacia el Herrero. Tipos de
     PlSetDamage: 0–5 alto/medio/bajo × frente/espalda, 7/8 → rutina (1,1), 9 → (1,2); f1=123.0 = sin
     dirección. Hueco: el delantal (LEATHER de 'legs') y las piezas de 'acc' son láminas abiertas; el
     juego no pinta caras traseras → game.py les añade la cara de atrás (3206 tris). Diagnóstico:
     /tmp/holes (raster con caras traseras visibles en rojo, posado con las animaciones).
     Andar al 70 % (61 fr, ~31 mm/fr), golpe ×1,3 (80 fr, impacto 31–40). Grito procedural roar()
     (96 fr: se encoge, echa la cabeza atrás, garra arriba, tiembla) sobre el breathing idle; HrSlot por
     Herrero: 240 frames andando (Walk/Dash) sin golpear → grito, luego sigue. Pack con 10 offsets.
   - **B87**: hombrera = cáscara cerrada de 14 mm (era un casquete macizo recortado dentro del cuerpo →
     abierto); 'acc' ya no se recorta contra el cuerpo (mesh.py NOCULL) y game.py solo dobla sus partes
     abiertas (brazaletes, sheets.open_sheets). Grito: brazo de la garra por IK (girar huesos daba el codo
     al revés), codo hacia fuera/abajo. Pasos (Se 1/2 como los Ganados) en el andar, frames 21/48.
     Sonidos de seq de em10: Se 1/2 pasos andar, 3/4 pasos correr, 5/6 golpes de cuerpo, 120, 62
     (serie), 124–127, 148, 169–171 sin identificar. GRITO GRAVE pendiente: no hay forma de oírlos
     aquí; los bancos están en los .das de cada sala (core.das común) → descifrar y elegir/sintetizar.
   - PENDIENTE Herrero: grito GRAVE (usuario).
   - **B88 – Herrero como enemigo NUEVO + escena del granero** (granja r103, stage 1 room 3; el Ganado de
     arriba es la entrada 99 de emleon00.esl, id 0x12, horca). Se acabó sustituir: em10/13/15/17 vuelven
     a ser los originales y em12.drs lleva 4 entradas extra en sus huecos vacíos 690–693 (antes del REL):
     BIN del Herrero, su TPL, una COPIA de la tabla de offsets del archivo rebasada a sí misma con las
     palabras 0x1BC/0x1BD (EM10_BIN_BODY/TPL_BODY de Em10Set) apuntando a nuestro cuerpo, y la textura I4
     del panel de sigilo (mod/tools/mktut.py). barn.c crea el Herrero como EmSetEvent PAL (0x800CB76C:
     create 0x801DE5F8 sobre EmMgr 0x80283160, campos de la lista, move por la vtable +40/+44) pero antes
     del primer move apunta su subArc/subArc2 (+0x378/+0x37C) a esa tabla: ARC(no) sigue siendo válido
     para todo y da nuestro cuerpo (tipo 0, flag 0x20000000 = arma clase hacha → rutina 0x26 = mazazo).
     Datos PAL: Em_list pG+0x52F4 (32 B), stage/room pG+0x4FA8/9, Stop_flg pG+0x170 (bits MSB primero:
     KEY 0x80000000, CAMERA 0x40000000 = CameraMove no mueve CamCtrl y usa pG->Camera.param tal cual,
     EM 0x20000000, PL 0x10000000), pG->Camera.param pG+0x74+0xA4 (Campos, Target, Roll, Fovy, Up +0xC4),
     SceAt OT pS+140 (be_flg +0x34, id +0x35, act_type +0x4A: 2 saltar fuera / 4 saltar abajo; escalera
     id 0x10, pos +0x5C, ang +0x68), em alive (be_flag & 0x201)==1, emset_no +0x398.
     Flujo: León arriba (y>2,5 m, cerca del Ganado vivo, libre 20 frames) → panel (juego parado con
     KEY|EM|PL, se cierra con A) y ventanas de salto desactivadas; muere el Ganado (y León libre 50 fr) →
     escena 300 fr: cámara a la cara de León, f36 aparece el Herrero en la "puerta", f40 SndCall(6,0x37)
     (puerta rota, emdoor) + temblor, f52–86 León se gira, f96+ cámara por encima del hombro siguiendo al
     Herrero; A salta tras 120 fr; luego se reactivan las ventanas. PUERTA: aún estimada desde la escalera
     (DOOR_KNOWN 0) → la prueba muestra x z y ángulo de León arriba a la izquierda en r103 para fijarla.
   - **B89**: B88 no hacía nada: barn.c pedía pl r_no_0 == 1, pero la rutina normal de León es 0
     (weapon.c CanSwap: r_no_0 0, r_no_1 ≤ 3 o 6). Puerta: captura del usuario con León en la puerta
     lateral (x −13562, z −12198, ángulo 0 = mirando a +z) viendo al fondo la abertura grande bajo el
     Ganado (z −1770) → puerta estimada (−13650, +2300) (el Ganado de abajo de la lista, entrada 96, está
     en (−13700, 2590)). Números de posición más separados.
   - **B90** (vídeo B89: el panel sale bien; la escena arranca con León agachado tras el sigilo, la
     cámara no llega a enfocar al Herrero —la puerta queda justo DEBAJO de León, el suelo de arriba la
     tapa— y sale "COGER" del objeto que suelta el Ganado; puerta correcta según el usuario): la escena
     levanta a León (crouch.c CrouchStand), bloquea comprobaciones de áreas y botones de acción
     (Stop_flg SCE_AT 0x00400000, ACTBTN 0x100) y el 2º plano pasa a la planta baja, de frente a la
     puerta (cámara en puerta + (900, 1350, −4300)) siguiendo al Herrero. Datos del vídeo: León arriba
     en (−12630, −5635), altura 3334; el Ganado de la horca muere en (−14190, −2664).
   - **B91** (vídeo B90, dos pruebas: en una el Herrero sale pero no anda, en otra no sale; el Ganado de
     fuera detecta a León durante la escena): flag del Herrero 0x20000001 (bit 1: em10 Wait llama a
     setFindPL → sabe dónde está León y va a por él; 0x40 = siempre activo); durante la escena SPF_EM
     (cEmMgr::move PAL 0x800C994C no mueve a nadie) y barn.c mueve solo a León y al Herrero con emMove
     PAL 0x800C9D5C; cámara de la planta baja más atrás (puerta + (1100, 1600, −6500), fovy 50→42).
     Diagnóstico en pantalla (5º número, verde): 1 = create falló, 2 = archivo raro, 3 = creado; con
     Herrero vivo 3000 + r_no_0·100 + r_no_1.
   - **B92** (vídeo B91: diagnóstico 3116 = creado y en Walk 0x10, pero INVISIBLE durante la escena →
     con SPF_EM tampoco se calcula su modelo; salía al acabar): la escena usa la pausa de eventos del
     propio juego: Status_flg[1] pG+0x501C bit 0x10000000 (STA_SUSPEND, emMove PAL lo mira) y be_flag
     0x800 en León y el Herrero → solo ellos se mueven (como sce_com.cpp). Ventana: también act_type 26
     (ACT_JUMP, "SALTAR"). Música: status +0x3C4 bit 0 (en combate) del Herrero mientras vive → música de
     combate del juego. Derribo arriba: si León está a >1 m de altura se le clava x/z durante el derribo
     (stealth.c hr_pin, 150 frames mientras r_no_0 == 1) para que no salga volando del altillo. Huecos:
     mesh.py ya no recorta nada (NOCULL total), puño y garra cerrados en la muñeca (plano a 41,3 mm, no
     justo en la rejilla), CLAW_BOX ampliada (el pulgar se salía → abierto), puño 170 y garra 320 tris,
     game.py dobla también el peto (LEATHER de 'body'). Pendiente: sonido de sorpresa (no sé el SE).
   - **B93** (vídeo B92: sigue invisible con 3116; la ventana "SALTAR SOBRE" = ACT_JUMP_OVER 5; música
     nada): la invisibilidad era el dibujo: cModel be_flag bit 2 (se dibuja) y alfa +0x154 solo los pone
     em10 Wait cuando León está cerca; el Herrero con flag 1 se salta Wait → se fuerzan cada frame
     mientras vive. Ventanas: tipos 2, 4, 5, 26. Música: el estado "en combate" no es la música (solo lo
     usa la cámara); la de combate de la granja es el stream de sala (r103.cpp la arranca a los 30 s con
     SndRoomStrStart(1, 0xF, 1)) → la escena la arranca al mostrar al Herrero (PAL 0x800586F8).
   - Lag al cambiar de arma (usuario, tras B80+): hipótesis: prefetch.c necesita un bloque libre del heap
     para leer el wepXX.drs por adelantado; con los em*.drs inflados por el Herrero (+450 KB cada uno) no
     cabe y vuelve la lectura bloqueante (~250 ms). B88 deja solo em12 grande. Pendiente confirmar.
   - **El Rastrero** (2º enemigo, bocetos del usuario: Ganado mutado rápido que va a 4 patas unos pasos para
     acercarse, poca vida, muy ágil): models/rastrero (mismo proceso que el Herrero, /home/claude/rastrero).
     Capucha de saco (ojos rotos, boca cosida, sangre), camisa rota en el hombro izq. y en la columna,
     tirantes, delantal hecho jirones, pantalón roto, botas; hoz oxidada en la mano der.; brazo izq. de la
     Plaga (fibras rojas, púas de hueso, garras de hueso); púas en la columna. Materiales nuevos SACK, BONE.
     Hoja 1 de diseño: rastrero_sheet.png (13.623 tris de detalle). Usuario: le falta detalle, será el
     CARNICERO del pueblo → hoja 2 carnicero_sheet.png (20.443 tris): delantal de carnicero con peto, tira
     al cuello, lazo atrás, bolsillo, remaches y cortes; brazal de cuero en el antebrazo der.; cinturón con
     cuchilla en anilla, cuchillo en funda, chaira y dos ganchos de carne con cadena; costuras, cuello,
     vueltas del pantalón, remiendo; capucha con parche cosido, hilos y boca hundida; sangre de carnicero
     (peto/delantal, antebrazo der., salpicaduras en pantalón/botas, hoz). Siguiente: opinión del usuario → pose a
     4 patas con IK, low-poly/formato del juego.
   - **Carnicero → formato del juego (B88, sin insertar aún)**: /home/claude/carnicero_lp (copia en
     models/carnicero/lowpoly): model.py = las formas de model_hi.py (el detallado) malladas gruesas
     (body 2000, mask 420, fist 120, claw 330, acc 260, weapon 300 → 3604 tris con dobles caras),
     tex.py pinta 2×512² leyendo materiales del detallado (hi_field), game.py = escritor del Herrero
     con firma 'CARN' en BIN+0x58 y pack de movimientos en +0x5C (mod/data/carnicero.bin + 2 cmpr).
     models/carnicero/anim/mkcarn.py (reutiliza mkanim.py del Herrero con el rig del Carnicero):
     run4 = galope a 4 patas (20 fr por zancada, 150 mm/fr ≈ 4,5 m/s, espalda casi horizontal, la
     garra y el puño de la hoz apoyados; pisadas Se 3/4) y swipe = salto con zarpazo (40 fr, golpe
     17–24). Falta: insertarlo (como el Herrero: entradas extra en el em*.drs de su sala + subArc
     falso), conectar rutinas (andar → erguido corto; lejos de León → run4; cerca → swipe; poca vida).
   - PLAN enemigo NUEVO (no sustituir): ESL (emleon00–09.esl, 255 entradas × 32 B) → entrada Ganado
     (id 0x10) con una marca en un campo libre; hook en la creación/carga de modelo de em10: si lleva
     la marca, usar el BIN/TPL del Herrero añadidos como entradas NUEVAS de em10.drs (restaurar las
     originales de em10/12/13/15/17), vida propia, reacciones/muerte propias. Falta: formato de la
     entrada ESL, cómo elige em10 cuerpo/cabeza, dónde engancharse.
   - PENDIENTE: localizar al Dr. Salvador (no es em18 = Buhonero ni em2b = Gigante; mirar modelos de
     em10–em1f con view.py), escala exacta de posiciones, tablas 0x40/0x44, resto de la cabecera del
     material, escritor de .BIN/TPL y cómo cargar un enemigo nuevo.
6. Más adelante: gesto de cambio de arma corriendo, interruptor Moderno/Clásico, tabla de controles
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
