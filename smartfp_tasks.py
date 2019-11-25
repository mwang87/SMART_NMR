from celery import Celery
from celery.signals import worker_init

import time
import os
import json
import requests
import glob
import pandas as pd
import matplotlib.pyplot as plt

#SMART import
import sys
sys.path.insert(0, "SMART_Finder")
import SMART_FPinder

celery_instance = Celery('smart_fp_tasks', backend='redis://smart-redis', broker='redis://smart-redis')

shared_model_data = {}

def worker_load_models(**kwargs):
    print("LOADING DATABASE", file=sys.stderr)

    #Loading the Model Globally
    DB = SMART_FPinder.load_db(db_folder="/SMART_Finder")
    
    #Creating the dataframes
    metadata_df = pd.read_csv("/SMART_Finder/projection/smart_metadata.tsv", sep="\t", names=["compound"], encoding="ISO-8859–1")
    database_df = pd.DataFrame(DB, columns=["compound", "smiles", "embedding", "mw"])

    shared_model_data["DB"] = DB
    shared_model_data["metadata_df"] = metadata_df
    shared_model_data["database_df"] = database_df

    return 0

@celery_instance.task()
def smart_fp_run(input_filename, output_result_table, output_result_nmr_image, output_result_fp_pred, mw):
    import requests
    import numpy as np

    start_time = time.time()
    print("PROCESSING", file=sys.stderr)

    mat = SMART_FPinder.CSV_converter(input_filename)

    # plotting and saving constructed HSQC images
    ## image without padding and margin
    height, width = mat.shape
    figsize = (10, 10*height/width) if height>=width else (width/height, 1)
    plt.figure(figsize=figsize)
    plt.imshow(mat, cmap=plt.cm.binary)
    plt.axis('off'), plt.xticks([]), plt.yticks([])
    plt.tight_layout()
    plt.subplots_adjust(left = 0, bottom = 0, right = 1, top = 1, hspace = 0, wspace = 0)
    plt.savefig(output_result_nmr_image, dpi=600)
    plt.close()

    # Tensorflow Serve fp query
    fp_pred_url = "http://smartfp-tf-server:8501/v1/models/HWK_sAug_1106_final_2048_cos:predict"
    payload = json.dumps({"instances": mat.reshape(1,200,240,1).tolist()})
    
    headers = {"content-type": "application/json"}
    json_response = requests.post(fp_pred_url, data=payload, headers=headers)

    fingerprint_prediction = np.asarray(json.loads(json_response.text)['predictions'])
    fingerprint_prediction_nonzero = np.where(fingerprint_prediction.round()[0]==1)[0]

    # Tensorflow Serve fp mw query
    fp_pred_url = "http://smartfp-mw-tf-server:8501/v1/models/VGG16_high_aug_MW_continue:predict"
    payload = json.dumps({"instances": mat.reshape(1,200,240,1).tolist()})
    
    headers = {"content-type": "application/json"}
    json_response = requests.post(fp_pred_url, data=payload, headers=headers)

    pred_MW = json.loads(json_response.text)['predictions'][0][0]

    print("FINISHED PREDICTION", time.time() - start_time, file=sys.stderr)

    DB = shared_model_data["DB"]
    topK = SMART_FPinder.search_database(fingerprint_prediction, fingerprint_prediction_nonzero, pred_MW, DB, mw=mw, top_candidates=20)
    topK.to_csv(output_result_table, index=None)

    print("FINISHED DB SEARCH", time.time() - start_time, file=sys.stderr)

    open(output_result_fp_pred, "w").write(json.dumps(fingerprint_prediction.tolist()))

    return 0

# Load the database when the worker starts
worker_init.connect(worker_load_models)
