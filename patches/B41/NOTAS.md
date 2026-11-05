# B41 (prueba: andar apuntando completo)

- Fuera la capa pMotionB de B38-B40: ese hueco es el de la mezcla de inclinacion del apuntado (cMot3 mot3: la postura de apuntar arriba/abajo se mezcla por pMotionB con Brate = |m3r|). Usarlo rompia el apuntado y la camara al disparar la escopeta.
- Nuevo: una vez por fotograma desde ModFrame (despues de actualizar a Leon y antes de dibujar) se pone en pelvis y piernas la pose del ciclo de Mixamo (adelante/atras/izq/der) y en el pecho la mitad de su balanceo y bote; luego partsWorldCalc. Entra y sale en 6 fotogramas y cambia de direccion fundiendo. La fase sigue la distancia real. El siguiente fotograma el juego parte de su propia pose (nada se queda en su estado).
- Tablas: anim/tools/mkwalk.py -> c/walk_data.h.
