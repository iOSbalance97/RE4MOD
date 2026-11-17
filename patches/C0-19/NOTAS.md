# C0-19 — revisión de C0-18

- Antorcha: la Wep 6 (bandera 0x04000000, mot[69]/[70]) es la guadaña de los zelotes; sus motions (0x13A, 0x140,
  0x144) están vacías en em17: voces raras, no corrían, fuego flotando. La antorcha del pueblo es la Wep 7
  (bandera 0x800, mot[71]/[72] = ARC 0x270/0x271, ya en em17; fuego setEffAlways 0x10/0x14), la que usan r111,
  r118 y la cabaña (r11d). Fuera el cambio de em17.drs de C0-18.
- Meterse en el contenedor: la animación del juego (Ashley compañera en la isla, pl11 ARC 0x2C salto + 0x43
  agacharse; salida 0x45 + 0x2C). anim/tools/mkhide.py → mod/data/ch0_hide.bin (rotaciones de las partes 1-25 y
  raíz, como el clip de miedo), en em12.drs tras el contenedor (CT_HD). crouch.c ClipApply. Por el lado largo
  más cercano, desde 400 fuera del borde.
- Captura: el juego agarra a la Ashley jugable con la estrangulación (R1 0x36), cuyo aviso lee un texto basura
  (0x8012DA30). Ahora un perseguidor a < 2,6 m (el golpe de antorcha empieza a 2,5) se la lleva al hombro como
  en el TakeAway: él 0x29F + 0x2A0 por su R1 0x66 (solo MotionMove), ella 0x2A2 / 0x2A3 del archivo del ganado,
  en su punto de carga (-176.17, 40.95).
- El clip de miedo de la intro pasa también al disco (sitio en el DOL).
- Puerta de la casa: el juego cierra la puerta en cuanto no hay nadie cerca (emDoorDoorAutoCloseCk, bandera
  0x20000000); al abrirse del todo se le quita esa bandera y, si se cierra, se vuelve a abrir. También tras
  volver a la cama con la llave.
- Callejones del establo: la caja grande del pueblo (SMD 43, bin 41) copiada en dos trabajos SMD libres antes de
  SmdSetup, empuje rectangular para Ashley y las cajas pequeñas debajo.
