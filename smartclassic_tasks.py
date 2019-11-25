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
sys.path.insert(0, "SMART_Classic")
sys.path.insert(0, "SMART_Classic/SMART")
import SMART_Classic

celery_instance = Celery('smart_classic_tasks', backend='redis://smartclassic-redis', broker='redis://smartclassic-redis')

shared_model_data = {}

def worker_load_models(**kwargs):
    import cli
    from model import SMARTModel
    import torch

    print('Loading model...', file=sys.stderr)
    try:
        with torch.no_grad():
            model = SMARTModel()
            model.load_state_dict(torch.load("/src/SMART_Classic/model/model.pt", map_location="cpu"))  
            model.eval()
            print('# params:', sum(p.numel() for p in model.parameters()), file=sys.stderr)
            print('Loading data...', file=sys.stderr)
    except Exception as e: 
        print("EROOOOOOOOOOORRRRRRRRRRRRRR", e, file=sys.stderr)
        raise

    shared_model_data["model"] = model

    # print("LOADING DATABASE", file=sys.stderr)

    # #Loading the Model Globally
    # DB = SMART_FPinder.load_db(db_folder="/SMART_Finder")
    
    # #Creating the dataframes
    # metadata_df = pd.read_csv("/SMART_Finder/projection/smart_metadata.tsv", sep="\t", names=["compound"], encoding="ISO-8859–1")
    # database_df = pd.DataFrame(DB, columns=["compound", "smiles", "embedding", "mw"])

    # shared_model_data["DB"] = DB
    # shared_model_data["metadata_df"] = metadata_df
    # shared_model_data["database_df"] = database_df

    return 0

@celery_instance.task()
def smart_classic_run(input_filename):
    import requests
    import numpy as np
    import cli
    from model import SMARTModel
    import torch

    start_time = time.time()
    print("PROCESSING", file=sys.stderr)

    SMART_Classic.HSQCtoNPY(input_filename, "test.npy")
    hsqc = np.load("test.npy")
    model = shared_model_data["model"]
    with torch.no_grad():
        cli.predict_embedding(model, hsqc, "test_output.npy", filetype="tsv")

    return 0

# Load the database when the worker starts
worker_init.connect(worker_load_models)
