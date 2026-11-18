# C0-22 — revisión de C0-21

- Escena del ganado del camino: salta a unos 3 m (antes 6,5 m).
- Ashley desaparecía en esa escena: la "caída" pl11 0x6A la bajaba 4,4 m (era caer por un hueco). Ahora es
  0x32 (derribada hacia atrás, en el sitio) + 0x33 hasta quedarse sentada en el suelo. El ganado espera encima
  y se abalanza cuando ya está sentada.
- Bloqueo al reiniciar tras esa captura: la embestida llevaba su SEQ (golpe) y la vida solo se rellenaba fuera
  de la captura. Embestida sin SEQ y vida llena también durante la captura.
- Cámara de salto: ya no salta al correr junto a la ventana (R1 3 = correr). Solo con los saltos: por encima
  (0x0C, la ventana), bajar de nivel (8) y caída (0x0E, 0x13), en todas partes (también tejado → suelo).
  Al aterrizar espera 12 fotogramas por si sigue la escena de miedo; si no, vuelve la cámara del juego.
- Los ganados no capturaban: em10CatchPLRtnCk exige no tener pWeapon o Be_flg 0x08000000 (Wep_type 0 no basta).
  Los que persiguen llevan ahora 0x08000000.
