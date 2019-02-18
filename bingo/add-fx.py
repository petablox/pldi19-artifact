#!/usr/bin/env python3

# Adds an XFactor hypothesis to each clause of the form DUPath(...) => Alarm(...), turning it into a clause of the form
# DUPath(...), FX(...) => Alarm(...), so that the common clause hypothesis is restored.

# ./bingo/add-fx.py < named_cons_all.txt > named_cons_all.txt.fx

import logging
import re
import sys

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

def splitTuple(t):
    relName, fields = t.split('(')
    assert fields.endswith(')')
    fields = fields[:-1]
    return (relName, fields)

########################################################################################################################
# 1. Read clauses

lines = { line.strip() for line in sys.stdin if len(line.strip()) > 0 }
rlines = { tuple([ cle.strip() for cle in line.split(':') if len(cle.strip()) > 0 ]) for line in lines }
for ruleName, clauseStr in rlines: assert ruleName.count(' ') == 0
rcls = { (ruleName, tuple([ literal.strip() for literal in clauseStr.split(', ') ])) \
         for ruleName, clauseStr in rlines }
clauses = { (ruleName, clause2Antecedents(clauseList), clause2Consequent(clauseList)) \
            for ruleName, clauseList in rcls }

logging.info('Read {} clauses'.format(len(clauses)))

########################################################################################################################
# 2. Compute Output

ans = set()

for clause in clauses:
    if not clause[2].startswith('Alarm('): ans.add(clause)
    else:
        alarmRelName, alarmFields = splitTuple(clause[2])
        assert len(clause[1]) == 1

        antecedent = set(clause[1]).pop()
        antRelName, antFields = splitTuple(antecedent)
        assert antRelName == 'DUPath'
        assert antFields == alarmFields

        newAnts = frozenset({ antecedent, 'FX({})'.format(antFields) })

        ans.add((clause[0], newAnts, clause[2]))

########################################################################################################################
# 3. Print Output

for ruleName, antecedents, consequent in ans:
    antStrs = [ 'NOT {}'.format(antStr) for antStr in antecedents ]
    antStrsJoin = ', '.join(antStrs)
    print('{}: {}, {}'.format(ruleName, antStrsJoin, consequent))

logging.info('Bye!')
