# B22

- Arreglo del cuelgue de B21: al volver a encender el cuello antes de que el juego le diera los movimientos nuevos, intentaba usar los del arma vieja (ya sobrescritos). Ahora no se toca el modo; se borran sus movimientos (cPlNeck::clear) y footwork le da los nuevos.
- Quitada la espera entre la lectura y la iniciacion del arma (como en B20).
