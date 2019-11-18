#FROM tensorflow/tensorflow
FROM continuumio/miniconda3:latest

WORKDIR /app

RUN conda create -n rdkit -c rdkit rdkit
COPY requirements.txt /app
RUN /bin/bash -c "source activate rdkit && pip install -r /app/requirements.txt"
