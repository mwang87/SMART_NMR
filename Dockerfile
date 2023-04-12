FROM continuumio/miniconda3:4.10.3
MAINTAINER Mingxun Wang "mwang87@gmail.com"

RUN apt-get update && apt-get install -y build-essential procps
RUN conda install -c conda-forge mamba

RUN mamba create -n rdkit -c rdkit rdkit=2020.03.3.0

WORKDIR /app
COPY requirements.txt /app
RUN /bin/bash -c "source activate rdkit && pip install -r /app/requirements.txt"

COPY . /app
