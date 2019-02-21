# Drake PLDI'19 Artifact
This directory contains the artifact of the paper "Continuous Program Reasoning
via Differential Bayesian Inference" published in PLDI 2019. The latest version
of the paper is available 
[here](https://www.cis.upenn.edu/~kheo/paper/pldi19.pdf).

## Getting Started
We provide the artifact as a [Docker](https://www.docker.com) image via this [link](https://drive.google.com/open?id=14Ma91b3PF-tcFsYlHOHl3w5EigyNsgNY).
All binaries have already built in the image. After downloading the image file, You can load and start the image with the following command:
```
$ docker load --input drake-artifact.tar
$ docker run -it --name drake drake
```
The artifact is in the `pldi19-artifact/` directory. Users should begin by setting up environment variables with the following command:
```
$ cd pldi19-artifact
$ . setenv
```

The artifact is organized as follows:
```
benchmark/ # benchmark source code and meta information (syntactic matching information and bug locations)
bingo/     # bayesian inference engine
datalog/   # datalog programs to extract derivation graphs
delta/     # shell scripts to run continuous reasoning
script/    # auxiliary scripts
sparrow/   # the Sparrow static analyzer
result/    # log files of the experimental results
```
Directory `benchmark` contains subdirectories for two versions of programs. In each subdirectory,
analysis results are stored in `sparrow-out`

Note that some of the experiments are very time and memory consuming. We highly recommend that the users run the experiments with at least 16GB of memory.
We also provide our results on a Linux machine with Intel Xeon Gold 6154 3GHz cpu and 40GB of memory in `result/` for reference.
The running time for each benchmark is reported in `result/runningtime.txt`.
Users can also generate summary tables from the existing log files with the following command:
```
$ script/table.sh
```
Note that rankings by Bayesian inference (Columns Init, Feedback, and #Iters) may be slightly
different from the paper because of the underlying nondeterminism of our implementation (e.g., Python's set library).

We tested the Docker image on Linux (Ubuntu) and Mac with the latest version of Docker.
Docker on other distributions of Linux (e.g., Fedora) may have permission issues with SELinux.
Please consult your documentation to disable SELinux.
Note that Docker for Mac is set to use 2GB of memory by default.
The users should increase memory limit following the [instruction](https://docs.docker.com/docker-for-mac/).

## To Run Drake on a Single Benchmark
Here is an example to run Drake on a single benchmark. Users can run Drake with different benchmarks and analyses in a similar way.
An analysis is either `interval` (for buffer overrun) or `taint` (for integer overflow and format string).
The characteristics of programs are described in Table 1.

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

The file N.out gives the ranking of alarms produced by our Bayesian inference system after N feedback.
The columns have the following meaning:
- Column 1: Rank of the alarm
- Column 2: The confidence score
- Column 3: The ground truth about the alarm: whether it is true or false.
- Column 4: “Unlabelled” if the alarm has not been labelled by the user, “PosLabel”
(“NegLabel”) if the user labels it true (false).
- Column 5: Debug message
- Column 6: The alarm itself

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
The following command will run continuous-mode program analysis on two versions of the benchmarks.
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
