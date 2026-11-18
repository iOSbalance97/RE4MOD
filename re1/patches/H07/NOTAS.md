# H07 — base limpia: colisión de UC, objetos, puertas de botón y sin scripts de RE4

Parche sobre el **disco 1 PAL limpio**. Entrada: puerta norte del pueblo → vestíbulo. La puerta principal del
vestíbulo vuelve al pueblo. Todas las puertas se abren con el botón de acción (como las del juego).

## Cambios respecto a H06
- **Colisión**: la de personajes del propio UC (`rNNN_chit.col`, formato BGHT: vértices sueltos, normales, atributo
  por triángulo) en vez de la generada. Escaleras como rampas, piso de arriba del vestíbulo y galería del comedor.
- **Salas bien identificadas**: con esa colisión, r111 de UC resulta ser una sala de la planta alta (el bosque solo se
  ve por las ventanas). Conexiones rehechas (20 + salida): comprobadas con los objetos puerta de UC y renders de cada lado.
- **Objetos**: cada `rNNNbgobj.arc` trae un modelo `rNNN_obj` cuyos huesos son las colocaciones (matriz de mundo en +0x70):
  puertas, sillas, mesas, candelabros, cuadros, jarrones, armaduras, libros...
- **Paredes que faltaban**: el filtro del reflejo del suelo quitaba todo lo que bajaba de y=0 (≈4.800 triángulos del
  vestíbulo). El reflejo son modelos aparte (`*_MirrorModel`, `*_mirror`): ahora se quitan por nombre.
- **Por las puertas se ve la sala de al lado** (geometría vecina a <5 m del umbral), como en UC; nada de huecos negros.
- **Sin scripts de RE4**: en los cuatro `Rel/st1_N.rel` la tabla de salas (setTbl, una copia por módulo) apunta Init/Main
  de nuestras 16 salas a una función vacía (blr) del mismo módulo (se cambia el addend de las reubicaciones).
- **Sin enemigos**: `etc/emleon00.esl` y `emleon01.esl` sin las entradas de nuestras salas (184 + 65).
- **Datos sueltos de RE4 anulados** (el juego comprueba si existen): objetos recogibles (ITA), objetos sueltos (ETS/ETM),
  sonidos/efectos/cámaras por área (ESE/EAR/SAR/CAM/FSE), efectos (EFF) y datos de cinemáticas (FCV/SEQ/BIN/TPL).
- Límite de 254 texturas por sala (índice de 1 byte): las menos vistas usan la más parecida (vestíbulo 6, comedor 15).

## Comprobado
SAT válidos (satcheck) en las 15 salas; colisión alineada con el suelo visible; 42 puertas simuladas con
areaHitCheck_xz4: ninguna llegada dentro de un área, todas sobre suelo, entrada del pueblo libre, las 15 salas
alcanzables desde el vestíbulo; tabla de salas releída tras el parche (Init/Main = blr); salas ≤ 4,65 MB
descomprimidas (original máx. 6,1 MB); parche aplicado = ISO esperada, 22 ficheros idénticos, sin solapes.

## Sin probar en juego
Iluminación (LIT original de cada sala), si la partida guardada trae la lista de enemigos ya cargada (se recarga al
cambiar entre salas ≤r10b y >r10b), sonido de pasos por defecto (FSE anulado).
