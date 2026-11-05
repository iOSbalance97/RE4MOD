# B25 (prueba con medidas)

- La lectura del arma usa el modo de interrupcion del juego (0x8101, el mismo que usa para cargar enemigos en partida): se lee de seguido en vez de un trozo por fotograma, la espera con la mano en la funda deberia acortarse.
- Medidas en pantalla 4 s tras cada cambio (arriba a la izquierda): [fotogramas de espera] [ms soltar arma] [ms leer+enlazar] [ms montar arma nueva].
- Incluye B24.
