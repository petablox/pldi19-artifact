#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# for camera ready
# plt.rc('text', usetex=True)

programs = [
    ("shntool", "benchmark/shntool-3.0.5/sparrow-out/taint"),
    ("latex2rtf", "benchmark/latex2rtf-2.1.1/sparrow-out/taint"),
    ("urjtag", "benchmark/urjtag-0.8/sparrow-out/taint"),
    ("optipng", "benchmark/optipng-0.5.3/sparrow-out/taint"),
    ("wget", "benchmark/wget-1.12/sparrow-out/interval"),
    ("grep", "benchmark/grep-2.19/sparrow-out/interval"),
    ("readelf", "benchmark/readelf-2.24/sparrow-out/interval"),
    ("sed", "benchmark/sed-4.3/sparrow-out/interval"),
    ("sort", "benchmark/sort-7.2/sparrow-out/interval"),
    ("tar", "benchmark/tar-1.28/sparrow-out/interval"),
]

tickfontsize = 15
markersize = 100

epsilons = [str(x) for x in [0.001, 0.005, 0.01, 0.05]] #, 0.1 ]

color = {
    '0.001': 'royalblue',
    '0.005': 'white',
    '0.01': 'white',
    '0.05': 'white',
    '0.1': 'white',
    '0.5': 'white'
}

ecolor = {
    '0.001': 'royalblue',
    '0.005': 'salmon',
    '0.01': 'forestgreen',
    '0.05': 'midnightblue',
    '0.1': 'salmon',
    '0.5': 'forestgreen',
}

hatch = {
    '0.001': None,
    '0.005': '//////',
    '0.01': None,
    '0.05': 'xxxxx',
    '0.1': '//////',
    '0.5': '.....',
}

marker = {
    '0.001': '.',
    '0.005': '+',
    '0.01': '*',
#    '0.05': 'x'
}

def figure1():
    ax.set_ylim(0, 100)
    xidx = 0
    for name, path in programs:
        alarm_file = path + '/bnet/Alarm.txt'
        total_alarms = sum(1 for line in open(alarm_file))
        i = 0
        for eps in epsilons:
            yidx = 0
            trues = []
            iteration_file = path + '/bingo_delta_sem-eps_strong_' + eps + '_stats.txt'
            for line in open(iteration_file):
                if 'TrueGround' in line:
                    trues.append(yidx * 100 / total_alarms)
                yidx += 1
            if xidx == 0:
                plt.scatter([xidx - 0.2 + 0.2 * i] * len(trues), trues, color=color[eps], marker=marker[eps], s=markersize, label=(r'$\epsilon =$' + eps))
            else:
                plt.scatter([xidx - 0.2 + 0.2 * i] * len(trues), trues, color=color[eps], marker=marker[eps], s=markersize)
            i += 1
        xidx += 1

def figure2():
    ax.set_ylim(0, 2)
    xidx = 0
    plt.plot([-0.2, 9.2], [1, 1], linestyle='--')
    plt.yticks([0,1,2])
    for name, path in programs:
        batch_file = path + '/bingo_stats.txt'
        batch_iters = sum(1 for line in open(batch_file)) - 1
        i = 0
        for eps in epsilons:
            yidx = 0
            trues = []
            iteration_file = path + '/bingo_delta_sem-eps_strong_' + eps + '_stats.txt'
            for line in open(iteration_file):
                if 'TrueGround' in line:
                    trues.append(yidx / batch_iters)
                yidx += 1
            if xidx == 0:
                plt.scatter([xidx - 0.2 + 0.2 * i] * len(trues), trues, color=color[eps], marker=marker[eps], s=markersize, label=(r'$\epsilon =$' + eps))
            else:
                plt.scatter([xidx - 0.2 + 0.2 * i] * len(trues), trues, color=color[eps], marker=marker[eps], s=markersize)
            i += 1
        xidx += 1

def figure3():
    fig, ax = plt.subplots()
    plt.xticks(range(0, 10), fontsize=tickfontsize, rotation=45)
    plt.yticks(fontsize=tickfontsize)
    ax.set_xticklabels([x for (x,y) in programs])
    ax.set_ylim(0, 2)
    xidx = 0
#    plt.plot([-0.3, 9.3], [1, 1], linestyle='--', color='royalblue', zorder=1)
    plt.yticks([0,1,2])
    trans = ax.get_xaxis_transform()
    bar_width=0.25
    for name, path in programs:
        base_file = path + '/bingo_delta_sem-eps_strong_0.001_stats.txt'
        base_iters = sum(1 for line in open(base_file)) - 1
        i = 0
        epsilons = [str(x) for x in [0.001, 0.005, 0.01]] #, 0.1 ]
        for eps in epsilons:
            yidx = 0
            trues = []
            iteration_file = path + '/bingo_delta_sem-eps_strong_' + eps + '_stats.txt'
            iters = sum(1 for line in open(iteration_file)) - 1
            if eps == "0.01":
                linewidth=1.4
            else:
                linewidth=1.4
            if xidx == 0:
                plt.bar(xidx + (i-1) * (bar_width + 0.03), iters / base_iters, bar_width, color=color[eps],
                        hatch=hatch[eps], edgecolor=ecolor[eps], zorder=2, linewidth=linewidth,
                        label=(r'$\epsilon =$' + eps))
            else:
                plt.bar(xidx + (i-1) * (bar_width + 0.03), iters / base_iters, bar_width, color=color[eps],
                        hatch=hatch[eps], edgecolor=ecolor[eps], zorder=2, linewidth=linewidth)
            if iters / base_iters > 2:
                if xidx == 5:
                    ax.annotate('{0:.1f}'.format(iters/base_iters), xy = (xidx + (i - 1.7) * (bar_width + 0.1), 1.01), size=8, xycoords=trans)
                elif xidx == 8 and eps == '0.005':
                    ax.annotate('{0:.1f}'.format(iters/base_iters), xy = (xidx + (i - 1.6) * (bar_width + 0.1), 1.01), size=8, xycoords=trans)
                else:
                    ax.annotate('{0:.1f}'.format(iters/base_iters), xy = (xidx + (i - 1.5) * (bar_width + 0.1), 1.01), size=8, xycoords=trans)
            i += 1
        xidx += 1
    plt.legend(fontsize=tickfontsize)
    plt.tight_layout()
    plt.savefig("sensitivity-last.pdf")

figure3()
