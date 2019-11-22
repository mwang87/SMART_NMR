from celery import Celery
from celery.signals import worker_init

import os
import json
import requests
import glob
import pandas as pd

#SMART import
import sys
sys.path.insert(0, "SMART_Finder")
import SMART_FPinder

celery_instance = Celery('smart_fp_tasks', backend='redis://smart-redis', broker='redis://smart-redis')


shared_model_data = {}

def worker_load_models(**kwargs):
    print("LOADING", file=sys.stderr)

    #Loading the Model Globally
    DB = SMART_FPinder.load_db(db_folder="/SMART_Finder")
    model, model_mw = SMART_FPinder.load_models(models_folder="/SMART_Finder/models")

    #Creating the dataframes
    metadata_df = pd.read_csv("/SMART_Finder/projection/smart_metadata.tsv", sep="\t", names=["compound"], encoding="ISO-8859–1")
    database_df = pd.DataFrame(DB, columns=["compound", "smiles", "embedding", "mw"])

    shared_model_data["DB"] = DB
    shared_model_data["model"] = model
    shared_model_data["model_mw"] = model_mw
    shared_model_data["metadata_df"] = metadata_df
    shared_model_data["database_df"] = database_df

    return 0


@celery_instance.task()
def smart_fp_run(input_filename, output_result_table, output_result_nmr_image, output_result_fp_pred, mw):
    print("PROCESSING", file=sys.stderr)

    DB = shared_model_data["DB"]
    model = shared_model_data["model"]
    model_mw = shared_model_data["model_mw"]
    metadata_df = shared_model_data["metadata_df"]
    database_df = shared_model_data["database_df"]

    print("SEARCHING", file=sys.stderr)

    SMART_FPinder.search_CSV(input_filename, DB, model, model_mw, output_result_table, output_result_nmr_image, output_result_fp_pred, mw=mw)

    print("DONE", file=sys.stderr)

    return 0

worker_init.connect(worker_load_models)