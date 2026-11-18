# C0-25 — captura sin piernas rotas + Parte 2 (r112 / r118)

- Captura: el IK de piernas y brazos del propio juego seguía corriendo sobre Ashley y llevaba los pies al suelo
  bajo el hombro del ganado. Mientras la llevan, sus cadenas de IK se saltan (bandera 0x80 en el gancho de
  InverseKinematics) y se devuelven después. El clip del secuestro usa además el giro base del muslo (canal 32).
- Parte 2:
  - r112: la puerta de vuelta al pueblo está apagada; la máquina de escribir no guarda: "Vaya máquina más
    antigua, ¿todavía se usa esto?". La puerta del juego que baja al cementerio (r118) funciona.
  - r118 sin enemigos ni frases de León en las tumbas. Seis velas (malla SMD 79, numeradas subiendo):
    1 (-14194, -31235), 2 (-12092, -19887), 3 (-6505, -28663), 4 (-2034, -26529), 5 (5144, -24796),
    6 (9141, -21318), junto a la puerta.
  - La puerta entre las antorchas (ETS 20 en x 12086, z -19918 / -15649) está cerrada ("Está cerrada.").
    Hay un papel junto a la antorcha sur (11250, -19100), "El orden del fuego ... 325.416".
  - Tocar las velas en el orden 3 2 5 4 1 6 la abre ("Algo ha sonado en la puerta."). Si te equivocas, se
    empieza de nuevo. Al cruzarla: "Fin de la Parte 2 (prueba)".
