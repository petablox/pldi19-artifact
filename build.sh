#!/bin/bash

set -e

echo "Build Sparrow"
git clone https://github.com/KihongHeo/sparrow.git
pushd sparrow
git checkout pldi19
./build.sh
popd

echo "Build Nichrome"
git clone --recurse-submodules https://github.com/nichrome-project/nichrome.git
pushd nichrome/main
ant
pushd libsrc
cp libdai/Makefile.LINUX libdai/Makefile.conf
make -j
popd
popd

echo "Build Bingo"
pushd bingo/prune-cons
make
popd

echo "Build Souffle"
sudo apt-add-repository https://dl.bintray.com/souffle-lang/deb-unstable
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 379CE192D401AB61
sudo apt-get update
sudo apt-get install souffle
