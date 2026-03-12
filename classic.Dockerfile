FROM ubuntu:22.04
MAINTAINER Mingxun Wang "mwang87@gmail.com"

RUN apt-get update && apt-get install -y build-essential libarchive-dev wget vim libgl1-mesa-glx libglib2.0-0

# Install Mamba
ENV CONDA_DIR /opt/conda
RUN wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh && /bin/bash ~/miniforge.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Adding to bashrc
RUN echo "export PATH=$CONDA_DIR:$PATH" >> ~/.bashrc

# Forcing version of Python with pytorch
RUN mamba create -n smartclassic python=3.10 pytorch torchvision cpuonly -c pytorch -c conda-forge -y

COPY requirements-worker.txt /src/requirements-worker.txt
RUN /bin/bash -c 'source activate smartclassic && pip install -r /src/requirements-worker.txt'

ADD . /src

WORKDIR /src

ENTRYPOINT []
