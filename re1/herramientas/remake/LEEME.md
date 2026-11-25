# Salas del REmake de GameCube (GBIP08) -> RE4

- `rvz.py disco.rvz iso salida.iso`: RVZ de GameCube a ISO.
- `remake.py`: lee `stN/rNNN.dat` (malla de la sala: sección 0 simple / colisión, sección 1 detallada) y `rNNN.bgz`
  (un bloque por cámara: ojo, objetivo, giro, apertura vertical en grados, formato 4:3, fondo JPEG 512x448).
- `remake_sala.py st rNNN salida`: malla detallada subdividida + cada triángulo texturizado con el fondo de la
  cámara que mejor lo ve (sin nada delante). Salen sala.obj + fondos + colision.obj.
- `obj2sat.py`: colisión a SAT/EAT de RE4.

Los parches que llevan contenido del REmake NO se suben a este repositorio público.

## H26: estilo del vestíbulo en todas las salas
- `convertir_uc.sh u:r:st`: salas con modelo de UC (uc_sala_v5.py). Paredes y techos grandes van al atlas de luz
  continua (`ATLAS_PAREDES=1`, sin rombos de luz); puertas, muebles, barandillas y suelos siguen nítidos.
- `convertir_s4.sh rNNN`: salas sin UC (remake_sala4.py). Toda la sala en atlas; el color y la luz salen de los fondos
  del REmake proyectados con z-buffer, y el detalle fino (<10 cm) de texturas de la mansión de UC (zócalo de madera,
  yeso, papel pintado, techo, suelos), elegidas por píxel con el corte del zócalo detectado por altura.
  La densidad depende de la cercanía a donde se camina (en escalones). Lámparas: zonas brillantes de los fondos.
- montar_remake.py usa re4/re_{r}_uc, si no re4/re_{r}_s4, con sus luces (salas_uc5 o salas4/{r}/luces.json).
