# B34

- Precarga con una sola lectura DMA del SDK (DVDReadAsyncPrio, 0x80075AF8) en vez de la cola del juego (que leia 128 KB por fotograma): llega en cuanto el lector lo da.
- El cambio ya no usa la tarea 1 (podia estar ocupada -> cambio de golpe desde disco = tiron grande corriendo). Ahora va paso a paso desde el bucle principal (ModFrame) y el cambio se hace en un solo paso con la copia en memoria.
- Quieto: funda 5 fotogramas, vuelta 6; el cambio en cuanto la mano casi llega y el archivo esta.
- Nota: la pistola en ARRIBA no cambia corriendo hacia delante porque OmniStation mete el stick en la cruceta (stick arriba = cruceta arriba) y el parche no puede distinguir la pulsacion real.
