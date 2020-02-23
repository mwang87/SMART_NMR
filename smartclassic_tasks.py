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

celery_instance = Celery('smart_classic_tasks', backend='redis://smartclassic-redis', broker='pyamqp://smartclassic-rabbitmq')

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
        db = json.loads(open("/src/SMART_Classic/DB.json").read())
    except Exception as e: 
        print("EROOOOOOOOOOORRRRRRRRRRRRRR", e, file=sys.stderr)
        raise
    
    shared_model_data["database"] = db
    shared_model_data["model"] = model

    return 0

@celery_instance.task()
def smart_classic_run(input_filename, output_result_table, output_result_nmr_image, output_result_embed, nmr_display="SMART 2.0 Query", perform_db_search=True):
    import requests
    import numpy as np
    import cli
    from model import SMARTModel
    import torch

    start_time = time.time()

    #Saving image
    smart_utils.draw_nmr(input_filename, output_result_nmr_image, display_name=nmr_display)

    hsqc = smart_utils.hsqc_to_np(input_filename)
    model = shared_model_data["model"]
    db = shared_model_data["database"]
    with torch.no_grad():
        #Predict Embedding
        embedding = cli.predict_embedding(model, hsqc)

        with open(output_result_embed, "w") as output_embed:
            output_embed.write(json.dumps(embedding.tolist()))

        if perform_db_search:
            #Performing DB Search
            search_results_df = cli.search_database(db, embedding, topk=100)

            #Save all results
            search_results_df.to_csv(output_result_table, index=None)

    return 0

@celery_instance.task()
def smart_classic_size(query_embedding_filename, query_result_table, filterresults=True, mapquery=True):
    db = shared_model_data["database"]
    if query_embedding_filename is None:
        return len(db)
    else:
        total_size = 0 
        if filterresults is True:
            df = pd.read_csv(query_result_table)
            all_db_ids = set(df["DBID"])
            output_list = [entry for entry in db if entry["ID"] in all_db_ids]
            total_size = len(output_list)
        else:
            total_size = len(db)

        #Reading Embedding of Query
        if mapquery is True:
            total_size += 1

        return total_size


@celery_instance.task()
def smart_classic_images(query_image_filename, query_result_table, filterresults=True, mapquery=True):
    db = shared_model_data["database"]
    if filterresults is True:
        df = pd.read_csv(query_result_table)
        all_db_ids = set(df["DBID"])
        structures_list = [entry["SMILES"] for entry in db if entry["ID"] in all_db_ids]
    else:
        structures_list = [entry["SMILES"] for entry in db]

    #TODO: Support structures with Special Query Image

    dimension = smart_utils.draw_structures(structures_list, query_image_filename)

    return dimension

@celery_instance.task()
def smart_classic_embedding(query_embedding_filename, query_result_table, filterresults=True, mapquery=True):
    db = shared_model_data["database"]

    if filterresults is True:
        df = pd.read_csv(query_result_table)
        all_db_ids = set(df["DBID"])
        output_list = ['\t'.join(map(str, entry["Embeddings"])) for entry in db if entry["ID"] in all_db_ids]
    else:
        output_list = ['\t'.join(map(str, entry["Embeddings"])) for entry in db]

    #Reading Embedding of Query
    if mapquery is True:
        embedding = json.loads(open(query_embedding_filename).read())
        output_list.append('\t'.join(map(str, embedding)))

    return "\n".join(output_list)

@celery_instance.task()
def smart_classic_embedding_global(output_filename):
    db = shared_model_data["database"]
    output_list = ['\t'.join(map(str, entry["Embeddings"])) for entry in db]

    with open(output_filename, "w") as out_file:
        out_file.write("\n".join(output_list))

    return 0

@celery_instance.task()
def smart_classic_metadata(query_embedding_filename, query_result_table, filterresults=True, mapquery=True):
    db = shared_model_data["database"]

    if filterresults is True:
        df = pd.read_csv(query_result_table)
        all_db_ids = set(df["DBID"])
        output_list = [entry["Compound_name"].replace("\n", "") for entry in db if entry["ID"] in all_db_ids]
    else:
        output_list = [entry["Compound_name"].replace("\n", "") for entry in db]

    #Reading Embedding of Query
    if mapquery is True:
        output_list.append("Query")

    return "\n".join(output_list)

@celery_instance.task()
def smart_classic_metadata_global(output_filename):
    db = shared_model_data["database"]
    output_list = [entry["Compound_name"].replace("\n", "") for entry in db]

    with open(output_filename, "wb") as out_file:
        out_file.write("\n".join(output_list).encode("ascii", errors="ignore"))

    return 0

# Load the database when the worker starts
worker_init.connect(worker_load_models)
