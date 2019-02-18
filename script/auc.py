#!/usr/bin/env python3

# Given a stats.txt file, computes the AUC score.
# ./auc.py bingo_stat.txt Alarm.txt

import math
import sys

rankedAlarmsFileName = sys.argv[1]
allAlarmsFileName= sys.argv[2]

numTrue = 0
numFalse = 0

index = 0
tpRatios = []
scores = []
xindices = [0]
yindices = [0]
lastTrue = 0

for line in open(rankedAlarmsFileName):
    if index > 0:
        if line.find('TrueGround') >= 0:
            numTrue = numTrue + 1
            lastTrue = index
        else:
            numFalse = numFalse + 1
        xindices.append(numFalse)
        yindices.append(numTrue)
    index = index + 1

totalAlarm = sum(1 for line in open(allAlarmsFileName))

while index <= totalAlarm:
    numFalse = numFalse + 1
    xindices.append(numFalse)
    yindices.append(numTrue)
    index = index + 1

print('Total alarms    : {0}'.format(numTrue + numFalse))
print('True alarms     : {0}'.format(numTrue))
print('False alarms    : {0}'.format(numFalse))
print('Last true alarm : {0}'.format(lastTrue))

if numTrue == 0 or numFalse == 0: exit(0)

xindices = list(map(lambda x: float(x) / float(numFalse), xindices))
yindices = list(map(lambda x: float(x) / float(numTrue), yindices))

# auc
x0 = 0.0
auc = 0.0
for (x,y) in zip(xindices, yindices):
    auc = auc + (x - x0) * y
    x0 = x

print('AUC: {0}'.format(auc))
