# B23

- Arreglo del cuelgue "Invalid read from 0x9C, PC 0x80144D4C" (visto junto a la maquina de escribir): durante la carga no hay arma y el juego le pregunta cosas a su objeto (Wep->m_pWep, NULL). Ahora hay un objeto de relleno cuyas funciones devuelven 0 mientras dura la carga.
- Incluye lo de B22 (cuello).
