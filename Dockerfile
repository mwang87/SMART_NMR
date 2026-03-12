FROM ubuntu:22.04
MAINTAINER Mingxun Wang "mwang87@gmail.com"

RUN apt-get update && apt-get install -y build-essential libarchive-dev wget vim procps

# Install Mamba
ENV CONDA_DIR /opt/conda
RUN wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh && /bin/bash ~/miniforge.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Adding to bashrc
RUN echo "export PATH=$CONDA_DIR:$PATH" >> ~/.bashrc

# Forcing version of Python with rdkit
RUN mamba create -n rdkit python=3.10 -c conda-forge rdkit -y

WORKDIR /app
COPY requirements.txt /app
RUN /bin/bash -c 'source activate rdkit && pip install -r /app/requirements.txt'

COPY . /app
