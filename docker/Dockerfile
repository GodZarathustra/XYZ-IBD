FROM nvidia/cudagl:11.4.1-runtime-ubuntu20.04

ENV USER bproc
ENV HOME /home/$USER
ENV DEBIAN_FRONTEND noninteractive
RUN useradd -m $USER
RUN chown $USER:$USER $HOME
USER $USER
WORKDIR $HOME

# use tuna apt source
USER root
RUN cp /etc/apt/sources.list /etc/apt/sources.list.backup
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal main restricted universe multiverse" > /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates main restricted universe multiverse" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-backports main restricted universe multiverse" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security main restricted universe multiverse" >> /etc/apt/sources.list

# use tuna pypi source
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN apt-get install -y vim zsh git wget curl zip gosu
RUN apt-get install -y libxi6 libxrender1 libglib2.0-0 libfontconfig1-dev

USER $USER
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple some-package -U
RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# download & extract blender to /root/blender
RUN wget https://mirrors.tuna.tsinghua.edu.cn/blender/release/Blender3.3/blender-3.3.1-linux-x64.tar.xz
RUN mkdir -p $HOME/blender
RUN tar xvf blender-3.3.1-linux-x64.tar.xz && mv blender-3.3.1-linux-x64 $HOME/blender
RUN rm blender-3.3.1-linux-x64.tar.xz

# pip install
RUN pip3 install pillow==9.4.0 h5py==3.7.0 matplotlib==3.6.2 numpy==1.24.1 progressbar==2.5 requests==2.28.1 fonttools==4.38.0 packaging==23.0 cycler==0.11.0 kiwisolver==1.4.4 pyyaml==6.0 imageio==2.24.0 opencv-python==4.7.0.68 rich==13.0.1 omegaconf==2.3.0 pytz==2022.7 scipy==1.10.0 pypng==0.20220715.0 vispy==0.12.1 PyOpenGL==3.1.6 PyOpenGL_accelerate==3.1.6

# blender pip install
RUN $HOME/blender/blender-3.3.1-linux-x64/3.3/python/bin/python3.10 -m ensurepip
RUN $HOME/blender/blender-3.3.1-linux-x64/3.3/python/bin/python3.10 -m pip install --upgrade pip
RUN $HOME/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install wheel pyyaml==5.1.2 imageio==2.9.0 gitpython==3.1.18 scikit-image==0.19.2 pypng==0.0.20 scipy==1.7.3 matplotlib==3.5.1 pytz==2021.1 h5py==3.6.0 pillow==8.3.2 opencv-contrib-python==4.5.5.64 scikit-learn==1.0.2 python-dateutil==2.8.2 rich==12.6.0 loguru==0.6.0 omegaconf==2.3.0

# install blenderproc
COPY output/archive.tar.gz .
RUN mkdir BlenderProc && mv archive.tar.gz BlenderProc && cd BlenderProc && tar xvf archive.tar.gz
RUN cd BlenderProc && pip install .
RUN mkdir -p $HOME/.imageio/freeimage
RUN mv BlenderProc/resources/libfreeimage-3.16.0-linux64.so $HOME/.imageio/freeimage
ENV PATH="$HOME/.local/bin:$PATH"
RUN echo 'export PATH="$HOME/.local/bin:$PATH"' >> .bashrc

USER root

## # warm up
## RUN $HOME/.local/bin/blenderproc quickstart
## RUN rm -rf output
