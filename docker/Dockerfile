FROM nvidia/cudagl:11.4.1-runtime-ubuntu20.04

WORKDIR /workspace

ENV USER=root
ENV DEBIAN_FRONTEND=noninteractive

# use tuna apt source
RUN cp /etc/apt/sources.list /etc/apt/sources.list.backup
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal main restricted universe multiverse" > /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates main restricted universe multiverse" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-backports main restricted universe multiverse" >> /etc/apt/sources.list
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security main restricted universe multiverse" >> /etc/apt/sources.list
RUN apt-get update

# use tuna python source
RUN apt-get install -y python3
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN apt-get install -y python3-pip
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple some-package -U
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

RUN apt-get install -y vim zsh git wget curl zip
RUN apt-get install -y libxi6
RUN apt-get install -y libxrender1
RUN apt-get install -y libglib2.0-0

# download & extract blender to /root/blender
RUN wget https://mirrors.tuna.tsinghua.edu.cn/blender/release/Blender3.3/blender-3.3.1-linux-x64.tar.xz
RUN mkdir -p /root/blender
RUN tar xvf blender-3.3.1-linux-x64.tar.xz && mv blender-3.3.1-linux-x64 /root/blender
RUN rm blender-3.3.1-linux-x64.tar.xz

# pip installs
RUN pip3 install pillow
RUN pip3 install h5py
RUN pip3 install matplotlib
RUN pip3 install numpy
RUN pip3 install progressbar
RUN pip3 install requests
RUN pip3 install fonttools
RUN pip3 install packaging
RUN pip3 install cycler
RUN pip3 install kiwisolver
RUN pip3 install pyyaml

# blender pip install
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/python3.10 -m ensurepip
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/python3.10 -m pip install --upgrade pip
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install wheel
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install pyyaml==5.1.2
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install imageio==2.9.0
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install gitpython==3.1.18
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install scikit-image==0.19.2
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install pypng==0.0.20
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install scipy==1.7.3
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install matplotlib==3.5.1
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install pytz==2021.1
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install h5py==3.6.0
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install pillow==8.3.2
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install opencv-contrib-python==4.5.5.64
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install scikit-learn==1.0.2
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install python-dateutil==2.8.2
RUN /root/blender/blender-3.3.1-linux-x64/3.3/python/bin/pip3 install rich==12.6.0

# install blenderproc
COPY output/archive.tar.gz .
RUN mkdir BlenderProc && mv archive.tar.gz BlenderProc && cd BlenderProc && tar xvf archive.tar.gz
RUN cd BlenderProc && pip install .
RUN rm -rf BlenderProc

# run once to speed up
RUN blenderproc quickstart
RUN rm -rf output

