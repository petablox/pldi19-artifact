#!/usr/bin/env python3

import re
import sys

problem_dir = sys.argv[1]
analysis = sys.argv[2]

def generate_buffer_overflow(name, line):
    line = line.strip()
    nodes = [ literal.strip() for literal in re.split("\t", line) ]
    if name == 'DUPath0':
        cons = "DUPath0: NOT DUEdge({},{}), DUPath({},{})\n" \
                .format(nodes[0], nodes[1], nodes[0], nodes[1])
    elif name == 'DUPath1':
        cons = "DUPath1: NOT TrueBranch({},{}), DUPath({},{})\n" \
                .format(nodes[0], nodes[1], nodes[0], nodes[1])
    elif name == 'DUPath2':
        cons = "DUPath2: NOT FalseBranch({},{}), DUPath({},{})\n" \
                .format(nodes[0], nodes[1], nodes[0], nodes[1])
    elif name == 'DUPath3':
        cons = ("DUPath3: NOT DUPath({},{}), NOT DUEdge({},{}), "
                "DUPath({},{})\n") \
                .format(nodes[0], nodes[1], nodes[1], nodes[2], \
                        nodes[0], nodes[2])
    elif name == 'DUPath4':
        cons = ("DUPath4: NOT DUPath({},{}), NOT TrueCond({}), "
                "NOT TrueBranch({},{}), DUPath({},{})\n") \
                .format(nodes[0], nodes[1], nodes[1], nodes[1], nodes[2], \
                        nodes[0], nodes[2])
    elif name == 'DUPath5':
        cons = ("DUPath5: NOT DUPath({},{}), NOT FalseCond({}), "
                "NOT FalseBranch({},{}), DUPath({},{})\n") \
                .format(nodes[0], nodes[1], nodes[1], nodes[1], nodes[2], \
                        nodes[0], nodes[2])
    return cons

def generate_integer_overflow(name, line):
    line = line.strip()
    nodes = [ literal.strip() for literal in re.split("\t", line) ]
    if name == 'DUPath0':
        cons = "DUPath0: NOT DUEdge({},{}), DUPath({},{})\n" \
                .format(nodes[0], nodes[1], nodes[0], nodes[1])
    elif name == 'DUPath1':
        cons = "DUPath1: NOT TrueBranch({},{}), DUPath({},{})\n" \
                .format(nodes[0], nodes[1], nodes[0], nodes[1])
    elif name == 'DUPath2':
        cons = "DUPath2: NOT FalseBranch({},{}), DUPath({},{})\n" \
                .format(nodes[0], nodes[1], nodes[0], nodes[1])
    elif name == 'DUPath3':
        cons = ("DUPath3: NOT DUEdge({},{}), NOT DUPath({},{}), "
                "DUPath({},{})\n") \
                .format(nodes[0], nodes[1], nodes[1], nodes[2], \
                        nodes[0], nodes[2])
    elif name == 'DUPath4':
        cons = ("DUPath4: NOT TrueCond({}), NOT TrueBranch({},{}), "
                "NOT DUPath({},{}), DUPath({},{})\n") \
                .format(nodes[0], nodes[0], nodes[1], nodes[1], nodes[2], \
                        nodes[0], nodes[2])
    elif name == 'DUPath5':
        cons = ("DUPath5: NOT FalseCond({}), NOT FalseBranch({},{}), "
                "NOT DUPath({},{}), DUPath({},{})\n") \
                .format(nodes[0], nodes[0], nodes[1], nodes[1], nodes[2], \
                        nodes[0], nodes[2])
    return cons

def generate_old(name, line):
    line = line.strip()
    nodes = [ literal.strip() for literal in re.split("\t", line) ]
    if name == 'DUSuperEdge0':
        if elide:
            cons = ("DUSuperEdgeElide0: NOT DUEdgeElide({},{}), NOT !CallElide({}), "
                    "NOT !CallElide({}), NOT !Exit({}), NOT !Exit({}), "
                    "DUSuperEdge({},{})\n")  \
                    .format(nodes[0], nodes[2],
                            nodes[0],
                            nodes[2],
                            nodes[0],
                            nodes[2],
                            nodes[0], nodes[2])
        else:
            cons = ("DUSuperEdge0: NOT DUEdge({},{},{}), NOT !Call({},{}), "
                    "NOT !Call({},{}), NOT !Exit({}), NOT !Exit({}), "
                    "DUSuperEdge({},{})\n")  \
                    .format(nodes[0], nodes[1], nodes[2],
                            nodes[0], "dummy",
                            nodes[2], "dummy",
                            nodes[0],
                            nodes[2],
                            nodes[0], nodes[2])
    elif name == 'DUSuperEdge1':
        if elide:
            cons = ("DUSuperEdgeElide1: NOT DUEdgeElide({},{}), NOT CallElide({}), "
                    "NOT DUEdgeElide({},{}), NOT Entry({}), "
                    "NOT DUEdgeElide({},{}), DUSuperEdge({},{})\n") \
                    .format(nodes[0], nodes[2],
                            nodes[2],
                            nodes[2], nodes[5],
                            nodes[5],
                            nodes[5], nodes[6],
                            nodes[0], nodes[6])
        else:
            cons = ("DUSuperEdge1: NOT DUEdge({},{},{}), NOT Call({},{}), "
                    "NOT Bind({},{}), NOT DUEdge({},{},{}), NOT Entry({}), "
                    "NOT DUEdge({},{},{}), DUSuperEdge({},{})\n") \
                    .format(nodes[0], nodes[1], nodes[2],
                            nodes[2], nodes[3],
                            nodes[1], nodes[4],
                            nodes[2], nodes[4], nodes[5],
                            nodes[5],
                            nodes[5], nodes[4], nodes[6],
                            nodes[0], nodes[6])
    elif name == 'DUSuperEdge2':
        if elide:
            cons = ("DUSuperEdgeElide2: NOT DUEdgeElide({},{}), NOT CallElide({}), "
                    "NOT DUEdgeElide({},{}), NOT Entry({}), "
                    "NOT DUEdgeElide({},{}), DUSuperEdge({},{})\n") \
                    .format(nodes[0], nodes[2],
                            nodes[2],
                            nodes[2], nodes[4],
                            nodes[4],
                            nodes[4], nodes[5],
                            nodes[0], nodes[5])
        else:
            cons = ("DUSuperEdge2: NOT DUEdge({},{},{}), NOT Call({},{}), "
                    "NOT DUEdge({},{},{}), NOT Entry({}), "
                    "NOT DUEdge({},{},{}), DUSuperEdge({},{})\n") \
                    .format(nodes[0], nodes[1], nodes[2],
                            nodes[2], nodes[3],
                            nodes[2], nodes[1], nodes[4],
                            nodes[4],
                            nodes[4], nodes[2], nodes[5],
                            nodes[0], nodes[5])
    elif name == 'DUSuperEdge3':
        if elide:
            cons = ("DUSuperEdgeElide3: NOT DUEdgeElide({},{}), NOT CallElide({}), "
                    "NOT DUEdgeElide({},{}), NOT !Entry({}), DUSuperEdge({},{})\n") \
                    .format(nodes[0], nodes[2],
                            nodes[2],
                            nodes[2], nodes[5],
                            nodes[5],
                            nodes[0], nodes[5])
        else:
            cons = ("DUSuperEdge3: NOT DUEdge({},{},{}), NOT Call({},{}), "
                    "NOT DUEdge({},{},{}), NOT !Entry({}), DUSuperEdge({},{})\n") \
                    .format(nodes[0], nodes[1], nodes[2],
                            nodes[2], nodes[3],
                            nodes[2], nodes[4], nodes[5],
                            nodes[5],
                            nodes[0], nodes[5])
    elif name == 'DUSuperEdge4':
        if elide:
            cons = ("DUSuperEdgeElide4: NOT DUEdgeElide({},{}), NOT Exit({}), "
                    "NOT DUEdgeElide({},{}), DUSuperEdge({},{})\n") \
                    .format(nodes[0], nodes[2],
                            nodes[2],
                            nodes[2], nodes[3],
                            nodes[0], nodes[3])
        else:
            cons = ("DUSuperEdge4: NOT DUEdge({},{},{}), NOT Exit({}), "
                    "NOT DUEdge({},{},{}), DUSuperEdge({},{})\n") \
                    .format(nodes[0], nodes[1], nodes[2],
                            nodes[2],
                            nodes[2], nodes[1], nodes[3],
                            nodes[0], nodes[3])
    elif name == 'DUPath0':
        cons = ("DUPath0: NOT DUSuperEdge({},{}), DUPath({},{})\n") \
                .format(nodes[0], nodes[1],
                        nodes[0], nodes[1])
    elif name == 'DUPath1':
        cons = ("DUPath1: NOT DUPath({},{}), NOT DUSuperEdge({},{}), "
                "DUPath({},{})\n") \
                .format(nodes[0], nodes[1],
                        nodes[1], nodes[2],
                        nodes[0], nodes[2])
    else:
        assert False
    return cons

def generate_alarm(line):
    line = line.strip()
    nodes = [ literal.strip() for literal in re.split("\t", line) ]
    cons = ("Alarm: NOT DUPath({},{}), Alarm({},{})\n" \
            .format(nodes[0], nodes[1], nodes[0], nodes[1]))
    return cons

if analysis == 'interval':
    with open(problem_dir + '/' + analysis + '/bnet/named_cons_all.txt', 'w') as output_file:
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath0.csv'):
            cons = generate_buffer_overflow('DUPath0', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath1.csv'):
            cons = generate_buffer_overflow('DUPath1', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath2.csv'):
            cons = generate_buffer_overflow('DUPath2', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath3.csv'):
            cons = generate_buffer_overflow('DUPath3', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath4.csv'):
            cons = generate_buffer_overflow('DUPath4', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath5.csv'):
            cons = generate_buffer_overflow('DUPath5', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Alarm.facts'):
            cons = generate_alarm(line)
            output_file.write(cons)
elif analysis == 'taint':
    with open(problem_dir + '/' + analysis + '/bnet/named_cons_all.txt', 'w') as output_file:
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath0.csv'):
            cons = generate_integer_overflow('DUPath0', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath1.csv'):
            cons = generate_integer_overflow('DUPath1', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath2.csv'):
            cons = generate_integer_overflow('DUPath2', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath3.csv'):
            cons = generate_integer_overflow('DUPath3', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath4.csv'):
            cons = generate_integer_overflow('DUPath4', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Deriv_DUPath5.csv'):
            cons = generate_integer_overflow('DUPath5', line)
            output_file.write(cons)
        for line in open(problem_dir + '/' + analysis + '/datalog/Alarm.facts'):
            cons = generate_alarm(line)
            output_file.write(cons)
else:
    assert False
