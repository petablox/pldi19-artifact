#!/usr/bin/env bash

# Usage: ./run.sh [program] [interval | taint] [reuse]
# ./run.sh benchmark/optipng-0.5.2.c

set -e

########################################################################################################################
# 1. Initialize Options for Various Benchmarks

PGM=$1
ANALYSIS=$2
BASE=$(basename $PGM)
BENCHMARK_DIR=$(dirname $PGM)
OUTPUT_DIR=$BENCHMARK_DIR/sparrow-out
echo $BASE
OPT_DEFAULT="-unsound_alloc -extract_datalog_fact_full -outdir $OUTPUT_DIR"
if [[ "$BASE" =~ shntool.+ ]] ||
  [[ "$BASE" =~ optipng.+ ]]; then
  OPT="$OPT_DEFAULT -taint"
elif [[ "$BASE" =~ urjtag.+ ]]; then
  OPT="$OPT_DEFAULT -taint -unsound_const_string -unsound_skip_file flex -unsound_skip_file bison"
elif [[ "$BASE" =~ latex2rtf.+ ]]; then
  OPT="$OPT_DEFAULT -taint -unsound_const_string -unsound_skip_function diagnostics"
elif [[ "$BASE" =~ wget.+ ]]; then
  OPT="$OPT_DEFAULT -inline alloc -filter_file hash.c \
    -filter_file html-parse.c -filter_file utils.c -filter_file url.c \
    -filter_allocsite _G_ -filter_allocsite extern
    -filter_allocsite uri_ -filter_allocsite url_ \
    -filter_allocsite fd_read_hunk
    -filter_allocsite main -filter_allocsite gethttp \
    -filter_allocsite strdupdelim -filter_allocsite checking_strdup \
    -filter_allocsite xmemdup \
    -filter_allocsite getftp -filter_allocsite cookie_header \
    -filter_allocsite dot_create -filter_allocsite yy -filter_function yy_scan_bytes"
elif [[ "$BASE" =~ grep.+ ]]; then
  OPT="$OPT_DEFAULT -inline alloc"
elif [[ "$BASE" =~ sed.+ ]]; then
  OPT="$OPT_DEFAULT -inline alloc -filter_allocsite match_regex -filter_file obstack.c \
    -filter_node match_regex-64558 -filter_node do_subst-* \
    -filter_allocsite extern -filter_allocsite _G_ -filter_allocsite quote \
    -filter_function str_append_modified -filter_function compile_regex_1"
elif [[ "$BASE" =~ sort.+ ]]; then
  OPT="$OPT_DEFAULT -inline alloc -unsound_skip_file getdate.y -filter_allocsite yyparse \
    -filter_allocsite extern -filter_allocsite main -filter_allocsite _G_ \
    -filter_file quotearg.c -filter_file printf-args.c -filter_file printf-parse.c"
elif [[ "$BASE" =~ readelf.+ ]]; then
  OPT="$OPT_DEFAULT -inline alloc -filter_allocsite extern \
    -filter_allocsite _G_ -filter_allocsite simple -filter_allocsite get_"
elif [[ "$BASE" =~ tar.+ ]]; then
  OPT="$OPT_DEFAULT -inline alloc -filter_extern -unsound_skip_file parse-datetime \
    -filter_allocsite _G_- -filter_allocsite parse -filter_allocsite delete_archive_members \
    -filter_allocsite hash -filter_allocsite main -filter_allocsite quote \
    -filter_allocsite hol -filter_allocsite header -filter_allocsite xmemdup \
    -filter_allocsite xmalloc -filter_allocsite dump"
else
  OPT=$OPT_DEFAULT
fi

if [[ "$3" == "reuse" ]]; then
  MARSHAL_OPT="-marshal_in"
  MSG=" (reading old results)"
else
  MARSHAL_OPT="-marshal_out"
fi

mkdir -p $OUTPUT_DIR/$ANALYSIS/bnet
touch rule-prob.txt

########################################################################################################################
# 2. Run Sparrow

START_TIME=$SECONDS
echo "Running Sparrow" $MSG
sparrow $OPT $MARSHAL_OPT $PGM >&/dev/null
ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo "Sparrow completes ($ELAPSED_TIME sec)"

########################################################################################################################
# 3. Run Souffle

START_TIME=$SECONDS
echo "Running Souffle"
if [[ $ANALYSIS == "interval" ]]; then
  souffle -F $OUTPUT_DIR/interval/datalog -D $OUTPUT_DIR/interval/datalog datalog/BufferOverflow.dl
else
  souffle -F $OUTPUT_DIR/taint/datalog -D $OUTPUT_DIR/taint/datalog datalog/IntegerOverflow.dl
fi
ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo "Souffle completes ($ELAPSED_TIME sec)"

########################################################################################################################
# 4. Build Bayesian Network

####
# 4a. Generate named_cons_all.txt

START_TIME=$SECONDS
echo "Building Bayesian Network"
bingo/generate-named-cons.py $OUTPUT_DIR $ANALYSIS
cat $OUTPUT_DIR/$ANALYSIS/datalog/Alarm.facts |
  sed 's/^/Alarm(/' |
  sed 's/\t/,/' | sed 's/$/)/g' \
    >$OUTPUT_DIR/$ANALYSIS/bnet/Alarm.txt

####
# 4b. Eliminate cycles, optimize network, build factor graph

bingo/build-bnet.sh $OUTPUT_DIR/$ANALYSIS rule-prob.txt \
  $OUTPUT_DIR/$ANALYSIS/bnet/Alarm.txt bnet
ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo "Building Bayesian Network completes ($ELAPSED_TIME sec)"

########################################################################################################################
# 5. Run Bingo

if [[ -f "$BENCHMARK_DIR/label.json" ]]; then
  START_TIME=$SECONDS
  echo "Running Bingo"
  # Generate $BENCHMARK_DIR/sparrow-out/datalog/GroundTruth.facts from $BENCHMARK_DIR/label.json
  bingo/generate-ground-truth.py $BENCHMARK_DIR $ANALYSIS
  cat $OUTPUT_DIR/$ANALYSIS/datalog/GroundTruth.facts |
    sed 's/^/Alarm(/' |
    sed 's/\t/,/' | sed 's/$/)/g' \
      >$OUTPUT_DIR/$ANALYSIS/bnet/GroundTruth.txt
  bingo/accmd $OUTPUT_DIR/$ANALYSIS $OUTPUT_DIR/$ANALYSIS/bnet/Alarm.txt \
    $OUTPUT_DIR/$ANALYSIS/bnet/GroundTruth.txt /dev/null 500 "" /dev/null bnet
  ELAPSED_TIME=$(($SECONDS - $START_TIME))
  echo "Bingo completes ($ELAPSED_TIME sec)"
  script/auc.py $OUTPUT_DIR/$ANALYSIS/bingo_stats.txt $OUTPUT_DIR/$ANALYSIS/bnet/Alarm.txt
else
  NUM_ALARMS=$(wc -l $OUTPUT_DIR/$ANALYSIS/bnet/Alarm.txt | cut -f 1 -d ' ')
  echo "Total alarms: $NUM_ALARMS"
fi
