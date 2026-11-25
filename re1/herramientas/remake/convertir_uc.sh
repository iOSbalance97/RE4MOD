#!/bin/bash
# uso: convertir_uc.sh u:r:st
IFS=: read u r st <<< "$1"
cd /home/claude/re1gc/work
rm -rf ../salas_uc5/$r
SUAVE_K=30 SUAVE_R=1.6 SUAVE_S=0.8 BRILLO=1.2 DECIMAR=0.45 LMAX=0.8 DOBLE=1 ATLAS_PAREDES=1 NIVELES=16 PAGINAS=3 MAXTEX=110 TEXG=256 TEXP=128 timeout 3000 python3 uc_sala_v5.py /home/claude/uc/m/$u/sala_sin_env.obj ../uc_alin/al_${u}_${r}.json $st $r ../salas_uc5/$r > ../salas_uc5/$r.log 2>&1 || { echo "$r: ERROR uc_sala"; exit 1; }
timeout 1200 python3 /home/claude/tools/re4room.py ../salas_uc5/$r/sala.obj ../re4/re_${r}_uc/mod --tex-max 1024 > ../salas_uc5/$r.room.log 2>&1 || { echo "$r: ERROR re4room"; exit 1; }
echo "$r <- $u: $(grep -o 'SMD total.*' ../salas_uc5/$r.room.log) | $(grep -o 'luces de objetos.*' ../salas_uc5/$r.log) | $(grep -o 'balaustres.*' ../salas_uc5/$r.log)"
