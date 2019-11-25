# views.py
from flask import abort, jsonify, render_template, request, redirect, url_for, make_response, send_from_directory
import uuid

from app import app
import os
import glob
import json
import requests
import pandas as pd
import requests_cache
import urllib.parse
from time import sleep

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return "{}"

@app.route('/', methods=['GET'])
def homepage():
    response = make_response(render_template('homepage.html'))
    return response

from smartfp_tasks import smart_fp_run

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
    output_result_fp_pred = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_fp_pred.json")

    # Performing calculation
    result = smart_fp_run.delay(input_filename, output_result_table, output_result_nmr_image, output_result_fp_pred, mw)
    
    while(1):
        if result.ready():
            break
        sleep(3)
    result = result.get()
    
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
    output_result_fp_pred = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_fp_pred.json")

    # Performing calculation
    #SMART_FPinder.search_CSV(input_filename, DB, model, model_mw, output_result_table, output_result_nmr_image, output_result_fp_pred, mw=mw)

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
EMBED_DIMENSIONS = 2048
EMBED_LENGTH = 2000

def set_to_vector(set_object, dim=2048):
    vector = [0] * dim

    for index in set_object:
        vector[index] = 1

    return vector

@app.route('/embedding_json/<task_id>', methods=['GET'])
def embedding_json(task_id):
    #Slow Filtering
    all_compounds = set(metadata_df["compound"])
    output_records = []
    for record in database_df.to_dict(orient="records"):
        if record["compound"] in all_compounds:
            output_records.append(record)

    SERVER_URL = "https://cors-anywhere.herokuapp.com/https://{}".format(os.getenv("VIRTUAL_HOST"))

    result_dict = {}
    result_dict["embeddings"] = [{
        "tensorName": "SMART Embeddings",
        "tensorShape": [len(output_records) + 1, EMBED_DIMENSIONS],
        "tensorPath": SERVER_URL + "/embedding_data/{}".format(task_id),
        "metadataPath": SERVER_URL + "/embedding_metadata/{}".format(task_id),
    }]
    
    return json.dumps(result_dict)

@app.route('/embedding_data/<task_id>', methods=['GET'])
def embedding_data(task_id):
    #Slow Filtering
    all_compounds = set(metadata_df["compound"])
    output_records = []
    output_embedding = []
    for record in database_df.to_dict(orient="records"):
        if record["compound"] in all_compounds:
            output_records.append(record)
            vector = set_to_vector(record["embedding"])
            vector = [str(x) for x in vector]
            output_embedding.append(vector)

    output_result_fp_pred = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_fp_pred.json")
    query_vector = json.loads(open(output_result_fp_pred, "r").read())[0]
    query_vector = [str(x) for x in query_vector]
    output_embedding.append(vector)

    print(len(output_embedding), file=sys.stderr)

    return "\n".join(["\t".join(vector) for vector in output_embedding])

@app.route('/embedding_metadata/<task_id>', methods=['GET'])
def embedding_metadata(task_id):
    #Slow Filtering
    all_compounds = set(metadata_df["compound"])
    output_metadata = []
    for record in database_df.to_dict(orient="records"):
        if record["compound"] in all_compounds:
            output_dict = {}
            output_dict["compound"] = record["compound"]
            output_dict["type"] = "db"
            output_dict["smiles"] = record["smiles"]
            output_dict["mw"] = record["mw"]

            # Attempting to do classyfire
            # try:
            #     r = requests.get("https://gnps-structure.ucsd.edu/classyfire?smiles=".format(urllib.parse.quote( record["smiles"])))
            #     output_dict["class"] = r.json()["class"]["name"]
            # except:
            #     print("No Classification", record["smiles"], file=sys.stderr)
            #     raise
                

            output_metadata.append(output_dict)

    output_dict = {}
    output_dict["compound"] = "query"
    output_dict["type"] = "query"
    output_metadata.append(output_dict)

    metadata_output_df = pd.DataFrame(output_metadata)

    
    return metadata_output_df.to_csv(sep="\t", index=False)

    