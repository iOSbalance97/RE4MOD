# C0-23 — revisión de C0-22

- Aviso "Invalid read from 0x34, PC 0x80074A04" (camino, puerta de la casa, ventana, tejado): la bandera Be_flg
  0x08000000 de C0-22 significa "va a por la compañera"; sin compañera (pSUB 0) em10NeckMove leía 0x34. Quitada.
  La captura se lanza ahora desde ch0.c: un ganado que persigue, a 1,25 m y de frente a Ashley, pasa a Catch
  (R1 0x33) → 0x66 (secuestro). Espera 3 s entre intentos.
- Reinicio tras la captura del camino: la sala es la misma (ROOM 0x11 durante toda la carga), así que el capítulo
  se daba por cargado al momento y el estado viejo de Ashley la volvía a capturar. Ahora espera a que esté en el
  punto de reinicio y en estado normal.
- Marcadores de los ganados: solo si el ganado tiene línea de visión (se veían puntos amarillos en el suelo de
  otras plantas).
- Sin maletín ni mapa en el capítulo (Triángulo / R3 / R1 no llegan al juego con Ashley).
- ch0.c con -Oz (el DOL se había pasado 64 B); 4,5 KB libres.
