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
    return redirect(url_for('classic'))
 
from smartfp_tasks import smart_fp_run
from smartclassic_tasks import smart_classic_run, smart_classic_size, smart_classic_embedding, smart_classic_metadata, smart_classic_embedding_global, smart_classic_metadata_global

@app.route('/classic', methods=['GET'])
def classic():
    projector_json_url = "https://cors-anywhere.herokuapp.com/https://{}/embedding_json_classic_global".format(os.getenv("VIRTUAL_HOST"))
    projector_json_url = urllib.parse.quote(projector_json_url)
    response = make_response(render_template('smartclassic.html', projector_json_url=projector_json_url))
    return response

@app.route('/analyzeuploadclassic', methods=['POST'])
def upload_1():
    # Saving file on disk
    if 'file' not in request.files:
        return "{}", 400

    request_file = request.files['file']
    task_id = str(uuid.uuid4())
    input_filename = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_input.tsv")
    request_file.save(input_filename)

    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    output_result_nmr_image = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_nmr.png")
    output_result_embed = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_embed.json")

    # Performing calculation
    result = smart_classic_run.delay(input_filename, output_result_table, output_result_nmr_image, output_result_embed, nmr_display=request_file.filename)
    
    while(1):
        if result.ready():
            break
        sleep(3)
    result = result.get()
    
    # task identifier for results
    result_dict = {}
    result_dict["task"] = task_id

    return json.dumps(result_dict)


@app.route('/analyzeentryclassic', methods=['POST'])
def process_entry():
    task_id = str(uuid.uuid4())

    input_filename = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_input.tsv")
    with open(input_filename, "w") as input_file:
        input_file.write(request.values["peaks"])

    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    output_result_nmr_image = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_nmr.png")
    output_result_embed = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_embed.json")

    # Performing calculation
    result = smart_classic_run.delay(input_filename, output_result_table, output_result_nmr_image, output_result_embed)
    
    while(1):
        if result.ready():
            break
        sleep(3)
    result = result.get()
    
    # task identifier for results
    result_dict = {}
    result_dict["task"] = task_id

    return json.dumps(result_dict)


# API to calculate classic embedding, assume input is a list of dicts
@app.route('/api/classic/embed', methods=['POST', 'GET'])
def apiclassicembed():
    task_id = str(uuid.uuid4())
    df = pd.DataFrame(json.loads(request.values["peaks"]))
    
    input_filename = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_input.tsv")
    df.to_csv(input_filename, sep=",", index=False)

    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    output_result_nmr_image = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_nmr.png")
    output_result_embed = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_embed.json")

    # Performing calculation
    result = smart_classic_run.delay(input_filename, None, output_result_nmr_image, output_result_embed, perform_db_search=False)
    
    while(1):
        if result.ready():
            break
        sleep(0.1)
    result = result.get()

    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(output_result_embed))

@app.route('/resultclassic', methods=['GET'])
def resultclassic():
    task_id = request.values["task"]

    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    candidates_df = pd.read_csv(output_result_table)

    projector_json_url = "https://cors-anywhere.herokuapp.com/https://{}/embedding_json_classic/{}".format(os.getenv("VIRTUAL_HOST"), task_id)
    projector_json_url = urllib.parse.quote(projector_json_url)

    embed_metadata_json_url = "https://{}/embedding_json_classic/{}".format(os.getenv("VIRTUAL_HOST"), task_id)

    resultclassictable_url = "https://{}/resultclassictable?task={}".format(os.getenv("VIRTUAL_HOST"), task_id)
    return make_response(render_template('results.html',
        candidates=candidates_df.to_dict(orient="records"), 
        task_id=task_id, projector_json_url=projector_json_url, 
        embed_metadata_json_url=embed_metadata_json_url,
        resultclassictable_url=resultclassictable_url))

@app.route('/resultclassictable', methods=['GET'])
def resultclassictable():
    task_id = request.values["task"]
    output_result_table = task_id + "_table.tsv"
    return send_from_directory(app.config['UPLOAD_FOLDER'], output_result_table)



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


# For Classic Embedder
@app.route('/embedding_json_classic/<task_id>', methods=['GET'])
def embedding_json_classic(task_id):
    output_result_embed = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_embed.json")
    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    size = smart_classic_size.delay(output_result_embed, output_result_table)

    # Calculating the images
    smart_classic_images.delay(output_result_embed, output_result_table)

    show_images = False
    if "images" in request.values:
        show_images = True

    while(1):
        if size.ready():
            break
        sleep(1)
    size = size.get()
    
    SERVER_URL = "https://cors-anywhere.herokuapp.com/https://{}".format(os.getenv("VIRTUAL_HOST"))

    result_dict = {}
    result_dict["embeddings"] = [{
        "tensorName": "SMART Classic Embeddings",
        "tensorShape": [size, 180],
        "tensorPath": SERVER_URL + "/embedding_data_classic/{}".format(task_id),
        "metadataPath": SERVER_URL + "/embedding_metadata_classic/{}".format(task_id),
    }]
    
    return json.dumps(result_dict)

@app.route('/embedding_data_classic/<task_id>', methods=['GET'])
def embedding_data_classic(task_id):
    output_result_embed = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_embed.json")
    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")

    embedding_string = smart_classic_embedding.delay(output_result_embed, output_result_table)

    while(1):
        if embedding_string.ready():
            break
        sleep(1)
    embedding_string = embedding_string.get()
    
    return embedding_string


@app.route('/embedding_metadata_classic/<task_id>', methods=['GET'])
def embedding_metadata_classic(task_id):
    output_result_embed = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_embed.json")
    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    
    metadata_string = smart_classic_metadata.delay(output_result_embed, output_result_table)

    while(1):
        if metadata_string.ready():
            break
        sleep(1)
    metadata_string = metadata_string.get()
    
    return metadata_string


# For Classic Global Embedder
@app.route('/embedding_json_classic_global', methods=['GET'])
def embedding_json_classic_global():
    size = smart_classic_size.delay(None, None)

    while(1):
        if size.ready():
            break
        sleep(1)
    size = size.get()
    
    SERVER_URL = "https://cors-anywhere.herokuapp.com/https://{}".format(os.getenv("VIRTUAL_HOST"))

    result_dict = {}
    result_dict["embeddings"] = [{
        "tensorName": "SMART Classic Embeddings",
        "tensorShape": [size, 180],
        "tensorPath": SERVER_URL + "/embedding_data_classic_global",
        "metadataPath": SERVER_URL + "/embedding_metadata_classic_global",
    }]
    
    return json.dumps(result_dict)

@app.route('/embedding_data_classic_global', methods=['GET'])
def embedding_data_classic_global():
    output_result_embed = os.path.join(app.config['UPLOAD_FOLDER'], "global_embed.txt")

    if os.path.isfile(output_result_embed) is False:
        embedding_string = smart_classic_embedding_global.delay(output_result_embed)

        while(1):
            if embedding_string.ready():
                break
            sleep(1)

    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(output_result_embed))


@app.route('/embedding_metadata_classic_global', methods=['GET'])
def embedding_metadata_classic_global():
    output_result_metadata = os.path.join(app.config['UPLOAD_FOLDER'], "global_metadata.txt")

    if os.path.isfile(output_result_metadata) is False:
        embedding_string = smart_classic_metadata_global.delay(output_result_metadata)

        while(1):
            if embedding_string.ready():
                break
            sleep(1)

    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(output_result_metadata))
