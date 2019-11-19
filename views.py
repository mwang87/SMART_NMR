# views.py
from flask import abort, jsonify, render_template, request, redirect, url_for, make_response, send_from_directory
import uuid

from app import app
import os
import glob
import json
import requests
import pandas as pd
import urllib.parse

#SMART import
import sys
sys.path.insert(0, "SMART_Finder")
import SMART_FPinder

#Loading the Model Globally
DB = SMART_FPinder.load_db(db_folder="/SMART_Finder")
#model, model_mw = SMART_FPinder.load_models(models_folder="/SMART_Finder/models")

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return "{}"

@app.route('/', methods=['GET'])
def homepage():
    print(request.environ.get('HTTP_X_REAL_IP', request.remote_addr), file=sys.stderr)
    response = make_response(render_template('homepage.html'))
    return response

@app.route('/analyzeupload', methods=['POST'])
def upload_1():
    mw = request.values.get("mw", None)
    try:
        mw = float(mw)
    except:
        mw = None
    
    # Saving file on disk
    if 'file' not in request.files:
        return "{}", 400

    request_file = request.files['file']
    task_id = str(uuid.uuid4())
    input_filename = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_input.tsv")
    request_file.save(input_filename)

    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    output_result_nmr_image = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_nmr.png")

    # Performing calculation
    SMART_FPinder.search_CSV(input_filename, DB, model, model_mw, output_result_table, output_result_nmr_image, "/dev/null", mw=mw)

    # task identifier for results
    result_dict = {}
    result_dict["task"] = task_id

    return json.dumps(result_dict)


@app.route('/analyzeentry', methods=['POST'])
def process_entry():
    mw = request.values.get("mw", None)
    try:
        mw = float(mw)
    except:
        mw = None

    task_id = str(uuid.uuid4())

    input_filename = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_input.tsv")
    with open(input_filename, "w") as input_file:
        input_file.write(request.values["peaks"])

    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    output_result_nmr_image = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_nmr.png")

    # Performing calculation
    SMART_FPinder.search_CSV(input_filename, DB, model, model_mw, output_result_table, output_result_nmr_image, "/dev/null", mw=mw)

    # task identifier for results
    result_dict = {}
    result_dict["task"] = task_id

    return json.dumps(result_dict)


@app.route('/result', methods=['GET'])
def result():
    task_id = request.values["task"]

    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    candidates_df = pd.read_csv(output_result_table)

    projector_json_url = "https://cors-anywhere.herokuapp.com/https://{}/embedding_json/{}".format(os.getenv("VIRTUAL_HOST"), task_id)
    projector_json_url = urllib.parse.quote(projector_json_url)

    return make_response(render_template('results.html', candidates=candidates_df.to_dict(orient="records"), task_id=task_id, projector_json_url=projector_json_url))

@app.route('/result_nmr', methods=['GET'])
def result_nmr():
    task_id = request.values["task"]
    output_result_nmr_image = task_id + "_nmr.png"
    return send_from_directory(app.config['UPLOAD_FOLDER'], output_result_nmr_image)


#Embedding end points
EMBED_DIMENSIONS = 180
EMBED_LENGTH = 2019


@app.route('/embedding_json/<task_id>', methods=['GET'])
def embedding_json(task_id):
    print(DB.shape, file=sys.stderr)
    print(DB[0], file=sys.stderr)

    SERVER_URL = "https://cors-anywhere.herokuapp.com/https://{}".format(os.getenv("VIRTUAL_HOST"))

    result_dict = {}
    result_dict["embeddings"] = [{
        "tensorName": "SMART Embeddings",
        "tensorShape": [EMBED_LENGTH, EMBED_DIMENSIONS],
        "tensorPath": SERVER_URL + "/embedding_data/{}".format(task_id),
        "metadataPath": SERVER_URL + "/embedding_metadata/{}".format(task_id),
    }]
    
    return json.dumps(result_dict)

@app.route('/embedding_data/<task_id>', methods=['GET'])
def embedding_data(task_id):
    return send_from_directory("/SMART_Finder/projection/", "smart_embedding.tsv")

@app.route('/embedding_metadata/<task_id>', methods=['GET'])
def embedding_metadata(task_id):
    return send_from_directory("/SMART_Finder/projection/", "smart_metadata.tsv")