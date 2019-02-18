#!/usr/bin/env bash

# Runs Bingo in batch mode on all the benchmarks
# Usage: ./run_all.sh [reuse]

set -e

mkdir -p result

if [[ "$@" =~ "reuse" ]]; then
  export REUSE=reuse
fi

taint_benchmarks=(
  "shntool-3.0.4"
  "shntool-3.0.5"
  "latex2rtf-2.1.0"
  "latex2rtf-2.1.1"
  "urjtag-0.7"
  "urjtag-0.8"
  "optipng-0.5.2"
  "optipng-0.5.3"
)

interval_benchmarks=(
  "wget-1.11.4"
  "wget-1.12"
  "readelf-2.23.2"
  "readelf-2.24"
  "grep-2.18"
  "grep-2.19"
  "sed-4.2.2"
  "sed-4.3"
  "sort-7.1"
  "sort-7.2"
  "tar-1.27"
  "tar-1.28"
)

function run_interval() {
  work=("$@")
  for p in "${work[@]}"; do
    echo $p
    ./run.sh benchmark/$p/$p.c interval $REUSE >&result/$p.batch.log
  done
}

function run_taint() {
  work=("$@")
  for p in "${work[@]}"; do
    echo $p
    ./run.sh benchmark/$p/$p.c taint $REUSE >&result/$p.batch.log
  done
}

run_taint ${taint_benchmarks[@]}
run_interval ${interval_benchmarks[@]}
