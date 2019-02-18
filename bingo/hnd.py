#!/usr/bin/env python3

# Prints all tuples with new derivations
# ./bingo/hnd.py old_named_cons_all.txt old_alarms.txt new_named_cons_all.txt new_alarms.txt

import graph
import logging
import re
import sys
import util

from graph_tool.all import *

old_cons_file = sys.argv[1]
old_alarm_file = sys.argv[2]
new_cons_file = sys.argv[3]
new_alarm_file = sys.argv[4]

log_fmt_str = ("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s")
logging.basicConfig(level=logging.INFO, format=log_fmt_str, datefmt="%H:%M:%S")
logging.info('Hello!')

old_alarms = util.read_alarm(old_alarm_file)
new_alarms = util.read_alarm(new_alarm_file)
logging.info('Building old graph')
old_graph = graph.build_graph(old_cons_file, old_alarms)
logging.info('Building new graph')
new_graph = graph.build_graph(new_cons_file, new_alarms)

og2 = old_graph['graph']
ng2 = new_graph['graph']

def allTuples(graph):
    return { graph.vertex_properties['info'][t]['label'] for t in graph.vertices() \
             if graph.vertex_properties['info'][t]['type'] == 'tuple' }

allOldTuples = allTuples(og2)
logging.info('Discovered {} tuples in old graph'.format(len(allOldTuples)))
allNewTuples = allTuples(ng2)
logging.info('Discovered {} tuples in new graph'.format(len(allNewTuples)))
trulyNewTuples = allNewTuples - allOldTuples
logging.info('Of the tuples in the new graph, {} are truly new'.format(len(trulyNewTuples)))

# assert old_alarms <= allOldTuples
assert new_alarms <= allNewTuples

def allConsequents(graph):
    return { graph.vertex_properties['info'][v]['label'] for u, v in graph.edges() \
             if graph.vertex_properties['info'][v]['type'] == 'tuple' }

allOldConsequents = allConsequents(og2)
allOldEDBs = allOldTuples - allOldConsequents
logging.info('Discovered {} EDB tuples in old graph'.format(len(allOldEDBs)))
allNewConsequents = allConsequents(ng2)
allNewEDBs = allNewTuples - allNewConsequents
logging.info('Discovered {} EDB tuples in new graph'.format(len(allNewEDBs)))
trulyNewEDBs = allNewEDBs - allOldEDBs
stat = {}
for t in trulyNewEDBs:
    logging.info(t)
    for e in t.split('(')[1].split(')')[0].split(','):
        if e in stat:
            stat[e] = stat[e] + 1
        else:
            stat[e] = 1
l = sorted(stat.items(), key=lambda x: x[1], reverse=True)
for x in l: print(x)
logging.info('Of the EDBs in the new graph, {} are truly new'.format(len(trulyNewEDBs)))

def successorClauses(graph, at):
    ans = { t: set() for t in at }
    for u, v in graph.edges():
        if graph.vertex_properties['info'][u]['type'] == 'tuple':
            assert graph.vertex_properties['info'][v]['type'] == 'clause'
            t = graph.vertex_properties['info'][u]['label']
            c = graph.vertex_properties['info'][v]['label']
            assert t in ans
            ans[t].add(c)
    return ans

oldSuccessorClauses = successorClauses(og2, allOldTuples)
newSuccessorClauses = successorClauses(ng2, allNewTuples)

def successorTuples(graph, at):
    ans = {}
    for u, v in graph.edges():
        if graph.vertex_properties['info'][u]['type'] == 'clause':
            assert graph.vertex_properties['info'][v]['type'] == 'tuple'
            c = graph.vertex_properties['info'][u]['label']
            t = graph.vertex_properties['info'][v]['label']
            if c in ans: assert ans[c] == t
            else: ans[c] = t
            # if c in ans: logging.info('{}; {}; {}; {}'.format(c, t, ans[c], u.out_degree()))
            # assert c not in ans
            # ans[c] = t
    return ans

oldSuccessorTuples = successorTuples(og2, allOldTuples)
newSuccessorTuples = successorTuples(ng2, allNewTuples)

hasNewDerivation = trulyNewEDBs
procClauses = set()
unprocClauses = set()
waitingClauses = { c for t in hasNewDerivation for c in newSuccessorClauses[t] }
while waitingClauses:
    c = waitingClauses.pop()
    procClauses.add(c)
    t = newSuccessorTuples[c]
    hasNewDerivation.add(t)
    for c in newSuccessorClauses[t]:
        if c not in procClauses and c not in waitingClauses: waitingClauses.add(c)

logging.info('Of the tuples in the new graph, {} have new derivations'.format(len(hasNewDerivation)))
alarmsWithNewDeriv = new_alarms & hasNewDerivation
logging.info('Of the {} alarms in the new graph, {} have new derivations'.format(len(new_alarms), len(alarmsWithNewDeriv)))
for t in new_alarms:
    if t not in alarmsWithNewDeriv:
        print('{}'.format(t))

logging.info('Bye!')
