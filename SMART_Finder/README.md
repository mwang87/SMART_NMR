# SMART

This is the source code to do development for SMART. This code contains two distinct ways to interact with SMART:

1. SMART-Classic - This includes the embedding work with Henry Mao
1. SMART-FP - This fingerprint prediction work with Hyunwoo Kim

## Dependency Installation

1. install rdkit via conda
1. install tensorflow with pip
1. install matplotlib with pip

## Models

Models and Database files are expected to be in a very specific location. The database must be named:

```FPinder_DB.npy```

and the model files must be in 

```
models/HWK_sAug_1106_final(2048r1)_cos.hdf5
models/VGG16_high_aug_MW_continue.hdf5
```

These can be converted to tensorflow serving formats using:

https://towardsdatascience.com/deploying-keras-models-using-tensorflow-serving-and-flask-508ba00f1037

## Input Format Definition

The input file must be a tsv (tab separated) or csv (comma separated) with the following columns: 1H and 13C. 

## Examples

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