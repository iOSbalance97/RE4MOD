#!/bin/bash
# uso: convertir_s4.sh rNNN   (sala del REmake sin modelo de UC -> estilo vestíbulo con atlas)
r=$1; st=${r:1:1}
cd /home/claude/re1gc/work
[ -d ../re4/re_${r}_uc ] && { echo "$r: tiene UC"; exit 0; }
rm -rf ../salas4/$r
PAGINAS=${PAGINAS:-4} timeout 2400 python3 remake_sala4.py $st $r ../salas/$r ../salas4/$r > ../salas4/$r.log 2>&1 || { echo "$r: ERROR sala4"; exit 1; }
timeout 1500 python3 /home/claude/tools/re4room.py ../salas4/$r/sala.obj ../re4/re_${r}_s4/mod --tex-max 1024 > ../salas4/$r.room.log 2>&1 || { echo "$r: ERROR re4room"; exit 1; }
echo "$r: $(grep -o 'atlas.*px/m' ../salas4/$r.log | head -1) | $(grep -o 'SMD total.*' ../salas4/$r.room.log)"
