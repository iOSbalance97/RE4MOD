# H11 — partida nueva en el hall, puertas cerradas, oscuridad + linterna + fuego

Parche sobre el **disco 1 PAL limpio**. Base: H10 (que funciona).

## Partida nueva → hall
La partida nueva empieza en St1/r120. r120 lleva ahora un AEV con una puerta automática (trg 1 = salta mientras Leon
está dentro) que cubre toda la sala y lleva a la entrada del vestíbulo (r103). Sus scripts (Rel) y enemigos (ESL),
fuera. Se ve r120 un instante y aparece el vestíbulo.

## Puertas cerradas
- Fuera las hojas abiertas/entreabiertas del recorrido de cámara de UC junto a los umbrales.
- En cada umbral sin hoja cerrada: puerta de UC (de la propia sala; doble si el hueco > 1,3 m) ajustada al hueco,
  medido en las paredes de la colisión de UC (o en la geometría visible si la colisión lo cierra).
- Ya no se añade la geometría de la sala vecina (con la puerta cerrada no se ve): salas más ligeras, texturas de 256 px.

## Ambiente
- LIT: ambiente casi negro, niebla negra 1,5–38 m; luces de Leon de la sala original a la mitad.
- **Linterna**: foco (tipo 3) pegado a Leon (ParentType 1, nº 0 = Leon), a 1,25 m de alto y 0,25 m delante,
  cono de 28°, alcance 16 m, mirando al frente y un poco abajo.
- **Fuego**: en las puntas de velas, candelabros (candle*, candlestand*, shokudai*) y anillo de las arañas (chandelier)
  de UC: antorcha TAIMATU01 de RE4 (etc 0x14, ETM et1400.bin/tpl + et14.eff de r10c) con el modelo colapsado → solo la
  llama; cada una con su luz naranja parpadeante (tipo 2, id 1, pegada a la antorcha: ParentType 3). Máx. 16 por sala.
- Lámparas (light*, lump*): luz cálida suave sin llama (máx. 10).
- EAR: 32 áreas de efectos que cubren todo (los efectos se muestran por áreas; las originales estaban en otro sitio).

## Comprobado
LIT releído (cortes, ≤32 luces, cada luz de antorcha con su antorcha), ETS/ETM (ficheros que pide Et14_init), EAR,
texturas ≤240, salas ≤ tamaño original, 42 puertas + rescate + arranque simulados sin problemas, parche = ISO esperada.

## Sin probar en juego
Dirección exacta de la linterna (eje del hueso 0 de Leon), altura de la llama respecto a la punta (supuesta a 30 cm
del origen de la antorcha), si las luces de antorcha dan suficiente luz con el ambiente tan oscuro.
