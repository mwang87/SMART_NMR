# SMART

This is the source code to do development for SMART. This code contains two distinct ways to interact with SMART:

1. SMART3.0 - This fingerprint, molecular weight, and class prediction work with Hyunwoo Kim

## Dependency Installation

1. install rdkit via conda
1. install tensorflow with pip
1. install matplotlib with pip

## Models

Models and Database files are expected to be in a very specific location. The database must be named:

```DB_010621_SM3.json```
but the 'date' can be changed if the DB is updated.

and the model files must be in 

```
models/(011721)SMART3_v3_1ch_RC.hdf5
models/(011721)SMART3_v3_2ch_RC.hdf5
models/(011621)SMART3_v3_1ch_class_g.hdf5
models/(011621)SMART3_v3_2ch_class_g.hdf5
```

These can be converted to tensorflow serving formats using:

https://towardsdatascience.com/deploying-keras-models-using-tensorflow-serving-and-flask-508ba00f1037

## Input Format Definition

The input file must be a tsv (tab separated), csv (comma separated), or xlsx (not recommend) with the following columns: 1H, 13C, and Intensity(optional, edited HSQC).
If you want to submit edited HSQC data, the 'Intensity' column should be presence in the input file 

## Examples
Exmaples are in 'inputs' folder.
The expected outputs are in 'outputs' folder.

We use docker to encapsule running the examples

```python ./SMART_FPinder.py input/cyclomarin_A_fenical_input.csv ./test.tsv ./test_nmr.png ./test_structures.png```

## Testing

To run all the tests, go to the test folder and type

```nose2 -v```

## Webserver

The webserver architecture has the following components:

1. Primary web end point
1. Tensorflow serve for SMART FP Models
1. redis for celery task management
1. celery worker to perform SMART-Classic Inference
