# H12 — escenario completo: mansión, patio, cuevas, residencia y laboratorio

Parche sobre el **disco 1 PAL limpio** (base: H11). 62 salas de RE4 montadas y conectadas entre sí.
Esquema de conexiones: `conexiones.png`.

## Arreglos en las salas que ya había (UC de la mansión)
- **Planta alta del vestíbulo**: la colisión de UC ahí iba 20–50 cm por encima del suelo que se ve
  (Leon flotaba y se salía por los bordes). Rehecha con la altura del suelo visible (rejilla de 0,4 m).
- **Envolvente** en todas las salas (`uc_envolvente.py`): UC solo modela lo que ve la cámara de su recorrido.
  Donde falta pared, techo o suelo se pone una pared/techo/losa con la textura de la propia sala, 30 cm por detrás
  de la geometría real (solo se ve donde había hueco). Rayos que se escapan al vacío desde puntos pisables:
  comedor 13 % → 2 %, pasillo oeste 6 % → 2 %, r114 7 % → 3 %, r111 12 % → 8 %, el resto ≈ 0 %.
- Puertas de la mansión que no llevaban a ningún sitio: ahora llevan a las salas nuevas (11 puertas reales de UC +
  una entrada al altar en el hueco bajo la escalera del vestíbulo).

## Salas nuevas (generadas con texturas de UC y de RE4)
Con un generador propio (`rgen.py` + `mundo_suites.py`): suelo, zócalo, papel pintado, moldura, techo, puertas
cerradas con marco, pasos abiertos entre estancias, escaleras con rampa de colisión, muebles (mesas, estanterías,
camas, piano, estatuas, lápidas, tanques, consolas), cuadros, velas con fuego y luz, lámparas en laboratorio/cuevas.
Paredes de roca con relieve en las cuevas. Texturas de RE4: piedra y puertas del castillo (cripta, sótano, tumba),
madera del pueblo (cabaña, cobertizo, habitación de Lisa), metal del castillo (caldera, laboratorio).

| Hueco | Sala | Estancias de RE1 que contiene |
|---|---|---|
| r117 | te_bar | Sala de té, bar, escalera oeste exterior, cocina (B1) |
| r118 | norte | Pasillo norte, sala del tigre, dormitorio del investigador, invernadero, escalera oeste interior, botiquín, trastero |
| r119 | arte | Sala de arte, sala de los espejos |
| r11a | oscuro | Pasillo oscuro, estudio del patio, galería grande |
| r11b | cementerio | Cementerio, bajada a la cripta, cripta, pasillos de hormigón |
| r11c | techado | Pasillo techado, cobertizo del jardín |
| r11d | bano | Pasillo sinuoso, baño, caldera exterior |
| r11e | salon | Sala del techo trampa, sala de estar |
| r11f | pasillo_c | Pasillo en C, sala de descanso, biblioteca pequeña, comedor pequeño |
| r200 | balcones | Balcón exterior, terraza |
| r201 | ciervo | Sala del ciervo, pasaje de la muerte, entrada al ático, ático |
| r202 | dormitorio | Dormitorio, estudio |
| r203 | ascensor | Pasillo del ascensor, sala de las columnas, sala de materiales, sala de la trampa, pasaje secreto |
| r204 | espejos | Pasillo de los espejos, sala de trofeos |
| r205 | altar | Escalera bajo el vestíbulo, tumba de Jessica |
| r206 | piscina | Camino en zigzag, piscina, cascada |
| r207 | cabana | Sendero del bosque, lápida pequeña, cabaña |
| r208 | cuevas_b1 | Pasajes, sala del generador, sala de la araña, sala de Enrico |
| r209 | cuevas_b2 | Pasaje sinuoso, compactador de basura, almacén subterráneo, habitación de Lisa |
| r20a | habitaciones | Habitaciones 001, 002 y 003 con sus baños |
| r20b | residencia | Sala de recreo, galería, enfermería, almacén |
| r20c | lab_entrada | Entrada del laboratorio, pasaje al helipuerto, sala del baúl, escalera, sala de datos visuales |
| r20d | lab_b3 | Morgue, rayos X, quirófano, sala del cirujano, celda, pasillo de la clave, control de energía |

## Salas de UC de fuera de la mansión (en la fase 2)
Patio r116/r117/r118/r119, cuevas r120/r121/r122, residencia r123/r125/r126/r130, acuario r127/r128,
laboratorio r133/r134/r135/r137/r138/r139/r140/r142, helipuerto r144. Huecos r20e…r227 (ver `mundo.py`).
Convertidas igual que la mansión (envolvente incluida; en exteriores sin techo). Puertas solo-AEV en los extremos
de lo pisable (el punto se ajusta al suelo de la colisión de UC); una lámpara encima de cada puerta para orientarse.

## Cómo está montado
- Fase 1 (St1): mansión de UC + 9 salas nuevas. Fase 2 (St2, también en el disco 1): el resto. Las puertas entre fases
  son como la del pueblo al castillo del juego original (AEV con fase de destino).
- Scripts de sala vaciados en `st1_*.rel` y `st2_*.rel`; enemigos quitados de esas salas en todos los `emleon0x.esl`.
- Todas las salas con oscuridad, linterna y fuego (como H11). Cada sala ≤ su tamaño original (r120: fuera su TEX
  para compensar el AEV nuevo).

## Comprobado
62 salas; todas alcanzables desde el vestíbulo; cada puerta con vuelta (salvo las del vestíbulo de inicio r103, que
vuelven al vestíbulo normal r113, como en H11); llegadas sobre suelo pisable y fuera de las áreas de puerta del
destino; antorchas = luces de antorcha; tamaños. Parche = ISO esperada (ida y vuelta con xdelta).

## Sin probar en juego (pendiente)
De H11: dirección de la linterna, altura de las llamas, cantidad de luz, si la puerta automática de r120 salta
nada más empezar, puertas 09 y 24. De H12: cambio de fase St1↔St2 con los scripts vaciados, colisión de las salas
nuevas (paredes en las dos caras), escaleras generadas, que el área de las puertas solo-AEV caiga donde se espera.
