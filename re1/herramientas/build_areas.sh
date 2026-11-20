#!/bin/bash
# salas de UC de fuera de la mansión: sin girar (metros de UC = mm/1000 de RE4)
T=/home/claude/tools; Z="0,0,0,0,0,0,0"
for r in ${@:-r116 r117 r118 r119 r120 r121 r122 r123 r125 r126 r127 r128 r130 r133 r134 r135 r137 r138 r139 r140 r142 r144}; do
  python3 $T/uc_prep.py $r > /dev/null
  ST=""; case $r in r116|r117|r118|r119|r144) ST=--sin-techo;; esac
  python3 $T/uc_envolvente.py $r $ST | cut -c1-120
  python3 $T/ucol2re4.py $r /home/claude/uc/re4/$r/col --colocar="$Z" > /home/claude/uc/re4/$r.col.log
  python3 $T/re4room.py /home/claude/uc/m/$r/sala.obj /home/claude/uc/re4/$r/mod --decimar 0.4 --tex-max 256 --colocar="$Z" > /home/claude/uc/re4/$r.room.log
  echo "   $(head -1 /home/claude/uc/re4/$r.room.log) | $(grep TPL /home/claude/uc/re4/$r.room.log) | $(tail -1 /home/claude/uc/re4/$r.col.log | cut -c1-60)"
done
