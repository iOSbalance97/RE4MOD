# C0-16 — C0-15 + ventana del tejado sin cristal

- La ventana de arriba que da al tejado (ETS 8, -938 4200 -13150) se rompe sola durante la intro (un golpe fuerte
  en su ranura de daño: arma 0x10, grupo 2 → hp 0); el juego la guarda rota, así Ashley pasa sin la animación de
  León de romperla.
- Contenedor de la isla (en curso): r310, cuerpo = bin 9 (1920 B), tapa = bin 8; ambos usan la textura 8 del
  TPL de la sala (54 texturas). Plan: TPL de una textura + bins con el índice a 0, cargados del disco y puestos
  en lugar del modelo de barril (et1100) o como objetos.
- Antorcha (en curso): los módulos de zelotes (em11/em1a/em1c...) tienen mot[69]/[70]; falta crear el arma y
  su fuego a mano en los ganados del pueblo.
