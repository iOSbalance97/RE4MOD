# Plan: salas del REmake de GameCube dentro de RE4 (desde H14)

Base: discos RE1 GC PAL (GBIP08) del usuario (repo privado UC-rip, release "Re1/re5"). En /home/claude/re1gc.
Formato (ver herramientas/remake/LEEME.md): .dat = mallas (sec. 0 simple/colisión, sec. 1 detallada), disparadores
(puntero en 0x20: registros 0x34: flags, quad XZ, tipo, sub, parámetro; tipo 0 = puerta n), zonas de cámara (2HCC);
.bgz = bloques por cámara (ojo, objetivo, giro, apertura VERTICAL, 4:3, diestro) + fondo JPEG 512x448.
Coordenadas propias de cada sala (no compartidas): las conexiones salen de los planos de progresión (VGCartography).

Pasos:
1. [hecho] Prueba H14: bar del piano (r10f) en el hueco r117. Proporción correcta en el juego.
2. [en curso] Convertir todas las salas (work/convertir_todas.sh): proyección de fondos + relleno con textura vecina.
3. Identificar cada rNNN del REmake con su nombre en los planos (mansión 1F/2F/3F/B1, patio, residencia,
   acuario, cuevas, altar, laboratorio, helipuerto) y sus puertas (disparadores tipo 0, posición en planta).
4. Reparto en huecos de RE4 (St1 29 + St2 42 = 71; el REmake tiene ~90 salas: juntar o dejar fuera las mínimas).
5. Enlaces según los planos; montar con montar3 (salas 're_*': luz horneada, sin fuego extra).
6. Calidad: superficies limpias donde ninguna cámara veía (techos, rincones) con texturas UC/RE4/RE5; brillo.
7. Verificar (verificar_H12, recorrido_H12), parche. Los parches con contenido del REmake NO van a RE4MOD (público).
