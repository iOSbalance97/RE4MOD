# H05 — Mansión de UC unida y jugable (15 salas)

Parche sobre el **disco 1 PAL limpio** (sha1 9e58a28b…). Salas sacadas del disco de Umbrella Chronicles,
todas con la misma transformación (las salas de UC comparten coordenadas del mundo, así que encajan entre sí).

Entrada: puerta norte del pueblo (la del granero) → vestíbulo, justo dentro de la puerta principal.

| Sala RE4 | Sala UC | Qué es | Puertas a |
|---|---|---|---|
| r103 / r113 | r102 | Vestíbulo | comedor, r105, exterior |
| r102 | r101 | Comedor | vestíbulo, r104 |
| r104 | r100 | pasillo junto al comedor | comedor, exterior |
| r105 | r103 | sala este del vestíbulo | vestíbulo, r106 |
| r106 → r107 → r108 | r104, r105, r106 | pasillos planta baja | cadena |
| r109 | r107 | escalera a planta alta | r108, r10a |
| r10a / r10b | r108 / r109 | galería planta alta / sala interior | |
| r10c | r111 | exterior (bosque) | vestíbulo, r104, r10d |
| r10d | r112 | escalera oeste | exterior, r10e |
| r10e → r10f → r112 | r113, r114, r115 | planta alta oeste, biblioteca | cadena |

Las puertas son registros AEV de puerta (copiados de la puerta 2 del pueblo): cilindro de 0,9 m de radio
pegado al hueco; se entra con el botón de acción. Llegada a ~1,2 m de la puerta mirando hacia dentro.

Comprobado antes de entregar: SAT/EAT válidos (satcheck), todos los puntos de llegada sobre suelo pisable,
salas ≤ 4,4 MB descomprimidas (menos que las originales), todas caben en su sitio en la ISO, parche aplicado
y ficheros extraídos de la ISO idénticos; r100, r101, r111 (pueblo) sin tocar.

Sin probar en juego: transición con AEV propios, enemigos/efectos/objetos originales de esas salas (siguen en
sus coordenadas antiguas), iluminación (no hay lightmaps). Al volver al vestíbulo desde otra sala se entra en r113.

## Cambio respecto a H04
H04 salía con una sola textura en toda la sala: al limpiar los OBJ de UC se perdieron los grupos y re4room
agrupaba solo por grupo. Ahora agrupa por grupo + material: cada sala usa todas sus texturas (vestíbulo 86).
Comprobado leyendo de vuelta el SMD de cada .das (partes y texturas por sala) y renderizándolo.
