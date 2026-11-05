# B31 (precarga)

- Al pulsar la cruceta se pide un bloque temporal al montón del juego y se lee ahi el archivo del arma nueva en segundo plano (lectura normal asincrona); el arma vieja sigue intacta.
- En el cambio, ReadWepData hace su lectura de golpe como siempre, pero cDvdQueue::fileReadAsync (0x800C5E84) se contesta desde la copia en memoria: el propio juego reparte REL, archivo y sonidos a velocidad de memoria.
- Sin bloque libre o con otro personaje: lectura normal (B30). El bloque se libera al terminar.
- Recuadro de prueba: [lecturas servidas desde memoria, 0 = disco] [ms soltar] [ms cargar] [ms montar].
