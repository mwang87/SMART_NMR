# FPinder

This is the source code to do development for FPinder. 

## Dependency Installation

1. install rdkit via conda
1. install tensorflow with pip
1. install matplotlib with pip

## Input Format Definition

The input file must be a csv (comma separated) with the following columns: 1H and 13C. 

## Examples

We use docker to encapsule running the examples

```python ./SMART_FPinder.py input/cyclomarin_A_fenical_input.csv ./test.tsv ./test_nmr.png ./test_structures.png```