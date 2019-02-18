# Drake PLDI'19 Artifact
This directory contains the artifact of the paper "Continuous Program Reasoning
via Differential Bayesian Inference" published in PLDI 2019. The latest version
of the paper is available via
[here](https://www.cis.upenn.edu/~kheo/paper/pldi19.pdf).

## Getting Started
We provide the artifact as a Docker image via this [link]().
All binaries have already built in the image.

```
$ docker load --input drake-artifact.tar
$ docker run -it --name drake drake
```
The artifact is in the `pldi19-artifact/`. Users should begin by setting up environment variables with the following command:
```
$ cd pldi19-artifact
$ . setenv
```

The artifact is organized as follows:
```
benchmark/ # benchmark source code and meta information (syntactic maching information and bug locations)
bingo/     # bayesian inference engine
datalog/   # datalog programs to extract derivation graphs
delta/     # shell scripts to run continuous reasoning
script/    # auxiliary scripts
sparrow/   # the Sparrow static analyzer
result/    # log files of the experimental results
```
Directory `benchmark` contains subdirectories for two versions of programs. In each subdirectory,
analysis results are stored in `sparrow-out`

Note that some of the experiments are very time consuming. We provide our results
on a Linux machine with Intel Xeon Gold 6154 3GHz cpu and 40GB of memory in `result/` for reference.
The running time for each benchmark is reported in `result/runningtime.txt`.
Users can also generate summary tables from the existing log files with the following command:
```
$ script/table.sh
```
Note that rankings by Bayesian inference (Columns Init, Feedback, and #Iters) may be slightly
different from the paper because of the underlying nondeterminism of our implementation (e.g., Python's set library).

## To Run Drake on a Single Benchmark
Here is an example to run Drake on a single benchmark. Users can run Drake with different benchmarks and analyses in a similar way.
An analysis is either `interval` (for buffer overrun) or `taint` (for integer overflow and format string).
The characteristics of programs is described in Table 1.

### Batch-mode analysis and Bingo
The following commands run Sparrow's taint analysis on two versions of `shntool`.
```
# run Sparrow on the old version
$ ./run.sh benchmark/shntool-3.0.4/shntool-3.0.4.c taint
# run Sparrow on the new version and apply Bingo
$ ./run.sh benchmark/shntool-3.0.5/shntool-3.0.5.c taint
```
### Syntactic masking and Drake-Unsound
Once you get the results from the first step, run the following command:
```
$ ./delta.sh benchmark/shntool-3.0.4 benchmark/shntool-3.0.5 taint unsound
```
Log files `benchmark/shntool-3.0.5/sparrow-out/taint/bingo_delta_syn_strong_combined/init.out`
and `benchmark/shntool-3.0.5/sparrow-out/taint/bingo_delta_syn_strong_combined/0.out`
show the rankings after initialization (Column "Initial") and feedback transfer (Column "Feedback"), respectively.

### Drake-Sound
To reproduce the results from Drake-Sound with epsilon 0.001, run the following command:
```
$ ./delta.sh benchmark/shntool-3.0.4 benchmark/shntool-3.0.5 taint sound 0.001
```
Log files `benchmark/shntool-3.0.5/sparrow-out/taint/bingo_delta_sem-eps_strong_0.001_combined/init.out`
and `benchmark/shntool-3.0.5/sparrow-out/taint/bingo_delta_sem-eps_strong_0.001_combined/0.out`
show the rankings after initialization (Column "Initial") and feedback transfer (Column "Feedback").

## To Reproduce All the Paper Results

### Running batch-mode program analysis and Bingo (Columns "Batch" and "Bingo" of Table 2)
The following command will run batch-mode program analysis on two versions of the benchmarks
and run Bingo on the new versions.
```
$ ./run_all.sh
```
The results will be stored in `result/<program>.batch.log`.

### Running unsound continuous program reasoning (Columns "SynMask" and "Drake-Unsound" of Table 2)
The following command will run continous-mode program analysis on two versions of the benchmarks.
```
$ ./delta_all.sh unsound
```
The results will be stored in `result/<new-version-program>.delta.unsound.log`. For each log file, `Total alarms`
reports the number of alarms after syntactic masking (Column "Diff") and "Last true alarm"
reports the number of iterations within which all bugs in each benchmark were discovered (Column "#Iters").
Log files
`benchmark/<new-version-program>/sparrow-out/<analysis>/bingo_delta_syn_strong_combined/init.out` and
`benchmark/<new-version-program>/sparrow-out/<analysis>/bingo_delta_syn_strong_combined/0.out` show
the rankings after initialization (Column "Initial") and feedback transfer (Column "Feedback"). `<analysis>`
is either `interval` or `taint` depending on the benchmark (Section 5.1 in the paper).
We report the last rankings of true alarms in the table.

### Running sound continuous program reasoning (Columns "Drake-Sound" of Table 2)
```
$ ./delta_all.sh sound 0.001
```
The results will be stored in `result/<new-version-program>.delta.sound.0.001.log`.
For each log file, `Total alarms`
reports the total number of alarms from the analysis and "Last true alarm"
reports the number of iterations within which all bugs in each benchmark were discovered (Column "#Iters").
Log files
`benchmark/<new-version-program>/sparrow-out/<analysis>/bingo_delta_sem-eps_strong_0.001_combined/init.out` and
`benchmark/<new-version-program>/sparrow-out/<analysis>/bingo_delta_sem-eps_strong_0.001_combined/0.out` show
the rankings after initialization (Column "Initial") and feedback transfer (Column "Feedback").

### Running sound continuous program reasoning with different parameters (i.e., epsilon) (Figure 7)
```
$ ./delta_all.sh sound [0.001 | 0.005 | 0.01]
```
`<eps>` is one of 0.001, 0.005, and 0.01 in our experiments.

### Comparing sizes of Bayesian networks (Table 3)
```
$ script/bnetsize.sh
```