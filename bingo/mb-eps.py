#!/usr/bin/env python3

# Given the set of old constraints and old alarms (both translated by translate-cons.py),
# and the set of new constraints and new alarms,
# outputs:
# 1. the constraints which form the merged Bayesian network,
# 2. all EDB tuples in the merged Bayesian network,
# 3. translated versions of the alarm tuples on which to provide negative feedback, and
# 4. combined list of alarms for use during constraint pruning.

# NOTE 1: mb-eps.py differs from mb.py in that for each EDB tuple t in the new constraints such that t also appears in
# the old constraints,
# a. tNEW is assigned a small positive probability, and
# b. tNEW is not identified as a target of silencing in fb0EDB.txt.

# Point (a) is achieved by introducing a dummy clause with no hypotheses which derives:
# Repsilon: tNEW.
# As a result, such tuples tNEW no longer appear as EDBs in the rest of the pipeline.
# Furthermore, no EDB tuples need silencing. This script does not produce an fb0EDB.txt.

# NOTE 2: Similar to mb.py, the constraints generated may contain underivable tuples, and must therefore be
# post-processed by keep-derivable.cpp. We guarantee that all underivable tuples are of the form tOLD.

# Intended to be run from the bingo-ci-experiment folder. Example usage:
# BENCHMARK_DIR=./benchmark/grep-2.19; OUTPUT_DIR=$BENCHMARK_DIR/sparrow-out/bnet; \
# ./bingo/mb.py $OUTPUT_DIR/trans_named_cons_all.txt $OUTPUT_DIR/OldAlarm.txt \
#               $OUTPUT_DIR/named_cons_all.txt $OUTPUT_DIR/Alarm.txt \
#               $BENCHMARK_DIR/sparrow-out/merged_bnet/named_cons_all.txt \
#               $BENCHMARK_DIR/sparrow-out/merged_bnet/AllEDB.txt \
#               $BENCHMARK_DIR/sparrow-out/merged_bnet/fb0Alarm.txt \
#               $BENCHMARK_DIR/sparrow-out/merged_bnet/SemAllAlarm.txt

import logging
import os
import re
import sys

oldConsFilename, oldAlarmFilename, \
newConsFilename, newAlarmFilename, \
mergedConsFilename, allEDBFilename, fb0AlarmFilename, combinedAlarmsFilename = sys.argv[1:]

log_fmt_str = ("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s")
logging.basicConfig(level=logging.INFO, format=log_fmt_str, datefmt="%H:%M:%S")
logging.info('Hello!')

########################################################################################################################
# 0. Prelude

def lit2Tuple(literal):
    return literal if not literal.startswith('NOT ') else literal[len('NOT '):]

def clause2Antecedents(clause):
    return frozenset([ lit2Tuple(literal) for literal in clause[:-1] ])

def clause2Consequent(clause):
    consequent = clause[-1]
    assert not consequent.startswith('NOT ')
    return consequent

def readClauses(filename):
    lines = { line.strip() for line in open(filename) }
    rlines = { tuple([ cle.strip() for cle in line.split(':') if len(cle.strip()) > 0 ]) for line in lines }
    for ruleName, clauseStr in rlines: assert ruleName.count(' ') == 0
    rcls = { (ruleName, tuple([ literal.strip() for literal in clauseStr.split(', ') ])) \
             for ruleName, clauseStr in rlines }
    rcs = { (ruleName, clause2Antecedents(clauseList), clause2Consequent(clauseList)) \
            for ruleName, clauseList in rcls }
    return frozenset(rcs)

# 0a. Read clauses

oldClauses = readClauses(oldConsFilename)
newClauses = readClauses(newConsFilename)
logging.info('Read {} old clauses and {} new clauses'.format(len(oldClauses), len(newClauses)))
commonClauses = oldClauses & newClauses
logging.info('{} clauses occur in common between the two sets'.format(len(commonClauses)))

# 0b. Read alarms

oldAlarms = frozenset({ line.strip() for line in open(oldAlarmFilename) if len(line.strip()) > 0 })
newAlarms = frozenset({ line.strip() for line in open(newAlarmFilename) if len(line.strip()) > 0 })
commonAlarms = oldAlarms & newAlarms

logging.info('Read {} old alarms and {} new alarms: {} alarms occur in common'.format(len(oldAlarms), \
                                                                                      len(newAlarms), \
                                                                                      len(commonAlarms)))

# 0c. Identify tuples occuring in clauses

def allTuples(clause):
    return clause[1] | frozenset({ clause[2] })

allOldTuples = frozenset({ t for clause in oldClauses for t in allTuples(clause) })
allOldIDBs = frozenset({ consequent for rule, antecedents, consequent in oldClauses })
allOldEDBs = allOldTuples - allOldIDBs
logging.info('Old clauses cover {} tuples: {} EDB and {} IDB tuples'.format(len(allOldTuples), \
                                                                            len(allOldEDBs), \
                                                                            len(allOldIDBs)))

allNewTuples = frozenset({ t for clause in newClauses for t in allTuples(clause) })
allNewIDBs = frozenset({ consequent for rule, antecedents, consequent in newClauses })
allNewEDBs = allNewTuples - allNewIDBs
logging.info('New clauses cover {} tuples: {} EDB and {} IDB tuples'.format(len(allNewTuples), \
                                                                            len(allNewEDBs), \
                                                                            len(allNewIDBs)))

allCommonTuples = allOldTuples & allNewTuples
commonEDBs = allOldEDBs & allNewEDBs
logging.info('{} tuples occur in common: {} common EDBs'.format(len(allCommonTuples), len(commonEDBs)))

# 0d. Confirm the common clause hypothesis
# Because the tuples under consideration encode data flow facts, the common clause hypothesis is true.
# The one exception is in case of the final DUPath(...) => Alarm(...) constraints. In this case, including mysterious
# FX(...) tuples restores the common clause hypothesis. This can be achieved by a preceding call to the add-fx.py
# script.

# NOTE: Because of efficiency considerations, Souffle does not compute the full fixpoint for some analyses, such as
# taint analysis for latex2rtf. In such cases, we disable the CCH check.

# Formulation 1: For each clause c in newClauses,
#                if every tuple appearing in allTuples(t) also appears in allOldTuples,
#                then c itself occurs in oldClauses.

if 'DISABLE_CCH' not in os.environ:
    for clause in newClauses:
        if allTuples(clause).issubset(allOldTuples) and clause not in oldClauses:
            logging.warn('Discovered clause {} which violates common clause hypothesis 1'.format(clause))

# Formulation 2: For each clause c in newClauses,
#                if every antecedent tuple t of c also appears in allOldTuples,
#                then c itself appears in oldClauses.

if 'DISABLE_CCH' not in os.environ:
    for clause in newClauses:
        if clause[1].issubset(allOldTuples) and clause not in oldClauses:
            logging.warn('Discovered clause {} which violates common clause hypothesis 2'.format(clause))

########################################################################################################################
# 1. Split Tuples and Clauses

def markTuple(t, mark): return t.replace('(', '{}('.format(mark))
def markTupleOld(t): return markTuple(t, 'OLD')
def markTupleNew(t): return markTuple(t, 'NEW')

def makeCombinations(antecedents):
    if not antecedents: return { frozenset() }
    else:
        firstTuple = antecedents.pop()
        combinationsRest = makeCombinations(antecedents)

        ans = set()
        if firstTuple in allOldTuples:
            firstTupleOld = markTupleOld(firstTuple)
            ans |= { crest | frozenset({ firstTupleOld }) for crest in combinationsRest }
        firstTupleNew = markTupleNew(firstTuple)
        ans |= { crest | frozenset({ firstTupleNew }) for crest in combinationsRest }

        return ans

# 1a. Split clauses

splitClauses = set()
emittedConsequents = set()
for ruleName, antecedents, consequent in newClauses:
    antCombinationAllOld = frozenset({ markTupleOld(t) for t in antecedents })
    antecedentCombinations = makeCombinations(set(antecedents))
    antCombinationsOneNew = antecedentCombinations - { antCombinationAllOld }

    consequentOld = markTupleOld(consequent)
    consequentNew = markTupleNew(consequent)

    if (ruleName, antecedents, consequent) in oldClauses:
        splitClauses.add((ruleName, antCombinationAllOld, consequentOld))
        emittedConsequents.add(consequentOld)

    for combination in antCombinationsOneNew:
        splitClauses.add((ruleName, combination, consequentNew))
        emittedConsequents.add(consequentNew)

# 1b. Mark all new EDB tuples which are also present in the old constraints as derivable anyway
# This step is new in mb-eps.py

for t in allNewEDBs & allOldEDBs:
    tNew = markTupleNew(t)
    splitClauses.add(('Repsilon', frozenset(), tNew))
    emittedConsequents.add(tNew)
    tOld = markTupleOld(t)
    splitClauses.add(('Rneps', frozenset(), tOld))
    emittedConsequents.add(tOld)
# 1c. Print output

with open(mergedConsFilename, 'w') as outFile:
    for ruleName, antecedents, consequent in splitClauses:
        antStrs = [ 'NOT {}'.format(antStr) for antStr in antecedents ]
        antStrsJoin = ', '.join(antStrs)
        if antStrsJoin: print('{}: {}, {}'.format(ruleName, antStrsJoin, consequent), file=outFile)
        else: print('{}: {}'.format(ruleName, consequent), file=outFile)

########################################################################################################################
# 2. Identify Tuples for Silencing and For Use by keep-derivable

# 2a. All combined EDB tuples
logging.info('Printing all EDB tuples to {}'.format(allEDBFilename))
with open(allEDBFilename, 'w') as outFile:
    for t in allNewEDBs:
        if t in allOldEDBs:
            # If t is also an old EDB tuple, then we have an Repsilon clause producing the new version of the tuple.
            # and an Rneps clause producing the old version of the tuple.
            # We therefore do not mark it as an EDB tuple
            pass
        else: print(markTupleNew(t), file=outFile)

# 2b. EDB tuples
# In contrast to mb.py, we are not silencing new EDB tuples
# We instead just perform some sanity checks

combinedTuples = { ant for ruleName, antecedents, consequent in splitClauses for ant in antecedents } | \
                 { consequent for ruleName, antecedents, consequent in splitClauses }

for t in allNewEDBs:
    if t not in allOldEDBs:
        tOld = markTupleOld(t)
        assert tOld not in combinedTuples
    else:
        tNew = markTupleNew(t)
        assert ('Repsilon', frozenset(), tNew) in splitClauses
        assert tNew in emittedConsequents
        tOld = markTupleOld(t)
        assert ('Rneps', frozenset(), tOld) in splitClauses
        assert tOld in emittedConsequents

# 2c. Alarm tuples

with open(fb0AlarmFilename, 'w') as outFile:
    for t in commonAlarms:
        print(markTupleOld(t), file=outFile)

########################################################################################################################
# 3. Print Combined List of Alarms

with open(combinedAlarmsFilename, 'w') as outFile:
    for t in oldAlarms | newAlarms:
        if markTupleOld(t) in emittedConsequents:
            print(markTupleOld(t), file=outFile)
        if markTupleNew(t) in emittedConsequents:
            print(markTupleNew(t), file=outFile)

logging.info('Bye!')
