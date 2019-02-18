#!/usr/bin/env python3

import json
import re
import os.path
import sys

problem_dir = sys.argv[1]
analysis = sys.argv[2]

label_file = problem_dir + "/label.json"
node_file = problem_dir + "/sparrow-out/node.json"
alarm_file = problem_dir + "/sparrow-out/" + analysis + "/datalog/Alarm.facts"
groundtruth_file = problem_dir + "/sparrow-out/" + analysis +"/datalog/GroundTruth.facts"

if not os.path.isfile(label_file):
    exit(0)

label_set = set()

with open(label_file) as f:
    labels = json.load(f)
    for label in labels:
        if analysis == 'taint' and 'source' in label:
            src = label['source']['file'] + ':' + str(label['source']['line'])
            sink = label['sink']['file'] + ':' + str(label['sink']['line'])
            label_set.add((src, sink))
        elif analysis == 'interval' and 'file' in label:
            src = None
            sink = label['file'] + ':' + str(label['line'])
            label_set.add((src, sink))
        else: pass

with open(node_file, 'rb') as f:
    node = json.loads(f.read().decode('utf-8', 'ignore'))['nodes']

groundtruth_set = set()
for line in open(alarm_file):
    line = line.strip()
    nodes = [ literal.strip() for literal in re.split("\t", line) ]
    if analysis == 'taint':
        src = node[nodes[0]]['loc']
        sink = node[nodes[1]]['loc']
    else:
        src = None
        sink = node[nodes[1]]['loc']
    if (src, sink) in label_set:
        groundtruth_set.add((nodes[0], nodes[1]))

with open(groundtruth_file, 'w') as f:
    for (src, sink) in groundtruth_set:
        f.write("{}\t{}\n".format(src, sink))
