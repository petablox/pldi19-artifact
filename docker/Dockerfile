FROM ubuntu:18.04
MAINTAINER Kihong Heo <kheo@cis.upenn.edu>

RUN apt-get update && \
      apt-get install -y software-properties-common && \
      apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 379CE192D401AB61 && \
      add-apt-repository https://dl.bintray.com/souffle-lang/deb-unstable/ && \
      add-apt-repository ppa:avsm/ppa && \
      apt-get update && \
      apt-get install -y git ant souffle make sudo curl unzip libboost-dev
RUN curl -sL https://github.com/ocaml/opam/releases/download/2.0.2/opam-2.0.2-x86_64-linux > /usr/bin/opam && \
          chmod +x /usr/bin/opam
RUN opam init --reinit --bare --disable-sandboxing
RUN cd / && git clone https://github.com/petablox-project/pldi19-artifact.git
RUN cd /pldi19-artifact && ./build.sh
