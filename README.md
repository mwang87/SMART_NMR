# SMART_NMR

Repository to help develop SMART 

![production-integration](https://github.com/mwang87/SMART_NMR/workflows/production-integration/badge.svg)
![unittest](https://github.com/mwang87/SMART_NMR/workflows/unittest/badge.svg)


## Test Server URL

https://smart.ucsd.edu/

## Database Format

The format of the database is a json file, that is a list of records. The following headers are included. 

1. Compound_name - Compound Name
1. Embeddings - 180 dimension embedding
1. SMILES - SMILES Structure
1. MW - exact mass
1. From - indicates the database

## Running Unit Tests

Although unit tests are automatically run with github actions, to run them yourself, go to test folder and run

```
nose2 -v
```
