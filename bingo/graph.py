#!/usr/bin/env python3

import re
import util

def get_vertex(g, name2idx, v_prop, typ, name, rulename=None, alarm=False):
    if name in name2idx:
        idx = name2idx[name]
        return idx
    else:
        v = g.add_vertex()
        v_prop[v] = {'label': name, 'type': typ, 'rulename': rulename,
                     'alarm': alarm}
        idx = g.vertex_index[v]
        name2idx[name] = idx
        return idx


# fmt is either 'origin' or 'compressed'
def build_graph(filename, alarms, fmt='origin'):
    g = Graph()
    name2idx = {}
    v_prop = g.new_vertex_property('object')
    edges = set()
    for line in open(filename):
        line = line.strip()
        # compressed bnet has derived EDBs
        if not util.is_clause(line.split(': ')[1]):
            if fmt == 'compressed':
                consequent = line.split(': ')[1]
                v = get_vertex(g, name2idx, v_prop, 'tuple', consequent,
                               alarm=consequent in alarms)
        else:
            clause = [literal.strip() for literal in re.split(':|, ', line)]
            rulename, clause = clause[0], clause[1:]
            antecedent_ids = [get_vertex(g, name2idx, v_prop, 'tuple', v, alarm=v in alarms)
                              for v in util.clause2Antecedents(clause)]
            consequent = util.clause2Consequent(clause)
            consequent_id = get_vertex(g, name2idx, v_prop, 'tuple', consequent,
                                   alarm=consequent in alarms)
            rule = get_vertex(g, name2idx, v_prop, 'clause',
                              re.split(': ', line)[1], rulename=rulename)
            for p in [p for p in antecedent_ids if g.edge(p, rule) is None]:
                edges.add((p, rule))
            if (rule, consequent_id) not in edges:
                edges.add((rule, consequent_id))
    g.add_edge_list(list(edges))
    g.vertex_properties['info'] = v_prop
    return {'graph': g, 'name2idx': name2idx}


def prepare_visualization(g, alarms, old_alarms, ground_truths):
    v_prop = g.vertex_properties['info']

    v_color = g.new_vertex_property('string')
    v_shape = g.new_vertex_property('string')

    for v in g.vertices():
        name = v_prop[v]['label']
        if name in ground_truths:
            v_color[v] = 'red'
        elif name in alarms:
            v_color[v] = 'blue'
        elif name in old_alarms:
            v_color[v] = 'gray'
        else:
            v_color[v] = 'white'

        typ = v_prop[v]['type']
        if typ == 'tuple':
            v_shape[v] = 'circle'
        else:
            v_shape[v] = 'square'

    g.vertex_properties['color'] = v_color
    g.vertex_properties['shape'] = v_shape


def draw(g, output):
    v_prop = g.vertex_properties['info']
    v_shape = g.vertex_properties['shape']
    v_color = g.vertex_properties['color']
    vprops = {'shape': v_shape}
    graphviz_draw(g, vcolor=v_color, vprops=vprops, size=(30,30),
                  overlap=False, output=output)

def print_node_id(g, output):
    v_prop = g.vertex_properties['info']

    with open(output, 'w') as f:
        for v in g.vertices():
            f.write('{}: {}\n'.format(v, v_prop[v]['label']))
