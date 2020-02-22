import requests
import os
import pandas as pd
import json
import glob

PRODUCTION_URL = os.environ.get("SERVER_URL", "https://smart.ucsd.edu")

def test_validation():
    validate_list = pd.read_csv("validation.csv").to_dict(orient="records")

    errors_list = []

    for validation_object in validate_list:
        print(validation_object)
        test_filename = os.path.join("Data", validation_object["filename"])
        if os.path.isfile(test_filename):
            #Lets do things!
            url = f"{PRODUCTION_URL}/analyzeuploadclassic"
            files = {'file': open(test_filename, encoding='ascii', errors='ignore').read()}
            r = requests.post(url, files=files)
            r.raise_for_status()

            task = r.json()["task"]
            url = f"{PRODUCTION_URL}/resultclassictable?task={task}"

            results_df = pd.read_csv(url)
            results_df = results_df[results_df["SMILES"] == validation_object["expectedmatch"]]

            if len(results_df) == 0:
                expected_name = validation_object["expectedname"]
                errors_list.append(f"{test_filename} could not find expected {expected_name} in set")

            #TODO: put expectation for score

    print("\n".join(errors_list))
        
    assert(len(errors_list) == 0)
