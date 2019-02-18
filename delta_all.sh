#!/usr/bin/env bash

set -e

# Usage: ./delta_all.sh [unsound | sound] [eps]

MODE=$1
EPS=$2

if [[ "$MODE" == "sound" ]]; then
  SUFFIX=delta.$MODE.$EPS
else
  SUFFIX=delta.$MODE
fi

if [[ "$@" =~ "reuse-trans" ]]; then
  REUSE_TRANS="reuse-trans"
fi

if [[ "$@" =~ "reuse-bnet" ]]; then
  REUSE_BNET="reuse-bnet"
fi

function run_shntool() {
  ANALYSIS="taint"
  ./delta.sh benchmark/shntool-3.0.4 benchmark/shntool-3.0.5 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/shntool-3.0.5.$SUFFIX.log
}

function run_latex2rtf() {
  ANALYSIS="taint"
  ./delta.sh benchmark/latex2rtf-2.1.0 benchmark/latex2rtf-2.1.1 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/latex2rtf-2.1.1.$SUFFIX.log
}

function run_optipng() {
  ANALYSIS="taint"
  ./delta.sh benchmark/optipng-0.5.2 benchmark/optipng-0.5.3 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/optipng-0.5.3.$SUFFIX.log
}

function run_grep() {
  ANALYSIS="interval"
  ./delta.sh benchmark/grep-2.18 benchmark/grep-2.19 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/grep-2.19.$SUFFIX.log
}

function run_sed() {
  ANALYSIS="interval"
  ./delta.sh benchmark/sed-4.2.2 benchmark/sed-4.3 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/sed-4.3.$SUFFIX.log
}

function run_wget() {
  ANALYSIS="interval"
  ./delta.sh benchmark/wget-1.11.4 benchmark/wget-1.12 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/wget-1.12.$SUFFIX.log
}

function run_readelf() {
  ANALYSIS="interval"
  ./delta.sh benchmark/readelf-2.23.2 benchmark/readelf-2.24 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/readelf-2.24.$SUFFIX.log
}

function run_urjtag() {
  ANALYSIS="taint"
  ./delta.sh benchmark/urjtag-0.7 benchmark/urjtag-0.8 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/urjtag-0.8.$SUFFIX.log
}

function run_tar() {
  ANALYSIS="interval"
  ./delta.sh benchmark/tar-1.27 benchmark/tar-1.28 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/tar-1.28.$SUFFIX.log
}

function run_sort() {
  ANALYSIS="interval"
  ./delta.sh benchmark/sort-7.1 benchmark/sort-7.2 $ANALYSIS $MODE $EPS $REUSE_TRANS $REUSE_BNET \
    >&result/sort-7.2.$SUFFIX.log
}

echo "shntool"
run_shntool
echo "latex2rtf"
run_latex2rtf
echo "urjtag"
run_urjtag
echo "optipng"
run_optipng
echo "grep"
run_grep
echo "sed"
run_sed
echo "wget"
run_wget
echo "readelf"
run_readelf
echo "sort"
run_sort
echo "tar"
run_tar
