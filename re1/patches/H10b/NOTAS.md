# H10 — vuelta a los datos de sala de H06 (pantalla gris en H07–H09)

H07–H09: pantalla gris uniforme (sin Leon, en pausa solo texto). H06 funcionaba. H07 cambió varias cosas a la vez;
la más sospechosa es haber anulado la cámara de la sala (CAM: si falta, CamCtrl trabaja con pCamData nulo).
H10 vuelve a conservar todo lo de la sala original salvo:
- SMD/SMX/SAT/EAT/AEV propios (como siempre); ITA (objetos recogibles) y ETS (objetos sueltos) renombrados;
  FCV/SEQ (cinemáticas, solo las usa el código de la sala) vaciados.
- Se conservan CAM, EAR, SAR, ESE, FSE, EFF, ETM, BIN, TPL.
Para que ninguna sala supere el tamaño de su original (límite seguro de memoria): hall, comedor y biblioteca con
texturas de 128 px y más simplificación; la biblioteca pasa a r105 y la sala este (UC r103) a r112.
Sigue: scripts de sala vaciados (Rel), enemigos quitados (etc/*.esl), suelo de seguridad y rescate en el hall,
límite de 240 texturas.
Comprobado: todas las salas ≤ original descomprimidas, 240 texturas máx., puertas simuladas sin problemas, 15 salas
alcanzables, parche = ISO esperada.

**H10b** = H10 con los Rel originales (scripts de sala sin quitar), para descartar el parche de los módulos.
