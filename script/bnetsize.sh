#!/bin/bash

old_programs=(
  "shntool-3.0.4/sparrow-out/taint"
  "latex2rtf-2.1.0/sparrow-out/taint"
  "urjtag-0.7/sparrow-out/taint"
  "optipng-0.5.2/sparrow-out/taint"
  "wget-1.11.4/sparrow-out/interval"
  "grep-2.18/sparrow-out/interval"
  "readelf-2.23.2/sparrow-out/interval"
  "sed-4.2.2/sparrow-out/interval"
  "sort-7.1/sparrow-out/interval"
  "tar-1.27/sparrow-out/interval"
)

new_programs=(
  "shntool-3.0.5/sparrow-out/taint"
  "latex2rtf-2.1.1/sparrow-out/taint"
  "urjtag-0.8/sparrow-out/taint"
  "optipng-0.5.3/sparrow-out/taint"
  "wget-1.12/sparrow-out/interval"
  "grep-2.19/sparrow-out/interval"
  "readelf-2.24/sparrow-out/interval"
  "sed-4.3/sparrow-out/interval"
  "sort-7.2/sparrow-out/interval"
  "tar-1.28/sparrow-out/interval"
)

echo "Old BNet"
total_tuples=0
total_clauses=0
printf "%-25s: %8s | %8s\n" "Program" "#Tuples" "#Clauses"
for p in "${old_programs[@]}"; do
  opt_clauses=$(grep "clauses" benchmark/$p/bnet/cons_all2bnet.log | head -n 1 | cut -f 5 -d ' ')
  opt_tuples=$(grep "tuples" benchmark/$p/bnet/cons_all2bnet.log | head -n 1 | cut -f 5 -d ' ')
  total_tuples=$(($total_tuples + $opt_tuples))
  total_clauses=$(($total_clauses + $opt_clauses))
  printf "%-25s: %8s | %8s \n" ${p%%/*} $opt_tuples $opt_clauses
done
printf "%-25s: %8s | %8s\n\n" "Total" $total_tuples $total_clauses

echo "New BNet"
total_tuples=0
total_clauses=0
printf "%-25s: %8s | %8s\n" "Program" "#Tuples" "#Clauses"
for p in "${new_programs[@]}"; do
  opt_clauses=$(grep "clauses" benchmark/$p/bnet/cons_all2bnet.log | head -n 1 | cut -f 5 -d ' ')
  opt_tuples=$(grep "tuples" benchmark/$p/bnet/cons_all2bnet.log | head -n 1 | cut -f 5 -d ' ')
  total_tuples=$(($total_tuples + $opt_tuples))
  total_clauses=$(($total_clauses + $opt_clauses))
  printf "%-25s: %8s | %8s \n" ${p%%/*} $opt_tuples $opt_clauses
done
printf "%-25s: %8s | %8s\n\n" "Total" $total_tuples $total_clauses

echo "Merged BNet"
total_tuples=0
total_clauses=0
total_time=0
printf "%-25s: %8s | %8s | %8s\n" "Program" "#Tuples" "#Clauses" "Time(s)"
for p in "${new_programs[@]}"; do
  opt_clauses=$(grep "clauses" benchmark/$p/merged_bnet_0.001/cons_all2bnet.log | head -n 1 | cut -f 5 -d ' ')
  opt_tuples=$(grep "tuples" benchmark/$p/merged_bnet_0.001/cons_all2bnet.log | head -n 1 | cut -f 5 -d ' ')
  interactions=$(tail -n +2 benchmark/$p/bingo_delta_sem-eps_strong_0.001_stats.txt | wc -l | cut -f 1 -d ' ')
  time=$(tail -n +2 benchmark/$p/bingo_delta_sem-eps_strong_0.001_stats.txt | cut -f 9 | paste -sd+ | bc)
  avg=$(($time / $interactions))
  total_tuples=$(($total_tuples + $opt_tuples))
  total_clauses=$(($total_clauses + $opt_clauses))
  total_time=$(($total_time + $avg))
  printf "%-25s: %8s | %8s | %8s\n" ${p%%/*} $opt_tuples $opt_clauses $time
done
printf "%-25s: %8s | %8s | %8s\n\n" "Total" $total_tuples $total_clauses $total_time
