# FPinder

This is the source code to do development for FPinder. 

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

## Input Format Definition

The input file must be a tsv (tab separated) or csv (comma separated) with the following columns: 1H and 13C. 

## Examples

We use docker to encapsule running the examples

```python ./SMART_FPinder.py input/cyclomarin_A_fenical_input.csv ./test.tsv ./test_nmr.png ./test_structures.png```

## Testing

To run all the tests, go to the test folder and type

```nose2 -v```