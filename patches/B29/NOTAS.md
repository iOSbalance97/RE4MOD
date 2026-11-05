# B29

- Medidas de B28: soltar 0 ms, montar 0 ms, leer 215-330 ms (una vez 570). La causa: ReadWepData pide la lectura con el modo 0x8001 y el bit 0 la hace BLOQUEANTE (blockRead): los ~250 ms se comen de golpe en un fotograma, sin importar desde que tarea se llame.
- Ahora modo 0x8000: la cola del juego lee en la tarea 3 un trozo de 128 KB por fotograma y ReadWepData espera con TaskSleep(1), asi que el juego sigue dibujando.
- La lectura empieza 3 fotogramas antes de que la mano llegue a la funda.
- Recuadro: [fotogramas aprox. de la carga] [ms soltar] [ms carga, total] [ms montar].
