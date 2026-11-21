# H13 — arreglos sobre H12: pasarela del vestíbulo, cámaras y luz

- **Planta alta del vestíbulo**: UC solo modeló la cara de abajo de la pasarela (la que ve su cámara desde la planta
  baja) y las barandillas por la cara que mira al centro; la GameCube no dibuja el reverso, así que se andaba sobre
  nada. Ahora: suelo de alfombra encima de toda la zona pisable que solo tenía cara de abajo (104 m2) y 7.183
  triángulos de barandilla/moldura de la franja 4,2–5,9 m con doble cara (`uc_envolvente.py --doble`, y el relleno
  ya solo cuenta como suelo lo que mira hacia arriba).
- **Cámaras raras**: las salas heredaban los datos de cámara (CAM) de las salas originales del pueblo y del castillo:
  zonas que fuerzan cámaras fijas en sus posiciones antiguas. Ahora todas llevan el CAM vacío ("EMPT", el que usan
  r112 y r22b del juego): cámara libre de RE4 en todas partes.
- **Luz**: una luz por grupo de llamas (una araña = una luz, no ocho), alcance 3,2–4,4 m e intensidad baja; lámparas
  más suaves; ambiente algo menos negro (se intuye la sala sin linterna); niebla de 4 a 30 m.
- **Escaleras nuevas** (cripta y altar) con techo.

Comprobado igual que H12 (62 salas alcanzables, recorrido a pie sin problemas, tamaños, parche = ISO).
Sigue pendiente lo grande: rehacer el mapa siguiendo los planos de progresión del RE1 y con piezas reales en vez de cajas.
