# C0-05 — Capítulo 0: cada ganado en su zona

- Cada ganado patrulla 2,5 m (1,25 m a cada lado, de través a donde mira), se para y mira en cada extremo.
- Si está a más de 4 m de su sitio (empujado, o tras perseguirte), vuelve andando a su sitio.
- Solo te persiguen cuando su marca se llena (detección propia del juego desactivada del todo: también
  flag 0x40 y Be_flg 0x08000000). Al perderte vuelven a su sitio.
- Arreglada la raíz cuadrada de las distancias (fallaba con distancias largas).
- Cartel recolocado: sin solapes, controles en columna.
- El primer ganado sigue de espaldas y quieto hasta que coges el desvío.
