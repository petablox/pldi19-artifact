#!/usr/bin/env python3

# Example:
# ./print_bnet.py named_cons_all.txt.cep Alarm.txt GroundTruth.txt output.svg
# This program will also generate output.svg.map that contains tha mapping
# from vertex numbers to nodes

import graph
import logging
import re
import sys
import util

from graph_tool.all import *

cons_file = sys.argv[1]
alarm_file = sys.argv[2]
ground_truth_file = sys.argv[3]
output_file = sys.argv[4]
old_alarm_file = sys.argv[5] if len(sys.argv) == 6 else None

alarms = util.read_alarm(alarm_file)
old_alarms = set() if old_alarm_file is None else util.read_alarm(old_alarm_file)
ground_truths = util.read_alarm(ground_truth_file)

g = graph.build_graph(cons_file, alarms)['graph']
graph.prepare_visualization(g, alarms, old_alarms, ground_truths)
graph.draw(g, output_file)
graph.print_node_id(g, output_file + '.map')
