#!/usr/bin/env python3

# Given the set of old constraints and old alarms (both translated by translate-cons.py),
# and the set of new constraints and new alarms,
# outputs:
# 1. the constraints which form the merged Bayesian network,
# 2. all EDB tuples in the merged Bayesian network,
# 3. identifies which EDB tuples to silence,
# 4. translated versions of the alarm tuples on which to provide negative feedback, and
# 5. combined list of alarms for use during constraint pruning.

# NOTE: The constraints generated may contain underivable tuples, and must therefore be post-processed by
# keep-derivable.cpp.

# Intended to be run from the bingo-ci-experiment folder. Example usage:
# BENCHMARK_DIR=./benchmark/grep-2.19; OUTPUT_DIR=$BENCHMARK_DIR/sparrow-out/bnet; \
# ./bingo/mb.py $OUTPUT_DIR/trans_named_cons_all.txt $OUTPUT_DIR/OldAlarm.txt \
#               $OUTPUT_DIR/named_cons_all.txt $OUTPUT_DIR/Alarm.txt \
#               $BENCHMARK_DIR/sparrow-out/merged_bnet/named_cons_all.txt \
#               $BENCHMARK_DIR/sparrow-out/merged_bnet/AllEDB.txt \
#               $BENCHMARK_DIR/sparrow-out/merged_bnet/fb0EDB.txt \
#               $BENCHMARK_DIR/sparrow-out/merged_bnet/fb0Alarm.txt \
#               $BENCHMARK_DIR/sparrow-out/merged_bnet/SemAllAlarm.txt

import logging
import os
import re
import sys

oldConsFilename, oldAlarmFilename, \
newConsFilename, newAlarmFilename, \
mergedConsFilename, allEDBFilename, fb0EDBFilename, fb0AlarmFilename, combinedAlarmsFilename = sys.argv[1:]

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

# 1b. Print output

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
        print(markTupleNew(t), file=outFile)
        if t in allOldEDBs: print(markTupleOld(t), file=outFile)

# 2b. EDB tuples

with open(fb0EDBFilename, 'w') as outFile:
    for t in allNewEDBs:
        if t in allOldEDBs: print(markTupleNew(t), file=outFile)
        else: print(markTupleOld(t), file=outFile)

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
