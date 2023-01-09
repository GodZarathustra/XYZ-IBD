FROM nvidia/cudagl:11.4.1-runtime-ubuntu20.04

ENV USER=root
WORKDIR /workspace

RUN apt-get update

RUN apt-get install -y python3 python3-pip
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN apt-get install -y zsh git curl vim zip
RUN apt-get install -y libxi6 libxrender1
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y libglib2.0-0

RUN apt-get install -y wget
RUN wget https://download.blender.org/release/Blender3.3/blender-3.3.1-linux-x64.tar.xz
RUN mkdir -p /root/blender
RUN tar xvf blender-3.3.1-linux-x64.tar.xz && mv blender-3.3.1-linux-x64 /root/blender
RUN rm blender-3.3.1-linux-x64.tar.xz

COPY output/archive.tar.gz .
RUN mkdir BlenderProc && mv archive.tar.gz BlenderProc && cd BlenderProc && tar xvf archive.tar.gz
RUN cd BlenderProc && pip install -e .
RUN blenderproc quickstart
RUN rm -rf output

