#!/bin/bash

OLD_VERSION=("shntool-3.0.4" "latex2rtf-2.1.0" "urjtag-0.7" "optipng-0.5.2" "wget-1.11.4"
  "readelf-2.23.2" "grep-2.18" "sed-4.2.2" "sort-7.1" "tar-1.27")
NEW_VERSION=("shntool-3.0.5" "latex2rtf-2.1.1" "urjtag-0.8" "optipng-0.5.3" "wget-1.12"
  "readelf-2.24" "grep-2.19" "sed-4.3" "sort-7.2" "tar-1.28")

echo ""
echo "Batch mode OLD alarms"
printf "%-25s: %7s \n" "Program" "Alarms"
total=0
for p in "${OLD_VERSION[@]}"; do
  ALARMS=$(grep -i "Total alarms" result/$p.batch.log | cut -d ':' -f 2)
  printf "%-25s: %7s\n" "$p" "$ALARMS"
  total=$(($total + $ALARMS))
done
printf "%-25s: %7s\n" "Total" "$total"

echo ""
echo "Batch mode NEW alarms and Bingo"
total_alarms=0
total_iters=0
total_bugs=0
printf "%-25s: %5s | %7s | %5s\n" "Program" "Bugs" "Alarms" "Iters"
for p in "${NEW_VERSION[@]}"; do
  BUGS=$(grep -i "True alarms" result/$p.batch.log | cut -d ':' -f 2)
  ALARMS=$(grep -i "Total alarms" result/$p.batch.log | cut -d ':' -f 2)
  ITERS=$(grep -i "Last true" result/$p.batch.log | cut -d ':' -f 2)
  printf "%-25s: %5s | %7s | %5s\n" "$p" "$BUGS" "$ALARMS" "$ITERS"
  total_bugs=$(($total_bugs + $BUGS))
  total_alarms=$(($total_alarms + $ALARMS))
  total_iters=$(($total_iters + $ITERS))
done
printf "%-25s: %5s | %7s | %5s\n" "Total" "$total_bugs" "$total_alarms" "$total_iters"

echo ""
echo "Syntactic Masking and Drake-Unsound"
total_alarms=0
total_iters=0
total_bugs=0
total_initial=0
total_feedback=0
printf "%-25s: %5s | %7s | %5s | %8s | %5s\n" "Program" "Bugs" "Diff" "Init" "Feedback" "Iters"
for p in "${NEW_VERSION[@]}"; do
  BUGS=$(grep -i "True alarms" result/$p.delta.unsound.log | cut -d ':' -f 2)
  ALARMS=$(grep -i "Total alarms" result/$p.delta.unsound.log | cut -d ':' -f 2)
  INITIAL=$(grep "TrueGround" $(find benchmark/$p/ -name bingo_delta_syn_strong_combined)/init.out | tail -n 1 | cut -f 1)
  if [[ $INITIAL == "" ]]; then
    INITIAL=0
  fi
  FEEDBACK=$(grep "TrueGround" $(find benchmark/$p/ -name bingo_delta_syn_strong_combined)/0.out | tail -n 1 | cut -f 1)
  if [[ $FEEDBACK == "" ]]; then
    FEEDBACK=0
  fi
  ITERS=$(grep -i "Last true" result/$p.delta.unsound.log | cut -d ':' -f 2)
  printf "%-25s: %5s | %7s | %5s | %8s | %5s\n" "$p" "$BUGS" "$ALARMS" "$INITIAL" "$FEEDBACK" "$ITERS"
  total_bugs=$(($total_bugs + $BUGS))
  total_alarms=$(($total_alarms + $ALARMS))
  total_initial=$(($total_initial + $INITIAL))
  total_feedback=$(($total_feedback + $FEEDBACK))
  total_iters=$(($total_iters + $ITERS))
done
printf "%-25s: %5s | %7s | %5s | %8s | %5s\n" "Total" "$total_bugs" "$total_alarms" "$total_initial" "$total_feedback" "$total_iters"

FB_MODE=("0.001" "0.005" "0.01")
for eps in "${FB_MODE[@]}"; do
  echo ""
  echo "Drake-Sound with eps = $eps"
  total_alarms=0
  total_iters=0
  total_bugs=0
  total_initial=0
  total_feedback=0
  printf "%-25s: %5s | %7s | %5s | %8s | %5s\n" "Program" "Bugs" "Alarms" "Init" "Feedback" "Iters"
  for p in "${NEW_VERSION[@]}"; do
    BUGS=$(grep -i "True alarms" result/$p.delta.sound.$eps.log | cut -d ':' -f 2)
    ALARMS=$(grep -i "Total alarms" result/$p.delta.sound.$eps.log | cut -d ':' -f 2)
    INITIAL=$(grep "TrueGround" $(find benchmark/$p/ -name bingo_delta_sem-eps_strong_${eps}_combined)/init.out | tail -n 1 | cut -f 1)
    FEEDBACK=$(grep "TrueGround" $(find benchmark/$p/ -name bingo_delta_sem-eps_strong_${eps}_combined)/0.out | tail -n 1 | cut -f 1)
    ITERS=$(grep -i "Last true" result/$p.delta.sound.$eps.log | cut -d ':' -f 2)
    printf "%-25s: %5s | %7s | %5s | %8s | %5s\n" "$p" "$BUGS" "$ALARMS" "$INITIAL" "$FEEDBACK" "$ITERS"
    total_bugs=$(($total_bugs + $BUGS))
    total_alarms=$(($total_alarms + $ALARMS))
    total_initial=$(($total_initial + $INITIAL))
    total_feedback=$(($total_feedback + $FEEDBACK))
    total_iters=$(($total_iters + $ITERS))
  done
  printf "%-25s: %5s | %7s | %5s | %8s | %5s\n" "Total" "$total_bugs" "$total_alarms" "$total_initial" "$total_feedback" "$total_iters"
done
