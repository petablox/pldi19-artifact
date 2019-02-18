#!/usr/bin/env python3

# ./bingo/translate-cons.py old/sparrow-out/bnet/named_cons_all.txt new/sparrow-out/bnet/named_cons_all.txt \
#                           old/sparrow-out/bnet/Alarm.txt new/sparrow-out/bnet/Alarm.txt \
#                           old/sparrow-out/node.json new/sparrow-out/node.json \
#                           new/line_matching.json \
#                           new/sparrow-out/bnet

import codecs
import logging
import json
import os
import re
import sys

old_cons_file = sys.argv[1]
new_cons_file = sys.argv[2]
old_alarm_file = sys.argv[3]
new_alarm_file = sys.argv[4]
old_node_file = sys.argv[5]
new_node_file = sys.argv[6]
line_matching_file = sys.argv[7]
output_dir = sys.argv[8]

logging.basicConfig(level=logging.INFO, \
                    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s", \
                    datefmt="%H:%M:%S")
logging.info('Hello!')

def read_json(filename):
    with codecs.open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        return json.loads(f.read())

def read_alarm_set(filename):
    alarm_set = set()
    for alarm in open(filename):
        alarm_set.add(alarm.strip())
    return alarm_set

def read_cons(filename):
    all_clauses = []
    for line in open(filename):
        line = line.strip()
        clause = [literal.strip() for literal in re.split(':|, ', line)]
        all_clauses.append(clause)
    return all_clauses

def node_to_location(node, node_info):
    elements = node_info['nodes'][node]['loc'].split(':')
    return (elements[0], int(elements[1]))

location_cache = {}
def trans_location(location, line_matching):
    if location in location_cache:
        return location_cache[location]
    changed_files = line_matching['changed_files']
    added_files = line_matching['added_files']
    filename, line = location[0], location[1]
    location_set = set()
    if filename in changed_files:
        idx = 1
        for new_line in changed_files[filename]:
            if line == new_line:
                location_set.add((filename, idx))
            idx += 1
    elif filename not in added_files: # unchanged file
        location_set.add((filename, line))
        return location_set

    if len(location_set) > 0:
        location_cache[location] = location_set
        return location_set
    else:
        location_cache[location] = None
        return None

# weakest matching: line number and command type
def match_node(old_cmd, location, info):
    typ = old_cmd[0] + '-' + str(old_cmd[1]) \
        if old_cmd[0] == 'assume' else old_cmd[0]
    if location == info['loc']:
        cmd = info['cmd']
        if typ.startswith('assume') and cmd[0] == 'assume':
            return (typ == cmd[0] + '-' + str(cmd[1]))
        elif typ == 'call' and cmd[0] == 'call':
            return (old_cmd[2] == cmd[2])
        else:
            return (typ == cmd[0])
    else:
        return False

def same_function(old_node, new_node):
    return old_node.split('-')[0] == new_node.split('-')[0]


def same_tag(old_node, old_node_info, new_node, new_node_info):
    old_cmd = old_node_info['nodes'][old_node]['cmd'][0]
    old_tag = old_node_info['nodes'][old_node]['cmd'][1]
    new_cmd = new_node_info['nodes'][new_node]['cmd'][0]
    new_tag = new_node_info['nodes'][new_node]['cmd'][1]
    return old_cmd == 'skip' and new_cmd == 'skip' and old_tag == new_tag

# normalize temp variables
def normalize_exp(exp):
    exp = re.sub(r'___[0-9]+', '', exp)
    exp = re.sub(r'__cil_tmp[0-9]+', '__cil_tmp', exp)
    exp = re.sub(r'([a-zA-Z_]+)[0-9]+', r'\1', exp)
    return exp

def normalize_cmd(cmd):
    if cmd[0] == 'skip':
        return cmd
    elif cmd[0] == 'set' or cmd[0] == 'alloc':
        new_cmd = cmd.copy()
        new_cmd[1] = normalize_exp(cmd[1])
        new_cmd[2] = normalize_exp(cmd[2])
        return new_cmd
    elif cmd[0] == 'assume':
        new_cmd = cmd.copy()
        new_cmd[2] = normalize_exp(cmd[2])
        return new_cmd
    elif cmd[0] == 'salloc':
        new_cmd = cmd.copy()
        new_cmd[1] = normalize_exp(cmd[1])
        return new_cmd
    elif cmd[0] == 'call' and cmd[1] is not None:
        new_cmd = cmd.copy()
        new_cmd[1] = normalize_exp(cmd[1])
        new_cmd[3] = normalize_exp(cmd[3])
        return new_cmd
    elif cmd[0] == 'call':
        new_cmd = cmd.copy()
        new_cmd[3] = normalize_exp(cmd[3])
        return new_cmd
    elif cmd[0] == 'return' and cmd[1] is not None:
        new_cmd = cmd.copy()
        new_cmd[1] = normalize_exp(cmd[1])
        return new_cmd
    else:
        return cmd

def get_parents(node, node_info, normalize=False):
    parent_node_ids = [e[0] for e in node_info['edges'] if e[1] == node]
    parent_node_cmds = [node_info['nodes'][node]['cmd'] for node in parent_node_ids]
    if normalize:
        parent_node_cmds = [normalize_cmd(node_info['nodes'][node]['cmd']) \
                            for node in parent_node_ids]
    else:
        parent_node_cmds = [node_info['nodes'][node]['cmd'] \
                            for node in parent_node_ids]
    return {tuple(cmd) for cmd in parent_node_cmds}

def get_children(node, node_info, normalize=False):
    children_node_ids = [e[1] for e in node_info['edges'] if e[0] == node]
    children_node_cmds = [node_info['nodes'][node]['cmd'] for node in children_node_ids]
    logging.debug(children_node_cmds)
    if normalize:
        children_node_cmds = [normalize_cmd(node_info['nodes'][node]['cmd']) \
                              for node in children_node_ids]
    else:
        children_node_cmds = [node_info['nodes'][node]['cmd'] \
                              for node in children_node_ids]
    return {tuple(cmd) for cmd in children_node_cmds}


def same_parents(old_node, old_node_info, new_node, new_node_info, normalize=False):
    old_parents = get_parents(old_node, old_node_info, normalize=normalize)
    new_parents = get_parents(new_node, new_node_info, normalize=normalize)
    return old_parents == new_parents

def same_children(old_node, old_node_info, new_node, new_node_info, normalize=False):
    old_children = get_children(old_node, old_node_info, normalize=normalize)
    new_children = get_children(new_node, new_node_info, normalize=normalize)
    return old_children == new_children

def match_node2(old_node, old_node_info, new_node, new_node_info):
    if old_node_info['nodes'][old_node]['cmd'][0] == 'skip':
        return same_tag(old_node, old_node_info, new_node, new_node_info)
    elif old_node_info['nodes'][old_node]['cmd'][0] == 'set':
        return normalize_exp(old_node_info['nodes'][old_node]['cmd'][1]) == \
            normalize_exp(new_node_info['nodes'][new_node]['cmd'][1])
    else:
        return True

def node_not_found(old_node):
    logging.warn('Node Not found {}'.format(old_node))
    return (old_node + '-OLD')

def match_exp(exp1, exp2):
    # normalize temp variables
    exp1 = normalize_exp(exp1)
    exp2 = normalize_exp(exp2)
    return exp1 == exp2

ambiguous = {}
def select_node(old_node, old_node_info, new_node_info, node_set):
    logging.debug("Ambiguous0: {} -> {}".format(old_node, node_set))
    old_info = old_node_info['nodes'][old_node]
    filtered_node_set = set()
    # stronger matching
    for candidate in node_set:
        new_info = new_node_info['nodes'][candidate]
        old_cmd = old_info['cmd']
        new_cmd = new_info['cmd']
        if (old_cmd[0] == 'skip' and old_cmd[1] == new_cmd[1]) \
                or (old_cmd[0] == 'set' and match_exp(old_cmd[2], new_cmd[2])) \
                or (old_cmd[0] == 'alloc' and match_exp(old_cmd[1], new_cmd[1])) \
                or (old_cmd[0] == 'salloc' and match_exp(old_cmd[1], new_cmd[1])) \
                or (old_cmd[0] == 'assume' and match_exp(old_cmd[2], new_cmd[2])) \
                or (old_cmd[0] == 'call' and match_exp(old_cmd[2], new_cmd[2])) \
                or (old_cmd[0] == 'return' and old_cmd[1] is not None \
                    and new_cmd[1] is not None and match_exp(old_cmd[1], new_cmd[1])):
            filtered_node_set.add(candidate)

    if len(filtered_node_set) == 0: return node_not_found(old_node)

    # much stronger matching
    # In Sparrow, the following happens because of inline or other reasons
    filtered_node_set = {node for node in filtered_node_set if \
                         same_function(old_node, node)}
    logging.debug("After filter1 : {} -> {}".format(old_node, filtered_node_set))
    if len(filtered_node_set) == 1:
        return filtered_node_set.pop()
    if len(filtered_node_set) == 0: return node_not_found(old_node)

    filtered_node_set = {node for node in filtered_node_set if \
                         match_node2(old_node, old_node_info, node, new_node_info)}
    logging.debug("After filter2 : {} -> {}".format(old_node, filtered_node_set))
    if len(filtered_node_set) == 1:
        return filtered_node_set.pop()
    if len(filtered_node_set) == 0: return node_not_found(old_node)

    filtered_node_set = {node for node in filtered_node_set if \
                          same_parents(old_node, old_node_info, node, new_node_info, normalize=True)}
    logging.debug('After filter3: {} -> {}'.format(old_node, filtered_node_set))
    if len(filtered_node_set) == 1:
        return filtered_node_set.pop()
    if len(filtered_node_set) == 0: return node_not_found(old_node)

    filtered_node_set = {node for node in filtered_node_set if \
                          same_parents(old_node, old_node_info, node, new_node_info, normalize=False)}
    logging.debug('After filter4: {} -> {}'.format(old_node, filtered_node_set))
    if len(filtered_node_set) == 1:
        return filtered_node_set.pop()
    if len(filtered_node_set) == 0: return node_not_found(old_node)

    filtered_node_set = {node for node in filtered_node_set if \
                          same_children(old_node, old_node_info, node, new_node_info, normalize=True)}
    logging.debug('After filter5: {} -> {}'.format(old_node, filtered_node_set))
    if len(filtered_node_set) == 1:
        return filtered_node_set.pop()
    if len(filtered_node_set) == 0: return node_not_found(old_node)

    filtered_node_set = {node for node in filtered_node_set if \
                          same_children(old_node, old_node_info, node, new_node_info, normalize=False)}
    logging.debug('After filter6: {} -> {}'.format(old_node, filtered_node_set))
    if len(filtered_node_set) == 1:
        return filtered_node_set.pop()

    if tuple(filtered_node_set) in ambiguous:
        ambiguous[tuple(filtered_node_set)].add(old_node)
    else:
        new_set = set()
        new_set.add(old_node)
        ambiguous[tuple(filtered_node_set)] = new_set

    return node_not_found(old_node)

def find_node(old_node, old_node_info, locations, new_node_info):
    location_strings = ['{}:{}'.format(location[0], location[1])
                        for location in locations]
    cmd = old_node_info['nodes'][old_node]['cmd']
    node_set = set()
    for target, info in new_node_info['nodes'].items():
        for location_string in location_strings:
            if match_node(cmd, location_string, info):
                node_set.add(target)
    if len(node_set) == 1:
        return node_set.pop()
    elif len(node_set) == 0:
        logging.warn('Not found: {} @ {}'.format(old_node, locations))
        return (old_node + '-OLD')
    else:
        return select_node(old_node, old_node_info, new_node_info, node_set)

def lit2Tuple(literal):
    return literal if not literal.startswith('NOT ') else literal[len('NOT '):]

def clause2Antecedents(clause):
    return [ lit2Tuple(literal) for literal in clause[:-1] ]

def clause2Consequent(clause):
    consequent = clause[-1]
    assert not consequent.startswith('NOT ')
    return consequent

node_cache = {}
node_taken = set()
def trans_node(node, old_node_info, new_node_info, line_matching, second=False):
    if second:
        if node.endswith('-OLD') and node.replace('-OLD', '') in node_cache:
            return node_cache[node.replace('-OLD', '')]
        else:
            return node
    if node.endswith('-ENTRY') or node.endswith('-EXIT'):
        return node
    if node in node_cache:
        return node_cache[node]
    if 'node_map' in line_matching and node in line_matching['node_map']:
        return line_matching['node_map'][node]
    old_location = node_to_location(node, old_node_info)
    # if source locations cannot be determined
    if old_location[1] == -1: return node + '-OLD'
    new_locations = trans_location(old_location, line_matching)
    if new_locations == None:
        logging.warn('Not found: {} @ {}'.format(node, old_location))
        new_node = node + '-OLD'
        node_cache[node] = new_node
        return new_node
    new_node = find_node(node, old_node_info, new_locations, new_node_info)
    if new_node in node_taken:
        new_node = node + '-OLD'
    node_cache[node] = new_node
    node_taken.add(new_node)
    return new_node

def trans_tuple(tup, old_node_info, new_node_info, line_matching, second=False):
    name, body = tup.split('(', 1)
    if name == 'DUEdge' or name == 'DUPath' or name == 'TrueCond' \
            or name == 'FalseCond' or 'TrueBranch' or 'FalseBranch' \
            or name == 'Alarm':
        elems = [ literal.strip() for literal in re.split('\(|,|\)', tup)[:-1] ][1:]
        trans = [ trans_node(n, old_node_info, new_node_info, line_matching, second=second) \
                  for n in elems ]
        return '{}({})'.format(name, ",".join(trans))
    else:
        logging.warn('WARN: ' + name)
        return tup

def trans_literal(literal, old_node_info, new_node_info, line_matching, second=False):
    if literal.startswith('NOT '):
        tup = trans_tuple(literal[4:], old_node_info, new_node_info, line_matching, second=second)
        return 'NOT ' + tup
    else:
        return trans_tuple(literal, old_node_info, new_node_info, line_matching, second=second)

def trans_cons(cons, old_node_info, new_node_info, line_matching, second=False):
    name, literals = cons[0], cons[1:]
    new_literals = [trans_literal(l, old_node_info, new_node_info, line_matching, second=second)
                    for l in literals]
    return [name] + new_literals

old_cons_all = read_cons(old_cons_file)

old_node_info = read_json(old_node_file)
new_node_info = read_json(new_node_file)
line_matching = read_json(line_matching_file)

old_alarm_set = read_alarm_set(old_alarm_file)
new_alarm_set = read_alarm_set(new_alarm_file)

# handle unchanged files and functions
unchanged_functions = set()
for node, info in old_node_info['nodes'].items():
    filename = info['loc'].split(':')[0]
    if node.endswith('ENTRY') \
            and filename in line_matching['unchanged_files'] \
            and filename not in line_matching['changed_files'] \
            and filename not in line_matching['added_files']:
        unchanged_functions.add(node.split('-')[0])
if 'unchanged_functions' in line_matching:
    for functionname in line_matching['unchanged_functions']:
        unchanged_functions.add(functionname)
else: logging.warn('Cannot find field unchanged_functions in line_matching')

if 'location_map' in line_matching:
    for old, new in line_matching['location_map'].items():
        old_location = (old.split(':')[0], int(old.split(':')[1]))
        new_location = {(new.split(':')[0], int(new.split(':')[1]))}
        location_cache[old_location] = new_location

logging.info('{} unchanged functions {}'.format(len(unchanged_functions), \
                                                str(unchanged_functions)))

old_unchanged_nodes = {f: [] for f in unchanged_functions}
new_unchanged_nodes = {f: [] for f in unchanged_functions}
for node, info in old_node_info['nodes'].items():
    functionname = node.split('-')[0]
    nodeid = node.split('-')[1]
    if functionname in unchanged_functions \
            and nodeid != 'ENTRY' and nodeid != 'EXIT':
        old_unchanged_nodes[functionname].append(node)

for node, info in new_node_info['nodes'].items():
    functionname = node.split('-')[0]
    nodeid = node.split('-')[1]
    if functionname in unchanged_functions \
            and nodeid != 'ENTRY' and nodeid != 'EXIT':
        new_unchanged_nodes[functionname].append(node)


for function in unchanged_functions:
    old_nodes = old_unchanged_nodes[function]
    new_nodes = new_unchanged_nodes[function]
    if len(old_nodes) != len(new_nodes):
        logging.warn('#unchanged nodes in {}: {}'.format(function, len(old_nodes)))
        logging.warn('#unchanged nodes in {}: {}'.format(function, len(new_nodes)))
        logging.warn('old: {}'.format(sorted(old_nodes)))
        logging.warn('new: {}'.format(sorted(new_nodes)))
        del old_unchanged_nodes[function]
        del new_unchanged_nodes[function]

def compare_node(node1, node2):
    function_name1 = node1.split('-')[0]
    function_name2 = node2.split('-')[0]
    if function_name1 == function_name2:
        node_id1 = int(node1.split('-')[1])
        node_id2 = int(node2.split('-')[1])
        return node_id1 - node_id2
    else:
        return function_name1 > function_name2

def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

old_unchanged_nodes = [node for nodes in old_unchanged_nodes.values() for node in nodes]
new_unchanged_nodes = [node for nodes in new_unchanged_nodes.values() for node in nodes]
sorted_old_unchanged_nodes = sorted(old_unchanged_nodes, key=cmp_to_key(compare_node))
sorted_new_unchanged_nodes = sorted(new_unchanged_nodes, key=cmp_to_key(compare_node))
for old_node, new_node in zip(sorted_old_unchanged_nodes, sorted_new_unchanged_nodes):
    node_cache[old_node] = new_node

idx = 0
length = len(old_cons_all)
def mapping(x):
    global idx
    global length
    logging.debug('{}/{}'.format(idx,length))
    idx+=1
    return trans_cons(x, old_node_info, new_node_info, line_matching)

# translate constraints
trans_cons_all = [mapping(c) for c in old_cons_all]

# handle ambiguous sets
for news, olds in ambiguous.items():
    if len(olds) == len(news):
        sorted_olds = sorted(list(olds), key=cmp_to_key(compare_node))
        sorted_news = sorted(list(news), key=cmp_to_key(compare_node))
        for old_node, new_node in zip(sorted_olds, sorted_news):
            node_cache[old_node] = new_node

name = os.path.basename(old_cons_file)
with open(output_dir + '/trans_' + name, 'w') as f:
    for cons in trans_cons_all:
        rule = [trans_literal(l, old_node_info, new_node_info, line_matching, second=True) \
                if '-OLD' in l else l for l in cons[1:]]
        f.write("{}: {}\n".format(cons[0], ", ".join(rule)))

trans_alarms = set()

for alarm in old_alarm_set:
    trans_alarm = trans_tuple(alarm, old_node_info, new_node_info, line_matching)
    trans_alarms.add(trans_alarm)

with open(output_dir + '/translation.map', 'w') as f:
    for old, new in node_cache.items():
        f.write("{} -> {}\n".format(old, new))

with open(output_dir + '/OldAlarm.txt', 'w') as f:
    for alarm in trans_alarms:
        f.write("{}\n".format(alarm))

logging.info('Bye!')
