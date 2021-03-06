import requests
import os
import pandas as pd
import json
import glob
import urllib.parse

PRODUCTION_URL = os.environ.get("SERVER_URL", "https://smart.ucsd.edu")

def test_validation():
    validate_list = pd.read_csv("validation.csv").to_dict(orient="records")

    errors_list = []

    for validation_object in validate_list:
        if validation_object["validated"] != 1:
            continue

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

            expected_inchi_key = requests.get("https://gnps-structure.ucsd.edu/inchikey?smiles={}".format(urllib.parse.quote(validation_object["expectedmatch"]))).text
            expected_inchi_key = expected_inchi_key.split("-")[0]

            results_df = pd.read_csv(url)
            # Calculating inchi_keys
            result_list = results_df.to_dict(orient="records")

            for record in result_list:
                smiles = record["SMILES"]
                result_inchi_key = requests.get("https://gnps-structure.ucsd.edu/inchikey?smiles={}".format(urllib.parse.quote(smiles))).text
                result_inchi_key = result_inchi_key.split("-")[0]
                record["InChiKey"] = result_inchi_key
            results_df = pd.DataFrame(result_list)
            results_df = results_df[results_df["InChiKey"] == expected_inchi_key]

            if len(results_df) == 0:
                expected_name = validation_object["expectedname"]
                errors_list.append(f"{test_filename} could not find expected {expected_name} in set")

            #TODO: put expectation for score

    if len(errors_list) > 0:
        print("===================ERROR===================")
        print("\n".join(errors_list))
    else:
        print("Success!")
    
    assert(len(errors_list) == 0)

