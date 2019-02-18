#!/usr/bin/env bash

# Runs Delta-Bingo in the syn mode.
# Usage: ./delta-sem.sh OLD_PROGRAM_DIR NEW_PROGRAM_DIR [interval | taint] [strong | weak]

########################################################################################################################
# 0. Prelude

set -e

if [[ $# -ne 4 ]]; then
  echo "Invalid Argument" 1>&2
  exit 1
fi

OLD_PGM=$1
NEW_PGM=$2
ANALYSIS=$3
FB_MODE=$4
OLD_OUTPUT_DIR=$OLD_PGM/sparrow-out
NEW_OUTPUT_DIR=$NEW_PGM/sparrow-out

echo "Running Delta Bingo (syn)" 1>&2

########################################################################################################################
# 1. Translating Constraints

echo "Step 1: Translating constraints" 1>&2
START_TIME=$SECONDS

####
# 1a. Invoke translate-cons.py

# translate-cons.py takes as input:
# 1. the old- and new named_cons_all.txt.cep files ($OLD_PGM/.../bnet/named_cons_all.txt.cep and
#    $NEW_PGM/.../bnet/named_cons_all.txt.cep respectively),
# 2. the old- and new sets of alarms ($OLD_PGM/.../bnet/Alarm.txt and $NEW_PGM/.../bnet/Alarm.txt respectively),
# 3. the old- and new node.json files ($OLD_PGM/.../node.json and $NEW_PGM/.../node.json respectively),
# 4. the line matching file produced by Sparrow ($NEW_PGM/line_matching.json), and
# 5. the name of the output directory ($NEW_PGM/sparrow-out/bnet).

# In the output directory, it places:
# 1. $NEW_PGM/sparrow-out/bnet/trans_named_cons_all.txt.
#    TODO: Confirm the contents of trans_named_cons_all.txt with Kihong, specifically the ???.
#    Every tuple R(a_1, a_2, ..., a_k) is transformed into R(b_1, b_2, ..., b_k), where
#        b_i = h(a_i) if h(a_i) occurs in $NEW_PGM/.../bnet/named_cons_all.txt, and
#              ???-OLD, otherwise.
# 2. $NEW_PGM/sparrow-out/bnet/translation.map.
# 3. $NEW_PGM/sparrow-out/bnet/OldAlarm.txt. This file contains the list of old alarms transformed by the h-function.

# 1b. Compute the set of new alarms

# DEFINITION: The new alarms are those which were not observed in the old program.
# By ``syntactic masking'', we mean that we are only going to rank the new alarms. We store these alarms in
# $NEW_OUTPUT_DIR/bnet/NewAlarm.txt.

comm -13 <(sort $NEW_OUTPUT_DIR/$ANALYSIS/bnet/OldAlarm.txt) \
         <(sort $NEW_OUTPUT_DIR/$ANALYSIS/bnet/Alarm.txt) \
         > $NEW_OUTPUT_DIR/$ANALYSIS/bnet/NewAlarm.txt

comm -12 <(sort $NEW_OUTPUT_DIR/$ANALYSIS/bnet/OldAlarm.txt) \
         <(sort $NEW_OUTPUT_DIR/$ANALYSIS/bnet/Alarm.txt) \
         > $NEW_OUTPUT_DIR/$ANALYSIS/bnet/CommonAlarm.txt

echo "`wc -l $NEW_OUTPUT_DIR/$ANALYSIS/bnet/CommonAlarm.txt | cut -f 1 -d ' '` syntactically common alarms detected" 1>&2
echo "`wc -l $NEW_OUTPUT_DIR/$ANALYSIS/bnet/NewAlarm.txt | cut -f 1 -d ' '` syntactically new alarms detected" 1>&2

ELAPSED_TIME=$(($SECONDS - $START_TIME))
echo "Finished translating constraints ($ELAPSED_TIME sec)" 1>&2

########################################################################################################################
# 2. Running accmd

if [[ -f "$NEW_PGM/label.json" ]]; then
  echo "Step 2: Executing Interaction" 1>&2
  START_TIME=$SECONDS

  ####
  # 2a. Compute feedback sets

  if [[ "$FB_MODE" == "strong" ]]; then
    # In the strong feedback mode, we give negative feedback on all old alarms
    export FBFILE=$NEW_OUTPUT_DIR/$ANALYSIS/bnet/CommonAlarm.txt
  else
    # In the weak feedback mode, we simply ignore all old alarms
    export FBFILE=/dev/null
  fi

  ####
  # 2b. Invoke accmd

  echo "Executing accmd" 1>&2
  bingo/accmd $NEW_OUTPUT_DIR/$ANALYSIS \
              $NEW_OUTPUT_DIR/$ANALYSIS/bnet/NewAlarm.txt \
              <(comm -12 <(sort $NEW_OUTPUT_DIR/$ANALYSIS/bnet/NewAlarm.txt) \
                         <(sort $NEW_OUTPUT_DIR/$ANALYSIS/bnet/GroundTruth.txt)) \
              /dev/null \
              500 \
              delta_syn_${FB_MODE}_ \
              $FBFILE \
              bnet

  ####
  # 2c. Compute AUC

  echo "Computing AUC" 1>&2
  script/auc.py $NEW_OUTPUT_DIR/$ANALYSIS/bingo_delta_syn_${FB_MODE}_stats.txt \
                $NEW_OUTPUT_DIR/$ANALYSIS/bnet/NewAlarm.txt

  ELAPSED_TIME=$(($SECONDS - $START_TIME))
  echo "Interaction completes ($ELAPSED_TIME sec)"
else
  NUM_ALARMS=`wc -l $NEW_OUTPUT_DIR/$ANALYSIS/bnet/NewAlarm.txt | cut -f 1 -d ' '`
  echo "Total alarms: $NUM_ALARMS"
fi
