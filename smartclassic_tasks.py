from celery import Celery
from celery.signals import worker_init

import time
import os
import json
import requests
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#SMART import
import sys
sys.path.insert(0, "SMART_Classic")
sys.path.insert(0, "SMART_Classic/SMART")
import smart_utils

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


    try:
        #Loading the database
        db = np.load("/src/SMART_Classic/DB.npy", allow_pickle=True)
    except Exception as e: 
        print("EROOOOOOOOOOORRRRRRRRRRRRRR", e, file=sys.stderr)
        raise
    
    shared_model_data["database"] = db
    shared_model_data["model"] = model

    return 0

@celery_instance.task()
def smart_classic_run(input_filename, output_result_table, output_result_nmr_image):
    import requests
    import numpy as np
    import cli
    from model import SMARTModel
    import torch

    start_time = time.time()
    print("PROCESSING", file=sys.stderr)

    #Saving image
    smart_utils.draw_nmr(input_filename, output_result_nmr_image)

    hsqc = smart_utils.hsqc_to_np(input_filename)
    model = shared_model_data["model"]
    db = shared_model_data["database"]
    with torch.no_grad():
        #Predict Embedding
        embedding = cli.predict_embedding(model, hsqc)

        #Performing DB Search
        search_results_df = cli.search_database(db, embedding)

    #Save all results
    search_results_df.to_csv(output_result_table, index=None)

    return 0


@celery_instance.task()
def smart_classic_size(query_embedding_filename):
    db = shared_model_data["database"]

    return len(db)

@celery_instance.task()
def smart_classic_embedding(query_embedding_filename):
    db = shared_model_data["database"]
    
    output_list = ['\t'.join(map(str, entry[1])) + "\t" + entry[0] for entry in db if len(entry[0]) > 5 and len(entry[1]) > 100]

    print(len(output_list), file=sys.stderr)

    return "\n".join(output_list)

@celery_instance.task()
def smart_classic_metadata(query_embedding_filename):
    db = shared_model_data["database"]
    
    output_list = [entry[0] for entry in db if len(entry[0]) > 5 and len(entry[1]) > 100]

    print(len(output_list), file=sys.stderr)

    return "\n".join(output_list)

# Load the database when the worker starts
worker_init.connect(worker_load_models)
