# B30 (estable)

- B29 se colgaba: con la lectura repartida en varios fotogramas, el juego sigue dibujando cosas (p. ej. modelos ligados al arma) que leen del archivo mientras se sobrescribe. La lectura vuelve a ser de golpe (modo 0x8001), como en B24.
- Sin recuadro de medidas. Igual que B24 (cuadro marca el arma elegida, arma de relleno, cuello).
- Leccion: no se puede leer el arma en su propio sitio por partes; la unica forma fluida es precargarla en otra zona de memoria.
