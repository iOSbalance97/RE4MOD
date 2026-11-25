#!/bin/bash
# uso: convertir_hall.sh u:r:st  -> sala UC con los parámetros del vestíbulo aprobado (nítido, sin atlas en paredes)
IFS=: read u r st <<< "$1"; cd /home/claude/re1gc/work
rm -rf ../salas_uc5/$r
SUAVE_K=12 BRILLO=1.2 DECIMAR=0.45 LMAX=1.1 DOBLE=1 NIVELES=16 PAGINAS=2 MAXTEX=${MAXTEX:-80} timeout 3000 python3 uc_sala_v5.py /home/claude/uc/m/$u/sala_sin_env.obj ../uc_alin/al_${u}_${r}.json $st $r ../salas_uc5/$r > ../salas_uc5/$r.log 2>&1 || { echo "$r: ERROR"; tail -3 ../salas_uc5/$r.log; exit 1; }
python3 noche.py ../salas_uc5/$r > /dev/null
rm -rf ../re4/re_${r}_uc; timeout 1500 python3 /home/claude/tools/re4room.py ../salas_uc5/$r/sala.obj ../re4/re_${r}_uc/mod --tex-max 1024 > ../salas_uc5/$r.room.log 2>&1 || { echo "$r: ERROR re4room"; exit 1; }
echo "$r <- $u: $(grep -o 'SMD total.*' ../salas_uc5/$r.room.log) | $(grep 'luces de objetos' ../salas_uc5/$r.log) | $(grep 'balaustres añadidos' ../salas_uc5/$r.log)"
