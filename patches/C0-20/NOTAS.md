# C0-20 — revisión de C0-19

- Escena de la puerta sur (los dos que entran corriendo): también al llegar a la puerta de la casa de la llave
  sin haber pasado por el establo.
- Contenedor: si está agachada, primero se levanta (CrouchStand) y luego salta. Dentro se queda visible,
  agachada y girada hacia el lado por el que entró (primera fila de la salida), como hace el juego.
- Captura: ya no por distancia. em17 br_Catch (REL .text 0x1D670) manda el agarre de la Ashley jugable a R1 0x66
  en vez de la estrangulación 0x36; ch0.c lo ve y pone el secuestro. Es el agarre real del juego.
- Error al cargar tras la captura (0x802CFB1C): Areas() recorría la lista de SceAt antigua; OtNext comprueba el
  puntero.
- Ganado del camino contra la pared: el rodeo de C0-18 lo metía 2,2 m de lado en un camino de 2 m. Ahora el rodeo
  solo va a un lado sin pared (hitCheck sobre SatMgr a la altura de la rodilla), y espera 3 s quieto.
- Escena de la llave: los tres se colocan en la puerta durante varios fotogramas (uno lejano volvía resbalando).
- Escena de miedo al salir por la ventana: justo al terminar el salto (lado del tejado).
