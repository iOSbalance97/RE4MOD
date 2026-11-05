# B38 (prueba: piernas al apuntar + agacharse)

- Piernas al moverse apuntando: segundo movimiento (pMotionB) con pelvis y piernas de Mixamo (Pistol Walk / Walk Backward / strafe izq. / der.), FK, encima del movimiento de apuntar; las cadenas IK de piernas del apuntado se apagan mientras (flag 0x80 en partes 18/22). La fase sigue la distancia real recorrida (mm por ciclo: 2250 / 1600 / 1343 / 1597).
- Agacharse con Circulo: rutina de cobertura del propio juego (0x11). Circulo otra vez se levanta (se le da un B a la rutina). Desde agachado se puede apuntar (lo hace el juego).
- Generado con anim/tools/mklegs.py.
