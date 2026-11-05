# B37

- Banda del aviso dibujada en el render despues de ExecOt(0x13) y antes de la pasada de la camara de objetos ExecOt(0x14) (gancho 0x80169718): el icono 3D y el texto quedan encima. Se repone la proyeccion de itemCamera al terminar.
- Apuntado al cambiar: tambien se repone m3r (cDelayF en 0x8021D970, la inclinacion que sigue la camara de hombro via cPlWep::getPitch). Encontrado con el patron de getPitch en PAL (0x801461B8).
- Idioma: la tabla espanola de nombres (core.das entrada 17, idioma 5) trae "Treasure Box (S)/(L)" sin traducir; el resto sale en espanol.
