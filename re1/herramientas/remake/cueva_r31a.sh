cd /home/claude/re1gc/work
rm -rf ../salas_cas/r31a
CUEVA=1 OSCURO=0.55 CELDAS="-6.6,1;-11.2,-1;-13.3,1" PAREDES_PLANAS="-1.0,1.0,9.9,13.0,-4.9,-4.8,0.55,2.3;-14.45,-14.3,0.0,4.0,1.5,4.0,0.55,2.3" MODELOS_EXTRA="/home/claude/re1gc/modelos/verja/verja.obj;/home/claude/re1gc/modelos/verja/verja_r315.obj" python3 sala_colision.py r31a ../salas_cas/r31a
