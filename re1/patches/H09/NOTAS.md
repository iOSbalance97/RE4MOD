# H09 — partida guardada en la granja: suelo de seguridad y rescate

Igual que H08 salvo el vestíbulo (r103/r113).

**Problema (H07/H08)**: al cargar una partida guardada en la granja, el juego pone a Leon en la posición guardada,
que queda fuera del vestíbulo (la granja original ocupa x -51..14 m, z -38..10 m, suelo a ~0 m). La colisión de UC
solo tiene el suelo del vestíbulo → cae sin fin: pantalla gris sin error. (En H06 la colisión generada tenía suelo de
sobra alrededor.)

**Arreglo**:
- Suelo de seguridad invisible a y = 0 en x -70..30 m, z -55..30 m (baldosas de 10 m; SAT con bloques de 4 m).
- Rescate: 4 áreas de puerta (botón) que cubren todo lo de fuera del vestíbulo y llevan a la entrada del vestíbulo
  (donde deja la puerta norte del pueblo).
Comprobado: ningún punto del suelo del vestíbulo dentro del rescate; todo el suelo de la granja original dentro del
rescate o del perímetro del vestíbulo; ninguna llegada dentro de un área; parche = ISO esperada, 22 ficheros idénticos.
