#!/bin/bash
# todas las salas del REmake -> salas/rNNN (OBJ) -> re4/re_rNNN (SMD + colisión)
for st in 1 2 3 4 5; do
  for f in /home/claude/re1gc/files/st$st/r*.dat; do
    r=$(basename $f .dat)
    [ -f /home/claude/re1gc/re4/re_$r/v2 ] && continue
    python3 /home/claude/re1gc/work/remake_sala2.py $st $r /home/claude/re1gc/salas/$r 700 > /home/claude/re1gc/salas/$r.log 2>&1 || { echo "$r: error en conversión"; continue; }
    python3 /home/claude/tools/re4room.py /home/claude/re1gc/salas/$r/sala.obj /home/claude/re1gc/re4/re_$r/mod --tex-max 512 --colocar=0,0,0,0,0,0,0 > /home/claude/re1gc/salas/$r.room.log 2>&1 || { echo "$r: error en re4room"; continue; }
    python3 /home/claude/tools/obj2sat.py /home/claude/re1gc/salas/$r/colision.obj /home/claude/re1gc/re4/re_$r/col > /home/claude/re1gc/salas/$r.col.log 2>&1 || echo "$r: error en colisión"; touch /home/claude/re1gc/re4/re_$r/v2
    echo "$r: $(grep -o "proyección buena.*" /home/claude/re1gc/salas/$r.log) | $(grep TPL /home/claude/re1gc/salas/$r.room.log)"
  done
done
echo FIN
