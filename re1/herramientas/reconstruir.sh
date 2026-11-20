#!/bin/bash
# Reconstruye las salas de UC en RE4 desde cero (H12+):
#  uc_prep (sala + objetos) -> puertas cerradas -> colisión -> envolvente -> re4room -> uc_montar2 -> Rel
# uso: reconstruir.sh [salas...]   (sin argumentos: todas)
set -e
T=/home/claude/tools; COL="19.4,0,15.0,-47609,12,7084,-1.253"
SALAS=${@:-"r100 r101 r102 r103 r104 r105 r106 r107 r108 r109 r111 r112 r113 r114 r115"}
for r in $SALAS; do python3 $T/uc_prep.py $r | tail -1; done
python3 $T/uc_puertas_cerradas.py /home/claude/uc/re4/conexiones2.json | tail -3
for r in $SALAS; do
  case $r in
    r102) python3 $T/ucol2re4.py $r /home/claude/uc/re4/$r/col --colocar="$COL" --suelo-extra=-70000,-55000,30000,30000,0 --bloque 4000 --suelo-visible 3.9,7 > /home/claude/uc/re4/$r.col.log ;;
  esac
  python3 $T/uc_envolvente.py $r
  tm=256; [ $r = r115 ] && tm=128
  python3 $T/re4room.py /home/claude/uc/m/$r/sala.obj /home/claude/uc/re4/$r/mod --decimar 0.4 --tex-max $tm --colocar="$COL" > /home/claude/uc/re4/$r.room.log
  head -1 /home/claude/uc/re4/$r.room.log
done
