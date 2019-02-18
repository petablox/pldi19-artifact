#!/usr/bin/env python3

def lit2Tuple(literal):
    return literal if not literal.startswith('NOT ') else literal[len('NOT '):]

def clause2Antecedents(clause):
    return [lit2Tuple(literal) for literal in clause[:-1]]

def clause2Consequent(clause):
    consequent = clause[-1]
    assert not consequent.startswith('NOT ')
    return consequent

def is_clause(line):
    return line.startswith('NOT ')

def read_alarm(alarm_file):
    alarms = set()
    for line in open(alarm_file):
        alarms.add(line.strip())
    return alarms
