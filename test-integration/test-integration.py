import requests
import os
import pandas as pd
import json

PRODUCTION_URL = os.environ.get("SERVER_URL", "https://smart.ucsd.edu")

def test_heartbeat():
    r = requests.get(f"{PRODUCTION_URL}/heartbeat")
    r.raise_for_status()

def test_moliverse():
    r = requests.get(f"{PRODUCTION_URL}/embedding_json_classic_global")
    r.raise_for_status()

    r = requests.get(f"{PRODUCTION_URL}/embedding_data_classic_global")
    r.raise_for_status()

    r = requests.get(f"{PRODUCTION_URL}/embedding_metadata_classic_global")
    r.raise_for_status()

def test_entry():
    url = f"{PRODUCTION_URL}/analyzeentryclassic"
    PARAMS = {'peaks': open("Data/CDCl3_SwinholideA.csv").read()} 
    requests.post(url, params=PARAMS)

    PARAMS = {'peaks': open("Data/cyclomarin_A_duggan2_input.csv").read()} 
    requests.post(url, params=PARAMS)

    PARAMS = {'peaks': open("Data/cyclomarin_A_duggan_tsv.txt").read()} 
    requests.post(url, params=PARAMS)

    PARAMS = {'peaks': open("Data/cyclomarin_A_fenical_semicolon.csv").read()} 
    requests.post(url, params=PARAMS)

    PARAMS = {'peaks': open("Data/cyclomarin_A_fenical_tsv.txt").read()} 
    requests.post(url, params=PARAMS)

def test_api():
    df = pd.read_csv("Data/CDCl3_SwinholideA.csv", sep=",")
    peaks_json = df.to_dict(orient="records")
    r = requests.post(f"{PRODUCTION_URL}/api/classic/embed", data={"peaks":json.dumps(peaks_json)})
    r.raise_for_status()

