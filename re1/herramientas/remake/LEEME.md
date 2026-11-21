# Salas del REmake de GameCube (GBIP08) -> RE4

- `rvz.py disco.rvz iso salida.iso`: RVZ de GameCube a ISO.
- `remake.py`: lee `stN/rNNN.dat` (malla de la sala: sección 0 simple / colisión, sección 1 detallada) y `rNNN.bgz`
  (un bloque por cámara: ojo, objetivo, giro, apertura vertical en grados, formato 4:3, fondo JPEG 512x448).
- `remake_sala.py st rNNN salida`: malla detallada subdividida + cada triángulo texturizado con el fondo de la
  cámara que mejor lo ve (sin nada delante). Salen sala.obj + fondos + colision.obj.
- `obj2sat.py`: colisión a SAT/EAT de RE4.

Los parches que llevan contenido del REmake NO se suben a este repositorio público.
