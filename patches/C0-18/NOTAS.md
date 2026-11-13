# C0-18 — contenedores, antorchas y revisión de la captura

- Contenedores de la isla (r310, disco 2: cuerpo = bin 9 del SMD, 3424 B; textura = imagen 8 del TPL, 512x128
  CMPR con 5 mips) en lugar de los barriles. mkfiles.py los pone al final de em12.drs (cabecera de imagen +
  bin + textura, c/ch0_cont.h). ch0.c: se leen en Ch0Ita; en Ch0Ets el cuerpo sustituye a et1100.bin del ETM
  (ETS - 0x9CF60, solo si la palabra 0 sigue siendo 0x40) con dcbf, y la imagen 0 del TPL del EFM 9 (et11.eff)
  pasa a ser la nuestra (dato como puntero, unpacked 1). El barril id 30 pasa a id 17. Cinco sitios junto a la
  pared más cercana (CONT); el primero, en la boca del callejón hacia la plaza (el callejón mide 2,2 m y lo
  cerraba). Empuje rectangular para Ashley (ContPush). Escondida: no se dibuja (be_flag bit 2).
- Antorchas: em11 (entradas 0x26A/0x26B) copiadas en los huecos vacíos de em17.drs y Em17WeaponSet (REL .text
  0x440A8-0x440F0) cambiada para llenar mot[69]/[70]: el juego crea la antorcha (Wep 6) y su fuego (0x10/0x49).
  El ganado de la casa (HouseGanado) también lleva antorcha (antes dinamita).
- Captura: el agarre del juego a Ashley cuelga (PC 0x8012DA30, lectura de un puntero de texto basura). Ahora
  un perseguidor a < 1,6 m la captura antes (grab), todos se quedan quietos y el fundido empieza antes.
- Atascos: un ganado que camina y casi no se mueve en 2,5 s rodea por un lado (2,2 m) y sigue a su destino.
- Escena de la llave: el que sube va puerta → centro de la sala → pie de la escalera → arriba (UPW) y luego a
  por ella; si se atasca en un tramo 10 s, pasa al punto (ella está arriba y no lo ve).
