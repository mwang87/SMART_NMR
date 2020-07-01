# SMART NMR Server

Repository to help develop SMART 

![production-integration](https://github.com/mwang87/SMART_NMR/workflows/production-integration/badge.svg)
![unittest](https://github.com/mwang87/SMART_NMR/workflows/unittest/badge.svg)


## Production Server 

https://smart.ucsd.edu/

## URL Deep Integration

If you want to link to SMART and prepopulate a query from your software, you simply have to encode the string in the URL hash, for example:

https://smart.ucsd.edu/classic#1H%2C13C%0A5.79%2C113.2%0A7.58%2C153.3%0A1.88%2C12.3%0A6.08%2C142.2%0A2.46%2C37.4%0A2.18%2C37.4%0A4.14%2C66.6%0A1.58%2C40.8%0A1.73%2C40.8%0A4.51%2C65.7%0A5.69%2C129.8%0A5.78%2C123.2%0A1.82%2C29.9%0A2.27%2C29.9%0A3.86%2C65.8%0A1.46%2C33.8%0A2.14%2C33.8%0A4.01%2C75.1%0A3.35%2C57.4%0A1.68%2C41%0A0.81%2C9.4%0A3.83%2C73.8%0A1.62%2C38.4%0A3.98%2C71.3%0A1.75%2C41.3%0A0.97%2C9.2%0A5.36%2C74.3%0A1.95%2C37.6%0A0.84%2C9.1%0A3.12%2C76%0A1.65%2C33.2%0A0.99%2C17.7%0A1.27%2C23.9%0A1.38%2C23.9%0A1.3%2C29.3%0A1.9%2C29.3%0A4.02%2C71.4%0A1.6%2C34.8%0A1.82%2C34.8%0A3.53%2C73.2%0A3.33%2C55.2%0A1.18%2C38.8%0A1.96%2C38.8%0A3.69%2C64.5%0A1.2%2C21.7

## Database Format

The format of the database is a json file, that is a list of records. The following headers are included. 

1. Compound_name - Compound Name
1. Embeddings - 180 dimension embedding
1. SMILES - SMILES Structure
1. MW - exact mass
1. From - indicates the database
1. ID - unique identifier to give the database a pseudo accession. These can be integers or simply uuids, but they must be unique per entry and must not be NULL. 
1. External_link - external link for compounds. JEOL and Pubchem links are included.
1. GNPS_ID - GNPS ID for the compound which is from GNPS DB

## Running Unit Tests

Although unit tests are automatically run with github actions, to run them yourself, go to test folder and run

```
nose2 -v
```
