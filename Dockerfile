#FROM tensorflow/tensorflow
FROM continuumio/miniconda3:4.7.12

WORKDIR /app

RUN conda create -n rdkit -c rdkit rdkit=2020.03.3.0
COPY requirements.txt /app
RUN /bin/bash -c "source activate rdkit && pip install -r /app/requirements.txt"
RUN apt-get update
RUN apt-get install procps -y

COPY . /app