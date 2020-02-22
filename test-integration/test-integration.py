import requests
import os
import pandas as pd
import json
import glob

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

    test_files = glob.glob("Data/*")

    for test_file in test_files:
        if "topspin" in test_file:
            continue
        print(test_file)
        PARAMS = {'peaks': open(test_file, encoding='ascii', errors='ignore').read()} 
        r = requests.post(url, params=PARAMS)
        r.raise_for_status()

        task = r.json()["task"]
        r = requests.get(f"{PRODUCTION_URL}/embedding_json_classic/{task}")
        r.raise_for_status()
        r = requests.get(f"{PRODUCTION_URL}/embedding_metadata_classic/{task}")
        r.raise_for_status()
        r = requests.get(f"{PRODUCTION_URL}/embedding_data_classic/{task}")
        r.raise_for_status()

def test_upload():
    url = f"{PRODUCTION_URL}/analyzeuploadclassic"

    test_files = glob.glob("Data/*")

    for test_file in test_files:
        print(test_file)
        files = {'file': open(test_file, encoding='ascii', errors='ignore').read()}
        r = requests.post(url, files=files)
        r.raise_for_status()

        task = r.json()["task"]
        r = requests.get(f"{PRODUCTION_URL}/embedding_json_classic/{task}")
        r.raise_for_status()
        r = requests.get(f"{PRODUCTION_URL}/embedding_metadata_classic/{task}")
        r.raise_for_status()
        r = requests.get(f"{PRODUCTION_URL}/embedding_data_classic/{task}")
        r.raise_for_status()

def test_api():
    test_files = glob.glob("Data/*")

    for test_file in test_files:
        if "topspin" in test_file:
            continue
        print(test_file)

        df = pd.read_csv(test_file, sep=",")
        peaks_json = df.to_dict(orient="records")
        r = requests.post(f"{PRODUCTION_URL}/api/classic/embed", data={"peaks":json.dumps(peaks_json)})
        r.raise_for_status()


