#!/bin/bash
# H36: vestíbulo, comedor y sala de la estatua (UC) con los parámetros aprobados
cd /home/claude/re1gc/work
sala() {  # u r st extra_env...
  u=$1; r=$2; st=$3; alin=$4; shift 4
  rm -rf /tmp/h36_$r
  env SUAVE_K=12 BRILLO=1.2 DOBLE=1 NIVELES=16 PAGINAS=2 MAXTEX=1 "$@" timeout 3000 python3 uc_sala_v5.py /home/claude/uc/m/$u/sala_sin_env.obj $alin $st $r /tmp/h36_$r > /tmp/h36_$r.log 2>&1 || { echo "$r ERROR"; tail -5 /tmp/h36_$r.log; return 1; }
  python3 noche.py /tmp/h36_$r > /dev/null
  rm -rf ../salas_uc5/$r; cp -r /tmp/h36_$r ../salas_uc5/$r; cp /tmp/h36_$r.log ../salas_uc5/$r.log
  rm -rf ../re4/re_${r}_uc; timeout 1500 python3 /home/claude/tools/re4room.py ../salas_uc5/$r/sala.obj ../re4/re_${r}_uc/mod --tex-max 1024 > ../salas_uc5/$r.room.log 2>&1 || { echo "$r ERROR re4room"; return 1; }
  echo "$r: $(grep -o 'SMD total.*' ../salas_uc5/$r.room.log)"
}
case $1 in
  r106) sala r102 r106 1 ../uc_alin/r106.json DECIMAR=0.45 LMAX=1.5 BALAUSTRES_TOTAL=1 PASAMANOS_A_PARED=1 NO_MACIZO="stairs|lug15|wood13|wood15" BALAUSTRE_UC="2.84,3.0,-2.69,-2.53,0.0" ZOCALO_BAL=0.08 ZOCALO_MAT=wood14 PASO_BALAUSTRE=0.2 BALAUSTRE_UC_Y=4.6 ESQUINERO_UC="2.8,3.05,-3.35,-3.05" HUECO_IGNORAR="ceil" HUECO_MAT="ceilling01" HUECO_CAJAS="2.8,6.7,-7.0,-1.2,5.5,6.9;-6.7,-2.8,-7.0,-1.2,5.5,6.9;-2.9,2.9,-3.7,-1.2,6.2,6.9" ;;
  r105) sala r101 r105 1 ../uc_alin/al_r101_r105.json DECIMAR=0 LMAX=1.1 MEJORAR="gaku|kaiga|emily" NIVEL_MIN_MEJ=0.5 ;;
  r103) sala r100 r103 1 ../uc_alin/al_r100_r103.json DECIMAR=0.45 LMAX=1.1 QUITAR_PAREDES_PASO=1 BRILLO=2.6 HUECO_YMAX=6.5 ;;
  r107) sala r103 r107 1 ../uc_alin/al_r103_r107.json DECIMAR=0.6 LMAX=1.1 QUITAR_PAREDES_PASO=1 MEJORAR="gaku|kaiga|emily" NIVEL_MIN_MEJ=0.5 ;;
esac
