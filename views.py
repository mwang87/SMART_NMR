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
DB, model, model_mw = SMART_FPinder.load_models(db_folder="/SMART_Finder", models_folder="/SMART_Finder/models")

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return "{}"

@app.route('/', methods=['GET'])
def homepage():
    response = make_response(render_template('homepage.html'))
    return response

@app.route('/analyzeupload', methods=['POST'])
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

    # Performing calculation
    SMART_FPinder.search_CSV(input_filename, DB, model, model_mw, output_result_table, output_result_nmr_image, "/dev/null")

    # task identifier for results
    result_dict = {}
    result_dict["task"] = task_id

    return json.dumps(result_dict)


@app.route('/analyzeentry', methods=['POST'])
def process_entry():
    print(request.values)

    task_id = str(uuid.uuid4())

    input_filename = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_input.tsv")
    with open(input_filename, "w") as input_file:
        input_file.write(request.values["peaks"])

    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    output_result_nmr_image = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_nmr.png")

    # Performing calculation
    SMART_FPinder.search_CSV(input_filename, DB, model, model_mw, output_result_table, output_result_nmr_image, "/dev/null")

    # task identifier for results
    result_dict = {}
    result_dict["task"] = task_id

    return json.dumps(result_dict)


@app.route('/result', methods=['GET'])
def result():
    task_id = request.values["task"]

    output_result_table = os.path.join(app.config['UPLOAD_FOLDER'], task_id + "_table.tsv")
    candidates_df = pd.read_csv(output_result_table)

    return make_response(render_template('results.html', candidates=candidates_df.to_dict(orient="records"), task_id=task_id))

@app.route('/result_nmr', methods=['GET'])
def result_nmr():
    task_id = request.values["task"]
    output_result_nmr_image = task_id + "_nmr.png"
    return send_from_directory(app.config['UPLOAD_FOLDER'], output_result_nmr_image)